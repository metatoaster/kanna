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
    output = line.lstrip()
    spaces = len(line) - len(output)
    col = col_start + spaces
    start = tparm(tigetstr("cup"), row, col).decode('ascii')
    # print up to the maximum amount of cols.
    chars = max(0, get_width() - col)
    print(start + output[:chars])


def bleed_lines(lines, col, startrow):
    setupterm()
    for row, line in enumerate(lines, start=startrow):
        _bleed_row(line, row, col)


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

    # TODO abort if wrong height
    bleed_text(text, count, offset, startrow, period)


main('kanna.txt')
