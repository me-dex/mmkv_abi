from mmkv_abi.item_attribute import ItemAttribute
from mmkv_abi.title_tree.chapter import Chapter
from mmkv_abi.title_tree.tree_node import TreeNode


class ChapterList(TreeNode):
    def __init__(self, makemkv, handle, size):
        super().__init__(makemkv, handle)
        self._chapters = [None] * size

    def add_chapter(self, index, handle):
        self._chapters[index] = Chapter(self._makemkv(), handle)

    def __getitem__(self, index):
        return self._chapters[index]

    def __contains__(self, item):
        return self._chapters.__contains__(item)

    def __iter__(self):
        return self._chapters.__iter__()
    
    def __len__(self):
        return len(self._chapters)

    async def get_chapter_count(self):
        return await self.get_info(ItemAttribute.ChapterCount)
