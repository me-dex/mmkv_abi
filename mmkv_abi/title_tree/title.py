from datetime import timedelta
from mmkv_abi.item_attribute import ItemAttribute
from mmkv_abi.title_tree.chapter import Chapter
from mmkv_abi.title_tree.chapter_list import ChapterList
from mmkv_abi.title_tree.track import Track
from mmkv_abi.title_tree.tree_node import TreeNode


class Title(TreeNode):
    def __init__(self, makemkv, handle: int, chapter_handle: int, chapter_size: int, track_size: int):
        super().__init__(makemkv, handle)
        self.chapters = ChapterList(makemkv, chapter_handle, chapter_size)
        self.tracks = [None] * track_size

    def add_track(self, index, handle):
        self.tracks[index] = Track(self._makemkv(), handle)

    def add_chapter(self, index, handle):
        self.chapters.add_chapter(index, handle)

    async def get_chapter_count(self):
        return await self.get_info(ItemAttribute.ChapterCount)

    async def get_duration(self):
        raw = await self.get_info(ItemAttribute.Duration)
        hours, minutes, seconds = raw.split(':')

        return timedelta(hours=int(hours), minutes=int(minutes), seconds=int(seconds))

    async def get_disc_size(self):
        return await self.get_info(ItemAttribute.DiskSize)
