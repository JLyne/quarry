class BufferUnderrun(Exception):
    pass


from quarry.types.buffer.v1_20_3 import Buffer1_20_3
from quarry.types.buffer.v1_20_5 import Buffer1_20_5


# Versioned buffers used after handshaking
buff_types = [
    (765, Buffer1_20_3),
    (766, Buffer1_20_5),
]


# Used by NBT and during handshaking
class Buffer(buff_types[-1][1]):
    pass
