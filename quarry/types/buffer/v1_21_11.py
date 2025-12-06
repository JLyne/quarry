from quarry.types.buffer.v1_21_9 import Buffer1_21_9
from quarry.types.buffer.item.v1_21_11 import ItemBuffer1_21_11


class Buffer1_21_11(Buffer1_21_9):
    items = ItemBuffer1_21_11

    def __init__(self, data=None):
        super(Buffer1_21_9, self).__init__(data)
        self.items = ItemBuffer1_21_11(self)

Buffer1_21_11.items.buffer = Buffer1_21_11
