from mmkv_abi.item_attribute import ItemAttribute
from mmkv_abi.title_tree.tree_node import TreeNode


class Track(TreeNode):
    async def get_codec_long(self):
        return await self.get_info(ItemAttribute.CodecLong)

    async def get_type(self):
        return await self.get_info(ItemAttribute.Type)
