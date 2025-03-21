from typing import TYPE_CHECKING

from quarry.types.buffer.item.v1_21_2 import ItemBuffer1_21_2

if TYPE_CHECKING:
    from quarry.types.buffer import Buffer1_21_2


class ItemBuffer1_21_4(ItemBuffer1_21_2):
    component_handlers = ItemBuffer1_21_2.component_handlers
    component_handlers['custom_model_data'] = lambda cls: cls.pack_custom_model_data, lambda self: self.unpack_custom_model_data,

    def __init__(self, buffer: 'Buffer1_21_2'):
        super(ItemBuffer1_21_2, self).__init__(buffer)

    # Equippable ---------------------------------------------------------------

    @classmethod
    def pack_equippable(cls, value):
        value['asset_id'] = value.get('model', None) # Model renamed to asset_id
        del value['model']

        return super().pack_equippable(value)

    def unpack_equippable(self):
        data = super().unpack_equippable()

        data['asset_id'] = data.get('Model', None) # Model renamed to asset_id
        del data['model']

        return data

    # Custom Model Data ---------------------------------------------------------------

    @classmethod
    def pack_custom_model_data(cls, value):
        floats = value.get('floats', [])
        flags = value.get('flags', [])
        strings = value.get('strings', [])
        colors = value.get('colors', [])

        data = cls.buffer.pack_varint(len(floats)) + \
            cls.buffer.pack_array('f', floats) + \
            cls.buffer.pack_varint(len(flags)) + \
            cls.buffer.pack_array('?', flags) + \
            cls.buffer.pack_varint(len(strings))

        for string in strings:
            data += cls.buffer.pack_string(string)

        data += cls.buffer.pack_varint(len(colors))

        for color in colors:
            if isinstance(color, list): # int rgb array
                data += cls.buffer.pack('i', color[0]<<16 + color[1]<<8 + color[2])
            else: # Single int
                data += cls.buffer.pack('i', color)

        return data

    def unpack_custom_model_data(self):
        return {
            'floats': self.buffer.unpack_array('f', self.buffer.unpack_varint()),
            'flags': self.buffer.unpack_array('?', self.buffer.unpack_varint()),
            'strings': [self.buffer.unpack_string() for _ in self.buffer.unpack_varint()],
            'colors': [self.buffer.unpack('i') for _ in self.buffer.unpack_varint()],
        }
