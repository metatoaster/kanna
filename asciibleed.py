#!/usr/bin/env python
import os
import re
import sys

from argparse import ArgumentParser
from argparse import ArgumentDefaultsHelpFormatter
from curses import setupterm
from curses import tigetnum
from curses import tigetstr
from curses import tparm
from time import sleep

default_encoding = sys.getdefaultencoding()


def get_width():
    return tigetnum('cols')


def get_height():
    return tigetnum('lines')


def _bleed_row(line, row, col_start):
    counter = col_start
    for fragment in re.split('( +)', line):
        if not fragment:
            continue
        if fragment[0] != ' ':
            start = tparm(tigetstr("cup"), row, counter).decode('ascii')
            # print up to the maximum amount of cols.
            chars = max(0, get_width() - counter)
            sys.stdout.write(start + fragment[:chars])

        counter += len(fragment)


def bleed_lines(lines, col, startrow):
    setupterm()
    height = get_height()
    for row, line in enumerate(lines, start=startrow):
        if row >= height:
            break
        _bleed_row(line, row, col)
    else:
        sys.stdout.write('\n')
    sys.stdout.flush()


def loader(filename):
    if not os.path.exists(filename):
        raise ValueError("'%s' not found\n" % filename)

    if not os.path.isfile(filename):
        raise ValueError("'%s' is not a file\n" % filename)

    try:
        with open(filename, 'rb') as fd:
            raw = fd.read()
    except (IOError, OSError):
        raise ValueError("error reading '%s'\n" % filename)

    encodings = ['utf-8', 'ascii', default_encoding]
    for c in encodings:
        try:
            return raw.decode('utf-8')
        except UnicodeDecodeError:
            continue

    raise ValueError("error decoding '%s' with encodings: %s\n" % (
        filename, ', '.join(set(encodings))))


def parse_script(text):
    """
    First line is the version (omitted for now)

    Second line lists all the files; they will be read into a list for
    usage by the remaining lines by numeric reference (0th-indexed)

    Remaining lines list out the frames to be animated for the current
    frame per line.  Every new line advances th ecolumn count by a given
    offset (in run_script)
    """

    try:
        lines = text.splitlines()
        files = lines[1].split(':')
        frames = [loader(f).splitlines() for f in files]
        return [[frames[int(i)] for i in s.split(',')] for s in lines[2:]]
    except ValueError as e:
        raise ValueError(
            "values listed in the script must be an integer in the range of "
            "[0-%d]\n" % len(files)
        )
    except IndexError as e:
        raise ValueError(
            "a value listed in the script lies outside the valid range of "
            "[0-%d]\n" % len(files)
        )


def run_script(script, offset, startrow, period):
    """
    count - how many times to "bleed" (Kobayashi OP Kanna default = 23)
    offset - how many columns to offset
    startrow - rows to offset from the top
    """

    current_col = 0

    for shifts in script:
        for lines in shifts:
            bleed_lines(lines, current_col, startrow)
            sleep(period)
        # shift right
        current_col += offset


def main(
        filename, script=False, count=23, offset=23, startrow=10,
        period=0.084, fps=24, background=None):
    """
    count - how many times to "bleed" (Kobayashi OP Kanna default = 23)
    offset - how many columns to offset
    startrow - rows to offset from the top
    """

    try:
        text = loader(filename)
        if script:
            period = 1.0 / max(1, fps)
            script = parse_script(text)
        else:
            # legacy mode; lazily generate the "script"
            script = [[text.splitlines()]] * count

        if background:
            bg_lines = loader(background).splitlines()
            bleed_lines(bg_lines, 0, 0)

        run_script(script, offset, startrow, period)
    except ValueError as e:
        sys.stderr.write(str(e))
        return 1
    except KeyboardInterrupt:
        sys.stderr.write('quitting...\n')
        return 0

    sys.stdout.write('\n')
    return 0


if __name__ == '__main__':
    argparser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    argparser.add_argument('filename', action='store')
    argparser.add_argument(
        '-s', '--script', action='store_true',
        help="treat the provided filename as the script")
    argparser.add_argument(
        '-b', '--background', action='store',
        help="provide a file as a background")
    argparser.add_argument(
        '-r', '--startrow', action='store', default=10, type=int,
        help="number of rows to offset from top")
    argparser.add_argument(
        '-o', '--offset', action='store', default=23, type=int,
        help="number of columns for horizontal offsets")
    argparser.add_argument(
        '--count', action='store', default=23, type=int,
        help="print this number of times in simple mode")
    argparser.add_argument(
        '--period', action='store', default=0.083, type=float,
        help="period (timeout per frame for simple (not script) mode)")
    argparser.add_argument(
        '--fps', action='store', default=24, type=int,
        help="fps (for script mode)")

    args = argparser.parse_args(sys.argv[1:])
    sys.exit(main(**vars(args)))
