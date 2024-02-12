import asyncio
from collections import namedtuple
from logging import getLogger
from shutil import which
import struct
from subprocess import PIPE, STDOUT
import zlib

from .app_string import AppString
from .command import Command
from .drive_info import DriveInfo
from .exception import ABIVersionMismatch, CommunicationError, MakeMKVNotFound
from .item_attribute import ItemAttribute
from .language_data import LanguageData
from .title_tree import TitleList

TIMEOUT = 5
ABIResponse = namedtuple('ABIResponse', ('cmd', 'args', 'data'))


class MakeMKV:
    ABI_VERSION = 'A0001'
    TRANSPORT = 'std'  # pipe transport

    @staticmethod
    def _32t64(x, y):
        return x + (y << 32)

    def __init__(self, logger=None):
        self.language_data = None
        self.current_info = [None] * 10
        self.job_mode = False
        self.current_bar = 0
        self.total_bar = 0

        self.drives = {}
        self.titles = None

        if logger is None:
            logger = getLogger(__name__)

        self.logger = logger

        logger.debug('ABI version: %s', MakeMKV.ABI_VERSION)
        logger.debug('Transport: %s', MakeMKV.TRANSPORT)

        self._exec = which('makemkvcon')
        logger.debug('makemkvcon: %s', self._exec)

        if self._exec is None:
            raise MakeMKVNotFound()

    async def init(self, load_interface_language_data=True):
        self._process = await asyncio.create_subprocess_exec(
            self._exec, 'guiserver', f'{MakeMKV.ABI_VERSION}+{MakeMKV.TRANSPORT}',
            stdout=PIPE, stderr=STDOUT, stdin=PIPE
        )

        abi_version = str(await self._process.stdout.read(len(MakeMKV.ABI_VERSION)), 'utf-8')
        self.logger.debug('makemkvcon ABI version: %s', abi_version)

        if MakeMKV.ABI_VERSION != abi_version:
            raise ABIVersionMismatch()

        stdout = b'\x00'
        while stdout[-1] != 0xaa:
            stdout = await self._process.stdout.read(4)

        self._process.stdin.write(b'\xbb')
        await self._process.stdin.drain()

        if load_interface_language_data:
            await self.load_interface_language_data()

        self._init = True

    async def idle(self):
        await self._transact(Command.CallOnIdle)

    async def update_available_drives(self, flags: int = 0):
        await self._transact(Command.CallUpdateAvailableDrives, ('<I', flags))

    async def get_app_string(self, key: AppString | int, index_1=0, index_2=0):
        data = (await self._transact(
            Command.CallAppGetString,
            ('<I', key if isinstance(key, int) else key.value), ('<I', index_1), ('<I', index_2)
        )).data
        return str(data, 'utf-8')

    async def open_cd_disk(self, index, flags: int = 0):
        await self._transact(Command.CallOpenCdDisk, ('<I', index), ('<I', flags))

    async def get_ui_item_info(self, handle, item_attribute: ItemAttribute):
        res = await self._transact(Command.CallGetUiItemInfo, ('<Q', handle), ('<I', item_attribute.value))
        if res.args[0] != 0:
            if self.language_data is None:
                self.logger.warning('Language data not loaded; returning raw index')
                return res.args[0]

            return self.language_data[res.args[0]]
        elif res.args[1] != 0:
            return str(res.data[:-1], 'utf-8')

    async def load_interface_language_data(self):
        # AP_APP_LOC_MAX = 7000
        res = await self._transact(Command.CallGetInterfaceLanguageData, ('<I', 7000))
        unpacked_size, packed_size = res.args
        packed_data = res.data

        if len(packed_data) != packed_size:
            raise RuntimeError('Packed language data does not match expected size')

        unpacked_data = zlib.decompress(packed_data, bufsize=unpacked_size)
        if len(unpacked_data) != unpacked_size:
            raise RuntimeError('Unpacked language data does not match expected size')

        self.language_data = LanguageData(unpacked_data)

    async def get_ui_item_state(self, handle):
        res = await self._transact(Command.CallGetUiItemState, ('<Q', handle))
        return res.args[0]

    async def set_ui_item_state(self, handle, state):
        await self._transact(Command.CallSetUiItemState, ('<Q', handle), ('<I', state))

    async def set_output_folder(self, folder: str):
        await self._transact(Command.CallSetOutputFolder, data=bytes(folder, 'utf-8') + b'\x00')

    async def save_all_selected_to_mkv(self):
        await self._transact(Command.CallSaveAllSelectedTitlesToMkv)

    async def _transact(self, cmd: Command, *args, data: bytes = b''):
        await self._send_cmd(cmd, *args, data=data)
        return await self._recv_cmd()

    async def _send_cmd(self, cmd: Command, *args, data: bytes = b''):
        buffer = b''

        for fmt, arg in args:
            buffer += struct.pack(fmt, arg)

        buffer = struct.pack('<HBB', len(data), int(len(buffer) / 4), cmd.value) + buffer + data

        self.logger.debug('Sending: %s', buffer)
        self._process.stdin.write(buffer)
        await self._process.stdin.drain()

    async def _recv_cmd(self):
        while True:
            response = await self._unpack_received(self._process.stdout)
            if response is None:
                return None

            cmd, args, data = response
            ack_args = ()

            if cmd is Command.Nop:
                pass
            elif cmd is Command.BackUpdateDrive:
                drive_info = DriveInfo.from_update(args, data)
                if drive_info is not None:
                    self.drives[args[0]] = drive_info
            elif cmd is Command.BackSetTitleCollInfo:
                handle = self._32t64(args[0], args[1])
                self.titles = TitleList(args[2], self, handle)
            elif cmd is Command.BackSetTitleInfo:
                handle = self._32t64(args[1], args[2])
                chapter_handle = self._32t64(args[5], args[6])
                self.titles.add_title(args[0], handle, chapter_handle, args[4], args[3])
            elif cmd is Command.BackSetTrackInfo:
                handle = self._32t64(args[2], args[3])
                self.titles.get_title(args[0]).add_track(args[1], handle)
            elif cmd is Command.BackSetChapterInfo:
                handle = self._32t64(args[2], args[3])
                self.titles.get_title(args[0]).chapters.add_chapter(args[1], handle)
            elif cmd is Command.BackUpdateCurrentInfo:
                # TODO: Handle other cases
                if args[0] < 10:
                    self.current_info[args[0]] = str(data[:-1], 'utf-8')
            elif cmd is Command.BackEnterJobMode:
                self.job_mode = True
            elif cmd is Command.BackLeaveJobMode:
                self.job_mode = False
            elif cmd is Command.BackUpdateCurrentBar:
                self.current_bar = args[0]
            elif cmd is Command.BackUpdateTotalBar:
                self.total_bar = args[0]
            elif cmd is Command.Return:
                return ABIResponse(cmd, args, data)

            await self._send_cmd(Command.ClientDone, *ack_args)

    async def _unpack_received(self, stream):
        try:
            buffer = await asyncio.wait_for(stream.read(4), TIMEOUT)
            self.logger.debug('Received: %s', buffer)
        except asyncio.exceptions.TimeoutError:
            raise CommunicationError()

        if len(buffer) == 4:
            data_size, arg_len, cmd = struct.unpack('<HBB', buffer)
            cmd = Command(cmd)
        elif len(buffer) == 1:
            cmd = int.from_bytes(buffer, 'little')
            if cmd < 0xf0:
                raise RuntimeError('Received invalid command')

            data_size = arg_len = 0
            cmd = Command(int.from_bytes(buffer, 'little') - 0xf0)

        self.logger.debug('Received cmd: %s', cmd)
        self.logger.debug('Received arg length: %d', arg_len)
        self.logger.debug('Received data size: %d', data_size)

        args = [struct.unpack('<I', await stream.readexactly(4))[0] for _ in range(arg_len)]
        self.logger.debug('Received args: %s', args)

        try:
            data = await asyncio.wait_for(stream.readexactly(data_size), 1)
        except asyncio.exceptions.TimeoutError:
            raise CommunicationError()

        self.logger.debug('Received data: %s', data)

        return cmd, args, data
