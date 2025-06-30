from quarry.types.buffer.v1_21_6 import Buffer1_21_6
from quarry.types.buffer.item.v1_21_7 import ItemBuffer1_21_7


class Buffer1_21_7(Buffer1_21_6):
    items = ItemBuffer1_21_7

    def __init__(self, data=None):
        super(Buffer1_21_6, self).__init__(data)
        self.items = ItemBuffer1_21_7(self)


Buffer1_21_7.items.buffer = Buffer1_21_7
