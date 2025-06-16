from typing import TYPE_CHECKING

from quarry.types.buffer.item.v1_20_5 import ItemBuffer1_20_5, attribute_operations, attribute_slots

if TYPE_CHECKING:
    from quarry.types.buffer import Buffer1_20_5


class ItemBuffer1_21(ItemBuffer1_20_5):
    component_handlers = list(ItemBuffer1_20_5.component_handlers.items())
    component_handlers.insert(42, ('jukebox_playable', (lambda cls: cls.pack_jukebox_playable, lambda self: self.unpack_jukebox_playable)))

    component_handlers = dict(component_handlers)
    component_types = list(component_handlers.keys())

    def __init__(self, buffer: 'Buffer1_20_5'):
        super(ItemBuffer1_21, self).__init__(buffer)

    @classmethod
    def pack_single_item(cls, value):
        if value is None:
            return cls.buffer.pack_varint(0)

        return cls.buffer.pack_varint(cls.buffer.registry.encode('minecraft:item', value['item'])) + \
            cls.pack_structured_data(value.get('structured_data', {}))

    def unpack_single_item(self):
        item = self.buffer.registry.decode('minecraft:item', self.buffer.unpack_varint())

        return {
            'count': 1,
            'item': item,
            'structured_data': self.unpack_structured_data()
        }

    # Attribute Modifiers ------------------------------------------------------------------

    @classmethod
    def pack_attribute_modifier(cls, value):
        return cls.buffer.pack_varint(cls.buffer.registry.encode('minecraft:attribute', value['type'])) + \
            cls.buffer.pack_string(value['id']) + \
            cls.buffer.pack('d', value['amount']) + \
            cls.buffer.pack_varint(attribute_operations.index(value['operation'])) + \
            cls.buffer.pack_varint(attribute_slots.index(value['slot']))

    def unpack_attribute_modifier(self):
        return {
            'type': self.buffer.registry.decode('minecraft:attribute', self.buffer.unpack_varint()),
            'id': self.buffer.unpack_string(),
            'amount': self.buffer.unpack('d'),
            'operation': attribute_operations[self.buffer.unpack_varint()],
            'slot': attribute_slots[self.buffer.unpack_varint()],
        }

    # Food ------------------------------------------------------------------

    @classmethod
    def pack_food(cls, value):
        effects = value.get('effects', [])
        can_always_eat = value.get('can_always_eat', False)
        eat_seconds = value.get('eat_seconds', 1.6)

        data = cls.buffer.pack_varint(value['nutrition']) + \
            cls.buffer.pack('f?f', value['saturation'], can_always_eat, eat_seconds) + \
            cls.buffer.pack_optional(cls.pack_single_item, value.get('using_converts_to', None)) + \
            cls.buffer.pack_varint(len(effects))

        for effect in effects:
            data += cls.pack_food_effect(effect)

        return data

    def unpack_food(self):
        return {
            'nutrition': self.buffer.unpack_varint(),
            'saturation': self.buffer.unpack('f'),
            'can_always_eat': self.buffer.unpack('?'),
            'eat_seconds': self.buffer.unpack('f'),
            'using_converts_to': self.buffer.unpack_optional(self.unpack_single_item),
            'effects': [self.unpack_food_effect() for _ in range(self.buffer.unpack_varint())],
        }

    # Jukebox Playable ------------------------------------------------------------------

    @classmethod
    def pack_jukebox_playable(cls, value):
        show_in_tooltip = value.get('show_in_tooltip', True)

        data = cls.buffer.pack_string(cls.buffer.registry.encode('minecraft:jukebox_song', value['song'])) + \
            cls.buffer.pack('?', show_in_tooltip)

        return data

    def unpack_jukebox_playable(self):
        return {
            'song': self.buffer.registry.decode('minecraft:jukebox_song', self.buffer.unpack_varint()),
            'show_in_tooltip': self.buffer.unpack('?'),
        }
