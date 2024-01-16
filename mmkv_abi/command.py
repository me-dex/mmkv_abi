from enum import Enum

class Command(Enum):
    '''
    Ported from the aproxy.h file
    '''
    Nop = 0
    Return = 1
    ClientDone = 2
    CallSignalExit = 3
    CallOnIdle = 4
    CallCancelAllJobs = 4

    CallSetOutputFolder=16
    CallUpdateAvailableDrives = 17
    CallOpenFile = 18
    CallOpenCdDisk = 19
    CallOpenTitleCollection = 20
    CallCloseDisk = 21
    CallEjectDisk = 22
    CallSaveAllSelectedTitlesToMkv = 23
    CallGetUiItemState = 24
    CallSetUiItemState = 25
    CallGetUiItemInfo = 26
    CallGetSettingInt = 27
    CallGetSettingString = 28
    CallSetSettingInt = 29
    CallSetSettingString = 30
    CallSaveSettings = 31
    CallAppGetString = 32
    CallBackupDisc = 33
    CallGetInterfaceLanguageData = 34
    CallSetUiItemInfo = 35
    CallSetProfile = 36
    CallInitMMBD = 37
    CallOpenMMBD = 38
    CallDiscInfoMMBD = 39
    CallDecryptUnitMMBD = 40
    CallSetExternAppFlags = 41
    CallManageState = 42
    CallAppSetString = 43

    BackEnterJobMode = 192
    BackLeaveJobMode = 193
    BackUpdateDrive = 194
    BackUpdateCurrentBar = 195
    BackUpdateTotalBar = 196
    BackUpdateLayout = 197
    BackSetTotalName = 198
    BackUpdateCurrentInfo = 199
    BackReportUiMessage = 200
    BackExit = 201
    BackSetTitleCollInfo = 202
    BackSetTitleInfo = 203
    BackSetTrackInfo = 204
    BackSetChapterInfo = 205
    BackReportUiDialog = 206

    BackFatalCommError = 224
    BackOutOfMem = 225
    Unknown = 239
