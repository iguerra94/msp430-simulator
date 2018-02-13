#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
##  memory.py
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

import sys
import pdb

class MemoryException(Exception): pass


class Memory():
    def __init__(self, mem_size,            # Tamaño de la memoria (en bytes)
                       mem_start = 0,       # Inicio de la memoria (en bytes)
                       readonly = False):   # Si la memoria puede ser modificado por código

        self.mem_size    = mem_size
        self.mem_start   = mem_start
        self.readonly    = readonly

        self.instruction_words = []

        self.initialize()

    def __str__(self):
        return self.dump()

    # Imprime el contenido de la memoria
    def dump(self, addr = None, nr_words = None):
        words_per_line = 16

        if addr == None:
            addr = 0
        else:
            addr = addr - self.mem_start

        if nr_words == None:
            nr_words = self.mem_size

        s = ""
        end_addr = addr + nr_words
        while addr < end_addr:
            s += "%04x " % (self.mem_start + addr)
            for offs in range(words_per_line):
                try:
                    s += " {:04x}".format(self.load_mem_word_at(addr + offs*2))
                except MemoryException:
                    s += " ...."
            s += "\n"
            addr += words_per_line * 2
        return s


    # Inicializa la memoria seteando todas las posiciones de memoria en None
    def initialize(self):
        self.mem = [None] * self.mem_size


    # Determina si el desplazamiento en la memoria <offs> esta dentro del rango de la memoria
    def in_mem_range(self, offs):
        return 0 <= offs < self.mem_size

    def get_instruction_words(self):
        return self.instruction_words

    # Retorna el contenido de la memoria en la posicion <offs> y <offs +1>
    # Controla que esas posiciones no esten fuera de rango y que esten inicializadas
    def load_mem_word_at(self, offs):
        """ <offs> es el offset en self.mem! NO la dirección en la memoria
        """
        if not self.in_mem_range(offs) or not self.in_mem_range(offs+1):
            raise MemoryException("Dirección fuera de rango (Offset: 0x{:04x})".format(offs))
        
        if self.mem[offs] == None or self.mem[offs+1] == None:
            raise MemoryException("Lectura de memoria no inicializada (Offset: 0x{:04x})".format(offs))

        return (self.mem[offs] + (self.mem[offs + 1] << 8))

    # Guarda el contenido de la palabra <word> en la posicion <offs> y <offs +1>
    # Controla que esas posiciones no esten fuera de rango 
    # En la posicion <offs> guarda el byte de la parte mas baja de la palabra
    # En la posicion <offs +1> guarda el byte de la parte mas alta de la palabra
    def store_mem_word_at(self, offs, word):
        """ <offs> es el offset en self.mem! NO la dirección en la memoria
        """
        if not self.in_mem_range(offs) or not self.in_mem_range(offs+1):
            raise MemoryException("Dirección fuera de rango (Offset: 0x{:04x})".format(offs))

        self.mem[offs] = word & 0xff
        self.mem[offs + 1] = word >> 8



    def load_from_intel(self, fname):
        """ Carga el contenido del archivo (de nombre <fname>). El formato Intel
            del archivo es:
                    :02001000A522xx
                                 ++----Suma de control
                             ++++------Datos
                           ++----------Tipo de linea: 00: datos,
                                                      01: fin de archivo
                                                      Otros: ignorar
                       ++++------------Direccion de destino
                     ++----------------Numero de bytes de datos
                    +------------------':' es el inicio del registro
        """
        self.initialize()

        # Limpiar la lista de instrucciones
        self.instruction_words.clear()

        with open(fname, "r") as inf:
            for line in inf:
                line = line.rstrip('\n')
                if line[0] != ":": continue
                if len(line) < 11:
                    print("Linea invalida en archivo hex [%s]" % line)
                    sys.exit(1)

                nrb = int(line[1:3], 16)         # Extrae nro de bytes
                adr = int(line[3:7], 16)         # Extrae direccion
                typ = int(line[7:9], 16)         # Extrae tipo de linea

                if typ == 0:
                    byte_nr = 0

                    for byte_nr in range(nrb):
                        s = line[9 + byte_nr*2 : 11 + byte_nr*2]
                        value = int(s, 16)
                        self.store_byte_at(adr, value)
                        adr += 1
                        s = ""
                        byte_nr += 1                            

                    addr = int(line[3:7], 16)

                    for i in range(0, int(nrb/2)):
                        if hex(addr) != "0xfffe":
                            try:
                                if self.load_word_at(addr+2) < int("0x1000", 16) or self.load_word_at(addr+2) > int("0x12B0", 16):
                                    nrb -= 2
                                    # print(nrb)
                                addr += 2
                            except MemoryException:
                                addr += 2

                    addr = int(line[3:7], 16)

                    # print(int(nrb/2))

                    # Inicializar las listas con las instrucciones y las palabras de memoria
                    for i in range(0, int(nrb/2)):
                        if hex(addr) != "0xfffe":
                            if nrb > 0 and nrb <= 2:
                                if self.load_word_at(addr) >= int("0x1000", 16) and self.load_word_at(addr) <= int("0x12B0", 16):
                                    # Instruction word
                                    self.instruction_words.append({ "LOCATION": addr, "CONTENT": self.load_word_at(addr), "OFFSET": None, "OFFSET_LOCATION": None })
                            else:
                                # Instruction word
                                try:
                                    if self.load_word_at(addr+2) < int("0x1000", 16) or self.load_word_at(addr+2) > int("0x12B0", 16):
                                        # Instruction word con offset
                                        self.instruction_words.append({ "LOCATION": addr, "CONTENT": self.load_word_at(addr), "OFFSET": self.load_word_at(addr+2), "OFFSET_LOCATION": addr+2 })
                                        addr += 2
                                    else:
                                        # Instruction word sin offset
                                        self.instruction_words.append({ "LOCATION": addr, "CONTENT": self.load_word_at(addr), "OFFSET": None, "OFFSET_LOCATION": None })

                                except MemoryException:
                                    self.instruction_words.append({ "LOCATION": addr, "CONTENT": self.load_word_at(addr), "OFFSET": None, "OFFSET_LOCATION": None })

                            addr += 2

                elif typ == 1:
                    break
                else:
                    continue

            # print("I,", self.instruction_words)


    def check_intel_line(self, line):
        if line[0] != ':': return False
        if len(line) < 11: return False

        checksum = 0
        i = 1
        while i < len(line):
            try:
                checksum += int(line[i:i+2], 16)
            except ValueError:
                return False
            i += 2

        return (checksum & 0xff) == 0


    def store_to_intel(self, fname):
        words_per_line = 8

        addr = 0
        intel = ""
        line_break = True
        word_count = 0
        last_addr = -4

        while addr < self.mem_size:
            if self.mem[addr] != None:
                opcode = self.load_word_at(addr + self.mem_start)
                opc_l = opcode & 0xff
                opc_h = (opcode & 0xff00) >> 8
                addr_abs = addr + self.mem_start
                addr_l = addr_abs & 0xff
                addr_h = (addr_abs & 0xff00) >> 8

                if (last_addr + 2) != addr:
                    if word_count != 0:
                        checksum += word_count
                        intel += ":{:02x}".format(word_count * 2) + \
                                 s + \
                                 "{:02x}\n".format(256 - checksum & 0xff)
                        first_line = False
                        word_count = 0

                    s = "{:04x}00".format(addr_abs)
                    checksum = addr_l + addr_h

                s += "{:02x}{:02x}".format(opc_l, opc_h)
                checksum += opc_l + opc_h
                last_addr = addr

                word_count += 1
                if word_count == words_per_line:
                    last_addr -= 2              # Forzar salto de bloque

            addr += 2

        if word_count != 0:
            checksum += word_count
            intel += ":{:02x}".format(word_count * 2) + \
                     s + \
                     "{:02x}\n".format(256 - checksum & 0xff)

        intel += ":00000001FF\n"

        with open(fname, "w") as outf:
            outf.write(intel)

        return


    def store_to_intel_with_words_list(self, fname, instruction_words_list = []):
        # print(instruction_words_list)

        words_per_line = 8

        addr = 0
        intel = ""
        line_break = True
        word_count = 0
        last_addr = -4

        for word in instruction_words_list:
            opcode = word["CONTENT"]
            opc_l = opcode & 0xff
            opc_h = (opcode & 0xff00) >> 8
            addr_abs = word["LOCATION"]
            addr_l = addr_abs & 0xff
            addr_h = (addr_abs & 0xff00) >> 8

            if (last_addr + 2) != addr:
                if word_count != 0:
                    checksum += word_count
                    intel += ":{:02x}".format(word_count * 2) + \
                                s + \
                                "{:02x}\n".format(256 - checksum & 0xff)
                    first_line = False
                    word_count = 0

                s = "{:04x}00".format(addr_abs)
                checksum = addr_l + addr_h

            s += "{:02x}{:02x}".format(opc_l, opc_h)
            checksum += opc_l + opc_h
            last_addr = addr

            word_count += 1
            if word_count == words_per_line:
                last_addr -= 2              # Forzar salto de bloque

            addr += 2

            if (word["OFFSET"] != None):
                opcode = word["OFFSET"]
                opc_l = opcode & 0xff
                opc_h = (opcode & 0xff00) >> 8
                addr_abs = word["OFFSET_LOCATION"]
                addr_l = addr_abs & 0xff
                addr_h = (addr_abs & 0xff00) >> 8

                if (last_addr + 2) != addr:
                    if word_count != 0:
                        checksum += word_count
                        intel += ":{:02x}".format(word_count * 2) + \
                                    s + \
                                    "{:02x}\n".format(256 - checksum & 0xff)
                        first_line = False
                        word_count = 0

                    s = "{:04x}00".format(addr_abs)
                    checksum = addr_l + addr_h

                s += "{:02x}{:02x}".format(opc_l, opc_h)
                checksum += opc_l + opc_h
                last_addr = addr

                word_count += 1
                if word_count == words_per_line:
                    last_addr -= 2              # Forzar salto de bloque

                addr += 2

        if word_count != 0:
            checksum += word_count
            intel += ":{:02x}".format(word_count * 2) + \
                     s + \
                     "{:02x}\n".format(256 - checksum & 0xff)

        intel += ":02fffe0000c240\n"
        intel += ":00000001FF\n"

        # print(intel)

        with open(fname, "w") as outf:
            outf.write(intel)

        return


    def load_word_at(self, addr):
        """ Load devuelve el contenido de la memory en la direccion <addr>.
            Controla si <addr> se encuentra en el rango correcto.
        """

        if addr == None:
            return

        if addr < self.mem_start or addr >= (self.mem_start + self.mem_size):
            print("Direccion fuera de rango (%d, 0x%x)" % (addr, addr))
            return

        if (addr % 2) == 1:
            print("Dirección para acceso por palabra debe ser par (%d)" % (addr, ))
            return
        
        w = self.load_mem_word_at(addr - self.mem_start)
        return w


    def store_word_at(self, addr, value):
        """ Store almacena <value> en la memoria en la direccion <addr>
            Controla si <addr> se encuentra en el rango correcto.
        """
        if addr < self.mem_start or addr >= (self.mem_start + self.mem_size):
            print("Direccion fuera de rango")
            return

        if (addr % 2) == 1:
            print("Dirección para acceso por palabra debe ser par (%d)" % (addr, ))
            return

        self.store_mem_word_at(addr - self.mem_start, value)
        return


    def store_words_at(self, addr, words):
        """ Almacena multiple words en la memoria:
               addr     Direccion inicial
               words    Secuencia de words a cargar en la memoria
        """
        for i, word in enumerate(words):
            self.store_word_at(addr + i*2, word)


    def load_byte_at(self, addr):
        """ Load devuelve el contenido de la memory en la direccion <addr>.
            Controla si <addr> se encuentra en el rango correcto.
            Note that if addr_res is less than word size,
        """
        if (addr < self.mem_start or
            addr >= (self.mem_start + self.mem_size)):
            print("Dirección fuera de rango (%d, 0x%x)" % (addr, addr))
            return

        b = self.mem[addr - self.mem_start]
        return b


    def store_byte_at(self, addr, value):
        """ Store almacena <value> en la memoria en la direccion <addr>
            Controla si <addr> se encuentra en el rango correcto.
        """
        if (addr < self.mem_start or
            addr >= (self.mem_start+self.mem_size)):
            print("Direccion fuera de rango")
            return

        self.mem[addr - self.mem_start] = value
        return



