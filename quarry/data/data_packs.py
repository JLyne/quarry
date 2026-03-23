import glob
import os.path
import re
from typing import Dict

from quarry.types.data_pack import DataPack
from quarry.types.namespaced_key import NamespacedKey
from quarry.types.nbt import NBTFile


def _load() -> Dict[int, DataPack]:
    data_packs = {}
    nbt_paths = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        "data_packs",
        "*.nbt"))
    for nbt_path in glob.glob(nbt_paths):
        match = re.match('(\d+)_(.+)\.nbt', os.path.basename(nbt_path))
        if not match:
            continue

        protocol_version = int(match.group(1))
        minecraft_version = match.group(2)
        pack = NBTFile.load(nbt_path).root_tag.body.to_obj()
        contents = {}

        for registry_id in configurable_registries[protocol_version]:
            registry = pack.get(str(registry_id), None)
            values = {}

            if not registry:
                continue

            for item in registry['value']:
                key = NamespacedKey.from_string(item.get('name'))
                values[key] = item.get('element', None)

            contents[registry_id] = values

        data_packs[protocol_version] = DataPack(NamespacedKey.minecraft('core'), minecraft_version,
                                                pack_formats[protocol_version], contents)

    return data_packs

pack_formats = {
    765: 41,
    766: 45,
    767: 48,
    768: 57,
    769: 61,
    770: 71,
    771: 80,
    772: 81,
    773: 88,
    774: 94.1,
    1073742127: 101.1
}

