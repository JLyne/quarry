from typing import TYPE_CHECKING

from quarry.types.buffer.item.v1_21 import ItemBuffer1_21

if TYPE_CHECKING:
    from quarry.types.buffer import Buffer1_21

consume_effect_types = [
    "apply_effects",
    "remove_effects",
    "clear_all_effects",
    "teleport_randomly",
    "play_sound"
]

equipment_slots = [
    "mainhand",
    "offhand",
    "feet",
    "legs",
    "chest",
    "head",
    "body",
]


class ItemBuffer1_21_2(ItemBuffer1_21):
    component_handlers = list(ItemBuffer1_21.component_handlers.items())
    component_handlers.insert(7, ('item_model', (lambda cls: cls.buffer.pack_string, lambda self: self.buff.unpack_string)))
    component_handlers.insert(22, ('consumable', (lambda cls: cls.pack_consumable, lambda self: self.unpack_consumable)))
    component_handlers.insert(23, ('use_remainder', (lambda cls: cls.pack_single_item, lambda self: self.unpack_single_item)))
    component_handlers.insert(24, ('use_cooldown', (lambda cls: cls.pack_use_cooldown, lambda self: self.unpack_use_cooldown)))
    del component_handlers[25] # Remove fire_resistant
    component_handlers.insert(25, ('damage_resistant', (lambda cls: cls.buffer.pack_string, lambda self: self.buff.unpack_string)))
    component_handlers.insert(27, ('enchantable', (lambda cls: cls.buffer.pack_varint, lambda self: self.buff.unpack_varint)))
    component_handlers.insert(28, ('equippable', (lambda cls: cls.pack_equippable, lambda self: self.unpack_equippable)))
    component_handlers.insert(29, ('repairable', (lambda cls: cls.pack_repairable, lambda self: self.unpack_repairable)))
    component_handlers.insert(30, ('glider', None))
    component_handlers.insert(31, ('tooltip_style', (lambda cls: cls.buffer.pack_string, lambda self: self.buff.unpack_string)))
    component_handlers.insert(32, ('death_protection', (lambda cls: cls.pack_death_protection, lambda self: self.unpack_death_protection)))

    component_handlers = dict(component_handlers)
    component_types = list(component_handlers.keys())

    item_use_animations = [
        "none",
        "eat",
        "drink",
        "block",
        "bow",
        "spear",
        "crossbow",
        "spyglass",
        "toot_horn",
        "brush"
    ]

    def __init__(self, buffer: 'Buffer1_21'):
        super(ItemBuffer1_21, self).__init__(buffer)

    # Food ------------------------------------------------------------------

    @classmethod
    def pack_food(cls, value):
        can_always_eat = value.get('can_always_eat', False)

        data = cls.buffer.pack_varint(value['nutrition']) + \
            cls.buffer.pack('f?', value['saturation'], can_always_eat)

        return data

    def unpack_food(self):
        return {
            'nutrition': self.buffer.unpack_varint(),
            'saturation': self.buffer.unpack('f'),
            'can_always_eat': self.buffer.unpack('?')
        }

    # Consumable ------------------------------------------------------------------

    @classmethod
    def pack_consumable(cls, value):
        consume_seconds = value.get('consume_seconds', 1.6)
        animation = value.get('animation', 'eat')
        has_consume_particles = value.get('has_consume_particles', True)
        on_consume_effects = value.get('on_consume_effects', [])

        data = cls.buffer.pack('f', consume_seconds) + \
               cls.buffer.pack_varint(cls.item_use_animations.index(animation)) + \
               cls.pack_sound_event(value.get('sound', {'sound_id', 'entity.generic.eat'})) + \
               cls.buffer.pack('?', has_consume_particles) + \
               cls.buffer.pack_varint(len(on_consume_effects))

        for effect in on_consume_effects:
            data += cls.pack_consume_effect(effect)

        return data

    def unpack_consumable(self):
        return {
            'consume_seconds': self.buffer.unpack('f'),
            'animation': self.item_use_animations[self.buffer.unpack_varint()],
            'sound': self.unpack_sound_event(),
            'has_consume_particles': self.buffer.unpack('?'),
            'on_consume_effects': [self.unpack_consume_effect for _ in range(self.buffer.unpack_varint())],
        }

    @classmethod
    def pack_consume_effect(cls, value):
        type = value.get('type')

        if not type in consume_effect_types:
            raise ValueError('Unknown consumable effect type')

        data = cls.buffer.pack_varint(consume_effect_types.index(type))

        if type == "apply_effects":
            probability = value.get('probability', 1)
            effects = value.get('effects', [])

            data += cls.buffer.pack_varint(len(effects))

            for effect in effects:
                data += cls.pack_potion_effect(effect)

            return data + cls.buffer.pack('f', probability)

        if type == "remove_effects":
            for effect in value.get('effects', []):
                data += cls.buffer.registry.encode('minecraft:mob_effect', effect)

            return data

        if type == "teleport_randomly":
            diameter = value.get('diameter', 16.0)

            return data + cls.buffer.pack('f', diameter)

        if type == "play_sound":
            return data + cls.pack_sound_event(value['sound'])


    def unpack_consume_effect(self):
        type = consume_effect_types[self.buffer.unpack_varint()]

        if type == 'apply_effects':
            return {
                'type': type,
                'effects': [self.unpack_potion_effect() for _ in range(self.buffer.unpack_varint())],
                'probability': self.buffer.unpack('f')
            }

        if type == 'remove_effects':
            return {
                'type': type,
                'effects': [self.buffer.registry.decode('minecraft:mob_effect', self.buffer.unpack_varint()) for _ in range(self.buffer.unpack_varint())],
            }

        if type == 'teleport_randomly':
            return {
                'type': type,
                'diameter': self.buffer.unpack('f'),
            }

        if type == 'play_sound':
            return {
                'type': type,
                'sound': self.unpack_sound_event()
            }

        return {
            'type': type
        }

    # Use cooldown -------------------------------------------------------------

    @classmethod
    def pack_use_cooldown(cls, value):
        seconds = value['seconds']
        cooldown_group = value.get('cooldown_group', None)

        return cls.buffer.pack('f', seconds) + \
               cls.buffer.pack_optional(cls.buffer.pack_string, cooldown_group)

    def unpack_use_cooldown(self):
        return {
            'seconds': self.buffer.unpack('f'),
            'cooldown_group': self.buffer.unpack_optional(self.buffer.unpack_string)
        }

    # Equippable ---------------------------------------------------------------

    @classmethod
    def pack_equippable(cls, value):
        slot = value.get('slot')
        equip_sound = value.get('equip_sound', {'sound_id', 'item.armor.equip_generic'})
        model = value.get('model', None)
        camera_overlay = value.get('camera_overlay', None)
        allowed_entities = value.get('allowed_entities', None)
        dispensable = value.get('dispensable', True)
        swappable = value.get('swappable', True)
        damage_on_hurt = value.get('damage_on_hurt', True)

        data = cls.buffer.pack_varint(equipment_slots.index(slot)) + \
            cls.pack_sound_event(equip_sound) + \
            cls.buffer.pack_optional(cls.buffer.pack_string, model) + \
            cls.buffer.pack_optional(cls.buffer.pack_string, camera_overlay)

        data += cls.buffer.pack('?', allowed_entities is not None)

        if allowed_entities is not None:
            data += cls.buffer.pack_varint(len(allowed_entities))

            #FIXME: -1 tag

            for entity in allowed_entities:
                data += cls.buffer.pack_varint(cls.buffer.registry.encode('minecraft:entity_type', entity))

        data += cls.buffer.pack('?', dispensable) + \
                cls.buffer.pack('?', swappable) + \
                 cls.buffer.pack('?', damage_on_hurt)

        return data

    def unpack_equippable(self):
        return {
            'slot': equipment_slots[self.buffer.unpack_varint()],
            'equip_sound': self.unpack_sound_event(),
            'model': self.buffer.unpack_optional(self.buffer.unpack_string),
            'camera_overlay': self.buffer.unpack_optional(self.buffer.unpack_string),
            #FIXME: -1 tag
            'allowed_entities': self.buffer.unpack_optional(lambda: [
                self.buffer.registry.decode('minecraft:entity_type', self.buffer.unpack_varint())
                for _ in range(self.buffer.unpack_varint())
            ]),
            'dispensable': self.buffer.unpack('?'),
            'swappable': self.buffer.unpack('?'),
            'damage_on_hurt': self.buffer.unpack('?'),
        }

    # Repairable ---------------------------------------------------------------

    @classmethod
    def pack_repairable(cls, value):
        data = cls.buffer.pack_varint(len(value['items']))

        #FIXME: -1 tag

        for item in value['items']:
            data += cls.buffer.pack_varint(cls.buffer.registry.encode('minecraft:item', item))

        return data

    def unpack_repairable(self):
        #FIXME: -1 tag
        return {
            'items': [
                self.buffer.registry.decode('minecraft:item', self.buffer.unpack_varint())
                for _ in range(self.buffer.unpack_varint())
            ]
        }

    # Death protection ---------------------------------------------------------

    @classmethod
    def pack_death_protection(cls, value):
        death_effects = value.get('death_effects', None)

        data = cls.buffer.pack('?', death_effects is not None)

        if death_effects is not None:
            data += cls.buffer.pack_varint(len(death_effects))

            for effect in death_effects:
                data += cls.pack_consume_effect(effect)

        return data

    def unpack_death_protection(self):
        return {
            'death_effects': [self.unpack_consume_effect() for _ in range(self.buffer.unpack_varint())],
        }

    # Potions ------------------------------------------------------------------

    @classmethod
    def pack_potion_contents(cls, value):
        data = super().pack_potion_contents(value)
        custom_name = value.get('custom_name', None) # Added

        # Added
        data += cls.buffer.pack('?', custom_name is not None)

        if custom_name is not None:
            data += cls.buffer.pack_string(custom_name)

        return data

    def unpack_potion_contents(self):
        result = super().unpack_potion_contents()
        result['custom_name'] = self.buffer.unpack_optional(self.buffer.unpack_string)

        return result

    # Instrument ------------------------------------------------------------------

    @classmethod
    def pack_instrument(cls, value):
        return cls.pack_sound_event(value['sound_event']) + \
               cls.buffer.pack('f', value['use_duration']) + \
               cls.buffer.pack('f', value['range']) + \
               cls.buffer.pack_chat(value['description'])

    def unpack_instrument(self):
        return {
            'sound_event': self.unpack_sound_event(),
            'use_duration': self.buffer.unpack('f'),
            'range': self.buffer.unpack('f'),
            'description': self.buffer.unpack_chat()
        }

    # Lock --------------------------------------------------------------------

    @classmethod
    def pack_lock(cls, value):
        raise NotImplementedError('Not Implemented')

    def unpack_lock(self):
        raise NotImplementedError('Not Implemented')
