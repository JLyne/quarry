from quarry.types.buffer.v1_20_3 import Buffer1_20_3


class Buffer1_20_5(Buffer1_20_3):
    @classmethod
    def pack_entity_metadata(cls, metadata):
        """
        Packs entity metadata.
        """

        pack_position = lambda pos: cls.pack_position(*pos)
        pack_global_position = lambda pos: cls.pack_global_position(*pos)

        out = b""
        for ty_key, val in metadata.items():
            ty, key = ty_key
            out += cls.pack('B', key)
            out += cls.pack_varint(ty)

            if   ty == 0:  out += cls.pack('b', val)
            elif ty == 1:  out += cls.pack_varint(val)
            elif ty == 2:  raise ValueError("TODO")  # VarLong
            elif ty == 3:  out += cls.pack('f', val)
            elif ty == 4:  out += cls.pack_string(val)
            elif ty == 5:  out += cls.pack_chat(val)
            elif ty == 6:  out += cls.pack_optional(cls.pack_chat, val)
            elif ty == 7:  out += cls.pack_slot(**val)
            elif ty == 8:  out += cls.pack('?', val)
            elif ty == 9:  out += cls.pack_rotation(*val)
            elif ty == 10:  out += cls.pack_position(*val)
            elif ty == 11: out += cls.pack_optional(pack_position, val)
            elif ty == 12: out += cls.pack_direction(val)
            elif ty == 13: out += cls.pack_optional(cls.pack_uuid, val)
            elif ty == 14: out += cls.pack_block(val)
            elif ty == 15: out += cls.pack_optional(cls.pack_block, val)
            elif ty == 16: out += cls.pack_nbt(val)
            elif ty == 17: out += cls.pack_particle(*val)
            elif ty == 18: raise ValueError("TODO")  # Particle array
            elif ty == 19: out += cls.pack_villager(*val)
            elif ty == 20: out += cls.pack_optional_varint(val)
            elif ty == 21: out += cls.pack_pose(val)
            elif ty == 22: out += cls.pack_varint(val)
            elif ty == 23: out += cls.pack_varint(val)
            elif ty == 24: out += cls.pack_varint(val)
            elif ty == 25: out += cls.pack_optional(pack_global_position, val)
            elif ty == 26: out += cls.pack_varint(val)
            elif ty == 27: out += cls.pack_varint(val)
            elif ty == 28: out += cls.pack_varint(val)
            elif ty == 29: raise ValueError("TODO")  # Vector3
            elif ty == 30: raise ValueError("TODO")  # Quaternion
            else: raise ValueError("Unknown entity metadata type: %d" % ty)
        out += cls.pack('B', 255)
        return out

    def unpack_entity_metadata(self):
        """
        Unpacks entity metadata.
        """

        metadata = {}
        while True:
            key = self.unpack('B')
            if key == 255:
                return metadata
            ty = self.unpack('B')
            if   ty == 0:  val = self.unpack('b')
            elif ty == 1:  val = self.unpack_varint()
            elif ty == 2:  raise ValueError("TODO")  # VarLong
            elif ty == 3:  val = self.unpack('f')
            elif ty == 4:  val = self.unpack_string()
            elif ty == 5:  val = self.unpack_chat()
            elif ty == 6:  val = self.unpack_optional(self.unpack_chat)
            elif ty == 7:  val = self.unpack_slot()
            elif ty == 8:  val = self.unpack('?')
            elif ty == 9:  val = self.unpack_rotation()
            elif ty == 10:  val = self.unpack_position()
            elif ty == 11: val = self.unpack_optional(self.unpack_position)
            elif ty == 12: val = self.unpack_direction()
            elif ty == 13: val = self.unpack_optional(self.unpack_uuid)
            elif ty == 14: val = self.unpack_block()
            elif ty == 15: val = self.unpack_optional(self.unpack_block())
            elif ty == 16: val = self.unpack_nbt()
            elif ty == 17: val = self.unpack_particle()
            elif ty == 18: raise ValueError("TODO")  # Particle array
            elif ty == 19: val = self.unpack_villager()
            elif ty == 20: val = self.unpack_optional_varint()
            elif ty == 21: val = self.unpack_pose()
            elif ty == 22: val = self.unpack_varint()
            elif ty == 23: val = self.unpack_varint()
            elif ty == 24: val = self.unpack_varint()
            elif ty == 25: val = self.unpack_optional(self.unpack_global_position)
            elif ty == 26: val = self.unpack_varint()
            elif ty == 27: val = self.unpack_varint()
            elif ty == 28: val = self.unpack_varint()
            elif ty == 29: raise ValueError("TODO")  # Vector3
            elif ty == 30: raise ValueError("TODO")  # Quaternion
            else: raise ValueError("Unknown entity metadata type: %d" % ty)
            metadata[ty, key] = val
