import re
import sys

from curses import setupterm
from curses import tigetnum
from curses import tigetstr
from curses import tparm
from time import sleep


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


def main(filename, count=23, offset=23, startrow=10, period=0.084):
    """
    count - how many times to "bleed" (Kobayashi OP Kanna default = 23)
    offset - how many columns to offset
    startrow - rows to offset from the top
    """

    with open(filename) as fd:
        text = fd.read()

    bleed_text(text, count, offset, startrow, period)
    return 0


if __name__ == '__main__':
    if not sys.argv[1:]:
        sys.stderr.write('usage: %s <textfile>\n' % sys.argv[0])
        sys.exit(1)
    sys.exit(main(sys.argv[1]))
