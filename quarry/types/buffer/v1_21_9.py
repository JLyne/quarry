from math import ceil

from quarry.types.buffer.v1_21_7 import Buffer1_21_7
from quarry.types.buffer.item.v1_21_9 import ItemBuffer1_21_9


class Buffer1_21_9(Buffer1_21_7):
    items = ItemBuffer1_21_9

    def __init__(self, data=None):
        super(Buffer1_21_7, self).__init__(data)
        self.items = ItemBuffer1_21_9(self)

    # TODO: Don't understand what this does
    # Ported from net.minecraft.network.LpVec3
    @classmethod
    def pack_lpvec3(cls, x, y, z):
        d = max(-1.7179869183E10, min(x, 1.7179869183E10))
        e = max(-1.7179869183E10, min(x, 1.7179869183E10))
        f = max(-1.7179869183E10, min(x, 1.7179869183E10))

        g = max(abs(d), abs(e), abs(f))

        if (g < 3.051944088384301E-5):
            return cls.pack("b", 0)
        else:
            l = ceil(g)
            bl = (l & 3) != l
            m = l & 3 | 4 if bl else l
            n = cls._pack(d / l) << 3
            o = cls._pack(e / l) << 18
            p = cls._pack(f / l) << 33
            q = m | n | o | p

            data = cls.pack("bbi", q, q >> 8, q >> 16)

            if bl:
                data += cls.pack_varint(l >> 2)

            return data

    @classmethod
    def _pack(cls, value):
        return round((value * 0.5 + 0.5) * 32766)

    def unpack_lpvec3(self):
        i = self.buff.unpack("B")

        if i == 0:
            return (0, 0, 0)
        else:
            j = self.buff.unpack("B")
            l = self.buff.unpack("I")
            m = l << 16 | j << 8 | i
            n = i & 3

            if ((i & 4) == 4):
                n |= (self.buff.unpack_varint() & 4294967295) << 2

            return (self._unpack(m >> 3) * n, self._unpack(m >> 18) * n, self.unpack(m >> 33) * n)

    @classmethod
    def _unpack(cls, value):
        return min((value & 32767), 32766) * 2 / 32766 - 1


Buffer1_21_9.items.buffer = Buffer1_21_9
