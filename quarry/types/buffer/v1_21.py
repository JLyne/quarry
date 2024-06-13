from quarry.types.buffer.item.v1_21 import ItemBuffer1_21
from quarry.types.buffer.v1_20_5 import Buffer1_20_5


class Buffer1_21(Buffer1_20_5):
    items = ItemBuffer1_21

    def __init__(self, data=None):
        super(Buffer1_20_5, self).__init__(data)
        self.items = ItemBuffer1_21(self)


Buffer1_21.items.buffer = Buffer1_21
