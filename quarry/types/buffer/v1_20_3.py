import json
import string
import struct
import zlib
from typing import List

from cryptography.hazmat.primitives._serialization import Encoding, PublicFormat

from quarry.net.auth import PlayerPublicKey
from quarry.net.crypto import import_public_key
from quarry.types.buffer import BufferUnderrun
from quarry.types.chat import LastSeenMessage, SignedMessage, SignedMessageHeader, SignedMessageBody
from quarry.types.chunk import BlockArray
from quarry.types.registry import OpaqueRegistry
from quarry.types.uuid import UUID

directions = ("down", "up", "north", "south", "west", "east")
poses = ('standing', 'fall_flying', 'sleeping', 'swimming', 'spin_attack',
         'sneaking', 'dying')
smelt_types = ('minecraft:smelting', 'minecraft:blasting',
               'minecraft:smoking', 'minecraft:campfire_cooking')
simple_recipe_types = ('minecraft:crafting_decorated_pot', 'minecraft:crafting_special_armordye',
                       'minecraft:crafting_special_bookcloning', 'minecraft:crafting_special_mapcloning',
                       'minecraft:crafting_special_mapextending',  'minecraft:crafting_special_firework_rocket',
                       'minecraft:crafting_special_firework_star', 'minecraft:crafting_special_firework_star_fade',
                       'minecraft:crafting_special_tippedarrow', 'minecraft:crafting_special_bannerduplicate',
                       'minecraft:crafting_special_shielddecoration', 'minecraft:crafting_special_shulkerboxcoloring',
                       'minecraft:crafting_special_suspiciousstew', 'minecraft:crafting_special_repairitem')


