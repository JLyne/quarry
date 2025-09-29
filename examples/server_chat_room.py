"""
Example "chat room" server

This server authenticates players, then spawns them in an empty world and does
the bare minimum to keep them in-game. Players can speak to each other using
chat.

No attempt is made to handle signed chat messages. Clients will receive
system messages instead. See server_chat_room_advanced.py for an implementation
which does handle signed chat.
"""

from twisted.internet import reactor
from quarry.net.server import ServerFactory, ServerProtocol
from quarry.types.uuid import UUID


class ChatRoomProtocol(ServerProtocol):
    def player_joined(self):
        # Call super. This switches us to "play" mode, marks the player as
        #   in-game, and does some logging.
        ServerProtocol.player_joined(self)

        # Build up fields for "Join Game" packet
        entity_id = self.buff_type.pack("i", 830)
        max_players = self.buff_type.pack_varint(20)
        hashed_seed = self.buff_type.pack("q", 3072375911354491907)
        view_distance = self.buff_type.pack_varint(10)
        simulation_distance = self.buff_type.pack_varint(10)
        game_mode = self.buff_type.pack("B", 0)
        prev_game_mode = self.buff_type.pack("b", -1)
        is_hardcore = self.buff_type.pack("?", False)
        is_respawn_screen = self.buff_type.pack("?", True)
        is_reduced_debug = self.buff_type.pack("?", False)
        is_debug = self.buff_type.pack("?", False)
        is_flat = self.buff_type.pack("?", False)
        is_limited_crafting = self.buff_type.pack("?", False)
        portal_cooldown = self.buff_type.pack_varint(0)
        sea_level = self.buff_type.pack_varint(0)

        dimension_count = self.buff_type.pack_varint(1)
        dimension_name = self.buff_type.pack_string("minecraft:overworld")
        dimension_type = "minecraft:overworld"


        join_game = [
            entity_id,
            is_hardcore
        ]

        join_game.append(dimension_count)
        join_game.append(dimension_name)

        join_game.append(max_players)
        join_game.append(view_distance),
        join_game.append(simulation_distance)

        join_game.append(is_reduced_debug)
        join_game.append(is_respawn_screen)

        join_game.append(is_limited_crafting)

        if self.protocol_version >= 766:  # 1.20.5+ Dimension type is now varint id
            join_game.append(self.buff_type.pack_varint(0))
        else:
            join_game.append(self.buff_type.pack_string(dimension_type))

        join_game.append(dimension_name)
        join_game.append(hashed_seed)
        join_game.append(game_mode)
        join_game.append(prev_game_mode)

        join_game.append(is_debug)
        join_game.append(is_flat)

        # Optional last death location
        join_game.append(self.buff_type.pack("?", False))

        # Portal cooldown
        join_game.append(portal_cooldown)

        if self.protocol_version >= 768: # 1.21.2+ sea level
            join_game.append(sea_level)

        if self.protocol_version >= 766:  # 1.20.5 disable secure chat
            join_game.append(self.buff_type.pack("?", False))

        # Send "Join Game" packet
        self.send_packet("login", *join_game)

        # Send default spawn position, required to hide Loading Terrain screen
        if self.protocol_version > 772: # 1.21.9+
            self.send_packet("set_default_spawn_position",
                             self.buff_type.pack_global_position("minecraft:overworld", 0, 0, 0) # Now global position
                             + self.buff_type.pack('ff', 0, 0)) # Added pitch
        else:
            self.send_packet("set_default_spawn_position", self.buff_type.pack_position(0, 0, 0)
                             + self.buff_type.pack('f', 0))

        # Send game event so client loads chunks
        self.send_packet("game_event", self.buff_type.pack("Bf", 13, 0.0))


        # Send "Player Position and Look" packet
        player_position_data = [
            self.buff_type.pack("dddff?",
                0,                         # x
                500,                       # y  Must be >= build height to pass the "Loading Terrain" screen
                0,                         # z
                0,                         # yaw
                0,                         # pitch
                0b00000),                  # flags
            self.buff_type.pack_varint(0)  # teleport id
        ]

        self.send_packet("player_position", *player_position_data)

        # Start sending "Keep Alive" packets
        self.ticker.add_loop(20, self.update_keep_alive)

        # Announce player joined
        self.factory.send_chat("\u00a7e%s has joined." % self.display_name)

    def player_left(self):
        ServerProtocol.player_left(self)

        # Announce player left
        self.factory.send_chat("\u00a7e%s has left." % self.display_name)

    def update_keep_alive(self):
        # Send a "Keep Alive" packet
        self.send_packet("keep_alive", self.buff_type.pack('Q', 0))

    def packet_chat(self, buff):
        # When we receive a chat message from the player, ask the factory
        # to relay it to all connected players
        p_text = buff.unpack_string()
        self.factory.send_chat("<%s> %s" % (self.display_name, p_text),
                               sender=self.uuid)

        print("<%s> %s" % (self.display_name, p_text))

        buff.discard()


class ChatRoomFactory(ServerFactory):
    protocol = ChatRoomProtocol
    motd = "Chat Room Server"

    def send_chat(self, message, sender=None):
        if sender is None:
            sender = UUID(int=0)

        for player in self.players:
            if not player.in_game:
                continue

            # Use system message packet to avoid dealing with signatures
            player.send_packet("system_chat",
                               player.buff_type.pack_chat(message),
                               player.buff_type.pack('?', False))


def main(argv):
    # Parse options
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--host", default="", help="address to listen on")
    parser.add_argument("-p", "--port", default=25565, type=int, help="port to listen on")
    parser.add_argument("--offline", action="store_true", help="offline server")
    args = parser.parse_args(argv)

    # Create factory
    factory = ChatRoomFactory()

    factory.online_mode = not args.offline

    # Listen
    factory.listen(args.host, args.port)
    reactor.run()


if __name__ == "__main__":
    import sys
    main(sys.argv[1:])
