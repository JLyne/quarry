from quarry.types.buffer.v1_20_2 import Buffer1_20_2


class Buffer1_20_3(Buffer1_20_2):
    @classmethod
    def pack_chat(cls, message):
        """
        Pack an nbt-format Minecraft chat message.
        """
        from quarry.types import chat

        if not isinstance(message, chat.Message):
            message = chat.Message.from_string(message)
        return cls.pack_nbt(message.to_nbt())

    def unpack_chat(self):
        """
        Unpack an nbt-format Minecraft chat message.
        """
        from quarry.types import chat
        nbt = self.unpack_nbt()
        return chat.Message(nbt.body.to_obj())

    @classmethod
    def pack_chat_string(cls, message):
        return super().pack_chat(message)

    def unpack_chat_string(self):
        return super().unpack_chat()
