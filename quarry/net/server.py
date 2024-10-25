import base64
import hmac
import random
from copy import deepcopy
from enum import Enum
from typing import List, Tuple

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.padding import PKCS1v15
from cryptography.hazmat.primitives.hashes import SHA256
from twisted.internet import reactor
from cached_property import cached_property

from quarry.data.data_packs import configurable_registries
from quarry.net.auth import PlayerPublicKey
from quarry.net.protocol import Factory, Protocol, ProtocolError, ClientIntent
from quarry.net import auth, crypto
from quarry.types.chat import Message
from quarry.types.namespaced_key import NamespacedKey
from quarry.types.nbt import TagRoot
from quarry.types.uuid import UUID


class LoginState(Enum):
    HELLO = 0  # Login not started
    KEY = 1  # Awaiting online mode encryption response
    AUTHENTICATING = 2  # Authenticating user with mojang
    NEGOTIATING = 3  # Waiting for velocity plugin message
    VERIFYING = 4  # Compression etc
    WAITING_FOR_DUPE_DISCONNECT = 5  # Currently unused
    PROTOCOL_SWITCHING = 6  # Waiting for login acknowledgement
    ACCEPTED = 7  # Done


class ServerProtocol(Protocol):
    """This class represents a connection with a client"""

    recv_direction = "upstream"
    send_direction = "downstream"

    uuid = None
    display_name = None
    display_name_confirmed = False
    public_key_data: PlayerPublicKey = None
    transferred = False

    # the hostname/port that the client claims it connected to. Useful for
    # implementing virtual hosting.
    connect_host = None
    connect_port = None

    # used to stop people breaking the login process
    # by sending packets out-of-order or duplicated
    login_state = LoginState.HELLO

    def __init__(self, factory, remote_addr):
        Protocol.__init__(self, factory, remote_addr)
        self.server_id = crypto.make_server_id()
        self.verify_token = crypto.make_verify_token()
        self.velocity_message_id = random.randint(0, 2147483647)

    # Convenience functions ---------------------------------------------------
    def complete_login(self):
        if self.factory.compression_threshold:
            # Send set compression
            self.send_packet(
                "login_compression",
                self.buff_type.pack_varint(
                    self.factory.compression_threshold))
            self.set_compression(self.factory.compression_threshold)

        if self.protocol_version >= 766:  # 1.20.5+
            self.send_packet(
                "game_profile",
                self.buff_type.pack_uuid(self.uuid) +
                self.buff_type.pack_string(self.display_name) +
                self.buff_type.pack_varint(0) +
                self.buff_type.pack('?', True))  # strict error handling?
        else:
            self.send_packet(
                "game_profile",
                self.buff_type.pack_uuid(self.uuid) +
                self.buff_type.pack_string(self.display_name) +
                self.buff_type.pack_varint(0))  # Profile properties

        self.login_state = LoginState.PROTOCOL_SWITCHING

    def close(self, reason=None):
        """Closes the connection"""
        if not self.closed and reason is not None:
            # Kick the player if possible.
            if self.protocol_mode == "game":
                self.send_packet("disconnect", self.buff_type.pack_chat(reason))
                super(ServerProtocol, self).close(reason)
            else:
                if self.protocol_mode == "login":
                    self.send_packet(
                        "login_disconnect",
                        self.buff_type.pack_chat_string(reason))
                Protocol.close(self, reason)
        else:
            Protocol.close(self, reason)

    def start_configuration(self):
        super().start_configuration()
        self.configuration()

    def complete_configuration(self):
        if self.protocol_mode != "configuration":
            raise ProtocolError("Not in configuration mode")

        self.data_packs.lock()

        if self.protocol_version < 766:  # <1.20.5 just sends registries
            self.send_registries([])
            self.send_tags()
            self.send_packet("finish_configuration")  # Tell client to leave configuration mode
        else:
            self.send_known_data_packs()

    def send_registries(self, exclude: List[Tuple[NamespacedKey, str]]):
        if self.protocol_version < 766:  # <1.20.5 sends all registries at once
            self.send_packet("registry_data", self.buff_type.pack_nbt(self.data_packs.get_nbt_codec()))

        else:  # 1.20.5+ Each registry is now sent as a separate packet
            for registry in configurable_registries[self.protocol_version]:
                registry_data = self.data_packs.get_registry(registry, *exclude)

                data = [
                    self.buff_type.pack_string(str(registry)),  # Registry name
                    self.buff_type.pack_varint(len(registry_data))  # Number of items in registry
                ]

                for (key, value) in registry_data.items():
                    data.append(self.buff_type.pack_string(str(key)))  # Item name
                    data.append(self.buff_type.pack('?', value is not None))  # Whether value is present

                    # Value if present
                    if value is not None:
                        data.append(self.buff_type.pack_nbt(TagRoot.from_obj(value)))

                self.send_packet("registry_data", *data)

    def send_tags(self):
        tags = self.data_packs.get_tags()

        if tags is None:
            return

        data = self.buff_type.pack_varint(len(tags))

        for (registry, registry_tags) in tags.items():
            data += self.buff_type.pack_string(str(registry)) + \
                self.buff_type.pack_varint(len(registry_tags))

            for (tag, values) in registry_tags.items():
                data += self.buff_type.pack_string(str(tag)) + \
                    self.buff_type.pack_varint(len(values))

                for value in values:
                    data += self.buff_type.pack_varint(value)

        self.send_packet("update_tags", data)

    # Callbacks ---------------------------------------------------------------

    def connection_lost(self, reason=None):
        """Called when the connection is lost"""
        if self.protocol_mode in ("login", "game"):
            self.factory.players.discard(self)
        Protocol.connection_lost(self, reason)

    def auth_ok(self, data):
        """Called when auth with mojang succeeded (online mode only)"""
        self.display_name_confirmed = True
        self.uuid = UUID.from_hex(data['id'])
        self.complete_login()

    def player_joined(self):
        """Called when the player joins the game"""
        Protocol.player_joined(self)

        self.logger.info("%s has joined." % self.display_name)

        self.switch_protocol_mode("game")

    def player_left(self):
        """Called when the player leaves the game"""
        Protocol.player_left(self)

        self.logger.info("%s has left." % self.display_name)

    def configuration(self):
        self.complete_configuration()

    # Packet handlers ---------------------------------------------------------

    def packet_intention(self, buff):
        p_protocol_version = buff.unpack_varint()
        p_connect_host = buff.unpack_string()
        p_connect_port = buff.unpack("H")

        try:
            p_intent = ClientIntent(buff.unpack_varint())
        except ValueError:
            raise ProtocolError("Unknown connection intent")

        if p_intent == ClientIntent.TRANSFER and not self.factory.accept_transfers:
            self.close(Message({'translate': 'multiplayer.disconnect.transfers_disabled'}))
            return

        if p_intent == ClientIntent.STATUS:
            self.switch_protocol_mode("status")
            return

        if p_intent == ClientIntent.LOGIN or p_intent == ClientIntent.TRANSFER:
            self.switch_protocol_mode("login")
            self.transferred = p_intent == ClientIntent.TRANSFER

            if self.factory.force_protocol_version is not None:
                if p_protocol_version != self.factory.force_protocol_version:
                    self.close("Wrong protocol version")
                    return
            else:
                if p_protocol_version not in self.factory.minecraft_versions:
                    self.close("Unknown protocol version")
                    return

            if len(self.factory.players) >= self.factory.max_players:
                self.close("Server is full")
                return
            else:
                self.factory.players.add(self)

            if self.factory.bungeecord_forwarding is True:
                # Bungeecord ip forwarding, ip/uuid is included in host string separated by \00s
                split_host = str.split(p_connect_host, "\00")

                if len(split_host) < 3:
                    raise ProtocolError("Invalid bungeecord forwarding data")

                self.connect_host = split_host[1]
                self.uuid = UUID.from_hex(split_host[2])

        self.protocol_version = p_protocol_version
        self.buff_type = self.factory.get_buff_type(self.protocol_version)
        self.connect_host = p_connect_host
        self.connect_port = p_connect_port

    def packet_hello(self, buff):
        if self.login_state != LoginState.HELLO:
            raise ProtocolError("Unexpected hello packet")

        self.display_name = buff.unpack_string()

        if self.factory.online_mode:
            self.login_state = LoginState.KEY

            # send encryption request
            pack_array = lambda a: self.buff_type.pack_varint(len(a), max_bits=16) + a

            if self.protocol_version >= 766:  # 1.20.5+
                self.send_packet(
                    "hello",
                    self.buff_type.pack_string(self.server_id),
                    pack_array(self.factory.public_key),
                    pack_array(self.verify_token),
                    self.buff_type.pack('?', True))  # Should authenticate
            else:
                self.send_packet(
                    "hello",
                    self.buff_type.pack_string(self.server_id),
                    pack_array(self.factory.public_key),
                    pack_array(self.verify_token))

        elif self.factory.velocity_forwarding:
            self.login_state = LoginState.NEGOTIATING
            self.send_packet("custom_query",
                             self.buff_type.pack_varint(self.velocity_message_id),
                             self.buff_type.pack_string("velocity:player_info"),
                             b'')
        else:
            self.login_state = LoginState.VERIFYING
            self.display_name_confirmed = True
            self.uuid = UUID.from_offline_player(self.display_name)
            self.complete_login()

        buff.discard()

    def packet_custom_query_answer(self, buff):
        if self.login_state != LoginState.NEGOTIATING:
            raise ProtocolError("Out-of-order login")

        message_id = buff.unpack_varint()
        successful = buff.unpack('b')

        if message_id != self.velocity_message_id:
            raise ProtocolError("Unexpected login_plugin_response")

        if not successful or len(buff) == 0:
            raise ProtocolError("Empty velocity forwarding response")

        # Verify HMAC
        signature = buff.read(32)
        verify = hmac.new(key=str.encode(self.factory.velocity_forwarding_secret), msg=deepcopy(buff).read(),
                          digestmod="sha256").digest()

        if verify != signature:
            raise ProtocolError("Invalid velocity forwarding response received")

        version = buff.unpack_varint()

        if version != 1:
            raise ProtocolError("Unsupported velocity forwarding version")

        buff.unpack_string()  # Ip

        self.uuid = buff.unpack_uuid()
        self.display_name = buff.unpack_string()

        buff.discard()  # Don't care about the rest

        self.login_state = LoginState.VERIFYING
        self.display_name_confirmed = True
        self.complete_login()

    def packet_key(self, buff):
        if self.login_state != LoginState.KEY:
            raise ProtocolError("Unexpected key packet")

        unpack_array = lambda b: b.read(b.unpack_varint(max_bits=16))

        p_shared_secret = unpack_array(buff)
        salt = None

        p_verify_token = unpack_array(buff)

        shared_secret = crypto.decrypt_secret(
            self.factory.keypair,
            p_shared_secret)

        if salt is not None:
            try:
                self.public_key_data.key.verify(p_verify_token, self.verify_token + salt, PKCS1v15(), SHA256())
            except InvalidSignature:
                raise ProtocolError("Verify token incorrect")
        else:
            verify_token = crypto.decrypt_secret(
                self.factory.keypair,
                p_verify_token)

            if verify_token != self.verify_token:
                raise ProtocolError("Verify token incorrect")

        # enable encryption
        self.cipher.enable(shared_secret)
        self.logger.debug("Encryption enabled")

        # make digest
        digest = crypto.make_digest(
            self.server_id.encode('ascii'),
            shared_secret,
            self.factory.public_key)

        # do auth
        self.login_state = LoginState.AUTHENTICATING
        remote_host = None
        if self.factory.prevent_proxy_connections:
            remote_host = self.remote_addr.host
        deferred = auth.has_joined(
            self.factory.auth_timeout,
            digest,
            self.display_name,
            remote_host)
        deferred.addCallbacks(self.auth_ok, self.auth_failed)

    # Entering configuration mode
    def packet_login_acknowledged(self, buff):
        if self.login_state != LoginState.PROTOCOL_SWITCHING:
            raise ProtocolError("Unexpected login acknowledgement packet")

        buff.discard()
        self.login_state = LoginState.ACCEPTED
        self.start_configuration()

    # 1.20.5+ need to negotiate data packs before sending registry data and leaving configuration mode
    def packet_select_known_packs(self, buff):
        client_packs = []

        # Packs listed here should be excluded from registry data
        for i in range(buff.unpack_varint()):
            pack_id = NamespacedKey(buff.unpack_string(), buff.unpack_string())
            version = buff.unpack_string()
            client_packs.append((pack_id, version))

        print(f"Client data packs: {client_packs}")
        buff.discard()

        self.send_registries(client_packs)
        self.send_tags()
        self.send_packet("finish_configuration")  # Tell client to leave configuration mode

    # Leaving configuration mode
    def packet_finish_configuration(self, buff):
        # Go to play mode
        if not self.in_game:
            self.player_joined()

        buff.discard()

    def packet_status_request(self, buff):
        protocol_version = self.factory.force_protocol_version
        if protocol_version is None:
            protocol_version = self.protocol_version

        d = {
            "description": {
                "text":     self.factory.motd
            },
            "players": {
                "online":   len(self.factory.players),
                "max":      self.factory.max_players
            },
            "version": {
                "name":     self.factory.minecraft_versions.get(
                                protocol_version,
                                "???"),
                "protocol": protocol_version
            }
        }
        if self.factory.icon is not None:
            d['favicon'] = self.factory.icon

        # send status response
        self.send_packet("status_response", self.buff_type.pack_json(d))

    def packet_ping_request(self, buff):
        time = buff.unpack("Q")

        # send ping
        self.send_packet("pong_response", self.buff_type.pack("Q", time))
        self.close()


class ServerFactory(Factory):
    protocol = ServerProtocol

    motd = "A Minecraft Server"
    max_players = 20
    icon_path = None
    online_mode = True
    enforce_secure_profile = False
    prevent_proxy_connections = True
    accept_transfers = False
    bungeecord_forwarding = False
    velocity_forwarding = False
    velocity_forwarding_secret = None
    compression_threshold = 256
    auth_timeout = 30
    players = None

    def __init__(self):
        self.players = set()

        self.keypair = crypto.make_keypair()
        self.public_key = crypto.export_public_key(self.keypair)

    def listen(self, host, port=25565):
        if self.bungeecord_forwarding or self.velocity_forwarding:
            self.online_mode = False

        if self.velocity_forwarding and self.velocity_forwarding_secret is None:
            raise TypeError('No velocity forwarding secret provided')

        reactor.listenTCP(port, self, interface=host)

    @cached_property
    def icon(self):
        if self.icon_path is not None:
            with open(self.icon_path, "rb") as fd:
                return "data:image/png;base64," + base64.encodebytes(
                    fd.read()).decode('ascii').replace('\n', '')