class Buffer1_20_3:
    buff = b""
    pos = 0
    registry = OpaqueRegistry(14)

    def __init__(self, data=None):
        if data:
            self.buff = data

    def __len__(self):
        return len(self.buff) - self.pos

    def add(self, data):
        """
        Add some bytes to the end of the buffer.
        """

        self.buff += data

    def save(self):
        """
        Saves the buffer contents.
        """

        self.buff = self.buff[self.pos:]
        self.pos = 0

    def restore(self):
        """
        Restores the buffer contents to its state when :meth:`save` was last
        called.
        """

        self.pos = 0

    def discard(self):
        """
        Discards the entire buffer contents.
        """

        self.pos = len(self.buff)

    def read(self, length=None):
        """
        Read *length* bytes from the beginning of the buffer, or all bytes if
        *length* is ``None``
        """

        if length is None:
            data = self.buff[self.pos:]
            self.pos = len(self.buff)
        else:
            if self.pos + length > len(self.buff):
                raise BufferUnderrun()

            data = self.buff[self.pos:self.pos+length]
            self.pos += length

        return data

    def hexdump(self):
        data = self.buff[self.pos:]
        lines = ['']
        bytes_read = 0
        while len(data) > 0:
            data_line, data = data[:16], data[16:]

            l_hex = []
            l_str = []
            for i, c in enumerate(data_line):
                l_hex.append(f"{c:02x}")
                c_str = data_line[i:i + 1]
                l_str.append(c_str if c_str in string.printable else ".")

            l_hex.extend(['  '] * (16 - len(l_hex)))
            l_hex.insert(8, '')

            lines.append(f"{bytes_read:08x}  {' '.join(l_hex)}  |{''.join(l_str)}|")

            bytes_read += len(data_line)

        return "\n    ".join(lines + [f"{bytes_read:08x}"])

    # Basic data types --------------------------------------------------------

    @classmethod
    def pack(cls, fmt, *fields):
        """
        Pack *fields* into a struct. The format accepted is the same as for
        ``struct.pack()``.
        """

        return struct.pack(">"+fmt, *fields)

    def unpack(self, fmt):
        """
        Unpack a struct. The format accepted is the same as for
        ``struct.unpack()``.
        """
        fmt = ">" + fmt
        data = self.read(struct.calcsize(fmt))
        fields = struct.unpack(fmt, data)
        if len(fields) == 1:
            fields = fields[0]
        return fields

    # Array data types --------------------------------------------------------

    @classmethod
    def pack_array(cls, fmt, array):
        """
        Packs *array* into a struct. The format accepted is the same as for
        ``struct.pack()``.
        """
        return struct.pack(">" + fmt * len(array), *array)

    def unpack_array(self, fmt, length):
        """
        Unpack an array struct. The format accepted is the same as for
        ``struct.unpack()``.
        """
        data = self.read(struct.calcsize(">" + fmt) * length)
        return list(struct.unpack(">" + fmt * length, data))

    @classmethod
    def pack_byte_array(cls, data):
        """
        Packs an array of bytes preceded by variant denoting the array length.
        """
        return cls.pack_varint(len(data)) + data

    def unpack_byte_array(self):
        """
        Unpack an array of bytes preceded by variant denoting the array length.
        """
        return self.read(self.unpack_varint())

    # Optional ----------------------------------------------------------------

    @classmethod
    def pack_optional(cls, packer, val):
        """
        Packs a boolean indicating whether *val* is None. If not,
        ``packer(val)`` is appended to the returned string.
        """

        if val is None:
            return cls.pack('?', False)
        else:
            return cls.pack('?', True) + packer(val)

    def unpack_optional(self, unpacker):
        """
        Unpacks a boolean. If it's True, return the value of ``unpacker()``.
        Otherwise return None.
        """
        if self.unpack('?'):
            return unpacker()
        else:
            return None

    # Varint ------------------------------------------------------------------

    @classmethod
    def pack_varint(cls, number, max_bits=32):
        """
        Packs a varint.
        """

        number_min = -1 << (max_bits - 1)
        number_max = +1 << (max_bits - 1)
        if not (number_min <= number < number_max):
            raise ValueError(f"varint does not fit in range: {number_min:d} <= {number:d} < {number_max:d}")

        if number < 0:
            number += 1 << 32

        out = b""
        for i in range(10):
            b = number & 0x7F
            number >>= 7
            out += cls.pack("B", b | (0x80 if number > 0 else 0))
            if number == 0:
                break
        return out

    def unpack_varint(self, max_bits=32):
        """
        Unpacks a varint.
        """

        number = 0
        for i in range(10):
            b = self.unpack("B")
            number |= (b & 0x7F) << 7*i
            if not b & 0x80:
                break

        if number & (1 << 31):
            number -= 1 << 32

        number_min = -1 << (max_bits - 1)
        number_max = +1 << (max_bits - 1)
        if not (number_min <= number < number_max):
            raise ValueError(f"varint does not fit in range: {number_min:d} <= {number:d} < {number_max:d}")

        return number

    # Packet ------------------------------------------------------------------

    @classmethod
    def pack_packet(cls, data, compression_threshold=-1):
        """
        Unpacks a packet frame. This method handles length-prefixing and
        compression.
        """

        if compression_threshold >= 0:
            # Compress data and prepend uncompressed data length
            if len(data) >= compression_threshold:
                data = cls.pack_varint(len(data)) + zlib.compress(data)
            else:
                data = cls.pack_varint(0) + data

        # Prepend packet length
        return cls.pack_varint(len(data), max_bits=32) + data

    def unpack_packet(self, cls, compression_threshold=-1):
        """
        Unpacks a packet frame. This method handles length-prefixing and
        compression.
        """
        body = self.read(self.unpack_varint(max_bits=32))
        buff = cls(body)
        if compression_threshold >= 0:
            uncompressed_length = buff.unpack_varint()
            if uncompressed_length > 0:
                body = zlib.decompress(buff.read())
                buff = cls(body)

        return buff

    # String ------------------------------------------------------------------

    @classmethod
    def pack_string(cls, text):
        """
        Pack a varint-prefixed utf8 string.
        """

        text = text.encode("utf-8")
        return cls.pack_varint(len(text), max_bits=16) + text

    def unpack_string(self):
        """
        Unpack a varint-prefixed utf8 string.
        """

        length = self.unpack_varint(max_bits=16)
        text = self.read(length).decode("utf-8")
        return text

    # JSON --------------------------------------------------------------------

    @classmethod
    def pack_json(cls, obj):
        """
        Serialize an object to JSON and pack it to a Minecraft string.
        """
        return cls.pack_string(json.dumps(obj))

    def unpack_json(self):
        """
        Unpack a Minecraft string and interpret it as JSON.
        """

        obj = json.loads(self.unpack_string())
        return obj

    # Chat --------------------------------------------------------------------

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
        """
        Pack a Minecraft chat message.
        """
        from quarry.types import chat
        if not isinstance(message, chat.Message):
            message = chat.Message.from_string(message)
        return cls.pack_string(message.to_json())

    def unpack_chat_string(self):
        """
        Unpack a Minecraft chat message.
        """
        from quarry.types import chat
        return chat.Message(self.unpack_string())

    # UUID --------------------------------------------------------------------

    @classmethod
    def pack_uuid(cls, uuid):
        """
        Packs a UUID.
        """

        return uuid.to_bytes()

    def unpack_uuid(self):
        """
        Unpacks a UUID.
        """

        return UUID.from_bytes(self.read(16))

    # Position ----------------------------------------------------------------

    @classmethod
    def pack_position(cls, x, y, z):
        """
        Packs a Position.
        """

        def pack_twos_comp(bits, number):
            if number < 0:
                number = number + (1 << bits)
            return number

        return cls.pack('Q', sum((
            pack_twos_comp(26, x) << 38,
            pack_twos_comp(26, z) << 12,
            pack_twos_comp(12, y))))

    def unpack_position(self):
        """
        Unpacks a position.
        """

        def unpack_twos_comp(bits, number):
            if (number & (1 << (bits - 1))) != 0:
                number = number - (1 << bits)
            return number

        number = self.unpack('Q')
        x = unpack_twos_comp(26, (number >> 38))
        z = unpack_twos_comp(26, (number >> 12 & 0x3FFFFFF))
        y = unpack_twos_comp(12, (number & 0xFFF))
        return x, y, z

    # Block -------------------------------------------------------------------

    @classmethod
    def pack_block(cls, block, packer=None):
        """
        Packs a block.
        """
        if packer is None:
            packer = cls.pack_varint
        return packer(cls.registry.encode_block(block))

    def unpack_block(self, unpacker=None):
        """
        Unpacks a block.
        """
        if unpacker is None:
            unpacker = self.unpack_varint
        return self.registry.decode_block(unpacker())

    # Slot --------------------------------------------------------------------

    @classmethod
    def pack_slot(cls, item=None, count=1, tag=None):
        """
        Packs a slot.
        """

        if item is None:
            return cls.pack('?', False)
        else:
            return cls.pack('?', True) + \
                   cls.pack_varint(
                       cls.registry.encode('minecraft:item', item)) + \
                   cls.pack('b', count) + \
                   cls.pack_nbt(tag)

    def unpack_slot(self):
        """
        Unpacks a slot.
        """

        slot = {}
        item_id = self.unpack_optional(self.unpack_varint)
        if item_id is None:
            slot['item'] = None
        else:
            slot['item'] = self.registry.decode('minecraft:item', item_id)
            slot['count'] = self.unpack('b')
            slot['tag'] = self.unpack_nbt()
        return slot

    # NBT ---------------------------------------------------------------------

    @classmethod
    def pack_nbt(cls, tag=None):
        """
        Packs an NBT tag
        """

        from quarry.types.nbt import TagRoot
        if isinstance(tag, TagRoot):
            return tag.to_bytes(True)

        if tag is None:
            # slower but more obvious:
            #   from quarry.types import nbt
            #   tag = nbt.TagRoot({})
            return b"\x00"

        return tag.to_bytes()

    def unpack_nbt(self):
        """
        Unpacks NBT tag(s).
        """

        from quarry.types import nbt
        return nbt.TagRoot.from_buff(self, True)

    # Entity metadata ---------------------------------------------------------

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
            elif ty == 2:  out += cls.pack('q', val)
            elif ty == 3:  out += cls.pack('f', val)
            elif ty == 4:  out += cls.pack_string(val)
            elif ty == 5:  out += cls.pack_chat(val)
            elif ty == 6:  out += cls.pack_optional(cls.pack_chat, val)
            elif ty == 7:  out += cls.pack_slot(**val)
            elif ty == 8:  out += cls.pack('?', val)
            elif ty == 9:  out += cls.pack_rotation(*val)
            elif ty == 10: out += cls.pack_position(*val)
            elif ty == 11: out += cls.pack_optional(pack_position, val)
            elif ty == 12: out += cls.pack_direction(val)
            elif ty == 13: out += cls.pack_optional(cls.pack_uuid, val)
            elif ty == 14: out += cls.pack_block(val)
            elif ty == 15: out += cls.pack_block(val)
            elif ty == 16: out += cls.pack_nbt(val)
            elif ty == 17: out += cls.pack_particle(*val)
            elif ty == 18: out += cls.pack_villager(*val)
            elif ty == 19: out += cls.pack_optional_varint(val)
            elif ty == 20: out += cls.pack_pose(val)
            elif ty == 21: out += cls.pack_varint(val)
            elif ty == 22: out += cls.pack_varint(val)
            elif ty == 23: out += cls.pack_optional(pack_global_position, val)
            elif ty == 24: out += cls.pack_varint(val)  # Painting variant type
            elif ty == 25: out += cls.pack_varint(val)  # Sniffer state
            elif ty == 26: out += cls.pack('fff', val[0], val[1], val[2])  # Vector
            elif ty == 27: out += cls.pack('ffff', val[0], val[1], val[2], val[3])  # Quaternion
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
            elif ty == 2:  val = self.unpack('q')
            elif ty == 3:  val = self.unpack('f')
            elif ty == 4:  val = self.unpack_string()
            elif ty == 5:  val = self.unpack_chat()
            elif ty == 6:  val = self.unpack_optional(self.unpack_chat)
            elif ty == 7:  val = self.unpack_slot()
            elif ty == 8:  val = self.unpack('?')
            elif ty == 9:  val = self.unpack_rotation()
            elif ty == 10: val = self.unpack_position()
            elif ty == 11: val = self.unpack_optional(self.unpack_position)
            elif ty == 12: val = self.unpack_direction()
            elif ty == 13: val = self.unpack_optional(self.unpack_uuid)
            elif ty == 14: val = self.unpack_block()
            elif ty == 15: val = self.unpack_block()
            elif ty == 16: val = self.unpack_nbt()
            elif ty == 17: val = self.unpack_particle()
            elif ty == 18: val = self.unpack_villager()
            elif ty == 19: val = self.unpack_optional_varint()
            elif ty == 20: val = self.unpack_pose()
            elif ty == 21: val = self.unpack_varint()
            elif ty == 22: val = self.unpack_varint()
            elif ty == 23: val = self.unpack_optional(self.unpack_global_position)
            elif ty == 24: val = self.unpack_varint()  # Painting variant type
            elif ty == 25: val = self.unpack_varint()  # Sniffer state
            elif ty == 26: val = (self.unpack('f'), self.unpack('f'), self.unpack('f'))  # Vector
            elif ty == 27: val = (self.unpack('f'), self.unpack('f'), self.unpack('f'), self.unpack('f'))  # Quaternion
            else: raise ValueError("Unknown entity metadata type: %d" % ty)
            metadata[ty, key] = val

    # Direction ---------------------------------------------------------------

    @classmethod
    def pack_direction(cls, direction):
        """
        Packs a direction.
        """

        return cls.pack_varint(directions.index(direction))

    def unpack_direction(self):
        """
        Unpacks a direction.
        """

        return directions[self.unpack_varint()]

    # Rotation ----------------------------------------------------------------

    @classmethod
    def pack_rotation(cls, x, y, z):
        """
        Packs a rotation.
        """

        return cls.pack('fff', x, y, z)

    def unpack_rotation(self):
        """
        Unpacks a rotation
        """

        return self.unpack('fff')

    # Chunk section -----------------------------------------------------------

    @classmethod
    def pack_chunk(cls, sections):
        data = b""
        for section in sections:
            if section and not section[0].is_empty():
                data += cls.pack_chunk_section(*section)
        return data

    @classmethod
    def pack_chunk_bitmask(cls, sections):
        bitmask = 0
        for i, section in enumerate(sections):
            if section and not section[0].is_empty():
                bitmask |= 1 << i
        return cls.pack_varint(bitmask)

    @classmethod
    def pack_chunk_section(cls, blocks, block_lights=None, sky_lights=None):
        """
        Packs a chunk section. The supplied argument should be an instance of
        ``quarry.types.chunk.BlockArray``.
        """

        out = cls.pack('HB', blocks.non_air, blocks.storage.value_width)
        out += cls.pack_chunk_section_palette(blocks.palette)
        out += cls.pack_chunk_section_array(blocks.to_bytes())
        return out

    @classmethod
    def pack_chunk_section_palette(cls, palette):
        if not palette:
            return b""
        else:
            return cls.pack_varint(len(palette)) + b"".join(
                cls.pack_varint(x) for x in palette)

    @classmethod
    def pack_chunk_section_array(cls, data):
        return cls.pack_varint(len(data) // 8) + data

    def unpack_chunk(self, bitmask, overworld=True):
        sections = []
        for idx in range(16):
            if bitmask & (1 << idx):
                section = self.unpack_chunk_section(overworld)
            else:
                section = None
            sections.append(section)
        return sections

    def unpack_chunk_section(self, overworld=True):
        """
        Unpacks a chunk section. Returns a sequence of length 4096 (16x16x16).
        """

        non_air, value_width = self.unpack('HB')
        palette = self.unpack_chunk_section_palette(value_width)
        array = self.unpack_chunk_section_array(value_width)
        return BlockArray.from_bytes(
            bytes=array,
            palette=palette,
            registry=self.registry,
            non_air=non_air,
            value_width=value_width), None, None

    def unpack_chunk_section_palette(self, value_width):
        if value_width > 8:
            return []
        else:
            return [self.unpack_varint() for _ in range(self.unpack_varint())]

    def unpack_chunk_section_array(self, value_width):
        return self.read(self.unpack_varint() * 8)

    # Particle ----------------------------------------------------------------

    @classmethod
    def pack_particle(cls, kind, data=None):
        """
        Packs a particle.
        """
        id = cls.registry.encode('minecraft:particle_type', kind)
        data = data or {}
        out = cls.pack_varint(id)
        if id == 3 or id == 20:
            out += cls.pack_varint(data['block_state'])
        elif id == 11:
            out += cls.pack(
                'ffff',
                data['red'],
                data['green'],
                data['blue'],
                data['scale'])
        elif id == 27:
            out += cls.pack_slot(**data['item'])

        return out

    def unpack_particle(self):
        """
        Unpacks a particle. Returns an ``(id, data)`` pair.
        """

        id = self.unpack_varint()
        if id == 3 or id == 20:
            data = {'block_state': self.unpack_varint()}
        elif id == 11:
            data = dict(zip(
                ('red', 'green', 'blue', 'scale'),
                self.unpack('ffff')))
        elif id == 27:
            data = {'item': self.unpack_slot()}
        else:
            data = {}

        kind = self.registry.decode('minecraft:particle_type', id)
        return kind, data

    # Commands ----------------------------------------------------------------

    def unpack_commands(self, resolve_redirects=True):
        """
        Unpacks a command graph.

        If *resolve_redirects* is ``True`` (the default), the returned
        structure may contain contain circular references, and therefore cannot
        be serialized to JSON (or similar). If it is ``False``, all node
        redirect information is stripped, resulting in a directed acyclic
        graph.
        """

        # Unpack nodes
        node_count = self.unpack_varint()
        nodes = [self.unpack_command_node() for _ in range(node_count)]

        # Resolve children and redirects
        for node in nodes:
            node['children'] = {nodes[idx]['name']: nodes[idx]
                                for idx in node['children']}
            if node['redirect'] is not None:
                if resolve_redirects:
                    node['redirect'] = nodes[node['redirect']]
                else:
                    node['redirect'] = None

        return nodes[self.unpack_varint()]

    def unpack_command_node(self):
        """
        Unpacks a command node.
        """

        node = {}

        flags = self.unpack('B')
        node['type'] = ['root', 'literal', 'argument'][flags & 0x03]
        node['executable'] = bool(flags & 0x04)
        node['children'] = [self.unpack_varint() for _ in
                            range(self.unpack_varint())]
        node['redirect'] = self.unpack_varint() if flags & 0x08 else None
        node['name'] = self.unpack_string() if node['type'] != 'root' else None

        if node['type'] == 'argument':
            node['parser'] = self.unpack_string()
            node['properties'] = self.unpack_command_node_properties(node['parser'])

        node['suggestions'] = self.unpack_string() if flags & 0x10 else None

        return node

    def unpack_command_node_properties(self, parser):
        """
        Unpacks the properties of an ``argument`` command node.
        """

        namespace, parser = parser.split(":", 1)
        properties = {}

        if namespace == "brigadier":
            if parser == "bool":
                pass
            elif parser == "string":
                properties['behavior'] = self.unpack_varint()
            elif parser in ("double", "float", "integer"):
                fmt = parser[0]
                flags = self.unpack('B')
                properties['min'] = self.unpack(fmt) if flags & 0x01 else None
                properties['max'] = self.unpack(fmt) if flags & 0x02 else None

        elif namespace == "minecraft":
            if parser in ('entity', 'score_holder'):
                properties['allow_multiple'] = self.unpack('?')

            elif parser == 'range':
                properties['allow_decimals'] = self.unpack('?')

        return properties

    @classmethod
    def pack_commands(cls, root_node):
        """
        Packs a command graph.
        """

        # Enumerate nodes
        nodes = [root_node]
        idx = 0
        while idx < len(nodes):
            node = nodes[idx]
            children = list(node['children'].values())
            if node['redirect']:
                children.append(node['redirect'])

            for child in children:
                if child not in nodes:
                    nodes.append(child)
            idx += 1

        # Pack nodes
        out = cls.pack_varint(len(nodes))
        for node in nodes:
            out += cls.pack_command_node(node, nodes)

        out += cls.pack_varint(nodes.index(root_node))

        return out

    @classmethod
    def pack_command_node(cls, node, nodes):
        """
        Packs a command node.
        """

        out = b""

        flags = (
            ['root', 'literal', 'argument'].index(node['type']) |
            int(node['executable']) << 2 |
            int(node['redirect'] is not None) << 3 |
            int(node['suggestions'] is not None) << 4)
        out += cls.pack('B', flags)
        out += cls.pack_varint(len(node['children']))

        for child in node['children'].values():
            out += cls.pack_varint(nodes.index(child))

        if node['redirect'] is not None:
            out += cls.pack_varint(nodes.index(node['redirect']))

        if node['name'] is not None:
            out += cls.pack_string(node['name'])

        if node['type'] == 'argument':
            out += cls.pack_string(node['parser'])
            out += cls.pack_command_node_properties(node['parser'],
                                                    node['properties'])
        if node['suggestions'] is not None:
            out += cls.pack_string(node['suggestions'])

        return out

    @classmethod
    def pack_command_node_properties(cls, parser, properties):
        """
        Packs the properties of an ``argument`` command node.
        """

        namespace, parser = parser.split(":", 1)
        out = b""

        if namespace == "brigadier":
            if parser == "bool":
                pass
            elif parser == "string":
                out += cls.pack_varint(properties['behavior'])
            elif parser in ("double", "float", "integer"):
                fmt = parser[0]
                flags = (
                    int(properties['min'] is not None) |
                    int(properties['max'] is not None) << 1)
                out += cls.pack('B', flags)
                if properties['min'] is not None:
                    out += cls.pack(fmt, properties['min'])
                if properties['max'] is not None:
                    out += cls.pack(fmt, properties['max'])

        elif namespace == "minecraft":
            if parser in ('entity', 'score_holder'):
                out += cls.pack('?', properties['allow_multiple'])

            elif parser == 'range':
                out += cls.pack('?', properties['allow_decimals'])

        return out

    # Recipes -----------------------------------------------------------------

    def unpack_recipe(self):
        """
        Unpacks a crafting recipe.
        """
        recipe = {}
        recipe['type'] = self.unpack_string()
        recipe['name'] = self.unpack_string()

        if recipe['type'] == 'minecraft:crafting_shapeless':
            recipe['group'] = self.unpack_string()
            recipe['category'] = self.unpack_varint()
            recipe['ingredients'] = [
                self.unpack_ingredient() for _ in range(self.unpack_varint())]
            recipe['result'] = self.unpack_slot()

        elif recipe['type'] in simple_recipe_types:
            recipe['category'] = self.unpack_varint()

        elif recipe['type'] == 'minecraft:crafting_shaped':
            recipe['width'] = self.unpack_varint()
            recipe['height'] = self.unpack_varint()
            recipe['group'] = self.unpack_string()
            recipe['category'] = self.unpack_varint() # Crafting book category
            recipe['ingredients'] = [
                self.unpack_ingredient() for _ in range(recipe['width'] *
                                                    recipe['height'])]
            recipe['result'] = self.unpack_slot()
        elif recipe['type'] in smelt_types:
            recipe['group'] = self.unpack_string()
            recipe['category'] = self.unpack_varint() # Crafting book category
            recipe['ingredient'] = self.unpack_ingredient()
            recipe['result'] = self.unpack_slot()
            recipe['experience'] = self.unpack('f')
            recipe['cooking_time'] = self.unpack_varint()

        elif recipe['type'] == 'minecraft:stonecutting':
            recipe['group'] = self.unpack_string()
            recipe['ingredient'] = self.unpack_ingredient()
            recipe['result'] = self.unpack_slot()

        elif recipe['type'] == 'minecraft:smithing':
            recipe['ingredients'] = [self.unpack_ingredient(), self.unpack_ingredient()]
            recipe['result'] = self.unpack_slot()

        return recipe

    @classmethod
    def pack_recipe(cls, name, type, **recipe):
        """
        Packs a crafting recipe.
        """
        data = cls.pack_string(type) + cls.pack_string(name)

        if type == 'minecraft:crafting_shapeless':
            data += cls.pack_string(recipe['group'])
            data += cls.pack_varint(recipe['category'])
            data += cls.pack_varint(len(recipe['ingredients']))
            for ingredient in recipe['ingredients']:
                data += cls.pack_ingredient(ingredient)
            data += cls.pack_slot(**recipe['result'])
            data += cls.pack('?', recipe['show_notification']) # Show notification

        elif type in simple_recipe_types:
            data += cls.pack_varint(recipe['category'])

        elif type == 'minecraft:crafting_shaped':
            data += cls.pack_varint(recipe['width'])
            data += cls.pack_varint(recipe['height'])
            data += cls.pack_string(recipe['group'])
            data += cls.pack_varint(recipe['category']) # Crafting book category
            for ingredient in recipe['ingredients']:
                data += cls.pack_ingredient(ingredient)
            data += cls.pack_slot(**recipe['result'])

        elif type in smelt_types:
            data += cls.pack_string(recipe['group'])
            data += cls.pack_varint(recipe['category']) # Crafting book category
            data += cls.pack_ingredient(recipe['ingredient'])
            data += cls.pack_slot(**recipe['result'])
            data += cls.pack('f', recipe['experience'])
            data += cls.pack_varint(recipe['cooking_time'])

        elif type == 'minecraft:stonecutting':
            data += cls.pack_string(recipe['group'])
            data += cls.pack_ingredient(recipe['ingredient'])
            data += cls.pack_slot(**recipe['result'])

        elif type == 'minecraft:smithing':
            data += cls.pack_ingredient(recipe['ingredients'][0])
            data += cls.pack_ingredient(recipe['ingredients'][1])
            data += cls.pack_slot(**recipe['result'])

        return data

    def unpack_ingredient(self):
        """
        Unpacks a crafting recipe ingredient alternation.
        """
        return [self.unpack_slot() for _ in range(self.unpack_varint())]

    @classmethod
    def pack_ingredient(cls, ingredient):
        """
        Packs a crafting recipe ingredient alternation.
        """
        data = cls.pack_varint(len(ingredient))
        for slot in ingredient:
            data += cls.pack_slot(**slot)
        return data

    # Villager data -----------------------------------------------------------

    @classmethod
    def pack_villager(cls, kind, profession, level):
        """
        Packs villager data.
        """

        kind = cls.registry.encode('minecraft:villager_type', kind)
        profession = cls.registry.encode('minecraft:villager_profession', profession)
        return cls.pack_varint(kind) + \
               cls.pack_varint(profession) + \
               cls.pack_varint(level)

    def unpack_villager(self):
        """
        Unpacks villager data.
        """
        kind = self.registry.decode(
            'minecraft:villager_type', self.unpack_varint())
        profession = self.registry.decode(
            'minecraft:villager_profession', self.unpack_varint())
        level = self.unpack_varint()
        return kind, profession, level

    # Optional varint ---------------------------------------------------------

    @classmethod
    def pack_optional_varint(cls, number):
        """
        Packs an optional varint.
        """

        return cls.pack_varint(0 if number is None else number + 1)

    def unpack_optional_varint(self):
        """
        Unpacks an optional varint.
        """

        val = self.unpack_varint()
        if val == 0:
            return None
        else:
            return val - 1

    # Pose --------------------------------------------------------------------

    @classmethod
    def pack_pose(cls, pose):
        """
        Packs a pose.
        """

        return cls.pack_varint(poses.index(pose))

    def unpack_pose(self):
        """
        Unpacks a pose.
        """

        return poses[self.unpack_varint()]

    # Global Position ---------------------------------------------------------

    @classmethod
    def pack_global_position(cls, dimension, x, y, z):
        """
        Packs a global position.
        """

        return cls.pack_string(dimension) + cls.pack_position(x, y, z)

    def unpack_global_position(self):
        """
        Unpacks a global position.
        """

        return self.unpack_string(), self.unpack_position()

    # Player public key Position ----------------------------------------------

    @classmethod
    def pack_player_public_key(cls, data: PlayerPublicKey):
        return cls.pack('Q', data.expiry) \
               + cls.pack_byte_array(data.key.public_bytes(Encoding.DER, PublicFormat.SubjectPublicKeyInfo)) \
               + cls.pack_byte_array(data.signature)

    def unpack_player_public_key(self):
        expiry = self.unpack('Q')
        key_bytes = self.unpack_byte_array()
        signature = self.unpack_byte_array()

        return PlayerPublicKey(expiry, import_public_key(key_bytes), signature)

    # Secure chat -------------------------------------------------------------

    @classmethod
    def pack_last_seen_list(cls, entries: List[LastSeenMessage]):
        packed = cls.pack_varint(len(entries))

        if len(entries) > 5:
            from quarry.net.protocol import ProtocolError
            raise ProtocolError("Last seen list is too large")

        for entry in entries:
            packed = packed + cls.pack_last_seen_entry(entry)

        return packed

    def unpack_last_seen_list(self):
        seen_messages = []
        seen_messages_length = self.unpack_varint()

        if seen_messages_length > 5:
            from quarry.net.protocol import ProtocolError
            raise ProtocolError("Last seen list is too large")

        for i in range(seen_messages_length):
            seen_messages.append(self.unpack_last_seen_entry())

        return seen_messages

    @classmethod
    def pack_last_seen_entry(cls, entry: LastSeenMessage):
        return cls.pack_uuid(entry.sender) + cls.pack_byte_array(entry.signature)

    def unpack_last_seen_entry(self):
        return LastSeenMessage(self.unpack_uuid(), self.unpack_byte_array())

    @classmethod
    def pack_last_received(cls, entry: LastSeenMessage):
        return cls.pack_optional(cls.pack_last_seen_entry, entry)

    def unpack_last_received(self):
        return self.unpack_optional(self.unpack_last_seen_entry)

    @classmethod
    def pack_signed_message(cls, message: SignedMessage):
        return cls.pack_optional(cls.pack_byte_array, message.header.previous_signature) \
               + cls.pack_uuid(message.header.sender) \
               + cls.pack_byte_array(message.signature or b'') \
               + cls.pack_string(message.body.message) \
               + cls.pack_optional(cls.pack_chat, message.body.decorated_message) \
               + cls.pack('QQ', message.body.timestamp, message.body.salt) \
               + cls.pack_last_seen_list(message.body.last_seen) \
               + cls.pack_optional(cls.pack_chat, message.unsigned_content)

    def unpack_signed_message(self):
        previous_signature = self.unpack_optional(self.unpack_byte_array)
        uuid = self.unpack_uuid()
        signature = self.unpack_byte_array()
        message = self.unpack_string()
        decorated_message = self.unpack_optional(self.unpack_chat)
        timestamp = self.unpack('Q')
        salt = self.unpack('Q')
        last_seen = self.unpack_last_seen_list()
        unsigned_content = self.unpack_optional(self.unpack_chat)

        header = SignedMessageHeader(uuid, previous_signature)
        body = SignedMessageBody(message, timestamp, salt, decorated_message, last_seen)
        return SignedMessage(header, signature, 760, body, unsigned_content)

    @classmethod
    def pack_game_profile(cls, value):
        name = value.get('name', None)
        uuid = value.get('uuid', None)
        properties = value.get('properties', [])

        data = cls.pack_optional(cls.pack_string, name) + \
               cls.pack_optional(cls.pack_uuid, uuid) + \
               cls.pack_varint(len(properties))

        for property in properties:
            signature = value.get('signature', None)

            data += cls.pack_string(property['name']) + \
                    cls.pack_string(property['value']) + \
                    cls.pack_optional(cls.pack_byte_array, signature)

        return data

    def unpack_game_profile(self):
        def unpack_property():
            return {
                'name': self.unpack_string(),
                'value': self.unpack_string(),
                'signature': self.unpack_optional(self.unpack_byte_array)
            }

        return {
            'name': self.unpack_optional(self.unpack_string),
            'uuid': self.unpack_optional(self.unpack_uuid),
            'properties': [unpack_property() for _ in range(self.unpack_varint())]
        }
