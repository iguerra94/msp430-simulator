#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
##  disasm.py
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


import pdb
from memory import Memory

class Disassembler():
    def __init__(self, mem):
        self.mem = mem


    def one_opcode(self, addr):
        """ Desensambla la instruccion ubicada en la memoria ROM en la
            direccion <addr>.
            Retorna un string con el opcode y el operando, por ejemplo:
                rrc     25(R5)
        """
        self.addr = addr

        opcode = self.mem.load_word_at(self.addr)

        if self.addr >= 0xffc0:          # Estamos en la table de interrupciones?
            s = ".word   0x{:04x}".format(opcode)
            self.addr += 2
            return self.addr, s

        for mask, value, opc, opd in (
                         (0xff80, 0x1000, 'rrc',     self.opd_single_type1),
                         (0xff80, 0x1080, 'swpb',    self.opd_single_type2),
                         (0xff80, 0x1100, 'rra',     self.opd_single_type1),
                         (0xff80, 0x1180, 'sxt',     self.opd_single_type2),
                         (0xff80, 0x1200, 'push',    self.opd_single_type1),
                         (0xff80, 0x1280, 'call',    self.opd_single_type2),
                         (0xffff, 0x1300, 'reti',    self.opd_single_reti),

                         (0xfc00, 0x2000, 'jnz',     self.opd_jump),
                         (0xfc00, 0x2400, 'jz',      self.opd_jump),
                         (0xfc00, 0x2800, 'jnc',     self.opd_jump),
                         (0xfc00, 0x2c00, 'jc',      self.opd_jump),
                         (0xfc00, 0x3000, 'jn',      self.opd_jump),
                         (0xfc00, 0x3400, 'jge',     self.opd_jump),
                         (0xfc00, 0x3800, 'jl',      self.opd_jump),
                         (0xfc00, 0x3c00, 'jmp',     self.opd_jump),

                         (0xf000, 0x4000, 'mov',     self.opd_double),
                         (0xf000, 0x5000, 'add',     self.opd_double),
                         (0xf000, 0x6000, 'addc',    self.opd_double),
                         (0xf000, 0x7000, 'subc',    self.opd_double),
                         (0xf000, 0x8000, 'sub',     self.opd_double),
                         (0xf000, 0x9000, 'cmp',     self.opd_double),
                         (0xf000, 0xa000, 'dadd',    self.opd_double),
                         (0xf000, 0xb000, 'bit',     self.opd_double),
                         (0xf000, 0xc000, 'bic',     self.opd_double),
                         (0xf000, 0xd000, 'bis',     self.opd_double),
                         (0xf000, 0xe000, 'xor',     self.opd_double),
                         (0xf000, 0xf000, 'and',     self.opd_double),

                         (0x0000, 0x0000, 'nop',     self.opd_single_reti)):

            if (opcode & mask) == value:
                self.addr += 2

                s = opd(self.addr, opcode, opc)
                return self.addr, s


    # Retorna el registro destino en single operando
    def opc_register(self, opc):    return opc & 0x000f

    # Retorna el As
    def opc_As(self, opc):          return (opc >> 4) & 0x0003

    # Retorna si es una operacion de byte o word: Si el bit es 0 -> Word, sino es byte
    def opc_Byte(self, opc):        return (opc & 0x0040) != 0

    # Retorna el registro destino en doble operando
    def opc_destination(self, opc): return opc & 0x000f

    # Retorna el Ad
    def opc_Ad(self, opc):          return (opc >> 7) & 0x0001

    # Retorna el registro fuebte en doble operando
    def opc_source(self, opc):      return (opc >> 8) & 0x000f

    # retorna el sufijo '.b' si es una operacion de byte, sino retorna ''
    def opc_suffix(self, opc):      return '.b' if self.opc_Byte(opc) else ''


    def opd_As_select(self, opcode, regnr):
        As = self.opc_As(opcode)
        Rs = self.opc_source(opcode)

        if As == 0:
            if Rs == 3:
                s = "#0"
            else:
                s = "R%d" % regnr

        elif As == 1:
            if Rs == 2:
                s = "&%d" % self.mem.load_word_at(self.addr)
                self.addr += 2
            elif Rs == 3:
                s = "#1"
            else:
                s = "%d(R%d)" % (self.mem.load_word_at(self.addr),
                                 regnr)
                self.addr += 2

        elif As == 2:
            if Rs == 2:
                s = "#4"
            elif Rs == 3:
                s = "#2"
            else:
                s = "@R%d" % regnr

        elif As == 3:
            if Rs == 0:
                s = "#%d" % self.mem.load_word_at(self.addr)
                self.addr += 2
            elif Rs == 2:
                s = "#8"
            elif Rs == 3:
                s = "#-1"
            else:
                s = "@R%d+" % regnr
        return s


    def opd_Ad_select(self,opcode, regnr):
        Ad = self.opc_Ad(opcode)

        if Ad == 0:
            s = "R%d" % regnr

        elif Ad == 1:
            if regnr == 2:
                s = "&%d" % self.mem.load_word_at(self.addr)
            elif regnr == 3:
                s = "1(R%d)" % regnr
            else:
                s = "%d(R%d)" % (self.mem.load_word_at(self.addr),
                                 regnr)
            self.addr += 2

        return s

    #
    #   Instrucciones de simple operando
    #

    def opd_single_type1(self, addr, opcode, opcstr):
        """ Desensamblar instruccion RRC, RRA, PUSH """
        return "%-8s%s" % (opcstr + self.opc_suffix(opcode),
                           self.opd_As_select(opcode, self.opc_destination(opcode)))


    def opd_single_type2(self, addr, opcode, opcstr):
        """ Desensamblar instruccion SWPB, SXT, CALL """
        return "%-8s%s" % (opcstr,
                           self.opd_As_select(opcode, self.opc_destination(opcode)))


    def opd_single_reti(self, addr, opcode, opcstr):
        """ Desensamblar instruccion RETI """
        return "%-8s" % (opcstr)

    #
    #   Instrucciones de doble operando
    #

    def opd_double(self, addr, opcode, opcstr):
        return "%-8s%s, %s" % (opcstr + self.opc_suffix(opcode),
                               self.opd_As_select(opcode, self.opc_source(opcode)),
                               self.opd_Ad_select(opcode, self.opc_destination(opcode)))

    #
    #   Instrucciones de salto (condicional)
    #

    def opd_jump(self, addr, opcode, opcstr):
        offset = (opcode & 0x03ff) - 1
        if (offset & 0x0200) != 0:      # Positivo
            offset |= 0xfe00
        addr1 = (addr + 2*offset) & 0xffff

        return "%-8s0x%04x" % (opcstr, addr1)


    def disassemble(self, start, end):
        pc = start
        while pc <= end:
            new_pc, s = self.one_opcode(pc)
            print("{:04x}  {:s}".format(pc, s))
            pc = new_pc


    def disassemble_all(self):
        pc = self.mem.mem_start

        while pc < (self.mem.mem_start + self.mem.mem_size):
            try:
                self.mem.load_word_at(pc)
            except:
                pc += 2
                continue

            new_pc, s = self.one_opcode(pc)
            yield pc, new_pc, s
            pc = new_pc