def main():
    #~ M = Memory(1024, mem_start = 0xfc00)

    # Test word access
    #~ M.store_word_at(0xfd00, 0x1234)
    #~ M.store_word_at(0xfd02, 0x2345)
    #~ M.store_word_at(0xfe00, 0xcafe)
    #~ print(str(M))

    # Test byte access
    #~ M.store_byte_at(0xfd00, 0x12)
    #~ M.store_byte_at(0xfd01, 0x34)
    #~ M.store_byte_at(0xfd02, 0xfe)
    #~ M.store_byte_at(0xfd03, 0xca)
    #~ print(str(M))

    # Test file read
    if True:
        M = Memory(15872, mem_start = 0xc200)
        M.load_from_intel("utiles/ins_bic.hex")
        print(M.dump(0xc200))

    if False:
        M = Memory(1024, mem_start = 0xfc00)
        M.store_words_at(0xfd00, [
                    0x3c55, 0x3e55,
                    0x1005, 0x1015, 0x0019, 0x1026, 0x1037,
                    0x1088, 0x1098, 0x001a, 0x10a9, 0x10b9,
                    0x1105, 0x1196, 0x001b, 0x122b, 0x12bc,
                    0x1300])

        print(M.dump(0xfce0, 96))
        M.store_to_intel("test.hex")

        print("Check 'check_intel_line'... Some good lines:")
        print(M.check_intel_line(":08c24000a4110412441214121900541219002412e1"))
        print(M.check_intel_line(":08fd100098101a00a910b910051196111b002b1292"))
        print(M.check_intel_line(":00000001FF"))
        print("... and some bad lines:")
        print(M.check_intel_line(":08c24000a4110412441214121900541319002412e1"))    # Incorrect value
        print(M.check_intel_line(":08fd1000912"))                                   # Nibble missing
        print(M.check_intel_line(":08fd1000"))                                      # Too short
        print(M.check_intel_line(":08fd100098z01a00a910b910051196111b002b1292"))    # Invalid hex char

    return 0

if __name__ == '__main__':
    main()
