#!/usr/bin/env python
import os
import re
import sys

from argparse import ArgumentParser
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

    sys.stdout.write('\n')


def bleed_lines(lines, col, startrow):
    setupterm()
    # TODO abort if wrong height
    for row, line in enumerate(lines, start=startrow):
        _bleed_row(line, row, col)
    sys.stdout.flush()


def bleed_text(text, count, offset, startrow, period):
    lines = text.splitlines()
    for col in range(0, count * offset, offset):
        bleed_lines(lines, col, startrow)
        sleep(period)


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


def simple(filename, count=23, offset=23, startrow=10, period=0.084):
    """
    count - how many times to "bleed" (Kobayashi OP Kanna default = 23)
    offset - how many columns to offset
    startrow - rows to offset from the top
    """

    try:
        text = loader(filename)
    except ValueError as e:
        sys.stderr.write(str(e))
        return 1

    bleed_text(text, count, offset, startrow, period)
    return 0


if __name__ == '__main__':
    argparser = ArgumentParser()
    argparser.add_argument('filename', action='store')
    argparser.add_argument(
        '-r', '--startrow', action='store', default=10, type=int,
        help="number of rows to offset from top")
    argparser.add_argument(
        '-o', '--offset', action='store', default=23, type=int,
        help="number of columns for horizontal offsets")
    argparser.add_argument(
        '--period', action='store', default=0.083, type=float,
        help="period (timeout per frame for simple (not script) mode)")

    args = argparser.parse_args(sys.argv[1:])

    sys.exit(simple(
        args.filename,
        offset=args.offset,
        startrow=args.startrow,
        period=args.period,
    ))
