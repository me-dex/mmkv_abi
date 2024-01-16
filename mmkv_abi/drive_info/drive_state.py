from enum import IntEnum


class DriveState(IntEnum):
    EmptyClosed = 0
    EmptyOpen = 1
    Inserted = 2
    Loading = 3
    NoDrive = 256
    Unmounting = 257
