import functools
import json
import re
from typing import List, Optional, Tuple

from quarry.types.uuid import UUID


def _load_styles():
    data = {
        "0": "black",
        "1": "dark_blue",
        "2": "dark_green",
        "3": "dark_aqua",
        "4": "dark_red",
        "5": "dark_purple",
        "6": "gold",
        "7": "gray",
        "8": "dark_gray",
        "9": "blue",
        "a": "green",
        "b": "aqua",
        "c": "red",
        "d": "light_purple",
        "e": "yellow",
        "f": "white",
        "k": "obfuscated",
        "l": "bold",
        "m": "strikethrough",
        "n": "underline",
        "o": "italic",
        "r": "reset",
    }

    code_by_name = {}
    code_by_prop = {}
    for code, name in data.items():
        code_by_name[name] = code
        if code in "klmnor":
            if name == "underline":
                prop = "underlined"
            else:
                prop = name
            code_by_prop[prop] = code

    return code_by_name, code_by_prop


code_by_name, code_by_prop = _load_styles()


@functools.total_ordering
class Message(object):
    type_hints = {
        'text': 'text',
        'translatable': 'translate',
        'score': 'score',
        'selector': 'selector',
        'keybind': 'keybind',
        'nbt': 'nbt',
    }

    """
    Represents a Minecraft chat message.
    """
    def __init__(self, value):
        if isinstance(value, str):  # String, create component with string as text
            self.value = {'text': value}
        elif isinstance(value, list):  # list, create empty component with children
            extra = []
            for v in value:
                if isinstance(v, Message):
                    extra.append(v)
                else:
                    extra.append(Message(v))

            self.value = {'text': '', 'extra': extra}
        elif isinstance(value, dict):  # dict, validate and check for children
            self._validate(value)

            if 'extra' in value:
                extra = []
                for v in value['extra']:
                    if isinstance(v, Message):
                        extra.append(v)
                    else:
                        extra.append(Message(v))

                value['extra'] = extra

            self.value = value
        else:
            raise TypeError("Value is not a string or a list or dictionary")

    @classmethod
    def _validate(cls, message):
        type = cls._determine_type(message)

        if type != 'text' and cls.type_hints[type] not in message:
            raise TypeError(f"{type} message does not contain a f{cls.type_hints[type]} property")

    @classmethod
    def _determine_type(cls, message):
        if 'type' in message:
            if message.type not in cls.type_hints:
                raise TypeError("Unknown message type")

            return message.type

        for (type, field) in cls.type_hints.items():
            if field in message:
                return type

        return 'text'

    @classmethod
    def from_string(cls, string):
        return cls({'text': string})

    def to_string(self, strip_styles=True):
        """
        Minecraft uses a JSON format to represent chat messages; this method
        retrieves a plaintext representation, optionally including styles
        encoded using old-school chat codes (U+00A7 plus one character).
        """

        def parse(obj):
            if isinstance(obj, Message):  # Child components
                return obj.to_string()
            if isinstance(obj, str):
                return obj
            if isinstance(obj, list):
                return "".join((parse(e) for e in obj))
            if isinstance(obj, dict):
                text = ""
                for prop, code in code_by_prop.items():
                    if obj.get(prop):
                        text += "\u00a7" + code
                if "color" in obj:
                    text += "\u00a7" + code_by_name[obj["color"]]
                if "translate" in obj:
                    text += obj["translate"]
                    if "with" in obj:
                        args = ", ".join((parse(e) for e in obj["with"]))
                        text += "{%s}" % args
                if "text" in obj:
                    text += obj["text"]
                if "extra" in obj:
                    text += parse(obj["extra"])
                return text

        text = parse(self.value)
        if strip_styles:
            text = self.strip_chat_styles(text)
        return text

    def flatten(self):
        result = self.value.copy()
        if 'extra' in result:
            result['extra'] = [m.flatten() for m in result['extra']]

        return result

    def to_nbt(self):
        from quarry.types.nbt import TagRoot

        # Flatten all child components to dicts first
        return TagRoot.from_obj(self.flatten())

    def to_json(self):
        return json.dumps(self.flatten())

    @classmethod
    def strip_chat_styles(cls, text):
        return re.sub("\u00A7.", "", text)

    def __eq__(self, other):
        return self.value == other.value

    def __lt__(self, other):
        return self.value < other.value

    def __str__(self):
        return self.to_string()

    def __repr__(self):
        return "<Message %r>" % str(self)


