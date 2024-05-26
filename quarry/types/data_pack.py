from dataclasses import dataclass, field
from typing import Dict, Tuple, Union

from quarry.types.namespaced_key import NamespacedKey
from quarry.types.nbt import TagCompound


@dataclass(frozen=True)
class DataPack:
    id: NamespacedKey
    version: str
    format: Union[int, Tuple[int, int]]
    contents: Dict[NamespacedKey, Dict[NamespacedKey, TagCompound]] = field(repr=False)
    force_load: bool = False

    def is_compatible(self, protocol_version: int):
        from quarry.data.data_packs import pack_formats
        target_format = pack_formats[protocol_version]

        if isinstance(self.format, tuple):
            return self.format[0] <= target_format <= self.format[1]

        return self.format == target_format
