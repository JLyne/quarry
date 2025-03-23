from quarry.types.buffer.v1_21_4 import Buffer1_21_4
from quarry.types.buffer.item.v1_21_5 import ItemBuffer1_21_5


class Buffer1_21_5(Buffer1_21_4):
    items = ItemBuffer1_21_5

    def __init__(self, data=None):
        super(Buffer1_21_4, self).__init__(data)
        self.items = ItemBuffer1_21_5(self)


Buffer1_21_5.items.buffer = Buffer1_21_5
