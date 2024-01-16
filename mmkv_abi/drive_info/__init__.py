from datetime import datetime
from enum import IntEnum
import pprint
import struct

from .drive_state import DriveState
from .inquiry_data import InquiryData

class DriveInfoCategory(IntEnum):
    Invalid = 0
    DriveStandard = 1
    DriveSpecific = 2
    DiscStandard = 3
    DiscSpecific = 4
    UserPrivate = 5


class DriveInfoId(IntEnum):
    # Invalid
    InvalidValue = 0
    DriveioTag = (DriveInfoCategory.Invalid.value << 24) + (1 << 16)
    DriveioPad = (DriveInfoCategory.Invalid.value << 24) + (2 << 16)

    # DriveStandard
    InquiryData = (DriveInfoCategory.DriveStandard.value << 24) + (0 << 16)
    FeatureDescriptor = (DriveInfoCategory.DriveStandard.value << 24) + (1 << 16)
    FeatureDescriptor_DriveSerialNumber = (DriveInfoCategory.DriveStandard.value << 24) + (1 << 16) + 0x108
    FeatureDescriptor_FirmwareInformation = (DriveInfoCategory.DriveStandard.value << 24) + (1 << 16) + 0x10c
    FeatureDescriptor_AACS = (DriveInfoCategory.DriveStandard.value << 24) + (1 << 16) + 0x10d
    CurrentProfile = (DriveInfoCategory.DriveStandard.value << 24) + (2 << 16) + 0
    DriveCert = (DriveInfoCategory.DriveStandard.value << 24) + (3 << 16) + 0x38

    # DriveSpecific
    FirmwareDetailsString = (DriveInfoCategory.DriveSpecific.value << 24) + 0 + 1
    FirmwarePlatform = (DriveInfoCategory.DriveSpecific.value << 24) + 0 + 1
    FirmwareVendorSpecificInfo = (DriveInfoCategory.DriveSpecific.value << 24) + 0 + 2
    FirmwareFlashImage = (DriveInfoCategory.DriveSpecific.value << 24) + 0 + 3

    # DiscStandard
    DiscStructure = (DriveInfoCategory.DiscStandard.value << 24) + (0 << 16)
    DiscStructure_DVD_PhysicalFormat=(DriveInfoCategory.DiscStandard.value << 24) + (0 << 16) + 0x000
    DiscStructure_DVD_CopyrightInformation=(DriveInfoCategory.DiscStandard.value << 24) + (0 << 16) + 0x001
    DiscStructure_BD_DiscInformation=(DriveInfoCategory.DiscStandard.value << 24) + (0 << 16) + 0x100
    TOC = (DriveInfoCategory.DiscStandard.value << 24) + (1 << 16)
    DiscInformation = (DriveInfoCategory.DiscStandard.value << 24) + (2 << 16)
    DiscCapacity = (DriveInfoCategory.DiscStandard.value << 24) + (3 << 16)

    # DiscSpecific
    Aacs = (DriveInfoCategory.DiscSpecific.value << 24) + (0<<16)
    Aacs_VID = (DriveInfoCategory.DiscSpecific.value<<24) + (0<<16) + 0x80
    Aacs_KCD = (DriveInfoCategory.DiscSpecific.value<<24) + (0<<16) + 0x7f
    Aacs_PMSN = (DriveInfoCategory.DiscSpecific.value<<24) + (0<<16) + 0x81
    Aacs_MID = (DriveInfoCategory.DiscSpecific.value<<24) + (0<<16) + 0x82
    Aacs_DataKeys = (DriveInfoCategory.DiscSpecific.value<<24) + (0<<16) + 0x84
    Aacs_BEExtents = (DriveInfoCategory.DiscSpecific.value<<24) + (0<<16) + 0x85
    Aacs_BindingNonce = (DriveInfoCategory.DiscSpecific.value << 24) + (0<<16) + 0x7e


