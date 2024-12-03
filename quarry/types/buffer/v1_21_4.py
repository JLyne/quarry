from quarry.types.buffer.v1_21_2 import Buffer1_21_2
from quarry.types.buffer.item.v1_21_4 import ItemBuffer1_21_4


class Buffer1_21_4(Buffer1_21_2):
    items = ItemBuffer1_21_4

    def __init__(self, data=None):
        super(Buffer1_21_2, self).__init__(data)
        self.items = ItemBuffer1_21_4(self)


Buffer1_21_4.items.buffer = Buffer1_21_4
