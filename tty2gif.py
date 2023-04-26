#!/usr/bin/env python3
"""Script to convert ttyrec file to gifs"""

# based on https://gist.github.com/yangchenyun/17c616d05ee0fbbe27700156d77df729

import warnings
import argparse
import os
import sys
import struct
import glob
import time

warnings.filterwarnings("ignore")

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gdk, GdkPixbuf

FrameHead = struct.Struct('iii')

parser = argparse.ArgumentParser(description='Convert ttyrec data to gifs.')
parser.add_argument('action', choices=['replay', 'inspect', 'output'],
                    help='Action to be performed on the ttyrec binary.')
parser.add_argument('input', type=str, help='ttyrec filename to be processed.')
parser.add_argument('--output', type=str, default='tty.gif', help='Output gif filename')
parser.add_argument('--factor', type=int, default=1, help='Speedup factor.')

SKIP_THRESHOLD = 0.005
SKIP_LIMIT = 5


def _take_screenshot(filename):
    """Take screenshot of current terminal."""
    # capture current frame in png
    win = getattr(_take_screenshot, 'win', None)
    if win is None:
        screen = Gdk.Screen.get_default()
        win = _take_screenshot.win = screen.get_active_window()

        relx, rely, width, height = win.get_geometry()

        _take_screenshot.posx, _take_screenshot.posy = relx, rely
        _take_screenshot.w = width
        _take_screenshot.h = height

    pb = Gdk.pixbuf_get_from_window(
        _take_screenshot.win,
        _take_screenshot.posx,
        _take_screenshot.posy,
        _take_screenshot.w,
        _take_screenshot.h,
    )
    pb.savev(filename, "png", [], [])


def replay(payload, delay, skip=False):
    """No-op placeholder for replay action.

    The frame rate of replay reflects the delay of ttyrec with `--factor`
    parameter to adjust the speed.
    """
    sys.stdout.buffer.write(payload)
    sys.stdout.flush()
    time.sleep(delay)


def output(payload, delay, skip=False):
    """Write current frame to files.

    TODO: Different from replay, the frame rate of capturing is constant to
    preseve the original speed in final output gif.

    """
    if not skip:
        output.count = getattr(output, 'count', -1) + 1
        png_file = 'step_%04d.png' % output.count
        _take_screenshot(png_file)

    sys.stdout.buffer.write(payload)
    sys.stdout.flush()
    # time.sleep(0.005)


def inspect(payload, delay, skip=False):
    """Action to print out the frame data for inspection."""
    n = len(payload)
    print('%8.4f %4d %s' % (delay, n, repr(payload[:40])))


if __name__ == '__main__':
    args = parser.parse_args()
    try:
        action = globals()[args.action]
        factor = args.factor
    except KeyError:
        print('Action %s is not defined as method.' % args.action)
        exit(1)

    with open(args.input, 'rb') as script:
        basetime = None
        prevtime = None
        skip = False
        nskipped = 0
        while True:
            data = script.read(FrameHead.size)
            if not data:
                break
            sec, usec, n = FrameHead.unpack(data)
            payload = script.read(n)

            # compute the delay from last frame
            curtime = sec + usec / 1000000.0
            if basetime is None:
                basetime = prevtime = curtime
            delay = (curtime - prevtime) / factor
            prevtime = curtime

            # Skip actions for some
            if (delay <= SKIP_THRESHOLD):
                skip = True
                nskipped += 1
            else:
                skip = False
                nskipped = 0

            if (skip and nskipped > SKIP_LIMIT):
                nskipped = 0
                skip = False

            action(payload, delay, skip)

    # print "generating the final gif..."
    os.system('ffmpeg -i step_%04d.png -vf palettegen palette.png')
    os.system('ffmpeg -i step_%%04d.png -i palette.png -lavfi "paletteuse,setpts=2*PTS" -y %s' % (args.output,))
