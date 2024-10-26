"""
Player lister example client

This client requires a Mojang account for online-mode servers. It logs in to
the server and prints the players listed in the tab menu.
"""

from twisted.internet import reactor, defer
from quarry.net.client import ClientFactory, ClientProtocol
from quarry.net.auth import ProfileCLI


class PlayerListProtocol(ClientProtocol):
    def setup(self):
        self.players = {}

    def packet_player_info_update(self, buff):
        self.parse_old_packet(buff) if self.protocol_version < 767 else self.parse_new_packet(buff)

    def parse_new_packet(self, buff):
        p_actions = buff.unpack('b')
        p_count = buff.unpack_varint()

        for i in range(p_count):
            p_uuid = buff.unpack_uuid()

            if p_actions & 1:  # ADD_PLAYER
                p_player_name = buff.unpack_string()
                p_properties_count = buff.unpack_varint()
                p_properties = {}
                for j in range(p_properties_count):
                    p_property_name = buff.unpack_string()
                    p_property_value = buff.unpack_string()
                    p_property_is_signed = buff.unpack('?')
                    if p_property_is_signed:
                        p_property_signature = buff.unpack_string()

                    p_properties[p_property_name] = p_property_value

                self.players[p_uuid] = {
                    'name': p_player_name,
                    'properties': p_properties
                }

            if p_actions & 2:  # INITIALIZE_CHAT
                if(buff.unpack('?')): # Has signature data
                    buff.unpack_uuid() # Chat session id
                    buff.unpack('q') # Expiry time
                    public_key_length = buff.unpack_varint()
                    buff.read(public_key_length) # Public key
                    public_key_signature_length = buff.unpack_varint()
                    buff.read(public_key_signature_length) # Public key signature

            if p_actions & 4:  # UPDATE_GAMEMODE
                p_gamemode = buff.unpack_varint()

                if p_uuid in self.players:
                    self.players[p_uuid]['gamemode'] = p_gamemode

            if p_actions & 8:  # UPDATE_LISTED
                p_listed = buff.unpack('?')

                if p_uuid in self.players:
                    self.players[p_uuid]['listed'] = p_listed

            if p_actions & 16:  # UPDATE_LATENCY
                p_ping = buff.unpack_varint()

                if p_uuid in self.players:
                    self.players[p_uuid]['ping'] = p_ping

            if p_actions & 32:  # UPDATE_DISPLAY_NAME
                p_has_display_name = buff.unpack('?')
                if p_has_display_name:
                    p_display_name = buff.unpack_chat()
                else:
                    p_display_name = None

                if p_uuid in self.players:
                    self.players[p_uuid]['display_name'] = p_display_name

            if p_actions & 64:  # UPDATE_LIST_ORDER
                p_order = buff.unpack_varint()

                if p_uuid in self.players:
                    self.players[p_uuid]['order'] = p_order

    def parse_old_packet(self, buff):
        p_action = buff.unpack_varint()
        p_count = buff.unpack_varint()
        for i in range(p_count):
            p_uuid = buff.unpack_uuid()
            if p_action == 0:  # ADD_PLAYER
                p_player_name = buff.unpack_string()
                p_properties_count = buff.unpack_varint()
                p_properties = {}
                for j in range(p_properties_count):
                    p_property_name = buff.unpack_string()
                    p_property_value = buff.unpack_string()
                    p_property_is_signed = buff.unpack('?')
                    if p_property_is_signed:
                        p_property_signature = buff.unpack_string()

                    p_properties[p_property_name] = p_property_value
                p_gamemode = buff.unpack_varint()
                p_ping = buff.unpack_varint()
                p_has_display_name = buff.unpack('?')
                if p_has_display_name:
                    p_display_name = buff.unpack_chat()
                else:
                    p_display_name = None

                if buff.unpack('?'):
                    timestamp = buff.unpack("Q")
                    key_length = buff.unpack_varint()
                    key_bytes = buff.read(key_length)
                    signature_length = buff.unpack_varint()
                    signature = buff.read(signature_length)

                self.players[p_uuid] = {
                    'name': p_player_name,
                    'properties': p_properties,
                    'gamemode': p_gamemode,
                    'ping': p_ping,
                    'display_name': p_display_name
                }

            elif p_action == 1:  # UPDATE_GAMEMODE
                p_gamemode = buff.unpack_varint()

                if p_uuid in self.players:
                    self.players[p_uuid]['gamemode'] = p_gamemode
            elif p_action == 2:  # UPDATE_LATENCY
                p_ping = buff.unpack_varint()

                if p_uuid in self.players:
                    self.players[p_uuid]['ping'] = p_ping
            elif p_action == 3:  # UPDATE_DISPLAY_NAME
                p_has_display_name = buff.unpack('?')
                if p_has_display_name:
                    p_display_name = buff.unpack_chat()
                else:
                    p_display_name = None

                if p_uuid in self.players:
                    self.players[p_uuid]['display_name'] = p_display_name
            elif p_action == 4:  # REMOVE_PLAYER
                if p_uuid in self.players:
                    del self.players[p_uuid]

    def packet_level_chunk_with_light(self, buff):
        buff.discard()

        # convert self.players into a more readable format
        printable_players = []
        for data in self.players.values():
            if data['listed']:
                printable_players.append((data['name'], data['ping']))

        for display_name, ping in sorted(printable_players):
            self.logger.info("%4sms %s" % (ping, display_name))

        reactor.stop()


class PlayerListFactory(ClientFactory):
    protocol = PlayerListProtocol


@defer.inlineCallbacks
def run(args):
    # Log in
    profile = yield ProfileCLI.make_profile(args)

    # Create factory
    factory = PlayerListFactory(profile)

    # Connect!
    factory.connect(args.host, args.port)


def main(argv):
    parser = ProfileCLI.make_parser()
    parser.add_argument("host")
    parser.add_argument("-p", "--port", default=25565, type=int)
    args = parser.parse_args(argv)

    run(args)
    reactor.run()


if __name__ == "__main__":
    import sys
    main(sys.argv[1:])