from typing import TYPE_CHECKING

from quarry.types.buffer.item.v1_21_11 import ItemBuffer1_21_11

if TYPE_CHECKING:
    from quarry.types.buffer import Buffer26_1

dye_colors = [
    "white",
    "orange",
    "magenta",
    "light_blue",
    "yellow",
    "lime",
    "pink",
    "gray",
    "light_gray",
    "cyan",
    "purple",
    "blue",
    "brown",
    "green",
    "red",
    "black",
]

class ItemBuffer26_1(ItemBuffer1_21_11):
    component_handlers = list(ItemBuffer1_21_11.component_handlers.items())
    component_handlers.insert(41, ('additional_trade_cost', (lambda cls: cls.pack_int, lambda self: self.unpack_int)))
    component_handlers.insert(43, ('dye', (lambda cls: cls.pack_dye, lambda self: self.unpack_dye)))

    component_handlers = dict(component_handlers)
    component_handlers['provides_banner_patterns'] = (lambda cls: cls.pack_provides_banner_patterns, lambda self: self.unpack_provides_banner_patterns)
    component_handlers['damage_resistant'] = (lambda cls: cls.pack_damage_resistant, lambda self: self.unpack_damage_resistant)

    component_types = list(component_handlers.keys())

    def __init__(self, buffer: 'Buffer26_1'):
        super(ItemBuffer1_21_11, self).__init__(buffer)

    # Dye  ---------------------------------------------------------------

    @classmethod
    def pack_dye(cls, value):
        return cls.buffer.pack_varint(dye_colors.index(value))

    def unpack_dye(self):
        return dye_colors[self.buffer.unpack_varint()]

    # Blocks Attacks  ---------------------------------------------------------------

    @classmethod
    def pack_blocks_attacks(cls, value):
        block_delay_seconds = value.get('block_delay_seconds', 0.0)
        disable_cooldown_scale = value.get('disable_cooldown_scale', 1.0)
        damage_reductions = value.get('damage_reductions', [])
        item_damage = value.get('item_damage', {})
        bypassed_by = value.get('bypassed_by', None)
        block_sound = value.get('block_sound', None)
        disable_sound = value.get('disable_sound', None)

        pack_type = lambda v: cls.pack_registry_tag_or_list(v, "minecraft:damage_type")

        data = cls.buffer.pack('ff', block_delay_seconds, disable_cooldown_scale)
        data += cls.buffer.pack_varint(len(damage_reductions))

        for damage_reduction in damage_reductions:
            data += cls.pack_damage_reduction(damage_reduction)

        data += (cls.pack_item_damage_function(item_damage)
                 + cls.buffer.pack_optional(pack_type, bypassed_by)
                 + cls.buffer.pack_optional(cls.pack_sound_event, block_sound)
                 + cls.buffer.pack_optional(cls.pack_sound_event, disable_sound))

        return data

    def unpack_blocks_attacks(self):
        unpack_type = lambda: self.unpack_registry_tag_or_list("minecraft:damage_type")

        return {
            'block_delay_seconds': self.buffer.unpack('f'),
            'disable_cooldown_scale': self.buffer.unpack('f'),
            'damage_reductions': [self.unpack_damage_reduction() for _ in range(self.buffer.unpack_varint())],
            'item_damage': self.unpack_item_damage_function(),
            'bypassed_by': self.buffer.unpack_optional(unpack_type),
            'block_sound': self.buffer.unpack_optional(self.unpack_sound_event()),
            'disable_sound': self.buffer.unpack_optional(self.unpack_sound_event())
        }

    # Provides banner patterns  ---------------------------------------------------------------

    @classmethod
    def pack_provides_banner_patterns(cls, value):
        return cls.pack_registry_tag_or_list(value, "minecraft:banner_pattern")

    def unpack_provides_banner_patterns(self):
        return self.unpack_registry_tag_or_list("minecraft:banner_pattern")


    # Damage resistant  ---------------------------------------------------------------

    @classmethod
    def pack_damage_resistant(cls, value):
        return cls.pack_registry_tag_or_list(value, "minecraft:damage_type")

    def unpack_damage_resistant(self):
        return self.unpack_registry_tag_or_list("minecraft:damage_type")

