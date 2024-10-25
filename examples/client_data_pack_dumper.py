"""
Dumps the data pack info from the "join_game" packet to a file.
"""

from __future__ import print_function
from twisted.internet import reactor, defer

from quarry.data.data_packs import configurable_registries
from quarry.types.namespaced_key import NamespacedKey
from quarry.types.nbt import NBTFile, alt_repr, TagRoot
from quarry.net.client import ClientFactory, ClientProtocol
from quarry.net.auth import ProfileCLI


class DataPackDumperProtocol(ClientProtocol):
    result = {}
    tags_result = {
        'static': {},
        'configurable': {}
    }
    keys = {}

    def start_configuration(self):
        super().start_configuration()
        self.data_packs.clear_packs()

    def packet_registry_data(self, buff):
        if self.protocol_version >= 766:
            registry = buff.unpack_string()
            self.result[registry] = {
                "value": [],
                "type": registry
            }

            configurable = NamespacedKey.from_string(registry) in configurable_registries[self.protocol_version]

            if configurable:
                self.keys[registry] = []

            for i in range(buff.unpack_varint()):
                name = buff.unpack_string()

                if buff.unpack('?'):
                    nbt = buff.unpack_nbt()
                    self.result[registry]["value"].append({
                        "name": name,
                        "element": nbt.body.to_obj()
                    })
                else:
                    self.result[registry]["value"].append({
                        "name": name,
                        "element": {}
                    })

                # Track keys for data pack registries for later tag mapping
                if configurable:
                    self.keys[registry].append(name)
        else:
            data_pack = buff.unpack_nbt()

            for (registry, content) in data_pack.body.to_obj().items():
                self.keys[registry] = []

                for value in content['value']:
                    self.keys[registry].append(value['name'])

            if self.factory.output_path:
                data_pack = NBTFile(data_pack)
                data_pack.save(self.factory.output_path)
            else:
                print(alt_repr(data_pack))

            buff.discard()  # Ignore the rest of the packet
            reactor.stop()

    def packet_update_tags(self, buff):
        length = buff.unpack_varint()

        for i in range(length):
            registry = buff.unpack_string()
            registry_length = buff.unpack_varint()

            configurable = registry in self.keys
            tag_registry = {}

            if configurable:
                self.tags_result['configurable'][registry] = tag_registry
            else:
                self.tags_result['static'][registry] = tag_registry

            for j in range(registry_length):
                tag = buff.unpack_string()
                tag_length = buff.unpack_varint()
                items = []

                tag_registry[tag] = items

                for k in range(tag_length):
                    value = buff.unpack_varint()

                    # Map data packs registry tag values back to strings
                    if configurable:
                        value = self.keys[registry][value]

                    items.append(value)

        if self.protocol_version <= 765:
            self.save_tags()
            reactor.stop()

    def packet_login(self, buff):
        if self.protocol_version >= 766:
            nbt = TagRoot.from_obj(self.result)

            if self.factory.output_path:
                result = NBTFile(nbt)
                result.save(self.factory.output_path)
            else:
                print(alt_repr(nbt))

            self.save_tags()

            buff.discard()
            reactor.stop()

    def save_tags(self):
        tags_nbt = TagRoot.from_obj(self.tags_result)

        if self.factory.tags_output_path:
            result = NBTFile(tags_nbt)
            result.save(self.factory.tags_output_path)
        else:
            print(alt_repr(tags_nbt))


class DataPackDumperFactory(ClientFactory):
    protocol = DataPackDumperProtocol


@defer.inlineCallbacks
def run(args):
    # Log in
    profile = yield ProfileCLI.make_profile(args)

    # Create factory
    factory = DataPackDumperFactory(profile)
    factory.output_path = args.output_path
    factory.tags_output_path = args.tags_output_path

    # Connect!
    factory.connect(args.host, args.port)


def main(argv):
    parser = ProfileCLI.make_parser()
    parser.add_argument("host")
    parser.add_argument("-p", "--port", default=25565, type=int)
    parser.add_argument("-o", "--output-path")
    parser.add_argument("-t", "--tags-output-path")
    args = parser.parse_args(argv)

    run(args)
    reactor.run()


if __name__ == "__main__":
    import sys
    main(sys.argv[1:])
