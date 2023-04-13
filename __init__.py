from myvideos import MyVideos
from DialogResume import DialogResume
from ffmpegTranformation import ManiopulateVideoFFMPEG
from util import Util
from utilFileTimes import UtilFilesTimes
from TimeComponent import TimeComponent


version_tuple = (0, 0, 2)


def get_version_string():
    if isinstance(version_tuple[-1], str):
        return ".".join(map(str, version_tuple[:-1])) + version_tuple[-1]
    return ".".join(map(str, version_tuple))


__version__ = version = get_version_string()