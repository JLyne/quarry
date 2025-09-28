from typing import TYPE_CHECKING

from quarry.types.buffer.item.v1_21_5 import ItemBuffer1_21_5

if TYPE_CHECKING:
    from quarry.types.buffer import Buffer1_21_6

attribute_display_types = [
    'default',
    'hidden',
    'override'
]


class ItemBuffer1_21_6(ItemBuffer1_21_5):
    component_handlers = dict(ItemBuffer1_21_5.component_handlers)

    def __init__(self, buffer: 'Buffer1_21_6'):
        super(ItemBuffer1_21_5, self).__init__(buffer)

    # Equippable  ---------------------------------------------------------------

    @classmethod
    def pack_equippable(cls, value):
        data = super().pack_equippable(value)
        can_be_sheared = value.get('can_be_sheared', False)
        shearing_sound = value.get('can_be_sheared', {'sound_id', 'item.shears.snip'})

        return data + cls.buffer.pack('?', can_be_sheared) + cls.pack_sound_event(shearing_sound)

    def unpack_equippable(self):
        data = super().unpack_equippable()
        data['can_be_sheared'] = self.buffer.unpack('?')
        data['shearing_sound'] = self.unpack_sound_event()

        return data

    @classmethod
    def pack_attribute_modifier(cls, value):
        data = super().pack_attribute_modifier(value)
        display = value.get('display', {'type': 'default'})

        data += cls.buffer.pack_varint(attribute_display_types.index(display.get('type', 'default')))

        if display.get('type', 'default') == 'override':
            data += cls.buffer.pack_chat(display.get('text', ''))

    def unpack_attribute_modifier(self):
        data = super().unpack_attribute_modifier()

        display_type = attribute_display_types[self.buffer.unpack_varint()]

        data['display'] = {
            'type': display_type,
        }

        if display_type == 'override':
            data['display']['text'] = self.buffer.unpack_chat()

        return data