configurable_registries = {
    765: [
        NamespacedKey.minecraft('worldgen/biome'),
        NamespacedKey.minecraft('chat_type'),
        NamespacedKey.minecraft('trim_pattern'),
        NamespacedKey.minecraft('trim_material'),
        NamespacedKey.minecraft('dimension_type'),
        NamespacedKey.minecraft('damage_type')
    ],
    766: [
        NamespacedKey.minecraft('worldgen/biome'),
        NamespacedKey.minecraft('chat_type'),
        NamespacedKey.minecraft('trim_pattern'),
        NamespacedKey.minecraft('trim_material'),
        NamespacedKey.minecraft('dimension_type'),
        NamespacedKey.minecraft('damage_type'),
        NamespacedKey.minecraft('wolf_variant'),
        NamespacedKey.minecraft('banner_pattern')
    ],
    767: [
        NamespacedKey.minecraft('worldgen/biome'),
        NamespacedKey.minecraft('chat_type'),
        NamespacedKey.minecraft('trim_pattern'),
        NamespacedKey.minecraft('trim_material'),
        NamespacedKey.minecraft('dimension_type'),
        NamespacedKey.minecraft('damage_type'),
        NamespacedKey.minecraft('wolf_variant'),
        NamespacedKey.minecraft('banner_pattern'),
        NamespacedKey.minecraft('enchantment'),
        NamespacedKey.minecraft('jukebox_song'),
        NamespacedKey.minecraft('painting_variant')
    ],
    768: [
        NamespacedKey.minecraft('worldgen/biome'),
        NamespacedKey.minecraft('chat_type'),
        NamespacedKey.minecraft('trim_pattern'),
        NamespacedKey.minecraft('trim_material'),
        NamespacedKey.minecraft('dimension_type'),
        NamespacedKey.minecraft('damage_type'),
        NamespacedKey.minecraft('wolf_variant'),
        NamespacedKey.minecraft('banner_pattern'),
        NamespacedKey.minecraft('enchantment'),
        NamespacedKey.minecraft('jukebox_song'),
        NamespacedKey.minecraft('painting_variant'),
        NamespacedKey.minecraft('instrument')
    ],
    769: [
        NamespacedKey.minecraft('worldgen/biome'),
        NamespacedKey.minecraft('chat_type'),
        NamespacedKey.minecraft('trim_pattern'),
        NamespacedKey.minecraft('trim_material'),
        NamespacedKey.minecraft('dimension_type'),
        NamespacedKey.minecraft('damage_type'),
        NamespacedKey.minecraft('wolf_variant'),
        NamespacedKey.minecraft('banner_pattern'),
        NamespacedKey.minecraft('enchantment'),
        NamespacedKey.minecraft('jukebox_song'),
        NamespacedKey.minecraft('painting_variant'),
        NamespacedKey.minecraft('instrument')
    ],
    770: [
        NamespacedKey.minecraft('worldgen/biome'),
        NamespacedKey.minecraft('chat_type'),
        NamespacedKey.minecraft('trim_pattern'),
        NamespacedKey.minecraft('trim_material'),
        NamespacedKey.minecraft('dimension_type'),
        NamespacedKey.minecraft('damage_type'),
        NamespacedKey.minecraft('wolf_variant'),
        NamespacedKey.minecraft('banner_pattern'),
        NamespacedKey.minecraft('enchantment'),
        NamespacedKey.minecraft('jukebox_song'),
        NamespacedKey.minecraft('painting_variant'),
        NamespacedKey.minecraft('instrument'),
        NamespacedKey.minecraft('cat_variant'),
        NamespacedKey.minecraft('chicken_variant'),
        NamespacedKey.minecraft('cow_variant'),
        NamespacedKey.minecraft('frog_variant'),
        NamespacedKey.minecraft('pig_variant'),
        NamespacedKey.minecraft('test_environment'),
        NamespacedKey.minecraft('test_instance'),
        NamespacedKey.minecraft('wolf_sound_variant')
    ],
    771: [
        NamespacedKey.minecraft('worldgen/biome'),
        NamespacedKey.minecraft('chat_type'),
        NamespacedKey.minecraft('trim_pattern'),
        NamespacedKey.minecraft('trim_material'),
        NamespacedKey.minecraft('dimension_type'),
        NamespacedKey.minecraft('damage_type'),
        NamespacedKey.minecraft('wolf_variant'),
        NamespacedKey.minecraft('banner_pattern'),
        NamespacedKey.minecraft('enchantment'),
        NamespacedKey.minecraft('jukebox_song'),
        NamespacedKey.minecraft('painting_variant'),
        NamespacedKey.minecraft('instrument'),
        NamespacedKey.minecraft('cat_variant'),
        NamespacedKey.minecraft('chicken_variant'),
        NamespacedKey.minecraft('cow_variant'),
        NamespacedKey.minecraft('frog_variant'),
        NamespacedKey.minecraft('pig_variant'),
        NamespacedKey.minecraft('test_environment'),
        NamespacedKey.minecraft('test_instance'),
        NamespacedKey.minecraft('wolf_sound_variant'),
        NamespacedKey.minecraft('dialog')
    ],
    772: [
        NamespacedKey.minecraft('worldgen/biome'),
        NamespacedKey.minecraft('chat_type'),
        NamespacedKey.minecraft('trim_pattern'),
        NamespacedKey.minecraft('trim_material'),
        NamespacedKey.minecraft('dimension_type'),
        NamespacedKey.minecraft('damage_type'),
        NamespacedKey.minecraft('wolf_variant'),
        NamespacedKey.minecraft('banner_pattern'),
        NamespacedKey.minecraft('enchantment'),
        NamespacedKey.minecraft('jukebox_song'),
        NamespacedKey.minecraft('painting_variant'),
        NamespacedKey.minecraft('instrument'),
        NamespacedKey.minecraft('cat_variant'),
        NamespacedKey.minecraft('chicken_variant'),
        NamespacedKey.minecraft('cow_variant'),
        NamespacedKey.minecraft('frog_variant'),
        NamespacedKey.minecraft('pig_variant'),
        NamespacedKey.minecraft('test_environment'),
        NamespacedKey.minecraft('test_instance'),
        NamespacedKey.minecraft('wolf_sound_variant'),
        NamespacedKey.minecraft('dialog')
    ],
    773: [
        NamespacedKey.minecraft('worldgen/biome'),
        NamespacedKey.minecraft('chat_type'),
        NamespacedKey.minecraft('trim_pattern'),
        NamespacedKey.minecraft('trim_material'),
        NamespacedKey.minecraft('dimension_type'),
        NamespacedKey.minecraft('damage_type'),
        NamespacedKey.minecraft('wolf_variant'),
        NamespacedKey.minecraft('banner_pattern'),
        NamespacedKey.minecraft('enchantment'),
        NamespacedKey.minecraft('jukebox_song'),
        NamespacedKey.minecraft('painting_variant'),
        NamespacedKey.minecraft('instrument'),
        NamespacedKey.minecraft('cat_variant'),
        NamespacedKey.minecraft('chicken_variant'),
        NamespacedKey.minecraft('cow_variant'),
        NamespacedKey.minecraft('frog_variant'),
        NamespacedKey.minecraft('pig_variant'),
        NamespacedKey.minecraft('test_environment'),
        NamespacedKey.minecraft('test_instance'),
        NamespacedKey.minecraft('wolf_sound_variant'),
        NamespacedKey.minecraft('dialog')
    ],
    774: [
        NamespacedKey.minecraft('worldgen/biome'),
        NamespacedKey.minecraft('chat_type'),
        NamespacedKey.minecraft('trim_pattern'),
        NamespacedKey.minecraft('trim_material'),
        NamespacedKey.minecraft('dimension_type'),
        NamespacedKey.minecraft('damage_type'),
        NamespacedKey.minecraft('wolf_variant'),
        NamespacedKey.minecraft('banner_pattern'),
        NamespacedKey.minecraft('enchantment'),
        NamespacedKey.minecraft('jukebox_song'),
        NamespacedKey.minecraft('painting_variant'),
        NamespacedKey.minecraft('instrument'),
        NamespacedKey.minecraft('cat_variant'),
        NamespacedKey.minecraft('chicken_variant'),
        NamespacedKey.minecraft('cow_variant'),
        NamespacedKey.minecraft('frog_variant'),
        NamespacedKey.minecraft('pig_variant'),
        NamespacedKey.minecraft('test_environment'),
        NamespacedKey.minecraft('test_instance'),
        NamespacedKey.minecraft('wolf_sound_variant'),
        NamespacedKey.minecraft('dialog'),
        NamespacedKey.minecraft('timeline'),
        NamespacedKey.minecraft('zombie_nautilus_variant')
    ],
    1073742127: [
        NamespacedKey.minecraft('worldgen/biome'),
        NamespacedKey.minecraft('chat_type'),
        NamespacedKey.minecraft('trim_pattern'),
        NamespacedKey.minecraft('trim_material'),
        NamespacedKey.minecraft('dimension_type'),
        NamespacedKey.minecraft('damage_type'),
        NamespacedKey.minecraft('wolf_variant'),
        NamespacedKey.minecraft('banner_pattern'),
        NamespacedKey.minecraft('enchantment'),
        NamespacedKey.minecraft('jukebox_song'),
        NamespacedKey.minecraft('painting_variant'),
        NamespacedKey.minecraft('instrument'),
        NamespacedKey.minecraft('cat_variant'),
        NamespacedKey.minecraft('chicken_variant'),
        NamespacedKey.minecraft('cow_variant'),
        NamespacedKey.minecraft('frog_variant'),
        NamespacedKey.minecraft('pig_variant'),
        NamespacedKey.minecraft('test_environment'),
        NamespacedKey.minecraft('test_instance'),
        NamespacedKey.minecraft('wolf_sound_variant'),
        NamespacedKey.minecraft('dialog'),
        NamespacedKey.minecraft('timeline'),
        NamespacedKey.minecraft('zombie_nautilus_variant'),
        NamespacedKey.minecraft('cat_sound_variant'),
        NamespacedKey.minecraft('chicken_sound_variant'),
        NamespacedKey.minecraft('cow_sound_variant'),
        NamespacedKey.minecraft('pig_sound_variant'),
        NamespacedKey.minecraft('world_clock')
    ]
}

vanilla_data_packs: Dict[int, DataPack] = _load()
