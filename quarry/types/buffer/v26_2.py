from quarry.types.buffer.v26_1 import Buffer26_1
from quarry.types.buffer.item.v26_2 import ItemBuffer26_2


class Buffer26_2(Buffer26_1):
    items = ItemBuffer26_2

    def __init__(self, data=None):
        super(Buffer26_1, self).__init__(data)
        self.items = ItemBuffer26_2(self)

Buffer26_2.items.buffer = Buffer26_2
