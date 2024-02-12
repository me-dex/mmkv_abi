import weakref

from mmkv_abi.item_attribute import ItemAttribute


class TreeNode:
    def __init__(self, makemkv, handle: int):
        self._makemkv = weakref.ref(makemkv)
        self._handle = handle
        self._info_cache = {}
        self._state: int = None

    async def get_info(self, item_attribute: ItemAttribute):
        if item_attribute not in self._info_cache:
            self._info_cache[item_attribute] = await self._makemkv().get_ui_item_info(self._handle, item_attribute)

        return self._info_cache[item_attribute]

    async def get_name(self):
        return await self.get_info(ItemAttribute.Name)

    async def get_state(self):
        if self._state is None:
            self._state = await self._makemkv().get_ui_item_state(self._handle)

        return self._state

    async def set_state(self):
        if self._state is None:
            return

        return await self._makemkv().set_ui_item_state(self._handle, self._state)

    async def is_enabled(self):
        if self._state is None:
            await self.get_state()

        return await self.get_state() & 0x01 == 1

    async def is_expanded(self):
        if self._state is None:
            await self.get_state()

        await self.get_state() & 0x02 == 2

    async def set_enabled(self, value: bool):
        if self._state is None:
            await self.get_state()

        self._state = (self._state & 0xfffffffe) | int(value)
        await self.set_state()

    async def set_expanded(self, value: bool):
        if self._state is None:
            await self.get_state()

        self._state = (self._state & 0xfffffffd) | int(value) << 1
        await self.set_state()
