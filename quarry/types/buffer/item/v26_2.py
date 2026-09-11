from typing import TYPE_CHECKING

from quarry.types.buffer.item.v26_1 import ItemBuffer26_1

if TYPE_CHECKING:
    from quarry.types.buffer import Buffer26_2

class ItemBuffer26_2(ItemBuffer26_1):
    component_handlers = list(ItemBuffer26_1.component_handlers.items())
    component_handlers.insert(78, ('sulfur_cube_content', (lambda cls: cls.pack_item, lambda self: self.unpack_item)))

    component_handlers = dict(component_handlers)
    component_types = list(component_handlers.keys())

    def __init__(self, buffer: 'Buffer26_2'):
        super(ItemBuffer26_1, self).__init__(buffer)
