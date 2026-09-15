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
    775: 101.1,
    776: 107.1,
    777: 121.0
}

configurable_registries = {
    765: [
        NamespacedKey.minecraft('chat_type'),
        NamespacedKey.minecraft('damage_type'),
        NamespacedKey.minecraft('dimension_type'),
        NamespacedKey.minecraft('trim_material'),
        NamespacedKey.minecraft('trim_pattern'),
        NamespacedKey.minecraft('worldgen/biome')
    ],
    766: [
        NamespacedKey.minecraft('banner_pattern'), # New
        NamespacedKey.minecraft('chat_type'),
        NamespacedKey.minecraft('damage_type'),
        NamespacedKey.minecraft('dimension_type'),
        NamespacedKey.minecraft('trim_material'),
        NamespacedKey.minecraft('trim_pattern'),
        NamespacedKey.minecraft('wolf_variant'), # New
        NamespacedKey.minecraft('worldgen/biome')
    ],
    767: [
        NamespacedKey.minecraft('banner_pattern'),
        NamespacedKey.minecraft('chat_type'),
        NamespacedKey.minecraft('damage_type'),
        NamespacedKey.minecraft('dimension_type'),
        NamespacedKey.minecraft('enchantment'), # New
        NamespacedKey.minecraft('jukebox_song'), # New
        NamespacedKey.minecraft('painting_variant'), # New
        NamespacedKey.minecraft('trim_material'),
        NamespacedKey.minecraft('trim_pattern'),
        NamespacedKey.minecraft('wolf_variant'),
        NamespacedKey.minecraft('worldgen/biome')
    ],
    768: [
        NamespacedKey.minecraft('banner_pattern'),
        NamespacedKey.minecraft('chat_type'),
        NamespacedKey.minecraft('damage_type'),
        NamespacedKey.minecraft('dimension_type'),
        NamespacedKey.minecraft('enchantment'),
        NamespacedKey.minecraft('instrument'), # New
        NamespacedKey.minecraft('jukebox_song'),
        NamespacedKey.minecraft('painting_variant'),
        NamespacedKey.minecraft('trim_material'),
        NamespacedKey.minecraft('trim_pattern'),
        NamespacedKey.minecraft('wolf_variant'),
        NamespacedKey.minecraft('worldgen/biome')
    ],
    769: [
        NamespacedKey.minecraft('banner_pattern'),
        NamespacedKey.minecraft('chat_type'),
        NamespacedKey.minecraft('damage_type'),
        NamespacedKey.minecraft('dimension_type'),
        NamespacedKey.minecraft('enchantment'),
        NamespacedKey.minecraft('instrument'),
        NamespacedKey.minecraft('jukebox_song'),
        NamespacedKey.minecraft('painting_variant'),
        NamespacedKey.minecraft('trim_material'),
        NamespacedKey.minecraft('trim_pattern'),
        NamespacedKey.minecraft('wolf_variant'),
        NamespacedKey.minecraft('worldgen/biome')
    ],
    770: [
        NamespacedKey.minecraft('banner_pattern'),
        NamespacedKey.minecraft('cat_variant'), # New
        NamespacedKey.minecraft('chat_type'),
        NamespacedKey.minecraft('chicken_variant'), # New
        NamespacedKey.minecraft('cow_variant'), # New
        NamespacedKey.minecraft('damage_type'),
        NamespacedKey.minecraft('dimension_type'),
        NamespacedKey.minecraft('enchantment'),
        NamespacedKey.minecraft('frog_variant'), # New
        NamespacedKey.minecraft('instrument'),
        NamespacedKey.minecraft('jukebox_song'),
        NamespacedKey.minecraft('painting_variant'),
        NamespacedKey.minecraft('pig_variant'), # New
        NamespacedKey.minecraft('test_environment'), # New
        NamespacedKey.minecraft('test_instance'), # New
        NamespacedKey.minecraft('trim_material'),
        NamespacedKey.minecraft('trim_pattern'),
        NamespacedKey.minecraft('wolf_sound_variant'), # New
        NamespacedKey.minecraft('wolf_variant'),
        NamespacedKey.minecraft('worldgen/biome')
    ],
    771: [
        NamespacedKey.minecraft('banner_pattern'),
        NamespacedKey.minecraft('cat_variant'),
        NamespacedKey.minecraft('chat_type'),
        NamespacedKey.minecraft('chicken_variant'),
        NamespacedKey.minecraft('cow_variant'),
        NamespacedKey.minecraft('damage_type'),
        NamespacedKey.minecraft('dialog'), # New
        NamespacedKey.minecraft('dimension_type'),
        NamespacedKey.minecraft('enchantment'),
        NamespacedKey.minecraft('frog_variant'),
        NamespacedKey.minecraft('instrument'),
        NamespacedKey.minecraft('jukebox_song'),
        NamespacedKey.minecraft('painting_variant'),
        NamespacedKey.minecraft('pig_variant'),
        NamespacedKey.minecraft('test_environment'),
        NamespacedKey.minecraft('test_instance'),
        NamespacedKey.minecraft('trim_material'),
        NamespacedKey.minecraft('trim_pattern'),
        NamespacedKey.minecraft('wolf_sound_variant'),
        NamespacedKey.minecraft('wolf_variant'),
        NamespacedKey.minecraft('worldgen/biome')
    ],
    772: [
        NamespacedKey.minecraft('banner_pattern'),
        NamespacedKey.minecraft('cat_variant'),
        NamespacedKey.minecraft('chat_type'),
        NamespacedKey.minecraft('chicken_variant'),
        NamespacedKey.minecraft('cow_variant'),
        NamespacedKey.minecraft('damage_type'),
        NamespacedKey.minecraft('dialog'),
        NamespacedKey.minecraft('dimension_type'),
        NamespacedKey.minecraft('enchantment'),
        NamespacedKey.minecraft('frog_variant'),
        NamespacedKey.minecraft('instrument'),
        NamespacedKey.minecraft('jukebox_song'),
        NamespacedKey.minecraft('painting_variant'),
        NamespacedKey.minecraft('pig_variant'),
        NamespacedKey.minecraft('test_environment'),
        NamespacedKey.minecraft('test_instance'),
        NamespacedKey.minecraft('trim_material'),
        NamespacedKey.minecraft('trim_pattern'),
        NamespacedKey.minecraft('wolf_variant'),
        NamespacedKey.minecraft('wolf_sound_variant'),\
        NamespacedKey.minecraft('worldgen/biome')
    ],
    773: [
        NamespacedKey.minecraft('banner_pattern'),
        NamespacedKey.minecraft('cat_variant'),
        NamespacedKey.minecraft('chat_type'),
        NamespacedKey.minecraft('chicken_variant'),
        NamespacedKey.minecraft('cow_variant'),
        NamespacedKey.minecraft('damage_type'),
        NamespacedKey.minecraft('dialog'),
        NamespacedKey.minecraft('dimension_type'),
        NamespacedKey.minecraft('enchantment'),
        NamespacedKey.minecraft('frog_variant'),
        NamespacedKey.minecraft('instrument'),
        NamespacedKey.minecraft('jukebox_song'),
        NamespacedKey.minecraft('painting_variant'),
        NamespacedKey.minecraft('pig_variant'),
        NamespacedKey.minecraft('test_environment'),
        NamespacedKey.minecraft('test_instance'),
        NamespacedKey.minecraft('trim_material'),
        NamespacedKey.minecraft('trim_pattern'),
        NamespacedKey.minecraft('wolf_sound_variant'),
        NamespacedKey.minecraft('wolf_variant'),
        NamespacedKey.minecraft('worldgen/biome')
    ],
    774: [
        NamespacedKey.minecraft('banner_pattern'),
        NamespacedKey.minecraft('cat_variant'),
        NamespacedKey.minecraft('chat_type'),
        NamespacedKey.minecraft('chicken_variant'),
        NamespacedKey.minecraft('cow_variant'),
        NamespacedKey.minecraft('damage_type'),
        NamespacedKey.minecraft('dialog'),
        NamespacedKey.minecraft('dimension_type'),
        NamespacedKey.minecraft('enchantment'),
        NamespacedKey.minecraft('frog_variant'),
        NamespacedKey.minecraft('instrument'),
        NamespacedKey.minecraft('jukebox_song'),
        NamespacedKey.minecraft('painting_variant'),
        NamespacedKey.minecraft('pig_variant'),
        NamespacedKey.minecraft('test_environment'),
        NamespacedKey.minecraft('test_instance'),
        NamespacedKey.minecraft('timeline'), # New
        NamespacedKey.minecraft('trim_material'),
        NamespacedKey.minecraft('trim_pattern'),
        NamespacedKey.minecraft('wolf_sound_variant'),
        NamespacedKey.minecraft('wolf_variant'),
        NamespacedKey.minecraft('worldgen/biome'),
        NamespacedKey.minecraft('zombie_nautilus_variant') # New
    ],
    775: [
        NamespacedKey.minecraft('banner_pattern'),
        NamespacedKey.minecraft('cat_sound_variant'), # New
        NamespacedKey.minecraft('cat_variant'),
        NamespacedKey.minecraft('chat_type'),
        NamespacedKey.minecraft('chicken_sound_variant'), # New
        NamespacedKey.minecraft('chicken_variant'),
        NamespacedKey.minecraft('cow_sound_variant'), # New
        NamespacedKey.minecraft('cow_variant'),
        NamespacedKey.minecraft('damage_type'),
        NamespacedKey.minecraft('dialog'),
        NamespacedKey.minecraft('dimension_type'),
        NamespacedKey.minecraft('enchantment'),
        NamespacedKey.minecraft('frog_variant'),
        NamespacedKey.minecraft('instrument'),
        NamespacedKey.minecraft('jukebox_song'),
        NamespacedKey.minecraft('painting_variant'),
        NamespacedKey.minecraft('pig_sound_variant'), # New
        NamespacedKey.minecraft('pig_variant'),
        NamespacedKey.minecraft('test_environment'),
        NamespacedKey.minecraft('test_instance'),
        NamespacedKey.minecraft('timeline'),
        NamespacedKey.minecraft('trim_material'),
        NamespacedKey.minecraft('trim_pattern'),
        NamespacedKey.minecraft('wolf_sound_variant'),
        NamespacedKey.minecraft('wolf_variant'),
        NamespacedKey.minecraft('world_clock'), # New
        NamespacedKey.minecraft('worldgen/biome'),
        NamespacedKey.minecraft('zombie_nautilus_variant')
    ],
    776: [
        NamespacedKey.minecraft('banner_pattern'),
        NamespacedKey.minecraft('cat_sound_variant'),
        NamespacedKey.minecraft('cat_variant'),
        NamespacedKey.minecraft('chat_type'),
        NamespacedKey.minecraft('chicken_sound_variant'),
        NamespacedKey.minecraft('chicken_variant'),
        NamespacedKey.minecraft('cow_sound_variant'),
        NamespacedKey.minecraft('cow_variant'),
        NamespacedKey.minecraft('damage_type'),
        NamespacedKey.minecraft('dialog'),
        NamespacedKey.minecraft('dimension_type'),
        NamespacedKey.minecraft('enchantment'),
        NamespacedKey.minecraft('frog_variant'),
        NamespacedKey.minecraft('instrument'),
        NamespacedKey.minecraft('jukebox_song'),
        NamespacedKey.minecraft('painting_variant'),
        NamespacedKey.minecraft('pig_sound_variant'),
        NamespacedKey.minecraft('pig_variant'),
        NamespacedKey.minecraft('sulfur_cube_archetype'), # New
        NamespacedKey.minecraft('test_environment'),
        NamespacedKey.minecraft('test_instance'),
        NamespacedKey.minecraft('timeline'),
        NamespacedKey.minecraft('trim_material'),
        NamespacedKey.minecraft('trim_pattern'),
        NamespacedKey.minecraft('wolf_sound_variant'),
        NamespacedKey.minecraft('wolf_variant'),
        NamespacedKey.minecraft('world_clock'),
        NamespacedKey.minecraft('worldgen/biome'),
        NamespacedKey.minecraft('zombie_nautilus_variant')
    ],
    777: [
        NamespacedKey.minecraft('banner_pattern'),
        NamespacedKey.minecraft('block_transformer'), # New
        NamespacedKey.minecraft('cat_sound_variant'),
        NamespacedKey.minecraft('cat_variant'),
        NamespacedKey.minecraft('chat_type'),
        NamespacedKey.minecraft('chicken_sound_variant'),
        NamespacedKey.minecraft('chicken_variant'),
        NamespacedKey.minecraft('cow_sound_variant'),
        NamespacedKey.minecraft('cow_variant'),
        NamespacedKey.minecraft('damage_type'),
        NamespacedKey.minecraft('decorated_pot_pattern'), # New
        NamespacedKey.minecraft('dialog'),
        NamespacedKey.minecraft('dimension_type'),
        NamespacedKey.minecraft('enchantment'),
        NamespacedKey.minecraft('frog_variant'),
        NamespacedKey.minecraft('instrument'),
        NamespacedKey.minecraft('jukebox_song'),
        NamespacedKey.minecraft('painting_variant'),
        NamespacedKey.minecraft('pig_sound_variant'),
        NamespacedKey.minecraft('pig_variant'),
        NamespacedKey.minecraft('sulfur_cube_archetype'),
        NamespacedKey.minecraft('test_environment'),
        NamespacedKey.minecraft('test_instance'),
        NamespacedKey.minecraft('timeline'),
        NamespacedKey.minecraft('trim_material'),
        NamespacedKey.minecraft('trim_pattern'),
        NamespacedKey.minecraft('wolf_sound_variant'),
        NamespacedKey.minecraft('wolf_variant'),
        NamespacedKey.minecraft('world_clock'),
        NamespacedKey.minecraft('worldgen/biome'),
        NamespacedKey.minecraft('worldgen/block_state_provider'), # New
        NamespacedKey.minecraft('zombie_nautilus_variant')
    ]
}

vanilla_data_packs: Dict[int, DataPack] = _load()
