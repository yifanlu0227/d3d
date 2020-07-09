import datetime
import os
import xml.etree.ElementTree as ET
from collections import namedtuple
from enum import Enum, auto
from pathlib import Path

import numpy as np
from PIL import Image


class KittiObjectClass(Enum):
    DontCare = 0
    Car = auto()
    Van = auto()
    Truck = auto()
    Pedestrian = auto()
    Person_sitting = auto()
    Cyclist = auto()
    Tram = auto()
    Misc = auto()

# ========== Loaders ==========


def load_timestamps(basepath, file, formatted=False):
    """
    Read in timestamp file and parse to a list
    """
    timestamps = []
    if isinstance(basepath, (str, Path)):
        fin = Path(basepath, file).open()
    else:  # assume ZipFile object
        fin = basepath.open(str(file))

    with fin:
        if formatted:
            for line in fin.readlines():
                timestamps.append(np.datetime64(line))
        else:
            timestamps = (np.loadtxt(fin) * 1e9).astype("M8[ns]")

    return timestamps


def load_calib_file(basepath, file):
    """
    Read in a calibration file and parse into a dictionary.
    Accept path or file object as input
    """
    data = {}
    if isinstance(basepath, (str, Path)):
        fin = Path(basepath, file).open()
    else:  # assume ZipFile object
        fin = basepath.open(str(file))

    with fin:
        for line in fin.readlines():
            if not line.strip():
                continue
            if not isinstance(line, str):
                line = line.decode()

            key, value = line.split(':', 1)
            # The only non-float values in these files are dates, which we don't care about anyway
            try:
                data[key] = np.array([float(x) for x in value.split()])
            except ValueError:
                pass

    return data


def load_image(basepath, file, gray=False):
    """Load an image from file. Accept path or file object as basepath"""
    if isinstance(basepath, (str, Path)):
        return Image.open(Path(basepath, file)).convert('L' if gray else 'RGB')
    else:  # assume ZipFile object
        return Image.open(basepath.open(str(file))).convert('L' if gray else 'RGB')


def load_velo_scan(basepath, file, binary=True):
    """Load and parse a kitti file. Accept path or file object as basepath"""
    if binary:
        if isinstance(basepath, (str, Path)):
            scan = np.fromfile(Path(basepath, file), dtype=np.float32)
        else:
            with basepath.open(str(file)) as fin:
                buffer = fin.read()
            scan = np.frombuffer(buffer, dtype=np.float32)
    else:
        if isinstance(basepath, (str, Path)):
            scan = np.loadtxt(Path(basepath, file), dtype=np.float32)
        else:
            scan = np.loadtxt(basepath.open(str(file)), dtype=np.float32)
    return scan.reshape((-1, 4))


def load_label(basepath, file):
    '''
    Load label or result from text file in KITTI format
    '''
    data = []
    if isinstance(basepath, (str, Path)):
        fin = Path(basepath, file).open()
    else:  # assume ZipFile object
        fin = basepath.open(str(file))

    with fin:
        for line in fin.readlines():
            if not line.strip():
                continue
            if isinstance(line, bytes):
                line = line.decode()

            values = [KittiObjectClass[value] if idx == 0 else float(value)
                      for idx, value in enumerate(line.split(' '))]
            data.append(values)

    return data


class _TrackletPose(object):
    def __init__(self, xmlnode):
        for prop in xmlnode:
            setattr(self, prop.tag, float(prop.text))


class _TrackletObject(object):
    def __init__(self, xmlnode):
        for prop in xmlnode:
            if prop.tag == 'poses':
                self.poses = [_TrackletPose(item)
                              for item in prop if item.tag == 'item']
            elif prop.tag == "objectType":
                self.objectType = prop.text
            else:
                setattr(self, prop.tag, float(prop.text))


def load_tracklets(basepath, file):
    if isinstance(basepath, (str, Path)):
        fin = Path(basepath, file).open()
    else:  # assume ZipFile object
        fin = basepath.open(str(file))

    with fin:
        root = ET.fromstring(fin.read())
        root_tracklet = next(iter(root))
        tracklets = [_TrackletObject(item)
                     for item in root_tracklet if item.tag == 'item']
        return tracklets
