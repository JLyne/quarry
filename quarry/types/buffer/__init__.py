class BufferUnderrun(Exception):
    pass


from quarry.types.buffer.v1_20_3 import Buffer1_20_3
from quarry.types.buffer.v1_20_5 import Buffer1_20_5
from quarry.types.buffer.v1_21 import Buffer1_21
from quarry.types.buffer.v1_21_2 import Buffer1_21_2
from quarry.types.buffer.v1_21_4 import Buffer1_21_4


# Versioned buffers used after handshaking
buff_types = [
    (765, Buffer1_20_3),
    (766, Buffer1_20_5),
    (767, Buffer1_21),
    (768, Buffer1_21_2),
    (769, Buffer1_21_4),
]


# Used by NBT and during handshaking
class Buffer(buff_types[-1][1]):
    pass
