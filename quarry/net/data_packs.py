from collections import deque
from typing import Dict, Deque, Optional, List, Tuple

from quarry.data.data_packs import configurable_registries
from quarry.types.data_pack import DataPack
from quarry.types.namespaced_key import NamespacedKey
from quarry.types.nbt import TagCompound, TagRoot


class DataPacks:
    def __init__(self, protocol_version: int):
        self.locked = False
        self.protocol_version = protocol_version
        self.packs: Dict[NamespacedKey, DataPack] = {}
        self.load_order: Deque[NamespacedKey] = deque()

    #
    def add_data_pack(self, pack: DataPack):
        """Adds the given data pack at the end of the load order"""
        self._check_locked()
        self._validate_pack(pack)

        self.packs[pack.id] = pack
        self.load_order.append(pack.id)

    def add_data_pack_first(self, pack: DataPack):
        """Adds the given data pack at the start of the load order"""
        self._check_locked()
        self._validate_pack(pack)

        self.packs[pack.id] = pack
        self.load_order.appendleft(pack.id)

    def add_data_pack_after(self, pack: DataPack, after: NamespacedKey):
        """Adds the given data pack after the given target pack in the load order"""
        self._check_locked()
        self._validate_pack(pack)

        if after not in self.packs.values():
            raise TypeError("Target pack {} does not exist".format(after))

        self.packs[pack.id] = pack
        self.load_order.insert(self.load_order.index(after) + 1, pack.id)

    def add_data_pack_before(self, pack: DataPack, before: NamespacedKey):
        """Adds the given data pack before the given target pack in the load order"""
        self._check_locked()
        self._validate_pack(pack)

        if before not in self.packs.values():
            raise TypeError("Target pack {} does not exist".format(before))

        self.packs[pack.id] = pack
        self.load_order.insert(self.load_order.index(before), pack.id)

    def remove_data_pack(self, id: NamespacedKey):
        """Removes the data pack with the given id, if present"""
        self._check_locked()

        if id in self.packs.values():
            del self.packs[id]

        if id in self.load_order:
            self.load_order.remove(id)

    def get_pack(self, id: NamespacedKey) -> DataPack:
        """Returns the data pack with the given id, if present"""
        return self.packs.get(id, None)

    def get_packs(self) -> List[DataPack]:
        """Returns all loaded data packs"""
        return list(self.packs.values())

    def get_registry(self, registry_id: NamespacedKey, *exclude: List[Tuple[NamespacedKey, str]]) \
            -> Dict[NamespacedKey, Optional[TagCompound]]:
        """
        Computes the given registry with the currently loaded packs.
        Loaded packs with ids in the exclude list will be ignored.
        """
        data = {}

        for pack in self.load_order:
            excluded = (pack, self.packs[pack].version) in exclude
            registry = self.packs[pack].contents.get(registry_id, {})

            for (key, value) in registry.items():
                data[key] = None if excluded else value

        return data

    def get_nbt_codec(self):
        """
        Computes all registries and returns them as a single TagRoot
        Suitable for the <1.20.5 registry_data packet
        """
        contents = {}

        for registry_id in configurable_registries[self.protocol_version]:
            registry = self.get_registry(registry_id)

            registry_contents = {
                'type': str(registry_id),
                'value': []
            }

            index = 0

            for (key, value) in registry.items():
                registry_contents['value'].append({
                    'name': str(key),
                    'id': index,
                    'element': value
                })

                index += 1

            contents[str(registry_id)] = registry_contents

        return TagRoot.from_obj(contents)

    def clear_packs(self):
        """Removes all loaded data packs"""
        self._check_locked()

        self.packs.clear()
        self.load_order.clear()

    def lock(self):
        """
        Prevents further modification of data packs.
        Should be called when leaving configuration mode.
        """
        self.locked = True

    def _check_locked(self):
        if self.locked:
            raise TypeError("Data packs are locked")

    def _validate_pack(self, pack: DataPack):
        if pack in self.packs.values():
            raise TypeError("Pack '{}' already exists".format(pack.id))

        if not (pack.force_load or pack.is_compatible(self.protocol_version)):
            raise TypeError("Pack '{}' is not compatible with current protocol version".format(self.protocol_version))