class DriveInfo:
    def __init__(self):
        # Header info
        self.drive_id = None
        self.drive_name = None
        self.disc_name = None
        self.device_name = None

        # Additional info
        self.driveio_tag = None
        self.current_profile = None
        self.libredrive_info = None

        self.disc_timestamp = None

        self.disc_has_css = False
        self.disc_has_cprm = False
        self.disc_has_aacs = False
        self.disc_has_bdsvm = False

        self.disc_aacs_mkb_version = None
        self.disc_aacs_version = None
        self.disc_aacs_category = None

        self.disc_svm_version = None

        # Feature Descriptors
        self.drive_state = None

        self.drive_serial_number = None
        self.drive_firmware_date = None
        self.drive_firmware_string = None
        self.drive_highest_aacs = None

        # Disc Structure
        self.disc_capacity = None
        self.disc_type = None
        self.disc_size = None
        self.disc_read_rate = None
        self.disc_layers = None
        self.disc_layer_orientation = None
        self.disc_channel_bit_length = None

    @classmethod
    def from_update(cls, args, data):
        if len(data) == 0:
            return None

        data_view = memoryview(data)
        instance = cls()

        instance.drive_id = args[0]
        instance.drive_state = DriveState(args[2])

        disc_fs_flags = args[3]
        instance.disc_has_aacs = disc_fs_flags & 8 != 0
        instance.disc_has_bdsvm = disc_fs_flags & 16 != 0

        flags = args[1]
        start_idx = end_idx = 0

        if flags & 1 == 1:
            end_idx = data.find(b'\x00', start_idx) + 1
            instance.drive_name = str(data_view[start_idx:end_idx - 1], 'utf-8')
            start_idx = end_idx

        if flags & 2 == 2:
            end_idx = data.find(b'\x00', start_idx) + 1
            instance.disc_name = str(data_view[start_idx:end_idx - 1], 'utf-8')
            start_idx = end_idx

        if flags & 4 == 4:
            end_idx = data.find(b'\x00', start_idx) + 1
            instance.device_name = str(data_view[start_idx:end_idx - 1], 'utf-8')
            start_idx = end_idx

        while end_idx < len(data):
            start_idx = end_idx
            end_idx += 8
            cmd_id, data_size = struct.unpack('>II', data_view[start_idx:end_idx])

            start_idx = end_idx
            end_idx += data_size

            if cmd_id == DriveInfoId.DriveioTag:
                instance.driveio_tag = str(data_view[start_idx:end_idx - 1], 'utf-8').strip()
            elif cmd_id == DriveInfoId.InquiryData:
                if data_size >= 36:
                    manufacturer = str(data[start_idx + 8:start_idx + 16], 'utf-8').strip()  # 8 bytes
                    product = str(data[start_idx + 16:start_idx + 32], 'utf-8').strip()  # 16 bytes
                    revision = str(data[start_idx + 32:start_idx + 36], 'utf-8').strip()  # 4 bytes
                    instance.inquiry_data = InquiryData(manufacturer, product, revision)
            elif cmd_id == DriveInfoId.FeatureDescriptor_DriveSerialNumber:
                if data_size >= 8:
                    size = int(data_view[start_idx + 3])
                    instance.drive_serial_number = str(data_view[start_idx + 4:start_idx + size], 'utf-8')
            elif cmd_id == DriveInfoId.FeatureDescriptor_FirmwareInformation:
                if data_size == 20:
                    instance.drive_firmware_date = instance._parse_timestamp(data_view[start_idx:end_idx])
            elif cmd_id == DriveInfoId.FirmwareDetailsString:
                instance.drive_firmware_string = str(data_view[start_idx:end_idx], 'utf-8')
            elif cmd_id == DriveInfoId.CurrentProfile:
                if data_size >= 2:
                    profile_id = int.from_bytes(data_view[start_idx:end_idx], 'big')
                    instance.current_profile = cls._get_mmc_profile_string(profile_id)
            elif cmd_id == DriveInfoId.DiscCapacity:
                if data_size >= 8:
                    sec_size = int.from_bytes(data_view[start_idx:start_idx + 4], 'big')
                    instance.disc_capacity = sec_size / 1024 / 512
            elif cmd_id == DriveInfoId.DiscStructure_DVD_CopyrightInformation:
                if data_size >= 8:
                    protection = int(data_view[start_idx + 4])
                    if protection == 1:
                        instance.disc_has_css = True
                    elif protection == 2:
                        instance.disc_has_cprm = True
                    elif protection == 3 or protection == 16:
                        instance.disc_has_aacs = True
            elif cmd_id == DriveInfoId.DiscStructure_DVD_PhysicalFormat:
                if data_size < 16:
                    continue

                instance.disc_type = {
                    0: 'DVD-ROM',
                    1: 'DVD-RAM',
                    2: 'DVD-R',
                    3: 'DVD-RW',
                    4: 'HD DVD-ROM',
                    5: 'HD DVD-RAM',
                    6: 'HD DVD-R',
                    9: 'DVD+RW',
                    10: 'DVD+R',
                    11: 'DVD+RW DL',
                    12: 'DVD+R DL'
                }.get(int(data_view[start_idx + 4]) >> 4)

                instance.disc_size = {
                    0: '120mm',
                    1: '80mm'
                }.get(int(data_view[start_idx + 5]) >> 4)

                instance.disc_read_rate = {
                    0: 0.25,
                    1: 0.5,
                    2: 1,
                    3: 2,
                    4: 3
                }.get(int(data_view[start_idx + 5]) & 0x0f)

                instance.disc_layers = 1 + (int(data_view[start_idx + 6]) >> 5 & 3)
                instance.disc_layer_orientation = 'PTP' if int(data_view[start_idx + 6]) & 16 == 0 else 'OTP'
            elif cmd_id == DriveInfoId.DiscStructure_BD_DiscInformation:
                if data_size < 20:
                    continue

                if (
                    data_view[start_idx + 4:start_idx + 7] == b'DI\x01' and
                    bytes(data_view[start_idx + 12:start_idx + 15]) in [b'BDO', b'BDW', b'BDR', b'BDU']
                ):
                    instance.disc_type = {
                        1: 'BD-ROM',
                        2: 'BD-R',
                        4: 'BD-RE',
                        9: 'BD-ROM UHD'
                    }.get(int(data_view[start_idx + 16]) & 0x0f)

                    instance.disc_layers = int(data_view[start_idx + 16]) >> 4

                    instance.disc_channel_bit_length = {
                        1: '74.5 nm',
                        2: '69.0 nm'
                    }.get(int(data_view[start_idx + 17]) & 0x0f)
            elif cmd_id == 0x05102201:
                if data_size < 12:
                    continue

                if int(data_view[start_idx]) != 0x10:
                    continue

                instance.disc_aacs_mkb_version = int.from_bytes(data_view[start_idx + 8: start_idx + 12], 'big')
                instance.disc_aacs_version = {
                    10: '1.0/II',
                    20: '2.0',
                    21: '2.1'
                }.get(int(data_view[start_idx + 5]), '1.0')
            elif cmd_id == 0x05102202:
                if data_size < 17:
                    continue

                svm_year = int.from_bytes(data_view[start_idx + 13:start_idx + 15], 'big')
                svm_month = int(data_view[start_idx + 15])
                instance.disc_svm_version = f'{svm_year}.{svm_month}'
            elif cmd_id == 0x05102203:
                if data_size < 4:
                    continue

                instance.disc_aacs_category = {
                    0: 'C',
                    1: 'B',
                    2: 'A'
                }.get(int(data_view[start_idx + 1]))
            elif cmd_id == 0x05102204:
                if data_size != 4:
                    continue

                instance.drive_highest_aacs = int.from_bytes(data_view[start_idx:end_idx], 'big')
            elif cmd_id == 0x05102205:
                if data_size != 20:
                    continue

                instance.disc_timestamp = instance._parse_timestamp(data_view[start_idx:end_idx])
            elif cmd_id == 0x05102210:
                instance.libredrive_info = str(data_view[start_idx:end_idx - 2], 'utf-8').split('\n')[1:]
            else:
                #print(cmd_id, data_size, bytes(data_view[start_idx:end_idx]))
                pass

        return instance
    
    @classmethod
    def _parse_timestamp(cls, data):
        year = int(str(data[4:8], 'ascii'))
        month = int(str(data[8:10], 'ascii'))
        day = int(str(data[10:12], 'ascii'))

        hour = int(str(data[12:14], 'ascii'))
        minute = int(str(data[14:16], 'ascii'))

        if data[16:17] != b'\x00' and data[16:17] != b'\x20':
            second = int(str(data[16:18], 'ascii'))
        else:
            second = 0

        return datetime(year, month, day, hour, minute, second)

    @classmethod
    def _get_mmc_profile_string(cls, _id):
        return {
            8: 'CD-ROM',
            9: 'CD-R',
            10: 'CD-RW',
            16: 'DVD-ROM',
            17: 'DVD-R',
            18: 'DVD-RAM',
            19: 'DVD-RW',
            20: 'DVD-RW',
            21: 'DVD-R DL SR',
            22: 'DVD-R DL JR',
            23: 'DVD-RW DL',
            26: 'DVD+RW',
            27: 'DVD+R',
            42: 'DVD+RW DL',
            43: 'DVD+R DL',
            64: 'BD-ROM',
            65: 'BD-R SRM',
            66: 'BD-R RRM',
            67: 'BD-RE',
            80: 'HD DVD-ROM',
            81: 'HD DVD-R',
            82: 'HD DVD-RAM',
            83: 'HD DVD-RW',
            88: 'HD DVD-R DL',
            90: 'HD DVD-RW DL'
        }.get(_id)
