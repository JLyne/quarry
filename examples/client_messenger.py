"""
Messenger example client

Bridges minecraft chat (in/out) with stdout and stdin.

This client makes no attempt to verify received signed messages, or sign sent messages.
"""

import os
import sys
from time import time

from twisted.internet import defer, reactor, stdio
from twisted.protocols import basic
from quarry.net.auth import ProfileCLI
from quarry.net.client import ClientFactory, SpawningClientProtocol


class StdioProtocol(basic.LineReceiver):
    delimiter = os.linesep.encode('ascii')
    in_encoding  = getattr(sys.stdin,  "encoding", 'utf8')
    out_encoding = getattr(sys.stdout, "encoding", 'utf8')

    def lineReceived(self, line):
        self.minecraft_protocol.send_chat(line.decode(self.in_encoding))

    def send_line(self, text):
        self.sendLine(text.encode(self.out_encoding))


class MinecraftProtocol(SpawningClientProtocol):
    spawned = False
    
    def packet_system_chat(self, buff):
        p_text = buff.unpack_chat().to_string()
        # Ignore game info (action bar) messages
        p_display = not buff.unpack('?')  # Boolean for whether message is game info

        buff.discard()

        if p_display and p_text.strip():
            self.stdio_protocol.send_line(":: %s" % p_text)

    def packet_player_chat(self, buff):
        p_signed_message = buff.unpack_signed_message()
        buff.unpack_varint()  # Filter result
        p_position = buff.unpack_varint()
        p_sender_name = buff.unpack_chat()

        buff.discard()

        if p_position not in (1, 2):  # Ignore system and game info messages
            # Sender name is sent separately to the message text
            self.stdio_protocol.send_line(
                ":: <%s> %s" % (p_sender_name, p_signed_message.unsigned_content or p_signed_message.body.message))

    def send_chat(self, text):
        data = [self.buff_type.pack_string(text)]

        data.append(self.buff_type.pack('QQ', int(time() * 1000), 0))   # Current timestamp, empty salt
        data.append(self.buff_type.pack_byte_array(b''))  # Empty signature
        data.append(self.buff_type.pack('?', False))  # Not previewed
        data.append(self.buff_type.pack_last_seen_list([]))  # Add empty last seen list
        data.append(self.buff_type.pack('?', False))  # Don't provide optional last received message

        self.send_packet("chat", *data)


class MinecraftFactory(ClientFactory):
    protocol = MinecraftProtocol
    log_level = "WARN"

    def buildProtocol(self, addr):
        minecraft_protocol = super(MinecraftFactory, self).buildProtocol(addr)
        stdio_protocol = StdioProtocol()

        minecraft_protocol.stdio_protocol = stdio_protocol
        stdio_protocol.minecraft_protocol = minecraft_protocol

        stdio.StandardIO(stdio_protocol)
        return minecraft_protocol


@defer.inlineCallbacks
def run(args):
    # Log in
    profile = yield ProfileCLI.make_profile(args)

    # Create factory
    factory = MinecraftFactory(profile)

    # Connect!
    factory.connect(args.host, args.port)


def main(argv):
    parser = ProfileCLI.make_parser()
    parser.add_argument("host")
    parser.add_argument("port", nargs='?', default=25565, type=int)
    args = parser.parse_args(argv)

    run(args)
    reactor.run()


if __name__ == "__main__":
    main(sys.argv[1:])
