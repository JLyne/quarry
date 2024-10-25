import glob
import os.path
import re
from typing import Dict, List

from quarry.types.namespaced_key import NamespacedKey
from quarry.types.nbt import NBTFile


def _load():
    nbt_paths = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        "tags",
        "*.nbt"))
    for nbt_path in glob.glob(nbt_paths):
        match = re.match('(\d+)_(.+)\.nbt', os.path.basename(nbt_path))
        if not match:
            continue

        protocol_version = int(match.group(1))
        vanilla_configurable_tags[protocol_version] = {}
        vanilla_static_tags[protocol_version] = {}
        pack = NBTFile.load(nbt_path).root_tag.body.to_obj()

        for (registry, tags) in pack['configurable'].items():
            registry = NamespacedKey.from_string(registry)
            vanilla_configurable_tags[protocol_version][registry] = {}

            for (tag, values) in tags.items():
                vanilla_configurable_tags[protocol_version][registry][tag] = [NamespacedKey.from_string(value) for value in values]

        for (registry, tags) in pack['static'].items():
            registry = NamespacedKey.from_string(registry)
            vanilla_static_tags[protocol_version][registry] = {}

            for (tag, values) in tags.items():
                vanilla_static_tags[protocol_version][registry][tag] = values

vanilla_static_tags: Dict[int, Dict[NamespacedKey, Dict[str, List[int]]]] = {}
vanilla_configurable_tags: Dict[int, Dict[NamespacedKey, Dict[str, List[NamespacedKey]]]] = {}

_load()