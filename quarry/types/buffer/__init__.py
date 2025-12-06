class BufferUnderrun(Exception):
    pass


from quarry.types.buffer.v1_20_3 import Buffer1_20_3
from quarry.types.buffer.v1_20_5 import Buffer1_20_5
from quarry.types.buffer.v1_21 import Buffer1_21
from quarry.types.buffer.v1_21_2 import Buffer1_21_2
from quarry.types.buffer.v1_21_4 import Buffer1_21_4
from quarry.types.buffer.v1_21_5 import Buffer1_21_5
from quarry.types.buffer.v1_21_6 import Buffer1_21_6
from quarry.types.buffer.v1_21_7 import Buffer1_21_7
from quarry.types.buffer.v1_21_9 import Buffer1_21_9
from quarry.types.buffer.v1_21_11 import Buffer1_21_11


# Versioned buffers used after handshaking
buff_types = [
    (765, Buffer1_20_3),
    (766, Buffer1_20_5),
    (767, Buffer1_21),
    (768, Buffer1_21_2),
    (769, Buffer1_21_4),
    (770, Buffer1_21_5),
    (771, Buffer1_21_6),
    (772, Buffer1_21_7),
    (773, Buffer1_21_9),
    (774, Buffer1_21_11),
]


# Used by NBT and during handshaking
class Buffer(buff_types[-1][1]):
    pass
