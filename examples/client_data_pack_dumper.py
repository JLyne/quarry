"""
Dumps the data pack info from the "join_game" packet to a file.
"""

from __future__ import print_function
from twisted.internet import reactor, defer
from quarry.types.nbt import NBTFile, alt_repr
from quarry.net.client import ClientFactory, ClientProtocol
from quarry.net.auth import ProfileCLI


class DataPackDumperProtocol(ClientProtocol):
    result = {}

    def packet_registry_data(self, buff):
        if self.protocol_version >= 766:
            registry = buff.unpack_string()
            self.result[registry] = {
                "value": [],
                "type": registry
            }

            for i in range(buff.unpack_varint()):
                name = buff.unpack_string()

                if buff.unpack('?'):
                    self.result[registry]["value"].append({
                        "id": i,
                        "name": name,
                        "element": buff.unpack_nbt().body.to_obj()
                    })
                else:
                    self.result[registry]["value"].append({
                        "id": i,
                        "name": name,
                        "element": {}
                    })
        else:
            data_pack = buff.unpack_nbt()

            if self.factory.output_path:
                data_pack = NBTFile(data_pack)
                data_pack.save(self.factory.output_path)
            else:
                print(alt_repr(data_pack))

            buff.discard()  # Ignore the rest of the packet
            reactor.stop()

    def packet_join_game(self, buff):
        buff.discard()
        reactor.stop()


class DataPackDumperFactory(ClientFactory):
    protocol = DataPackDumperProtocol


@defer.inlineCallbacks
def run(args):
    # Log in
    profile = yield ProfileCLI.make_profile(args)

    # Create factory
    factory = DataPackDumperFactory(profile)
    factory.output_path = args.output_path

    # Connect!
    factory.connect(args.host, args.port)


def main(argv):
    parser = ProfileCLI.make_parser()
    parser.add_argument("host")
    parser.add_argument("-p", "--port", default=25565, type=int)
    parser.add_argument("-o", "--output-path")
    args = parser.parse_args(argv)

    run(args)
    reactor.run()


if __name__ == "__main__":
    import sys
    main(sys.argv[1:])
