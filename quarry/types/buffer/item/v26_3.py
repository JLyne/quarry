from typing import TYPE_CHECKING

from quarry.types.buffer.item.v1_21_11 import swing_animation_types
from quarry.types.buffer.item.v26_2 import ItemBuffer26_2

if TYPE_CHECKING:
    from quarry.types.buffer import Buffer26_2

class ItemBuffer26_3(ItemBuffer26_2):
    component_handlers = list(ItemBuffer26_2.component_handlers.items())
    component_handlers.insert(40, ('attack_animation', (lambda cls: cls.pack_swing_animation, lambda self: self.unpack_swing_animation)))
    component_handlers.insert(41, ('interact_animation', (lambda cls: cls.pack_swing_animation, lambda self: self.unpack_swing_animation)))
    component_handlers.insert(43, ('block_transformer', (lambda cls: cls.pack_block_transformer, lambda self: self.unpack_block_transformer)))
    component_handlers.insert(44, ('villager_food', (lambda cls: cls.pack_villager_food, lambda self: self.unpack_villager_food)))
    del component_handlers[42] # Remove swing_animation
    del component_handlers[48] # Remove map_color
    component_handlers.append(('compostable', (lambda cls: cls.pack_compostable, lambda self: self.unpack_compostable)))
    component_handlers.append(('cooking_fuel', (lambda cls: cls.pack_cooking_fuel, lambda self: self.unpack_cooking_fuel)))
    component_handlers.append(('brewing_fuel', (lambda cls: cls.pack_brewing_fuel, lambda self: self.unpack_brewing_fuel)))
    component_handlers.append(('mob_visibility', (lambda cls: cls.pack_mob_visibility, lambda self: self.unpack_mob_visibility)))
    component_handlers.append(('provides_pottery_pattern', (lambda cls: cls.pack_provides_pottery_pattern, lambda self: self.unpack_provides_pottery_pattern)))
    component_handlers.append(('sign_text_front', (lambda cls: cls.pack_sign_text, lambda self: self.unpack_sign_text)))
    component_handlers.append(('sign_text_back', (lambda cls: cls.pack_sign_text, lambda self: self.unpack_sign_text)))
    component_handlers.append(('waxed', None))

    component_handlers = dict(component_handlers)
    component_types = list(component_handlers.keys())
    component_types[88:88] = [None for i in range (88, 117)]

    def __init__(self, buffer: 'Buffer26_2'):
        super(ItemBuffer26_2, self).__init__(buffer)

    # Fixed size list  ---------------------------------------------------------------

    @classmethod
    def pack_fixed_size_list(cls, value, size, packer):
        if len(value) != size:
            raise TypeError(f"Invalid list size, expected {size}, but got {len(value)}")

        result = b""

        for i in value:
            result += packer(i)

        return result

    @classmethod
    def unpack_fixed_size_list(cls, size, unpacker):
        return [ unpacker() for i in size]

    # Number provider  ---------------------------------------------------------------

    @classmethod
    def pack_int_or_number_provider(cls, value):
        if isinstance(value, str):
            return cls.buffer.pack('?', False) + cls.buffer.pack_string(value)
        elif isinstance(value, int):
            return cls.buffer.pack('?i', True, value)
        else:
            raise TypeError("Value should be an int or string")

    def unpack_int_or_number_provider(self):
        if self.buffer.unpack('?'):
            return self.buffer.unpack('i')
        else:
            return self.buffer.unpack_string()

    @classmethod
    def pack_float_or_number_provider(cls, value):
        if isinstance(value, str):
            return cls.buffer.pack('?', False) + cls.buffer.pack_string(value)
        elif isinstance(value, float):
            return cls.buffer.pack('?f', True, value)
        else:
            raise TypeError("Value should be a float or string")

    def unpack_float_or_number_provider(self):
        if self.buffer.unpack('?'):
            return self.buffer.unpack('f')
        else:
            return self.buffer.unpack_string()

    # Swing Animation  ---------------------------------------------------------------

    @classmethod
    def pack_swing_animation(cls, value):
        swing_animation = value.get('type', "whack")
        duration = value.get('duration', 6)

        return (cls.buffer.pack_varint(swing_animation_types.index(swing_animation))
                + cls.buffer.unpack_varint(duration))

    def unpack_swing_animation(self):
        return {
            'type': swing_animation_types[self.buffer.unpack_varint()],
            'duration': self.buffer.unpack_varint(),
        }

    # Block transformer  ---------------------------------------------------------------

    @classmethod
    def pack_block_transformer(cls, value):
       return cls.buffer.registry.encode('minecraft:block_transformer', value)

    def unpack_block_transformer(self):
        return self.buffer.registry.decode('minecraft:block_transformer', self.buffer.unpack_varint())

    # Villager food  ---------------------------------------------------------------

    @classmethod
    def pack_villager_food(cls, value):
        nutrition = value.get('nutrition', 1)

        return cls.buffer.pack_varint(nutrition)

    def unpack_villager_food(self):
        return {
            'nutrition': self.buffer.unpack_varint(),
        }

    # Compostable  ---------------------------------------------------------------

    @classmethod
    def pack_compostable(cls, value):
        return cls.pack_float_or_number_provider(value.get('layers', 0))

    def unpack_compostable(self):
        return {'layers' : self.unpack_float_or_number_provider() }

    # Cooking fuel  ---------------------------------------------------------------

    @classmethod
    def pack_cooking_fuel(cls, value):
        return (cls.pack_int_or_number_provider(value.get('burn_time', 0))
                + cls.pack_float_or_number_provider(value.get('speed_multiplier', 0.0)))

    def unpack_cooking_fuel(self):
        return {
            'burn_time': self.unpack_int_or_number_provider(),
            'speed_multiplier': self.unpack_float_or_number_provider()
        }

    # Brewing fuel  ---------------------------------------------------------------

    @classmethod
    def pack_brewing_fuel(cls, value):
        return (cls.pack_int_or_number_provider(value.get('uses', 0))
                + cls.pack_float_or_number_provider(value.get('speed_multiplier', 0.0)))

    def unpack_brewing_fuel(self):
        return {
            'uses': self.unpack_int_or_number_provider(),
            'speed_multiplier': self.unpack_float_or_number_provider()
        }

    # Mob visibility  -------------------------------------------------------------

    @classmethod
    def pack_mob_visibility(cls, value):
        return (cls.pack_registry_tag_or_list(value.get('targeting_entity_types', []), "minecraft:entity_type")
                + cls.buffer.pack('f', value.get('visibility', 0.0)))

    def unpack_mob_visibility(self):
        return {
            'uses': self.unpack_registry_tag_or_list("minecraft:entity_type"),
            'visibility': self.buffer.unpack('f')
        }

    # Provides banner pattern  ----------------------------------------------------

    @classmethod
    def pack_provides_pottery_pattern(cls, value):
        return cls.buffer.pack_varint(cls.buffer.registry.encode("minecraft:decorated_pot_pattern", value))

    def unpack_provides_pottery_pattern(self):
        return self.buffer.registry.decode("minecraft:decorated_pot_pattern", self.buffer.unpack_varint())


    # Sign text front/back0000  ---------------------------------------------------

    @classmethod
    def pack_sign_text(cls, value):
        messages = value.get('messages', ["", "", "", ""])
        filtered_messages = value.get('filtered_messages', None)
        color = value.get('color', "white")
        has_glowing_text = value.get('has_glowing_text', False)

        pack_lines = lambda lines: cls.pack_fixed_size_list(lines, 4, lambda line: cls.buffer.pack_chat(line))

        return (pack_lines(messages) +
                cls.buffer.pack_optional(pack_lines, filtered_messages) +
                cls.pack_dye(color) + cls.buffer.pack('?', has_glowing_text))

    def unpack_sign_text(self):
        return {
            'messages': self.unpack_fixed_size_list(4, self.buffer.unpack_chat),
            'filtered_messages': self.buffer.unpack_optional(self.unpack_fixed_size_list(4, self.buffer.unpack_chat)),
            'color': self.unpack_dye(),
            'has_glowing_text': self.buffer.unpack('?')
        }

    # Pot Decorations ------------------------------------------------------------------

    @classmethod
    def pack_pot_decorations(cls, value):
        item1 = value.get(0, None)
        item2 = value.get(1, None)
        item3 = value.get(2, None)
        item4 = value.get(3, None)

        return (cls.buffer.pack_optional(cls.buffer.pack_slot, item1) +
                cls.buffer.pack_optional(cls.buffer.pack_slot, item2) +
                cls.buffer.pack_optional(cls.buffer.pack_slot, item3) +
                cls.buffer.pack_optional(cls.buffer.pack_slot, item4))

    def unpack_pot_decorations(self):
        return [
            self.buffer.unpack_optional(self.buffer.unpack_slot()),
            self.buffer.unpack_optional(self.buffer.unpack_slot()),
            self.buffer.unpack_optional(self.buffer.unpack_slot()),
            self.buffer.unpack_optional(self.buffer.unpack_slot())
        ]

    # Consumable

    @classmethod
    def pack_consume_effect(cls, value):
        type = value.get('type')
        
        data = super().pack_consume_effect(value)

        if type == "teleport_randomly":
            data += cls.buffer.pack('?', value.get('directional_particles', True))

        return data


    def unpack_consume_effect(self):
        result = super().unpack_consume_effect()

        if result['type'] == 'teleport_randomly':
            result['directional_particles'] = self.buffer.unpack('?')

        return result