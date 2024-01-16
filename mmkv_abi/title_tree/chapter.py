from datetime import timedelta
from mmkv_abi.item_attribute import ItemAttribute
from mmkv_abi.title_tree.tree_node import TreeNode


class Chapter(TreeNode):
    async def get_datetime(self):
        raw = await self.get_info(ItemAttribute.DateTime)
        hours, minutes, seconds = raw.split(':')

        return timedelta(hours=int(hours), minutes=int(minutes), seconds=int(seconds))
