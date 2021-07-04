from enum import Enum


class TimelapseGeneratorCommand(Enum):
    PAUSE = 0
    RESUME = 1
    STOP = 2

class Motion(Enum):
    STOP = 0
    IDLE = 1 # Car is started but still not moving
    DRIVE = 2