class SignedMessageHeader(object):
    """
    Represents the header of a signed minecraft chat message
    Includes the sender UUID, message index and optional signature
    """

    def __init__(self, sender: UUID, index: int, signature: bytes = None):
        self.sender = sender
        self.index = index
        self.signature = signature

    def __eq__(self, other):
        if isinstance(other, SignedMessageHeader):
            return self.sender == other.sender and self.index == other.index and self.signature == self.signature
        return NotImplemented


class SignedMessageBody(object):
    """
    Represents the body of a signed minecraft chat message
    Includes the message content, timestamp, salt and list of last seen messagesids/signatures
    """

    def __init__(self, message: str, timestamp: int, salt: int, last_seen: List[Tuple[int, Optional[bytes]]]):
        self.message = message
        self.timestamp = timestamp
        self.salt = salt
        self.last_seen = last_seen

    def digest(self):
        # TODO
        raise NotImplementedError()

    def __eq__(self, other):
        if isinstance(other, SignedMessageBody):
            return self.message == other.message \
                   and self.timestamp == other.timestamp \
                   and self.salt == other.salt
        return NotImplemented


class SignedMessageFormatting(object):
    """
    Represents the formatting information of a signed minecraft chat message
    Includes the chat message type, sender name and optional target name components
    """

    def __init__(self, chat_type: int, sender_name: Message, target_name: Message = None):
        self.chat_type = chat_type
        self.sender_name = sender_name
        self.target_name = target_name

    def __eq__(self, other):
        if isinstance(other, SignedMessageFormatting):
            return self.chat_type == other.chat_type and self.sender_name == other.sender_name and self.target_name == self.target_name
        return NotImplemented

class SignedMessageFiltering(object):
    """
    Represents the fitlering information of a signed minecraft chat message
    Includes the filter type and optional filter type bits
    """

    def __init__(self, filter_type: int, filter_type_bits: Optional[List[int]] = None):
        self.filter_type = filter_type

        if self.filter_type != 1 and filter_type_bits is not None:
            raise ValueError("Only partially filtered messages should have filter_type_bits")

        if self.filter_type == 1 and filter_type_bits is None:
            raise ValueError("filter_type_bits are required for partially filtered messages")

        self.filter_type_bits = filter_type_bits

    def __eq__(self, other):
        if isinstance(other, SignedMessageFiltering):
            return self.filter_type == other.filter_type and self.filter_type_bits == other.filter_type_bits
        return NotImplemented


class SignedMessage(object):
    """
    Represents a signed minecraft chat message
    Includes:
     - The message header, containing the sender UUID, message index and optional signature.
     - The message body, containing the message content, timestamp and salt.
     - The message filtering, containing the chat message filter type and optional filter type bits.
     - The message formatting, containing the chat message type, sender name and optional target name components.
     - Optional unsigned message content.
    The message signature can be checked with verify()
    """

    def __init__(self, header: SignedMessageHeader, body: SignedMessageBody,
                 filtering: SignedMessageFiltering, formatting: SignedMessageFormatting,
                 unsigned_content: Message = None):
        self.header = header
        self.body = body
        self.filtering = filtering
        self.formatting = formatting
        self.unsigned_content = unsigned_content

    def verify(self):
        # TODO
        raise NotImplementedError()

    def __eq__(self, other):
        if isinstance(other, SignedMessage):
            return self.header == other.header \
                   and self.body == other.body \
                   and self.filtering == other.filtering \
                   and self.formatting == other.formatting \
                   and self.unsigned_content == other.unsigned_content
        return NotImplemented
