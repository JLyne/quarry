from enum import Enum

from twisted.internet import reactor, protocol, defer
from twisted.python import failure

from quarry.types.chat import Message
from quarry.net.protocol import Factory, Protocol, ProtocolError, ClientIntent
from quarry.net import auth, crypto
from quarry.types.namespaced_key import NamespacedKey


class LoginState(Enum):
    CONNECTING = 0
    AUTHORIZING = 1
    ENCRYPTING = 2
    JOINING = 3


class ClientProtocol(Protocol):
    """This class represents a connection to a server"""

    recv_direction = "downstream"
    send_direction = "upstream"

    login_state = LoginState.CONNECTING

    # Convenience functions ---------------------------------------------------
    def send_handshake(self, intent: ClientIntent):
        # Send handshake
        addr = self.transport.connector.getDestination()
        self.send_packet(
            "handshake",
            self.buff_type.pack_varint(self.protocol_version) +
            self.buff_type.pack_string(addr.host) +
            self.buff_type.pack('H', addr.port) +
            self.buff_type.pack_varint(intent.value))

        # Switch buff type
        self.buff_type = self.factory.get_buff_type(self.protocol_version)

        if intent == ClientIntent.STATUS:
            self.switch_protocol_mode("status")
        elif intent == ClientIntent.LOGIN or ClientIntent.TRANSFER:
            self.switch_protocol_mode("login")

    def send_status_request(self):
        self.send_handshake(ClientIntent.STATUS)
        self.send_packet("status_request")

    def send_login_start(self):
        self.send_handshake(ClientIntent.LOGIN)

        # TODO: Implement signature sending
        self.send_packet("login_start",
                         self.buff_type.pack_string(self.factory.profile.display_name),
                         self.buff_type.pack_uuid(self.factory.profile.uuid))

    def enable_encryption(self):
        if self.login_state != LoginState.AUTHORIZING:
            raise ProtocolError(f"Can't switch to {LoginState.ENCRYPTING} from {self.login_state}")

        self.login_state = LoginState.ENCRYPTING

        # Send encryption response
        p_shared_secret = crypto.encrypt_secret(
            self.public_key,
            self.shared_secret)
        p_verify_token = crypto.encrypt_secret(
            self.public_key,
            self.verify_token)

        pack_array = lambda d: self.buff_type.pack_varint(len(d), max_bits=16) + d

        self.send_packet(
            "login_encryption_response",
            pack_array(p_shared_secret) +
            pack_array(p_verify_token))

        # Enable encryption
        self.cipher.enable(self.shared_secret)
        self.logger.debug("Encryption enabled")

    # Callbacks ---------------------------------------------------------------

    @defer.inlineCallbacks
    def connection_made(self):
        """Called when the connection is established"""
        super(ClientProtocol, self).connection_made()

        # Determine protocol version
        if self.factory.protocol_mode_next == "status":
            self.send_status_request()
            return
        elif self.factory.force_protocol_version is not None:
            self.protocol_version = self.factory.force_protocol_version
        else:
            factory = PingClientFactory()
            factory.connect(self.remote_addr.host, self.remote_addr.port)
            self.protocol_version = yield factory.detected_protocol_version

        self.send_login_start()

    def auth_ok(self, data):
        """
        Called if the Mojang session server responds to our query. Note that
        this method does not indicate that the server accepted our session; in
        this case :meth:`player_joined` is called.
        """
        self.enable_encryption()

    def player_joined(self):
        """
        Called when we join the game. If the server is in online mode, this
        means the server accepted our session.
        """
        Protocol.player_joined(self)
        self.logger.info("Joined the game.")

    def player_left(self):
        """Called when we leave the game."""
        Protocol.player_left(self)
        self.logger.info("Left the game.")

    def status_response(self, data):
        """
        If we're connecting in "status" mode, this is called when the server
        sends us information about itself.
        """
        self.close()

    # Packet handlers ---------------------------------------------------------

    def packet_status_response(self, buff):
        p_data = buff.unpack_json()
        self.status_response(p_data)

    def packet_login_plugin_request(self, buff):
        p_message_id = buff.unpack_varint()
        p_channel = buff.unpack_string()
        p_payload = buff.read()

        self.send_packet(
            "login_plugin_response",
            self.buff_type.pack_varint(p_message_id),
            self.buff_type.pack('?', False))

    def packet_login_disconnect(self, buff):
        p_data = buff.unpack_chat_string()

        self.logger.warn("Kicked: %s" % p_data)
        self.close()

    def packet_login_encryption_request(self, buff):
        if self.login_state != LoginState.CONNECTING:
            raise ProtocolError(f"Can't switch to {LoginState.AUTHORIZING} from {self.login_state}")

        self.login_state = LoginState.AUTHORIZING

        p_server_id = buff.unpack_string()

        unpack_array = lambda b: b.read(b.unpack_varint(max_bits=16))

        p_public_key = unpack_array(buff)
        p_verify_token = unpack_array(buff)
        p_should_auth = buff.unpack_bool()

        if not self.factory.profile.online:
            raise ProtocolError("Can't log into online-mode server while using"
                                " offline profile")

        self.shared_secret = crypto.make_shared_secret()
        self.public_key = crypto.import_public_key(p_public_key)
        self.verify_token = p_verify_token

        # make digest
        digest = crypto.make_digest(
            p_server_id.encode('ascii'),
            self.shared_secret,
            p_public_key)

        # do auth
        if p_should_auth:
            deferred = self.factory.profile.join(digest)
            deferred.addCallbacks(self.auth_ok, self.auth_failed)
        else:
            self.enable_encryption()

    def packet_login_success(self, buff):
        if self.login_state != LoginState.AUTHORIZING and self.login_state != LoginState.ENCRYPTING:
            raise ProtocolError(f"Can't switch to {LoginState.JOINING} from {self.login_state}")

        self.login_state = LoginState.JOINING

        p_uuid = buff.unpack_uuid()
        p_display_name = buff.unpack_string()

        buff.read()  # Properties

        # Go to configuration mode
        self.send_packet("login_acknowledged")
        self.start_configuration()

    def packet_login_set_compression(self, buff):
        self.set_compression(buff.unpack_varint())

    def packet_set_compression(self, buff):
        self.set_compression(buff.unpack_varint())

    # 1.20.5+ negotiate data packs
    def packet_select_known_packs(self, buff):
        server_packs = []

        # Get server packs
        for i in range(buff.unpack_varint()):
            pack_id = NamespacedKey(buff.unpack_string(), buff.unpack_string())
            version = buff.unpack_string()

            server_packs.append((pack_id, version))

        # Remove client packs the server isn't using
        for pack in self.data_packs.get_packs():
            if (pack.id, pack.version) not in server_packs:
                print(f"Removing unused pack {pack.id}")
                self.data_packs.remove_data_pack(pack.id)

        self.send_known_data_packs()

    # Go to play mode
    def packet_finish_configuration(self, buff):
        self.data_packs.lock()
        self.send_packet("finish_configuration")
        self.switch_protocol_mode("play")
        self.player_joined()

        buff.discard()

    packet_disconnect = packet_login_disconnect


