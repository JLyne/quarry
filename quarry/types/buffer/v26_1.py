from quarry.types.buffer.v1_21_11 import Buffer1_21_11
from quarry.types.buffer.item.v26_1 import ItemBuffer26_1


class Buffer26_1(Buffer1_21_11):
    items = ItemBuffer26_1

    def __init__(self, data=None):
        super(Buffer1_21_11, self).__init__(data)
        self.items = ItemBuffer26_1(self)

Buffer26_1.items.buffer = Buffer26_1
