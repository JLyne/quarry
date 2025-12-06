from typing import TYPE_CHECKING

from quarry.types.buffer.item.v1_21_9 import ItemBuffer1_21_9

if TYPE_CHECKING:
    from quarry.types.buffer import Buffer1_21_11

swing_animation_types = [
    "none",
    "whack",
    "stab"
]

class ItemBuffer1_21_11(ItemBuffer1_21_9):
    component_handlers = list(ItemBuffer1_21_9.component_handlers.items())
    component_handlers.insert(5, ('use_effects', (lambda cls: cls.pack_use_effects, lambda self: self.unpack_use_effects)))
    component_handlers.insert(7, ('minimum_attack_charge', (lambda cls: cls.pack_float, lambda self: self.unpack_float)))
    component_handlers.insert(8, ('damage_type', (lambda cls: cls.pack_damage_type, lambda self: self.unpack_damage_type)))
    component_handlers.insert(30, ('attack_range', (lambda cls: cls.pack_attack_range, lambda self: self.unpack_attack_range)))
    component_handlers.insert(38, ('piercing_weapon', (lambda cls: cls.pack_piercing_weapon, lambda self: self.unpack_piercing_weapon)))
    component_handlers.insert(39, ('kinetic_weapon', (lambda cls: cls.pack_kinetic_weapon, lambda self: self.unpack_kinetic_weapon)))
    component_handlers.insert(40, ('swing_animation', (lambda cls: cls.pack_swing_animation, lambda self: self.unpack_swing_animation)))

    component_handlers = dict(component_handlers)
    component_types = list(component_handlers.keys())

    item_use_animations = [
        "none",
        "eat",
        "drink",
        "block",
        "bow",
        "trident",
        "crossbow",
        "spyglass",
        "toot_horn",
        "brush",
        "bundle",
        "spear"
    ]

    def __init__(self, buffer: 'Buffer1_21_11'):
        super(ItemBuffer1_21_9, self).__init__(buffer)

    # Use Effects  ---------------------------------------------------------------

    @classmethod
    def pack_use_effects(cls, value):
        can_sprint = value.get('can_sprint', False)
        speed_multiplier = value.get('speed_multiplier', 0.2)
        interact_vibrations = value.get('interact_vibrations', True)

        return cls.buffer.pack('??f', can_sprint, interact_vibrations, speed_multiplier)

    def unpack_use_effects(self):
        return {
            'can_sprint': self.buffer.unpack('?'),
            'interact_vibrations': self.buffer.unpack('?'),
            'speed_multiplier': self.buffer.unpack('f')
        }

    # Damage Type  ---------------------------------------------------------------

    @classmethod
    def pack_damage_type(cls, value):
        return cls.buffer.pack_varint(cls.buffer.registry.encode("minecraft:damage_type", value))

    def unpack_damage_type(self):
        return self.buffer.registry.decode('minecraft:damage_type', self.buffer.unpack_varint())

    # Attack Range  ---------------------------------------------------------------

    @classmethod
    def pack_attack_range(cls, value):
        min_reach = value.get('min_reach', 0.0)
        max_reach = value.get('max_reach', 0.0)
        min_creative_reach = value.get('min_creative_reach', 0.0)
        max_creative_reach = value.get('max_creative_reach', 0.0)
        hitbox_margin = value.get('hitbox_margin', 0.3)
        mob_factor = value.get('hitbox_margin', 1.0)

        return cls.buffer.pack('ffffff', min_reach, max_reach, min_creative_reach,
                               max_creative_reach, hitbox_margin, mob_factor)

    def unpack_attack_range(self):
        return {
            'min_reach': self.buffer.unpack('f'),
            'max_reach': self.buffer.unpack('f'),
            'min_creative_reach': self.buffer.unpack('f'),
            'max_creative_reach': self.buffer.unpack('f'),
            'hitbox_margin': self.buffer.unpack('f'),
            'mob_factor': self.buffer.unpack('f')
        }

    # Piercing Weapon  ---------------------------------------------------------------

    @classmethod
    def pack_piercing_weapon(cls, value):
        deals_knockback = value.get('deals_knockback', True)
        dismounts = value.get('dismounts', False)
        sound = value.get('sound', None)
        hit_sound = value.get('hit_sound', None)

        return (cls.buffer.pack('??', deals_knockback, dismounts)
                + cls.buffer.pack_optional(cls.pack_sound_event, sound)
                + cls.buffer.pack_optional(cls.pack_sound_event, hit_sound))

    def unpack_piercing_weapon(self):
        return {
            'deals_knockback': self.buffer.unpack('?'),
            'dismounts': self.buffer.unpack('?'),
            'sound': self.buffer.unpack_optional(self.unpack_sound_event),
            'hit_sound': self.buffer.unpack_optional(self.unpack_sound_event),
        }

    # Kinetic Weapon  ---------------------------------------------------------------

    @classmethod
    def pack_kinetic_weapon(cls, value):
        contact_cooldown_ticks = value.get('contact_cooldown_ticks', 0)
        delay_ticks = value.get('delay_ticks', 0)
        damage_conditions = value.get('damage_conditions', {})
        dismount_conditions = value.get('dismount_conditions', {})
        knockback_conditions = value.get('knockback_conditions', {})
        forward_movement = value.get('forward_movement', 0.0)
        damage_multiplier = value.get('damage_multiplier', 1.0)
        sound = value.get('sound', None)
        hit_sound = value.get('hit_sound', None)

        return (cls.buffer.pack_varint(contact_cooldown_ticks)
                + cls.buffer.pack_varint(delay_ticks)
                + cls.pack_kinetic_weapon_condition(dismount_conditions)
                + cls.pack_kinetic_weapon_condition(knockback_conditions)
                + cls.pack_kinetic_weapon_condition(damage_conditions)
                + cls.buffer.pack('ff', forward_movement, damage_multiplier)
                + cls.buffer.pack_optional(cls.pack_sound_event, sound)
                + cls.buffer.pack_optional(cls.pack_sound_event, hit_sound))

    def unpack_kinetic_weapon(self):
        return {
            'contact_cooldown_ticks': self.buffer.unpack_varint(),
            'delay_ticks': self.buffer.unpack_varint(),
            'dismount_conditions': self.unpack_kinetic_weapon_condition(),
            'knockback_conditions': self.unpack_kinetic_weapon_condition(),
            'damage_conditions': self.unpack_kinetic_weapon_condition(),
            'forward_movement': self.buffer.unpack('f'),
            'damage_multiplier': self.buffer.unpack('f'),
            'sound': self.buffer.unpack_optional(self.unpack_sound_event),
            'hit_sound': self.buffer.unpack_optional(self.unpack_sound_event),
        }

    @classmethod
    def pack_kinetic_weapon_condition(cls, condition):
        max_duration_ticks = condition.get('max_duration_ticks', 0)
        min_speed = condition.get('min_speed', 0.0)
        min_relative_speed = condition.get('min_relative_speed', 0.0)

        return (cls.buffer.pack_varint(max_duration_ticks)
                + cls.buffer.pack('ff', min_speed, min_relative_speed))

    def unpack_kinetic_weapon_condition(self):
        return {
            'max_duration_ticks': self.buffer.unpack_varint(),
            'min_speed': self.buffer.unpack('f'),
            'min_relative_speed': self.buffer.unpack('f')
        }

    # Swing Animation  ---------------------------------------------------------------

    @classmethod
    def pack_swing_animation(cls, value):
        swing_animation = value.get('swing_animation', "whack")
        duration = value.get('duration', 6)

        return (cls.buffer.pack_varint(swing_animation_types.index(swing_animation))
                + cls.buffer.unpack_varint(duration))

    def unpack_swing_animation(self):
        return {
            'swing_animation': swing_animation_types[self.buffer.unpack_varint()],
            'duration': self.buffer.unpack_varint(),
        }
