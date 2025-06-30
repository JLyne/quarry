from quarry.types.buffer.v1_21_5 import Buffer1_21_5
from quarry.types.buffer.item.v1_21_6 import ItemBuffer1_21_6


class Buffer1_21_6(Buffer1_21_5):
    items = ItemBuffer1_21_6

    def __init__(self, data=None):
        super(Buffer1_21_5, self).__init__(data)
        self.items = ItemBuffer1_21_6(self)


Buffer1_21_6.items.buffer = Buffer1_21_6
