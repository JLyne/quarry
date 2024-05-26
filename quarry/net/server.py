import base64
import hmac
import random
from copy import deepcopy
from typing import List, Tuple

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.padding import PKCS1v15
from cryptography.hazmat.primitives.hashes import SHA256
from twisted.internet import reactor
from cached_property import cached_property

from quarry.data.data_packs import vanilla_data_packs, configuration_registries
from quarry.net.auth import PlayerPublicKey
from quarry.net.protocol import Factory, Protocol, ProtocolError, \
    protocol_modes
from quarry.net import auth, crypto
from quarry.types.namespaced_key import NamespacedKey
from quarry.types.nbt import TagRoot
from quarry.types.uuid import UUID


class ServerProtocol(Protocol):
    """This class represents a connection with a client"""

    recv_direction = "upstream"
    send_direction = "downstream"

    uuid = None
    display_name = None
    display_name_confirmed = False
    public_key_data: PlayerPublicKey = None

    # the hostname/port that the client claims it connected to. Useful for
    # implementing virtual hosting.
    connect_host = None
    connect_port = None

    # used to stop people breaking the login process
    # by sending packets out-of-order or duplicated
    login_expecting = 0

    def __init__(self, factory, remote_addr):
        Protocol.__init__(self, factory, remote_addr)
        self.server_id = crypto.make_server_id()
        self.verify_token = crypto.make_verify_token()
        self.velocity_message_id = random.randint(0, 2147483647)

    # Convenience functions ---------------------------------------------------
    def send_login_success(self):
        if self.factory.compression_threshold:
            # Send set compression
            self.send_packet(
                "login_set_compression",
                self.buff_type.pack_varint(
                    self.factory.compression_threshold))
            self.set_compression(self.factory.compression_threshold)

        if self.protocol_version >= 766:  # 1.20.5+
            self.send_packet(
                "login_success",
                self.buff_type.pack_uuid(self.uuid) +
                self.buff_type.pack_string(self.display_name) +
                self.buff_type.pack_varint(0) +
                self.buff_type.pack('?', True))  # strict error handling?
        else:
            self.send_packet(
                "login_success",
                self.buff_type.pack_uuid(self.uuid) +
                self.buff_type.pack_string(self.display_name) +
                self.buff_type.pack_varint(0))  # Profile properties

    def close(self, reason=None):
        """Closes the connection"""
        if not self.closed and reason is not None:
            # Kick the player if possible.
            if self.protocol_mode == "play":
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
            self.send_packet("finish_configuration")  # Tell client to leave configuration mode
        else:
            self.send_known_data_packs()

    def send_registries(self, exclude: List[Tuple[NamespacedKey, str]]):
        if self.protocol_version < 766:  # <1.20.5 sends all registries at once
            pack = vanilla_data_packs[self.protocol_version]
            # FIXME: Ignores other data packs currently
            self.send_packet("registry_data", self.buff_type.pack_nbt(TagRoot.from_body(pack.contents)))  # Required to get past Joining World screen

        else:  # 1.20.5+ Each registry is now sent as a separate packet
            for registry in configuration_registries:
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
                        data.append(self.buff_type.pack_nbt(TagRoot.from_body(value)))

                self.send_packet("registry_data", *data)

    # Callbacks ---------------------------------------------------------------

    def connection_lost(self, reason=None):
        """Called when the connection is lost"""
        if self.protocol_mode in ("login", "play"):
            self.factory.players.discard(self)
        Protocol.connection_lost(self, reason)

    def auth_ok(self, data):
        """Called when auth with mojang succeeded (online mode only)"""
        self.display_name_confirmed = True
        self.uuid = UUID.from_hex(data['id'])
        self.send_login_success()

    def player_joined(self):
        """Called when the player joins the game"""
        Protocol.player_joined(self)

        self.logger.info("%s has joined." % self.display_name)

        self.switch_protocol_mode("play")

    def player_left(self):
        """Called when the player leaves the game"""
        Protocol.player_left(self)

        self.logger.info("%s has left." % self.display_name)

    def configuration(self):
        self.complete_configuration()

    # Packet handlers ---------------------------------------------------------

    def packet_handshake(self, buff):
        p_protocol_version = buff.unpack_varint()
        p_connect_host = buff.unpack_string()
        p_connect_port = buff.unpack("H")
        p_protocol_mode = buff.unpack_varint()

        mode = protocol_modes.get(p_protocol_mode, p_protocol_mode)
        self.switch_protocol_mode(mode)

        if mode == "login":
            if self.factory.force_protocol_version is not None:
                if p_protocol_version != self.factory.force_protocol_version:
                    self.close("Wrong protocol version")
            else:
                if p_protocol_version not in self.factory.minecraft_versions:
                    self.close("Unknown protocol version")

            if len(self.factory.players) >= self.factory.max_players:
                self.close("Server is full")
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

    def packet_login_start(self, buff):
        if self.login_expecting != 0:
            raise ProtocolError("Out-of-order login")

        self.display_name = buff.unpack_string()

        if self.factory.online_mode:
            self.login_expecting = 1

            # send encryption request
            pack_array = lambda a: self.buff_type.pack_varint(len(a), max_bits=16) + a

            if self.protocol_version >= 766:  # 1.20.5+
                self.send_packet(
                    "login_encryption_request",
                    self.buff_type.pack_string(self.server_id),
                    pack_array(self.factory.public_key),
                    pack_array(self.verify_token),
                    self.buff_type.pack('?', True))  # Should authenticate
            else:
                self.send_packet(
                    "login_encryption_request",
                    self.buff_type.pack_string(self.server_id),
                    pack_array(self.factory.public_key),
                    pack_array(self.verify_token))

        elif self.factory.velocity_forwarding:
            self.login_expecting = 2
            self.send_packet("login_plugin_request",
                             self.buff_type.pack_varint(self.velocity_message_id),
                             self.buff_type.pack_string("velocity:player_info"),
                             b'')
        else:
            self.login_expecting = None
            self.display_name_confirmed = True
            self.uuid = UUID.from_offline_player(self.display_name)
            self.send_login_success()

        buff.discard()

    def packet_login_plugin_response(self, buff):
        if self.login_expecting != 2 or self.protocol_mode != "login":
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

        self.login_expecting = None
        self.display_name_confirmed = True
        self.send_login_success()

    def packet_login_encryption_response(self, buff):
        if self.login_expecting != 1:
            raise ProtocolError("Out-of-order login")

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

        self.login_expecting = None

        # enable encryption
        self.cipher.enable(shared_secret)
        self.logger.debug("Encryption enabled")

        # make digest
        digest = crypto.make_digest(
            self.server_id.encode('ascii'),
            shared_secret,
            self.factory.public_key)

        # do auth
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
        buff.discard()
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

    def packet_status_ping(self, buff):
        time = buff.unpack("Q")

        # send ping
        self.send_packet("status_pong", self.buff_type.pack("Q", time))
        self.close()


class ServerFactory(Factory):
    protocol = ServerProtocol

    motd = "A Minecraft Server"
    max_players = 20
    icon_path = None
    online_mode = True
    enforce_secure_profile = False
    prevent_proxy_connections = True
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
