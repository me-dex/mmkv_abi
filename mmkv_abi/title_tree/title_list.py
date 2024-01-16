from mmkv_abi.title_tree.title import Title
from mmkv_abi.title_tree.tree_node import TreeNode


class TitleList(TreeNode):
    def __init__(self, size, makemkv, handle):
        super().__init__(makemkv, handle)
        self._titles: [Title] = [None] * size

    def add_title(self, index: int, handle: int, chapter_handle: int, chapter_size: int, track_size: int):
        self._titles[index] = Title(self._makemkv(), handle, chapter_handle, chapter_size, track_size)

    def get_title(self, index: int) -> Title:
        return self._titles[index]
    
    def __getitem__(self, index):
        return self.get_title(index)

    def __len__(self):
        return len(self._titles)
    
    def __iter__(self):
        return iter(self._titles)

    async def print(self):
        async def selected_sym(node):
            return "✅" if await node.is_enabled() else "❎"

        print(await self.get_name())

        for i, title in enumerate(self._titles):
            p = ('└', ' ') if len(self._titles) - i == 1 else ('├', '│')

            print(f'{p[0]}─ {await selected_sym(title)} {await title.get_name()} - {await title.get_duration()}, {await title.get_chapter_count()} chapter(s), {await title.get_disc_size()}')

            print(f'{p[1]}  ├─ Chapters')
            for i, chapter in enumerate(title.chapters):
                q = '└' if len(title.chapters) - i == 1 else '├'
                print(f'{p[1]}  │  {q}─ {await chapter.get_name()} - {await chapter.get_datetime()}')

            print(f'{p[1]}  └─ Tracks')
            for i, track in enumerate(title.tracks):
                q = '└' if len(title.tracks) - i == 1 else '├'
                print(f'{p[1]}     {q}─ {await selected_sym(title)} {await track.get_type()} - {await track.get_codec_long()}')
