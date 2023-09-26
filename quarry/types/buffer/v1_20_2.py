from quarry.types.buffer.v1_19_4 import Buffer1_19_4


class Buffer1_20_2(Buffer1_19_4):
    @classmethod
    def pack_nbt(cls, tag=None):
        """
        Packs an NBT tag
        """
        from quarry.types.nbt import TagRoot
        if isinstance(tag, TagRoot):
            return tag.to_bytes(True)

        return super().pack_nbt(tag)

    def unpack_nbt(self):
        """
        Unpacks NBT tag(s).
        """

        from quarry.types import nbt
        return nbt.TagRoot.from_buff(self, True)
