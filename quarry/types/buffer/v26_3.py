from quarry.types.buffer.v26_2 import Buffer26_2
from quarry.types.buffer.item.v26_3 import ItemBuffer26_3


class Buffer26_3(Buffer26_2):
    items = ItemBuffer26_3

    def __init__(self, data=None):
        super(Buffer26_2, self).__init__(data)
        self.items = ItemBuffer26_3(self)

Buffer26_3.items.buffer = Buffer26_3
