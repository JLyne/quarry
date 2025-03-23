import logging
from typing import Tuple, Union, List
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from quarry.types.buffer import Buffer1_20_5

from quarry.types.chat import Message

attribute_operations = ["add_value", "add_multiplied_base", "add_multiplied_total"]
attribute_slots = ["any", "mainhand", "offhand", "hand", "feet", "legs", "chest", "head", "armor", "body"]
firework_shapes = [
    "small_ball",
    "large_ball",
    "star",
    "creeper",
    "burst"
]
rarities = [
    "common",
    "uncommon",
    "rare",
    "epic"
]
map_post_processing = [
    "lock",
    "scale"
]

logger = logging.getLogger()

class ItemBuffer1_20_5:
    buffer: 'Buffer1_20_5' = None

    component_handlers = {
        'custom_data': (lambda cls: cls.buffer.pack_nbt, lambda self: self.buff.unpack_nbt),  # Compound tag
        'max_stack_size': (lambda cls: cls.buffer.pack_varint, lambda self: self.buff.unpack_varint),
        'max_damage': (lambda cls: cls.buffer.pack_varint, lambda self: self.buff.unpack_varint),
        'damage': (lambda cls: cls.buffer.pack_varint, lambda self: self.buff.unpack_varint),
        'unbreakable': (lambda cls: cls.pack_boolean, lambda self: self.unpack_boolean),
        'custom_name': (lambda cls: cls.buffer.pack_chat, lambda self: self.buff.unpack_chat),
        'item_name': (lambda cls: cls.buffer.pack_chat, lambda self: self.buff.unpack_chat),
        'lore': (lambda cls: cls.pack_lore, lambda self: self.unpack_lore),
        'rarity': (lambda cls: lambda val: cls.buffer.pack_varint(rarities.index(val)), lambda self: lambda: rarities[self.buff.unpack_varint()]),
        'enchantments': (lambda cls: cls.pack_enchantments, lambda self: self.unpack_enchantments),
        'can_place_on': (lambda cls: cls.pack_adventure_mode_predicate, lambda self: self.unpack_adventure_mode_predicate),
        'can_break': (lambda cls: cls.pack_adventure_mode_predicate, lambda self: self.unpack_adventure_mode_predicate),
        'attribute_modifiers': (lambda cls: cls.pack_attribute_modifiers, lambda self: self.unpack_attribute_modifiers),
        'custom_model_data': (lambda cls: cls.buffer.pack_varint, lambda self: self.buff.unpack_varint),
        'hide_additional_tooltip': None,
        'hide_tooltip': None,
        'repair_cost': (lambda cls: cls.buffer.pack_varint, lambda self: self.buff.unpack_varint),
        'creative_slot_lock': None,
        'enchantment_glint_override': (lambda cls: cls.pack_boolean, lambda self: self.unpack_boolean),
        'intangible_projectile': None,
        'food': (lambda cls: cls.pack_food, lambda self: self.unpack_food),
        'fire_resistant': None,
        'tool': (lambda cls: cls.pack_tool, lambda self: self.unpack_tool),
        'stored_enchantments': (lambda cls: cls.pack_enchantments, lambda self: self.unpack_enchantments),
        'dyed_color': (lambda cls: cls.pack_dyed_color, lambda self: self.unpack_dyed_color),
        'map_color': (lambda cls: lambda val: cls.buffer.pack('i', val), lambda self: lambda: self.buff.unpack('i')),
        'map_id': (lambda cls: cls.buffer.pack_varint, lambda self: self.buff.unpack_varint),
        'map_decorations': (lambda cls: cls.buffer.pack_nbt, lambda self: self.buff.unpack_nbt),  #FIXME: Wrong
        'map_post_processing': (lambda cls: lambda val: cls.buffer.pack_varint(map_post_processing.index(val)), lambda self: lambda: map_post_processing[self.buff.unpack_varint()]),
        'charged_projectiles': (lambda cls: cls.pack_item_array, lambda self: self.unpack_item_array),
        'bundle_contents': (lambda cls: cls.pack_item_array, lambda self: self.unpack_item_array),
        'potion_contents': (lambda cls: cls.pack_potion_contents, lambda self: self.unpack_potion_contents),
        'suspicious_stew_effects': (lambda cls: cls.pack_suspicious_stew_effect, lambda self: self.unpack_suspicious_stew_effect), #FIXME: Should be array?
        'writable_book_content': (lambda cls: cls.pack_writable_book, lambda self: self.buffer.unpack_writable_book),
        'written_book_content': (lambda cls: cls.pack_written_book, lambda self: self.buffer.unpack_written_book),
        'trim': (lambda cls: cls.pack_armor_trim, lambda self: self.unpack_armor_trim),
        'debug_stick_state': (lambda cls: cls.buffer.pack_nbt, lambda self: self.buff.unpack_nbt),  # FIXME: ??? Compound tag
        'entity_data': (lambda cls: cls.buffer.pack_nbt, lambda self: self.buff.unpack_nbt),  # Compound tag
        'bucket_entity_data': (lambda cls: cls.buffer.pack_nbt, lambda self: self.buff.unpack_nbt),  # Compound tag
        'block_entity_data': (lambda cls: cls.buffer.pack_nbt, lambda self: self.buff.unpack_nbt),  # Compound tag
        'instrument': (lambda cls: cls.pack_instrument, lambda self: self.unpack_instrument),
        'ominous_bottle_amplifier': (lambda cls: cls.buffer.pack_varint, lambda self: self.buff.unpack_varint),
        'recipes': (lambda cls: cls.buffer.pack_nbt, lambda self: self.buff.unpack_nbt),  # FIXME: List of resource locations
        'lodestone_tracker': (lambda cls: cls.pack_lodestone_tracker, lambda self: self.unpack_lodestone_tracker),
        'firework_explosion': (lambda cls: cls.pack_firework_explosion, lambda self: self.unpack_firework_explosion),
        'fireworks': (lambda cls: cls.pack_fireworks, lambda self: self.unpack_fireworks),
        'profile': (lambda cls: cls.buffer.pack_game_profile, lambda self: self.buffer.unpack_game_profile),
        'note_block_sound': (lambda cls: cls.buffer.pack_string, lambda self: self.buff.unpack_string),
        'banner_patterns': (lambda cls: cls.pack_banner_pattern_layers, lambda self: self.unpack_banner_pattern_layers),
        'base_color': (lambda cls: cls.buffer.pack_varint, lambda self: self.buff.unpack_varint),
        'pot_decorations': (lambda cls: cls.pack_pot_decorations, lambda self: self.unpack_pot_decorations),
        'container': (lambda cls: cls.pack_item_array, lambda self: self.unpack_item_array),
        'block_state': (lambda cls: cls.pack_block_state, lambda self: self.unpack_block_state),
        'bees': (lambda cls: cls.pack_bees, lambda self: self.unpack_bees),
        'lock': (lambda cls: cls.buffer.pack_string, lambda self: self.buff.unpack_string),
        'container_loot': (lambda cls: cls.buffer.pack_nbt, lambda self: self.buff.unpack_nbt),  # FIXME: Wrong
    }

    component_types = list(component_handlers.keys())

    def __init__(self, buffer: 'Buffer1_20_5'):
        self.buffer = buffer

    @classmethod
    def pack_item(cls, value):
        if value is None:
            return cls.buffer.pack_varint(0)

        data = cls.buffer.pack_varint(value['count']) + \
            cls.buffer.pack_varint(
                cls.buffer.registry.encode('minecraft:item', value['item'])
            ) + cls.pack_structured_data(value.get('structured_data', {}))

        return data

    def unpack_item(self):
        count = self.buffer.pack_varint(0)

        if count == 0:
            return None

        item = self.buffer.registry.decode('minecraft:item', self.buffer.unpack_varint())

        return {
            'count': count,
            'item': item,
            'structured_data': self.unpack_structured_data()
        }

    @classmethod
    def pack_structured_data(cls, value):
        values = 0
        markers = 0

        for (data_key, data_value) in value.items():
            if data_value is not None:
                values += 1
            else:
                markers += 1

        data = cls.buffer.pack_varint(values) + \
            cls.buffer.pack_varint(markers)

        done = []

        # Structured data with values
        for (data_key, data_value) in value.items():
            if data_key not in cls.component_types:
                logger.warning("Ignoring unknown component type: %s", data_key)
                continue

            if cls.component_handlers[data_key] is None:
                continue

            done.append(data_key)
            component_handler = cls.component_handlers[data_key][0](cls)

            if data_value is not None:
                data += cls.buffer.pack_varint(cls.component_types.index(data_key)) + component_handler(data_value)
            else:
                logger.warning("Missing value for component type: %s", data_key)

        # Structured data without values (markers)
        for (data_key, data_value) in value.items():
            # Ignore already added valued components
            if data_key in done:
                continue

            if data_value is None:
                data += cls.buffer.pack_varint(cls.component_types.index(data_key))
            else:
                logger.warning("Ignoring value for valueless component type: %s", data_key)

        return data

    def unpack_structured_data(self):
        values = self.buffer.unpack_varint()
        markers = self.buffer.unpack_varint()
        structured_data = {

        }

        for _ in range(values):
            key = self.component_types[self.buffer.unpack_varint()]
            structured_data[key] = self.component_handlers[key][1](self)()

        for _ in range(markers):
            key = self.component_types[self.buffer.unpack_varint()]
            structured_data[key] = None

        return structured_data

    @classmethod
    def pack_item_array(cls, value):
        data = cls.buffer.pack_varint(len(value))

        for item in value:
            data += cls.pack_item(item)

        return data

    def unpack_item_array(self):
        return [self.unpack_item() for _ in self.buffer.unpack_varint()]

    @classmethod
    def pack_int(cls, value: bool):
        return cls.buffer.pack('i', value)

    def unpack_int(self) -> bool:
        return self.buffer.unpack('i')

    @classmethod
    def pack_boolean(cls, value: bool):
        return cls.buffer.pack('?', value)

    def unpack_boolean(self) -> bool:
        return self.buffer.unpack('?')

    @classmethod
    def pack_registry_tag_or_list(cls, value, registry):
        if isinstance(value, str):
            return cls.buffer.pack_varint(-1) + cls.buffer.pack_string(value)
        elif isinstance(value, list):
            data = cls.buffer.pack_varint(len(value) + 1)

            for item in value:
                data += cls.buffer.pack_varint(cls.buffer.registry.encode(registry, item))

            return data
        else:
            raise TypeError("Value should be a tag or a list of entries in the {} registry".format(registry))

    def unpack_registry_tag_or_list(self, registry):
        length = self.buffer.unpack_varint() - 1

        if length == -1:
            return self.buffer.unpack_string()
        else:
            return [
                self.buffer.registry.decode(registry, self.buffer.unpack_varint()) for _ in range(length)]

    @classmethod
    def pack_block_spec(cls, value):
       return cls.pack_registry_tag_or_list(value, 'minecraft:block')

    def unpack_block_spec(self):
        return self.unpack_registry_tag_or_list('minecraft:block')

    @classmethod
    def pack_block_state(cls, value):
        data = cls.buffer.pack_varint(len(value.items()))

        for (key, value) in value.items():
            data += cls.buffer.pack_string(key)

            if isinstance(value, str):
                data += cls.buffer.pack('?', True) + cls.buffer.pack_string(value)
            elif isinstance(value, list) and len(value) <= 2:
                data += cls.buffer.pack('?', False)
                data += cls.buffer.pack_optional(cls.buffer.pack_string, value[0] if len(value) >= 1 else None)
                data += cls.buffer.pack_optional(cls.buffer.pack_string, value[1] if len(value) == 2 else None)
            else:
                raise TypeError("Block state item should be a string or a list of 0-2 strings")

        return data

    def unpack_block_state(self):
        result = {}

        for i in range(self.buffer.unpack_varint()):
            key = self.buffer.unpack_string()

            if self.buffer.unpack('?'):  # List of 0-2 strings
                value = []

                if self.buffer.unpack('?'):
                    value.append(self.buffer.unpack_string())

                if self.buffer.unpack('?'):
                    value.append(self.buffer.unpack_string())
            else:  # Single string
                value = self.buffer.unpack_string()

            result[key] = value

        return result

    # Lore ------------------------------------------------------------------

    @classmethod
    def pack_lore(cls, value: List[Message]):
        data = cls.buffer.pack_varint(len(value))

        for item in value:
            data += cls.buffer.pack_chat(item)

        return data

    def unpack_lore(self) -> List[Message]:
        return [self.buffer.unpack_chat() for _ in range(self.buffer.unpack_varint())]

    # Enchantments ------------------------------------------------------------------

    @classmethod
    def pack_enchantments(cls, value):
        show_in_tooltip = value.get('show_in_tooltip', True)

        data = cls.buffer.pack_varint(len(value['levels']))

        for enchantment in value['levels'].items():
            data += cls.pack_enchantment(enchantment)

        data += cls.buffer.pack('?', show_in_tooltip)

        return data

    def unpack_enchantments(self):
        return {
            'levels': dict(self.unpack_enchantment() for _ in range(self.buffer.unpack_varint())),
            'show_in_tooltip': self.buffer.unpack('?')
        }

    @classmethod
    def pack_enchantment(cls, value: Tuple[Union[int, str], int]):
        return cls.buffer.pack_varint(cls.buffer.registry.encode('minecraft:enchantment', value[0])) + \
            cls.buffer.pack_varint(value[1])

    def unpack_enchantment(self) -> Tuple[Union[int, str], int]:
        return (
            self.buffer.registry.decode('minecraft:enchantment', self.buffer.unpack_varint()),
            self.buffer.unpack_varint()
        )

    # Adventure Mode Predicate ------------------------------------------------------------------

    @classmethod
    def pack_adventure_mode_predicate(cls, value):
        show_in_tooltip = value.get('show_in_tooltip', True)
        data = cls.buffer.pack_varint(len(value['predicates']))

        for predicate in value['predicates']:
            data += cls.pack_block_predicate(predicate)

        data += cls.buffer.pack('?', show_in_tooltip)

        return data

    def unpack_adventure_mode_predicate(self): #FIXME: Server can also send "simple" variant
        return {
            'predicates': [self.unpack_block_predicate() for _ in range(self.buffer.unpack_varint())],
            'show_in_tooltip': self.buffer.unpack('?')
        }

    @classmethod
    def pack_block_predicate(cls, value):
        return cls.buffer.pack_optional(cls.pack_block_spec, value['blocks']) + \
               cls.buffer.pack_optional(cls.pack_block_state, value['state']) + \
               cls.buffer.pack_optional(cls.buffer.pack_nbt, value['nbt'])

    def unpack_block_predicate(self):
        return {
            'blocks': self.buffer.unpack_optional(
                lambda: [self.unpack_block_spec() for _ in range(self.buffer.unpack_varint())]
            ),
            'state': self.buffer.unpack_optional(self.unpack_block_state),
            'nbt': self.buffer.unpack_optional(self.buffer.unpack_nbt)
        }

    # Attribute Modifiers ------------------------------------------------------------------

    @classmethod
    def pack_attribute_modifiers(cls, value):
        show_in_tooltip = value.get('show_in_tooltip', True)
        data = cls.buffer.pack_varint(len(value['modifiers']))

        for modifier in value['modifiers']:
            data += cls.pack_attribute_modifier(modifier)

        data += cls.buffer.pack('?', show_in_tooltip)

        return data

    def unpack_attribute_modifiers(self):
        return {
            'modifiers': [self.unpack_attribute_modifier() for _ in range(self.buffer.unpack_varint())],
            'show_in_tooltip': self.buffer.unpack('?')
        }

    @classmethod
    def pack_attribute_modifier(cls, value):
        return cls.buffer.pack_varint(cls.buffer.registry.encode('minecraft:attribute', value['type'])) + \
            cls.buffer.pack_uuid(value['uuid']) + \
            cls.buffer.pack_string(value['name']) + \
            cls.buffer.pack('d', value['amount']) + \
            cls.buffer.pack_varint(attribute_operations.index(value['operation'])) + \
            cls.buffer.pack_varint(attribute_slots.index(value['slot']))

    def unpack_attribute_modifier(self):
        return {
            'type': self.buffer.registry.decode('minecraft:attribute', self.buffer.unpack_varint()),
            'uuid': self.buffer.unpack_uuid(),
            'name': self.buffer.unpack_string(),
            'amount': self.buffer.unpack('d'),
            'operation': attribute_operations[self.buffer.unpack_varint()],
            'slot': attribute_slots[self.buffer.unpack_varint()],
        }

    # Dyed Color ------------------------------------------------------------------

    @classmethod
    def pack_dyed_color(cls, value):
        show_in_tooltip = value.get('show_in_tooltip', True)
        return cls.buffer.pack('i?', value['rgb'], show_in_tooltip)

    def unpack_dyed_color(self):
        return {
            'rgb': self.buffer.unpack('i'),
            'show_in_tooltip': self.buffer.unpack('?'),
        }

    # Armor Trim ------------------------------------------------------------------

    @classmethod
    def pack_armor_trim(cls, value):
        material = value['material']
        pattern = value['pattern']
        override_armor_materials = material.get('override_armor_materials', [])
        decal = pattern.get('decal', False)
        show_in_tooltip = value.get('show_in_tooltip', True)

        data = cls.buffer.pack_string(material['asset_name']) + \
            cls.buffer.pack_varint(cls.buffer.registry.encode('minecraft:item', material['ingredient'])) + \
            cls.buffer.pack('f', material['item_model_index']) + \
            cls.buffer.pack_varint(len(override_armor_materials))

        for (key, value) in override_armor_materials.items():
            data += cls.buffer.pack_string(key) + \
                    cls.buffer.pack_string(value)

        data += cls.buffer.pack_chat(material['description'])

        data += cls.buffer.pack_string(pattern['asset_name']) + \
            cls.buffer.pack_varint(cls.buffer.registry.encode('minecraft:item', pattern['template_item'])) + \
            cls.buffer.pack_chat(pattern['description']) + \
            cls.buffer.pack('?', decal)

        data += cls.buffer.pack('?', show_in_tooltip)

        return data

    def unpack_armor_trim(self):
        return {
            'material': {
                'asset_name': self.buffer.unpack_string(),
                'item': self.buffer.registry.decode('minecraft:item', self.buffer.unpack_varint()),
                'item_model_index': self.buffer.unpack('f'),
                'override_armor_materials': {
                    self.buffer.unpack_string(): self.buffer.unpack_string() for _ in range(self.buffer.unpack_varint())
                },
                'description': self.buffer.unpack_chat()
            },
            'pattern': {
                'asset_name': self.buffer.unpack_string(),
                'template_item': self.buffer.registry.decode('minecraft:item', self.buffer.unpack_varint()),
                'description': self.buffer.unpack_chat(),
                'decal': self.buffer.unpack('?')
            },
            'show_in_tooltip': self.buffer.unpack('?')
        }

    # Potions ------------------------------------------------------------------

    @classmethod
    def pack_potion_contents(cls, value):
        potion = value.get('potion', None)
        custom_color = value.get('custom_color', None)
        custom_effects = value.get('custom_effects', [])

        data = cls.buffer.pack('?', potion is not None)

        if potion is not None:
            data += cls.buffer.pack_varint(cls.buffer.registry.encode('minecraft:potion', value['potion']))

        data += cls.buffer.pack('?', custom_color is not None)

        if custom_color is not None:
            data += cls.buffer.pack('i', value['custom_color'])

        data += cls.buffer.pack_varint(len(value['custom_effects']))

        for effect in custom_effects:
            cls.pack_potion_effect(effect)

        return data

    def unpack_potion_contents(self):
        return {
            'potion': self.buffer.unpack_optional(
                lambda: self.buffer.registry.decode('minecraft:potion', self.buffer.unpack_varint())
            ),
            'custom_color': self.buffer.unpack_optional(lambda: self.buffer.unpack('i')),
            'custom_effects': [self.unpack_potion_effect() for _ in range(self.buffer.unpack_varint())]
        }

    @classmethod
    def pack_potion_effect(cls, value):
        return cls.buffer.pack_varint(cls.buffer.registry.encode('minecraft:mob_effect', value['effect'])) + \
            cls._pack_potion_effect_data(value)

    def unpack_potion_effect(self):
        effect = self.buffer.registry.decode('minecraft:mob_effect', self.buffer.unpack_varint())
        effect_data = self._unpack_potion_effect_data()

        effect_data['effect'] = effect
        return effect_data

    @classmethod
    def _pack_potion_effect_data(cls, value):
        amplifier = value.get('amplifier', 0)
        duration = value.get('duration', 1)
        ambient = value.get('ambient', False)
        show_particles = value.get('show_particles', True)
        show_icon = value.get('show_icon', True)

        data = cls.buffer.pack_varint(amplifier) + \
               cls.buffer.pack_varint(duration) + \
               cls.buffer.pack('????', ambient, show_particles, show_icon, 'hidden_effect' in value)

        if 'hidden_effect' in value:
            data += cls.pack_potion_effect(value['hidden_effect'])

        return data

    def _unpack_potion_effect_data(self):
        return {
            'amplifier': self.buffer.unpack_varint(),
            'duration': self.buffer.unpack_varint(),
            'ambient': self.buffer.unpack('?'),
            'show_particles': self.buffer.unpack('?'),
            'show_icon': self.buffer.unpack('?'),
            'hidden_effect': self.buffer.unpack_optional(self._unpack_potion_effect_data)
        }

    # Food ------------------------------------------------------------------

    @classmethod
    def pack_food(cls, value):
        effects = value.get('effects', [])
        can_always_eat = value.get('can_always_eat', False)
        eat_seconds = value.get('can_always_eat', 1.6)

        data = cls.buffer.pack_varint(value['nutrition']) + \
            cls.buffer.pack('f?f', value['saturation'], can_always_eat, eat_seconds) + \
            cls.buffer.pack_varint(len(effects))

        for effect in effects:
            data += cls.pack_food_effect(effect)

        return data

    def unpack_food(self):
        return {
            'nutrition': self.buffer.unpack_varint(),
            'saturation': self.buffer.unpack('f'),
            'can_always_eat': self.buffer.unpack('?'),
            'eat_seconds': self.buffer.unpack('f'),
            'effects': [self.unpack_food_effect() for _ in range(self.buffer.unpack_varint())],
        }

    @classmethod
    def pack_food_effect(cls, value):
        probability = value.get('probability', 1)

        return cls.pack_potion_effect(value['effect']) + cls.buffer.pack('f', probability)

    def unpack_food_effect(self):
        return {
            'effect': self.unpack_potion_effect(),
            'probability': self.buffer.unpack('f')
        }

    # Tool ------------------------------------------------------------------

    @classmethod
    def pack_tool(cls, value):
        rules = value.get('rules', [])
        default_mining_speed = value.get('default_mining_speed', 1.0)
        damage_per_block = value.get('damage_per_block', 1)

        data = cls.buffer.pack_varint(len(rules))

        for rule in rules:
            data += cls.pack_tool_rule(rule)

        data += cls.buffer.pack('f', default_mining_speed)
        data += cls.buffer.pack_varint(damage_per_block)

    def unpack_tool(self):
        return {
            'rules': [self.unpack_tool_rule() for _ in range(self.buffer.unpack_varint())],
            'default_mining_speed': self.buffer.unpack('f'),
            'damage_per_block': self.buffer.unpack_varint()
        }

    @classmethod
    def pack_tool_rule(cls, value):
        speed = value.get('speed', None)
        correct_for_drops = value.get('correct_for_drops', None)

        return cls.pack_block_spec(value['blocks']) + \
            cls.buffer.pack_optional(cls.buffer.pack('f'), speed) + \
            cls.buffer.pack_optional(cls.buffer.pack('?'), correct_for_drops)

    def unpack_tool_rule(self):
        return {
            'blocks': self.unpack_block_spec(),
            'speed': self.buffer.unpack_optional(lambda: self.buffer.unpack('f')),
            'correct_for_drops': self.buffer.unpack_optional(lambda: self.buffer.unpack('?'))
        }

    # Suspicious Stew ------------------------------------------------------------------

    @classmethod
    def pack_suspicious_stew_effect(cls, value):
        duration = value.get('duration', 160)

        return cls.buffer.pack_varint(cls.buffer.registry.encode('minecraft:mob_effect', value['effect'])) + \
            cls.buffer.pack_varint(duration)

    def unpack_suspicious_stew_effect(self):
        return {
            'effect': self.buffer.registry.decode('minecraft:mob_effect', self.buffer.unpack_varint()),
            'duration': self.buffer.unpack_varint()
        }

    # Instrument ------------------------------------------------------------------

    @classmethod
    def pack_instrument(cls, value):
        return cls.pack_sound_event(value['sound_event']) + \
               cls.buffer.pack_varint(value['use_duration']) + \
               cls.buffer.pack('f', value['range'])

    def unpack_instrument(self):
        return {
            'sound_event': self.unpack_sound_event(),
            'use_duration': self.buffer.unpack_varint(),
            'range': self.buffer.unpack('f')
        }

    @classmethod
    def pack_sound_event(cls, value):
        return cls.buffer.pack_string(value['sound_id']) + \
               cls.buffer.pack_optional(lambda: cls.buffer.pack('f'), value.get('range', None))

    def unpack_sound_event(self):
        return {
            'sound_id': self.buffer.unpack_string(),
            'range': self.buffer.unpack_optional(lambda: self.buffer.unpack('f')),
        }

    # Lodestone Tracker ------------------------------------------------------------------
    @classmethod
    def pack_lodestone_tracker(cls, value):
        target = value.get('target', None)
        tracked = value.get('tracked', True)

        def pack_pos():
            return cls.buffer.pack_global_position(
                value['target']['dimension'],
                value['target']['pos'][0],
                value['target']['pos'][1],
                value['target']['pos'][2])

        return cls.buffer.pack_optional(pack_pos, target) + cls.buffer.pack('?', tracked)

    def unpack_lodestone_tracker(self):
        target = self.buffer.unpack_optional(self.buffer.unpack_global_position)

        if target is not None:
            target = {
                'dimension': target[0],
                'pos': target[1]
            }

        return {
            'target': target,
            'tracked': self.buffer.unpack('?')
        }

    # Fireworks ------------------------------------------------------------------

    @classmethod
    def pack_fireworks(cls, value):
        explosions = value.get('explosions', [])
        flight_duration = value.get('flight_duration', 1)

        data = cls.buffer.pack_varint(flight_duration) + cls.buffer.pack_varint(len(explosions))

        for explosion in explosions:
            data += cls.pack_firework_explosion(explosion)

        return data

    def unpack_fireworks(self):
        return {
            'flight_duration': self.buffer.unpack_varint(),
            'explosions': [self.unpack_firework_explosion() for _ in range(self.buffer.unpack_varint())],
        }

    @classmethod
    def pack_firework_explosion(cls, value):
        return cls.buffer.pack_varint(firework_shapes.index(value['shape'])) + \
               cls.buffer.pack_varint(len(value['colors'])) + \
               cls.buffer.pack_array('i', value['colors']) + \
               cls.buffer.pack_varint(len(value['fade_colors'])) + \
               cls.buffer.pack_array('i', value['fade_colors']) + \
               cls.buffer.pack('??', value['has_trail'], value['has_twinkle'])

    def unpack_firework_explosion(self):
        return {
            'shape': firework_shapes[self.buffer.unpack_varint()],
            'colors': self.buffer.unpack_array('i', self.buffer.unpack_varint()),
            'fade_colors': self.buffer.unpack_array('i', self.buffer.unpack_varint()),
            'has_trail': self.buffer.unpack('?'),
            'has_twinkle': self.buffer.unpack('?'),
        }

    # Banner Patterns ------------------------------------------------------------------

    @classmethod
    def pack_banner_pattern_layers(cls, value):
        data = cls.buffer.pack_varint(len(value))

        for pattern in value:
            data += cls.pack_banner_pattern_layer(pattern)

        return data

    def unpack_banner_pattern_layers(self):
        return [self.unpack_banner_pattern_layer() for _ in range(self.buffer.unpack_varint())]

    @classmethod
    def pack_banner_pattern_layer(cls, value):
        return cls.pack_banner_pattern(value['pattern']) + cls.buffer.pack_varint(value['color'])

    def unpack_banner_pattern_layer(self):
        return {
            'pattern': self.unpack_banner_pattern(),
            'color': self.buffer.unpack_varint()
        }

    @classmethod
    def pack_banner_pattern(cls, value):
        return cls.buffer.pack_string(value['asset_id']) + cls.buffer.pack_string(value['translation_key'])

    def unpack_banner_pattern(self):
        return {
            'asset_id': self.buffer.unpack_string(),
            'translation_key': self.buffer.unpack_string()
        }

    # Bees ------------------------------------------------------------------

    @classmethod
    def pack_bees(cls, value):
        return cls.buffer.pack_nbt(value['entity_data']) + \
            cls.buffer.pack_varint(value['ticks_in_hive']) + \
            cls.buffer.pack_varint(value['min_ticks_in_hive'])

    def unpack_bees(self):
        return {
            'entity_data': self.buffer.unpack_nbt(),
            'ticks_in_hive': self.buffer.unpack_varint(),
            'min_ticks_in_hive': self.buffer.unpack_varint()
        }

    # Book ------------------------------------------------------------------

    @classmethod
    def pack_writable_book(cls, value):
        data = cls.buffer.pack_varint(len(value))

        for page in value:
            if isinstance(page, str):
                data += cls.buffer.pack_string(page) + cls.buffer.pack('?', False)
            else:
                data += (cls.buffer.pack_string(page['raw']) +
                         cls.buffer.pack_optional(cls.buffer.pack_string, page.get('filtered', None)))

        return data

    def unpack_writable_book(self):
        return [{
            'raw': self.buffer.unpack_string(),
            'filtered': self.buffer.unpack_optional(self.buffer.unpack_string)
        } for _ in range(self.buffer.unpack_varint())]

    @classmethod
    def pack_written_book(cls, value):
        title = value['title']
        pages = value.get('pages', [])

        if isinstance(title, str):
            data = cls.buffer.pack_string(title) + cls.buffer.pack('?', False)
        else:
            data = cls.buffer.pack_string(title['raw']) + \
                    cls.buffer.pack_optional(cls.buffer.pack_string, title.get('filtered', None))

        data += cls.buffer.pack_string(value['author']) + \
            cls.buffer.pack_varint(value['generation']) + \
            cls.buffer.pack_varint(len(pages))

        for page in pages:
            if isinstance(page, Message):
                data += cls.buffer.pack_chat(page) + cls.buffer.pack('?', False)
            else:
                data += cls.buffer.pack_chat(page['raw']) + cls.buffer.pack_optional(cls.buffer.pack_chat, page['filtered'])

        data += cls.buffer.pack('?', value['resolved'])

        return data

    def unpack_written_book(self):
        return {
            'title': {
                'raw': self.buffer.unpack_string(),
                'filtered': self.buffer.unpack_optional(self.buffer.unpack_string)
            },
            'author': self.buffer.unpack_string(),
            'generation': self.buffer.unpack_varint(),
            'pages': [{
                'raw': self.buffer.unpack_chat(),
                'filtered': self.buffer.unpack_optional(self.buffer.unpack_chat)
            } for _ in range(self.buffer.unpack_varint())],
            'resolved': self.buffer.unpack('?')
        }

    # Pot Decorations ------------------------------------------------------------------

    @classmethod
    def pack_pot_decorations(cls, value):
        data = cls.buffer.pack_varint(len(value))

        for item in value:
            data += cls.buffer.pack_varint(cls.buffer.registry.encode('minecraft:item', item))

        return data

    def unpack_pot_decorations(self):
        return [
            self.buffer.registry.decode('minecraft:item', self.buffer.unpack_varint())
            for _ in range(self.buffer.unpack_varint())
        ]
