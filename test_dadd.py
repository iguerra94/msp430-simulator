#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  test_dadd.py
#
#  Copyright 2017 John Coppens <john@jcoppens.com>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#

import pdb

def DADD_slow(reg1, reg2, carry_in = 0):
    """ Reg1 y reg2 son contenidos de registros codificados como BCD
        Resultado es una tupla con BCD y CY
    """
    bin1 = int("%x" % reg1)
    bin2 = int("%x" % reg2)
    bin_sum = bin1 + bin2 + carry_in
    bcd  = int("%d" % (bin_sum % 10000), 16)
    cy   = int("%d" % (bin_sum // 10000))
    return bcd, cy


def DADD_faster(reg1, reg2, carry_in = 0):
    result = 0; cy = 0
    for digit in range(4):
        dig = reg1 % 16 + reg2 % 16 + cy
        if dig > 9:
            cy = 1
            dig -= 10
        else:
            cy = 0
        result += dig * 16**digit
        reg1 //= 16
        reg2 //= 16
        #~ print(reg1, reg2, result)

    return result, cy


def main(args):
    DADD = DADD_slow
    #~ DADD = DADD_faster

    dadd, cy = DADD(0x1, 0x1)
    print("(%d) %04x" % (cy, dadd))

    dadd, cy = DADD(0x1, 0x9)
    print("(%d) %04x" % (cy, dadd))

    dadd, cy = DADD(0x1, 0x999)
    print("(%d) %04x" % (cy, dadd))

    dadd, cy = DADD(0x1, 0x9999)
    print("(%d) %04x" % (cy, dadd))

    dadd, cy = DADD(0x9999, 0x9999)
    print("(%d) %04x" % (cy, dadd))

    dadd, cy = DADD(0x1443, 0x3299)
    print("(%d) %04x" % (cy, dadd))

    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
