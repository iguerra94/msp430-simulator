#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
##  registers.py
#
#  Copyright 2017 Unknown <root@hp425>
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

class Registers():
    R0, R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, R11, R12, R13, R14, R15 = range(16)
    PC = R0
    SP = R1
    SR = CG1 = R2
    CG2 = R3

    def __init__(self):
        self.reg = [0] * 16
        self.reg[Registers.PC] = 0xfffe
        self.reg[Registers.SR] = 0


    def __str__(self):
        s = ""

        for lbl, r in (("PC", Registers.PC),
                       ("SP", Registers.SP),
                       ("SR", Registers.SR),
                       ("CG1", Registers.CG1),
                       ("CG2", Registers.CG2)):
            s += "{:3s}: 0x{:04x}  ".format(lbl, self.reg[r])
        s += "\n\n"

        for line in range(0, 16, 4):
            for r in range(4):
                s += "R{:02d}: 0x{:04x}  ".format(r + line, self.reg[r + line])
            s += "\n"

        return s


    def clear_upper(self, reg):
        """ Borra los bits 8 a 15, para cumplir con la regla de operaciones
            con bytes
        """
        self.reg[reg] &= 0x00ff


    def get(self, reg, bit = None):
        """ Leer registro o un bit de un registro:
            Si <bit> es None (o no definido)
                devuelve al registro <reg>  (16 bit)
            Si <bit> es un valor de 0 a 15:
                devuelve True o False según el bit <bit> (del registro <reg>)
        """
        if bit == None:
            return self.reg[reg]
        else:
            return (self.reg[reg] & (1 << bit)) != 0


    def set(self, reg, state, bit = None):
        """ Setear registro o un bit de un registro:
            Si <bit> es None (o no definido)
                <state> será asignado al registro <reg>  (16 bit)
            Si <bit> es un valor de 0 a 15:
                El bit <bit> (del registro <reg> será asignado <state>
                (<state> debe ser True o False)
        """
        if bit == None:
            self.reg[reg] = state
        else:
            if state:
                self.reg[reg] |= (1 << bit)
            else:
                self.reg[reg] &= ~(1 << bit)


    def get_PC(self):
        """ Leer el Program Counter """
        return self.get(Registers.PC)


    def set_PC(self, new_pc):
        """ Setear al Program Counter """
        self.set(Registers.PC, new_pc)


    def get_SR(self, bit = None):
        """ Leer al registro de Status:
            Si bit es None (o no definido):
                devuelve al Status registro (completo)
            Si bit es una letra de Z, C, N, V:
                devuelve (True o False) del bit requerido
        """
        sr = Registers.SR

        if bit == None:
            return self.reg[sr]
        elif bit == 'Z':
            return self.get(sr, 1)
        elif bit == 'C':
            return self.get(sr, 0)
        elif bit == 'N':
            return self.get(sr, 2)
        elif bit == 'V':
            return self.get(sr, 8)


    def set_SR(self, new_sr, bit = None):
        """ Setear al registro de Status:
            Si bit es None (o no definido):
                <new_sr> será asignado al Status registro (completo)
            Si bit es una letra de Z, C, N, V:
                <new_sr> (True o False) será asignado al bit especificado
        """
        sr = Registers.SR

        if bit == None:
            self.reg[sr] = new_sr
        elif bit == 'Z':
            self.set(Registers.SR, new_sr, 1)
        elif bit == 'C':
            self.set(Registers.SR, new_sr, 0)
        elif bit == 'N':
            self.set(Registers.SR, new_sr, 2)
        elif bit == 'V':
            self.set(Registers.SR, new_sr, 8)


    def get_registers(self):
        return self.reg



def main():
    r = Registers()
    print(str(r))

    flags = 'ZCNV'

    for flag in flags:
        r.set_SR(True, flag)
        print(str(r))

    for flag in flags:
        r.set_SR(False, flag)
        print(str(r))

    r.set_SR(0xaa)
    print(str(r))

    return 0


if __name__ == '__main__':
    main()