def main():
    m = Memory(1024, mem_start = 0xfc00)
    d = Disassembler(m)

    m.store_words_at(0xfd00, [
                0x3c55, 0x3e55,
                0x1005, 0x1015, 0x0019, 0x1026, 0x1037,
                0x1088, 0x1098, 0x001a, 0x10a9, 0x10b9,
                0x1105, 0x1196, 0x001b, 0x122b, 0x12bc,
                0x1300])

    print(m.dump(0xfd00, 96))

    print("             Debe ser:    Reportado:")
    print("Registro     13           {:d}".format(d.opc_register(0x3c5d)))
    print("As           3            {:d}".format(d.opc_As(0x3c7d)))
    print("Byte         True         {:s}".format(str(d.opc_Byte(0x3c7d))))
    print("Byte         False        {:s}".format(str(d.opc_Byte(0x3c3d))))
    print("Ad           1            {:d}".format(d.opc_Ad(0x3cfd)))
    print("Source       12           {:d}".format(d.opc_source(0x3c7d)))
    print("Destinat.    13           {:d}".format(d.opc_destination(0x3c7d)))

    #   d.disassemble(0xfd00, 0xfd11)

    dasm = d.disassemble_all()
    for pc, new_pc, s in dasm:
        print("{:04x}  {:s}".format(pc, s))

    return 0

if __name__ == '__main__':
    main()
