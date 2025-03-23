from typing import TYPE_CHECKING

from quarry.types.buffer.item.v1_21_4 import ItemBuffer1_21_4

if TYPE_CHECKING:
    from quarry.types.buffer import Buffer1_21_5


class ItemBuffer1_21_5(ItemBuffer1_21_4):
    component_handlers = list(ItemBuffer1_21_4.component_handlers.items())
    del component_handlers[15] # Remove hide_additional_tooltip
    del component_handlers[15] # Remove hide_tooltip
    component_handlers.insert(15, ('tooltip_display', (lambda cls: cls.pack_tooltip_display, lambda self: self.unpack_tooltip_display)))
    component_handlers.insert(26, ('weapon', (lambda cls: cls.pack_weapon, lambda self: self.unpack_weapon)))
    component_handlers.insert(33, ('blocks_attacks', (lambda cls: cls.pack_blocks_attacks, lambda self: self.unpack_blocks_attacks)))
    component_handlers.insert(43, ('potion_duration_scale', (lambda cls: cls.pack_float, lambda self: self.unpack_float)))
    component_handlers.insert(53, ('provides_trim_material', (lambda cls: cls.buffer.pack_string, lambda self: self.buff.unpack_string)))
    component_handlers.insert(56, ('provides_banner_patterns', (lambda cls: cls.buffer.pack_string, lambda self: self.buff.unpack_string)))
    component_handlers.insert(71, ('break_sound', (lambda cls: cls.pack_sound_event, lambda self: self.unpack_sound_event)))

    component_handlers = dict(component_handlers)
    component_handlers['dyed_color'] = (lambda cls: cls.pack_int, lambda self: self.unpack_int)
    component_handlers['jukebox_playable'] = (lambda cls: cls.buffer.pack_string, lambda self: self.buff.unpack_string)
    component_handlers['unbreakable'] = None

    component_types = list(component_handlers.keys())

    def __init__(self, buffer: 'Buffer1_21_5'):
        super(ItemBuffer1_21_4, self).__init__(buffer)

    # Tooltip Display  ---------------------------------------------------------------

    @classmethod
    def pack_tooltip_display(cls, value):
        hide_tooltip = value.get('hide_tooltip', False)
        hidden_components = value.get('hidden_components', [])

        data = cls.pack_boolean(hide_tooltip) + cls.buffer.pack_varint(len(hidden_components))

        for hidden_component in hidden_components:
            data += cls.buffer.pack_string(hidden_component)

        return data

    def unpack_tooltip_display(self):
        return {
            'hide_tooltip': self.unpack_boolean(),
            'hidden_components': [self.buffer.unpack_string() for _ in range(self.buffer.unpack_varint())]
        }

    # Weapon  ---------------------------------------------------------------

    @classmethod
    def pack_weapon(cls, value):
        item_damage_per_attack = value.get('item_damage_per_attack', 1)
        disable_blocking_for_seconds = value.get('disable_blocking_for_seconds', 0.0)

        return (cls.buffer.pack_varint(item_damage_per_attack)
                + cls.buffer.pack('f', disable_blocking_for_seconds))

    def unpack_weapon(self):
        return {
            'item_damage_per_attack': self.buffer.unpack_varint(),
            'disable_blocking_for_seconds': self.buffer.unpack('f')
        }

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

        data = cls.buffer.pack('ff', block_delay_seconds, disable_cooldown_scale)
        data += cls.buffer.pack_varint(len(damage_reductions))

        for damage_reduction in damage_reductions:
            data += cls.pack_damage_reduction(damage_reduction)

        data += (cls.pack_item_damage_function(item_damage)
                 + cls.buffer.pack_optional(cls.buffer.pack_string, bypassed_by)
                 + cls.buffer.pack_optional(cls.pack_sound_event, block_sound)
                 + cls.buffer.pack_optional(cls.pack_sound_event, disable_sound))

        return data

    def unpack_blocks_attacks(self):
        return {
            'block_delay_seconds': self.buffer.unpack('f'),
            'disable_cooldown_scale': self.buffer.unpack('f'),
            'damage_reductions': [self.unpack_damage_reduction() for _ in range(self.buffer.unpack_varint())],
            'item_damage': self.unpack_item_damage_function(),
            'bypassed_by': self.buffer.unpack_optional(self.buffer.unpack_string()),
            'block_sound': self.buffer.unpack_optional(self.unpack_sound_event()),
            'disable_sound': self.buffer.unpack_optional(self.unpack_sound_event())
        }

    @classmethod
    def pack_damage_reduction(cls, value):
        horizontal_blocking_angle = value.get('horizontal_blocking_angle', 90.0)
        types = value.get('types', None)
        base = value.get('base', 0.0)
        factor = value.get('factor', 0.0)

        pack_type = lambda v: cls.pack_registry_tag_or_list(v, "minecraft:damage_type")

        return (cls.buffer.pack('f', horizontal_blocking_angle)
                + cls.buffer.pack_optional(pack_type, types)
                + cls.buffer.pack('ff', base, factor))

    def unpack_damage_reduction(self):
        unpack_type = lambda: self.unpack_registry_tag_or_list("minecraft:damage_type")

        return {
            'horizontal_blocking_angle': self.buffer.unpack_varint(),
            'type': self.buffer.unpack_optional(unpack_type),
            'base': self.buffer.unpack('f'),
            'factor': self.buffer.unpack('f')
        }

    @classmethod
    def pack_item_damage_function(cls, value):
        threshold = value.get('threshold', 0.0)
        base = value.get('base', 0.0)
        factor = value.get('factor', 0.0)

        return cls.buffer.pack('fff', threshold, base, factor)

    def unpack_item_damage_function(self):
        return {
            'threshold': self.buffer.unpack('f'),
            'base': self.buffer.unpack('f'),
            'factor': self.buffer.unpack('f')
        }

    # Tool ------------------------------------------------------------------

    @classmethod
    def pack_tool(cls, value):
        can_destroy_blocks_in_creative = value.get('can_destroy_blocks_in_creative', True)

        return super().pack_tool(value) + cls.buffer.pack('?', can_destroy_blocks_in_creative)

    def unpack_tool(self):
        result = super().unpack_tool()

        result['can_destroy_blocks_in_creative'] = self.buffer.unpack('?')

    # Attribute Modifiers ------------------------------------------------------------------

    @classmethod
    def pack_attribute_modifiers(cls, value):
        data = cls.buffer.pack_varint(len(value))

        for modifier in value:
            data += cls.pack_attribute_modifier(modifier)

        return data

    def unpack_attribute_modifiers(self):
        return [self.unpack_attribute_modifier() for _ in range(self.buffer.unpack_varint())]

    # Adventure Mode Predicate ------------------------------------------------------------------

    @classmethod
    def pack_adventure_mode_predicate(cls, value):
        data = cls.buffer.pack_varint(len(value))

        for predicate in value:
            data += cls.pack_block_predicate(predicate)

        return data

    def unpack_adventure_mode_predicate(self):
        return [self.unpack_block_predicate() for _ in range(self.buffer.unpack_varint())]

    # Enchantments ------------------------------------------------------------------

    @classmethod
    def pack_enchantments(cls, value):
        data = cls.buffer.pack_varint(len(value))

        for enchantment in value.items():
            data += cls.pack_enchantment(enchantment)

        return data

    def unpack_enchantments(self):
        return dict(self.unpack_enchantment() for _ in range(self.buffer.unpack_varint()))

    # Armor Trim ------------------------------------------------------------------

    @classmethod
    def pack_armor_trim(cls, value):
        material = value['material']
        pattern = value['pattern']
        override_armor_materials = material.get('override_armor_materials', [])
        decal = pattern.get('decal', False)

        data = cls.buffer.pack_string(material['asset_name']) + \
            cls.buffer.pack_varint(cls.buffer.registry.encode('minecraft:item', material['ingredient'])) + \
            cls.buffer.pack('f', material['item_model_index']) + \
            cls.buffer.pack_varint(len(override_armor_materials))

        for (key, value) in override_armor_materials.items():
            data += cls.buffer.pack_string(key) + \
                    cls.buffer.pack_string(value)

        data += cls.buffer.pack_chat(material['description'])

        data += cls.buffer.pack_string(pattern['asset_name']) + \
            cls.buffer.pack_varint(cls.buffer.registry.encode('minecraft:item', pattern['template_item'])) + \
            cls.buffer.pack_chat(pattern['description']) + \
            cls.buffer.pack('?', decal)

        return data

    def unpack_armor_trim(self):
        return {
            'material': {
                'asset_name': self.buffer.unpack_string(),
                'item': self.buffer.registry.decode('minecraft:item', self.buffer.unpack_varint()),
                'item_model_index': self.buffer.unpack('f'),
                'override_armor_materials': {
                    self.buffer.unpack_string(): self.buffer.unpack_string() for _ in range(self.buffer.unpack_varint())
                },
                'description': self.buffer.unpack_chat()
            },
            'pattern': {
                'asset_name': self.buffer.unpack_string(),
                'template_item': self.buffer.registry.decode('minecraft:item', self.buffer.unpack_varint()),
                'description': self.buffer.unpack_chat(),
                'decal': self.buffer.unpack('?')
            }
        }