class SpawningClientProtocol(ClientProtocol):
    spawned = False

    def __init__(self, factory, remote_addr):
        # x, y, z, yaw, pitch
        self.pos_look = [0, 0, 0, 0, 0]

        super(SpawningClientProtocol, self).__init__(factory, remote_addr)

    # Send a 'player' packet every tick
    def update_player_inc(self):
        self.send_packet("player", self.buff_type.pack('?', True))

    # Sent a 'player position and look' packet every 20 ticks
    def update_player_full(self):
        self.send_packet(
            "player_position_and_look",
            self.buff_type.pack(
                'dddff?',
                self.pos_look[0],
                self.pos_look[1],
                self.pos_look[2],
                self.pos_look[3],
                self.pos_look[4],
                True))

    def packet_player_position_and_look(self, buff):
        p_pos_look = buff.unpack('dddff')

        p_flags = buff.unpack('B')

        for i in range(5):
            if p_flags & (1 << i):
                self.pos_look[i] += p_pos_look[i]
            else:
                self.pos_look[i] = p_pos_look[i]

        teleport_id = buff.unpack_varint()

        # Send Player Position And Look
        self.send_packet("teleport_confirm",
                         self.buff_type.pack_varint(teleport_id))

        if not self.spawned:
            self.spawn()

    def spawn(self):
        self.ticker.add_loop(1, self.update_player_inc)
        self.ticker.add_loop(20, self.update_player_full)
        self.spawned = True

    def packet_keep_alive(self, buff):
        self.send_packet('keep_alive', buff.read())


class ClientFactory(Factory, protocol.ClientFactory):
    protocol = ClientProtocol
    protocol_mode_next = "login"

    def __init__(self, profile=None):
        if profile is None:
            profile = auth.OfflineProfile()
        self.profile = profile

    def connect(self, host, port=25565):
        reactor.connectTCP(host, port, self, self.connection_timeout)


class PingClientProtocol(ClientProtocol):

    def status_response(self, data):
        self.close()
        detected_version = int(data["version"]["protocol"])
        if detected_version in self.factory.minecraft_versions:
            self.factory.detected_protocol_version.callback(detected_version)
        else:
            message = "Unsupported protocol version (%d)" % detected_version
            if 'description' in data:
                motd = Message(data['description'])
                message = "%s: %s" % (message, motd.to_string())
            self.factory.detected_protocol_version.errback(
                failure.Failure(ProtocolError(message)))


class PingClientFactory(ClientFactory):
    protocol = PingClientProtocol
    protocol_mode_next = "status"

    def __init__(self, profile=None):
        super(PingClientFactory, self).__init__(profile)
        self.detected_protocol_version = defer.Deferred()
