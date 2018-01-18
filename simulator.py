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

class Simulator():
    JNZ, JZ, JNC, JC, JGE, JN, JL, JMP = range(8)
    MOV, ADD, ADDC, SUBC, SUB, CMP, DADD, BIT, BIC, BIS, XOR, AND = range(12)
    RRC, SWPB, RRA, SXT, PUSH, CALL, RETI, NOP = range(8)

    def __init__(self, mem, regs):
        self.mem = mem
        self.regs = regs

    def one_step(self, addr):
        """ Ejecuta la instruccion ubicada en la memoria ROM en la
            direccion <addr>.
            Retorna el PC nuevo
        """
        self.addr = addr
        self.registers = self.regs.get_registers()

        opcode = self.mem.load_word_at(self.addr)
        
        if opcode == None:
            return 
        
        if self.addr >= 0xffc0:          # Estamos en la table de interrupciones?
            return opcode

        for mask, value, optype, opd in (
                    (0xff80, 0x1000, self.RRC,     self.opd_single_type1),
                    (0xff80, 0x1080, self.SWPB,    self.opd_single_type2),
                    (0xff80, 0x1100, self.RRA,     self.opd_single_type1),
                    (0xff80, 0x1180, self.SXT,     self.opd_single_type2),
                    (0xff80, 0x1200, self.PUSH,    self.opd_single_type1),
                    (0xff80, 0x1280, self.CALL,    self.opd_single_type2),
                    (0xffff, 0x1300, self.RETI,    self.opd_single_reti),

                    (0xfc00, 0x2000, self.JNZ,     self.opd_jump),
                    (0xfc00, 0x2400, self.JZ,      self.opd_jump),
                    (0xfc00, 0x2800, self.JNC,     self.opd_jump),
                    (0xfc00, 0x2c00, self.JC,      self.opd_jump),
                    (0xfc00, 0x3000, self.JN,      self.opd_jump),
                    (0xfc00, 0x3400, self.JGE,     self.opd_jump),
                    (0xfc00, 0x3800, self.JL,      self.opd_jump),
                    (0xfc00, 0x3c00, self.JMP,     self.opd_jump),

                    (0xf000, 0x4000, self.MOV,     self.opd_double),
                    (0xf000, 0x5000, self.ADD,     self.opd_double),
                    (0xf000, 0x6000, self.ADDC,    self.opd_double),
                    (0xf000, 0x7000, self.SUBC,    self.opd_double),
                    (0xf000, 0x8000, self.SUB,     self.opd_double),
                    (0xf000, 0x9000, self.CMP,     self.opd_double),
                    (0xf000, 0xa000, self.DADD,    self.opd_double),
                    (0xf000, 0xb000, self.BIT,     self.opd_double),
                    (0xf000, 0xc000, self.BIC,     self.opd_double),
                    (0xf000, 0xd000, self.BIS,     self.opd_double),
                    (0xf000, 0xe000, self.XOR,     self.opd_double),
                    (0xf000, 0xf000, self.AND,     self.opd_double),

                    (0x0000, 0x0000, self.NOP,     self.opd_single_reti)):

            if (opcode & mask) == value:
                self.addr += 2
                newpc = opd(self.addr, opcode, optype)
                return newpc

    def opc_register(self, opc):    return opc & 0x000f
    def opc_As(self, opc):          return (opc >> 4) & 0x0003
    def opc_Byte(self, opc):        return (opc & 0x0040) != 0
    def opc_destination(self, opc): return opc & 0x000f
    def opc_Ad(self, opc):          return (opc >> 7) & 0x0001
    def opc_source(self, opc):      return (opc >> 8) & 0x000f
    def opc_suffix(self, opc):      return '.b' if self.opc_Byte(opc) else ''

    #función que resuelve las excepciones MemoryException
    #situaciones como "la dirección debe ser par" y "en X lugar de memoria no hay nada"
    #devuelve el contenido de la dirección "suma" que mando como parámetro
    def a(self, suma):

        if (suma % 2) == 1:
            try:
                suma1 = suma + 0x0001
                self.mem.store_word_at(suma1, 0xcccf)
            except MemoryException as ex:
                print(str(ex))
            finally:
                return self.mem.load_word_at(suma1)

        else:
            try:
                self.mem.store_word_at(suma, 0xcccf)
            except MemoryException as ex:
                print(str(ex))
            finally:
                return self.mem.load_word_at(suma)



    #
    #   Instrucciones de simple operando
    #

    def opd_single_type1(self, addr, opcode, opcstr):
        """ Desensamblar instruccion RRC, RRA, PUSH """
        As = self.opc_As(opcode)
        Rs = self.opc_source(opcode)

        # Abreviamos el numero de registro
        regnr = self.opc_register(opcode)

        # Acordarse del estado del CY en ST
        cy = self.regs.get_SR('C')

        if As == 0:                                             # modo por registro

            if opcstr == 0: # Instruccion RRC.w o RRC.b

                # Hacer la operación de desplazamiento
                self.regs.set(regnr, self.regs.get(regnr) >> 1)

                # Mover el bit 0 del registro al CY
                self.regs.set_SR(self.regs.get(regnr, 0), 'C')

                # Acordarse del estado del CY en ST
                cy = self.regs.get_SR('C')

                # y setear el bit mas significativo con la memoria
                if self.opc_Byte(opcode):
                    self.regs.set(regnr, cy, 7)
                    self.regs.clear_upper(regnr)                    # Cada operacion de byte
                                                                        # borra bits 8-15
                else:
                    self.regs.set(regnr, cy, 15)

                # Ajustar los otros bits del status
                self.regs.set_SR('V', False)                        # Siempre a 0
                self.regs.set_SR('Z', self.regs.get(regnr) == 0)    # Según valor registro
                self.regs.set_SR('N', cy)                           # Mismo estado que Carry

            elif opcstr == 2: # Instruccion RRA.w o RRA.b

                # Mover el bit 0 del registro al CY
                self.regs.set_SR(self.regs.get(regnr, 0), 'C')

                # Acordarse del estado del CY en ST
                cy = self.regs.get_SR('C')

                if self.opc_Byte(opcode):
                    self.regs.clear_upper(regnr)                    # Cada operacion de byte
                                                                        # borra bits 8-15

                self.regs.set(regnr, self.regs.get(regnr) // 2)

                # Ajustar los otros bits del status
                self.regs.set_SR('V', False)                        # Siempre a 0
                self.regs.set_SR('Z', self.regs.get(regnr) == 0)    # Según valor registro
                self.regs.set_SR('N', cy)                           # Mismo estado que Carry

            elif opcstr == 4: # Instruccion PUSH.w o PUSH.b
                sp = self.regs.get(1) - 0x0002
                self.regs.set(1, sp)

                if self.opc_Byte(opcode):
                    self.regs.clear_upper(regnr)                    # Cada operacion de byte
                                                                    # borra bits 8-15

                self.mem.store_word_at(sp, self.regs.get(regnr))

            # if self.mem.load_byte_at(addr) != None:
            return addr

        elif As== 1:                                            # modo indexado
        #debo buscar lo que hay en la dirección + x lugares, que diga regnr, en memoria, y luego setearlo en regnr
            if opcstr == 0: # Instruccion RRC.w o RRC.b

                cy = None

                if self.opc_Byte(opcode): #si es byte
                    sumacontenidomemoria = self.mem.mem_start + self.regs.get(regnr) + self.mem.load_word_at(addr)

                    if (sumacontenidomemoria > 0xfffe):
                        sumacontenidomemoria = self.regs.get(regnr) + self.mem.load_word_at(addr)

                    contenido_memoria = self.a(sumacontenidomemoria)
                    self.regs.set(regnr, contenido_memoria)

                    #~ # Mover el bit 0 del registro al CY
                    self.regs.set_SR(self.regs.get(regnr, 0), 'C')

                    # Hacer la operación de desplazamiento
                    self.regs.set(regnr, self.regs.get(regnr) >> 1)

                    cy = self.regs.get_SR('C')

                    self.regs.clear_upper(regnr)                    # Cada operacion de byte, borra bits 8-15

                    # print("self.regs.get(regnr) >> 1: %d"%(self.regs.get(regnr) >> 1))

                    self.regs.set(regnr, cy, 7)

                else: #si es word
                    sumacontenidomemoria = self.mem.mem_start + self.regs.get(regnr) + self.mem.load_word_at(addr)

                    if sumacontenidomemoria > 0xfffe:
                        sumacontenidomemoria = self.regs.get(regnr) + self.mem.load_word_at(addr)

                    contenido_memoria = self.a(sumacontenidomemoria)
                    
                    # print("{:04x}".format(contenido_memoria));
                    self.regs.set(regnr, contenido_memoria)

                    #~ # Mover el bit 0 del registro al CY
                    self.regs.set_SR(self.regs.get(regnr, 0), 'C')
                    
                    # Hacer la operación de desplazamiento
                    self.regs.set(regnr, self.regs.get(regnr) >> 1)
                    
                    cy = self.regs.get_SR('C')
                    
                    self.regs.set(regnr, cy, 15)

                #Ajustar los otros bits del status
                self.regs.set_SR('V', False)                        # Siempre a 0
                self.regs.set_SR('Z', self.regs.get(regnr) == 0)    # Según valor registro
                self.regs.set_SR('N', cy)                           # Mismo estado que Carry

            elif opcstr == 2: # Instruccion RRA.w o RRA.b

                if self.opc_Byte(opcode):
                    sumacontenidomemoria = self.mem.mem_start + self.regs.get(regnr) + self.mem.load_word_at(addr)

                    if (sumacontenidomemoria > 0xfffe):
                        sumacontenidomemoria = self.regs.get(regnr) + self.mem.load_word_at(addr)

                    contenido_memoria = self.a(sumacontenidomemoria)
                    self.regs.set(regnr, contenido_memoria)

                    self.regs.clear_upper(regnr)                    # Cada operacion de byte, borra bits 8-15

                else: #si es word
                    sumacontenidomemoria = self.mem.mem_start + self.regs.get(regnr) + self.mem.load_word_at(addr)

                    if sumacontenidomemoria > 0xfffe:
                        sumacontenidomemoria = self.regs.get(regnr) + self.mem.load_word_at(addr)

                    contenido_memoria=self.a(sumacontenidomemoria)
                    self.regs.set(regnr, contenido_memoria)

                # Mover el bit 0 del registro al CY
                self.regs.set_SR(self.regs.get(regnr, 0), 'C')

                cy = self.regs.get_SR('C')

                self.regs.set(regnr, self.regs.get(regnr) // 2)

                # Ajustar los otros bits del status
                self.regs.set_SR('V', False)                        # Siempre a 0
                self.regs.set_SR('Z', self.regs.get(regnr) == 0)    # Según valor registro
                self.regs.set_SR('N', cy)                           # Mismo estado que Carry

            elif opcstr == 4: # Instruccion PUSH.w o PUSH.b

                sumacontenidomemoria = self.mem.mem_start + self.regs.get(regnr) + self.mem.load_word_at(addr)

                if (sumacontenidomemoria > 0xfffe):
                    sumacontenidomemoria = self.regs.get(regnr) + self.mem.load_word_at(addr)

                contenido_memoria = self.a(sumacontenidomemoria)

                self.regs.set(regnr, contenido_memoria)

                sp = self.regs.get(1) - 0x0002
                self.regs.set(1, sp)

                if self.opc_Byte(opcode):
                    self.regs.clear_upper(regnr)                    # Cada operacion de byte
                                                                        # borra bits 8-15
                    self.mem.store_byte_at(sp, self.regs.get(regnr))
                else:
                    self.mem.store_word_at(sp, self.regs.get(regnr))

                print("SP: %x" % sp)
                print(self.mem.dump(0xdff0, 32))
            
            if self.mem.load_byte_at(addr+2) != None:
                return addr+2
    
        elif As == 2:                                            # modo indirecto por registro
            if opcstr == 0: # Instruccion RRC.w o RRC.b

                try:
                    contenido_memoria = self.mem.load_word_at(self.regs.get(regnr))

                    #print(self.mem.dump(self.regs.get(regnr), 32))

                    self.regs.set(regnr, self.mem.load_word_at(self.regs.get(regnr)))

                    #~ # Mover el bit 0 del registro al CY
                    self.regs.set_SR(self.regs.get(regnr, 0), 'C')

                    cy = self.regs.get_SR('C')

                    # Hacer la operación de desplazamiento
                    self.regs.set(regnr, self.regs.get(regnr) >> 1)

                    # y setear el bit mas significativo con la memoria
                    if self.opc_Byte(opcode):
                        self.regs.clear_upper(regnr)                    # Cada operacion de byte
                                                                            # borra bits 8-15
                        self.regs.set(regnr, cy, 7)
                    else:
                        self.regs.set(regnr, cy, 15)

                    # Ajustar los otros bits del status
                    self.regs.set_SR('V', False)                        # Siempre a 0
                    self.regs.set_SR('Z', self.regs.get(regnr) == 0)    # Según valor registro
                    self.regs.set_SR('N', cy)                           # Mismo estado que Carry

                except MemoryException as ex:
                    if str(ex) == "Lectura de memoria no inicializada":
                        self.mem.store_word_at(self.regs.get(regnr), 0xABCD)

                        #print(self.mem.dump(self.regs.get(regnr), 32))

                        self.regs.set(regnr, self.mem.load_word_at(self.regs.get(regnr)))

                        #~ # Mover el bit 0 del registro al CY
                        self.regs.set_SR(self.regs.get(regnr, 0), 'C')

                        cy = self.regs.get_SR('C')

                        # Hacer la operación de desplazamiento
                        self.regs.set(regnr, self.regs.get(regnr) >> 1)

                        # y setear el bit mas significativo con la memoria
                        if self.opc_Byte(opcode):
                            self.regs.clear_upper(regnr)                    # Cada operacion de byte
                                                                                # borra bits 8-15
                            self.regs.set(regnr, cy, 7)
                        else:
                            self.regs.set(regnr, cy, 15)

                        # Ajustar los otros bits del status
                        self.regs.set_SR('V', False)                        # Siempre a 0
                        self.regs.set_SR('Z', self.regs.get(regnr) == 0)    # Según valor registro
                        self.regs.set_SR('N', cy)                           # Mismo estado que Carry

                    else:
                        if "Direccion fuera de rango" in str(ex):
                            self.mem.store_word_at(self.mem.mem_start + self.regs.get(regnr), 0xABCD)

                            #print(self.mem.dump(self.mem.mem_start + self.regs.get(regnr), 32))

                            self.regs.set(regnr, self.mem.load_word_at(self.mem.mem_start + self.regs.get(regnr)))

                            # Mover el bit 0 del registro al CY
                            self.regs.set_SR(self.regs.get(regnr, 0), 'C')

                            cy = self.regs.get_SR('C')

                            # Hacer la operación de desplazamiento
                            self.regs.set(regnr, self.regs.get(regnr) >> 1)

                            # y setear el bit mas significativo con la memoria
                            if self.opc_Byte(opcode):
                                self.regs.clear_upper(regnr)                    # Cada operacion de byte
                                                                                    # borra bits 8-15
                                self.regs.set(regnr, cy, 7)
                            else:
                                self.regs.set(regnr, cy, 15)

                            # Ajustar los otros bits del status
                            self.regs.set_SR('V', False)                        # Siempre a 0
                            self.regs.set_SR('Z', self.regs.get(regnr) == 0)    # Según valor registro
                            self.regs.set_SR('N', cy)                           # Mismo estado que Carry

            elif opcstr == 2: # Instruccion RRA.w o RRA.b

                try:
                    contenido_memoria = self.mem.load_word_at(self.regs.get(regnr))

                    print(self.mem.dump(self.regs.get(regnr), 32))

                    self.regs.set(regnr, self.mem.load_word_at(self.regs.get(regnr)))

                    # Mover el bit 0 del registro al CY
                    self.regs.set_SR(self.regs.get(regnr, 0), 'C')

                    cy = self.regs.get_SR('C')

                    if self.opc_Byte(opcode):
                        self.regs.clear_upper(regnr)                    # Cada operacion de byte
                                                                            # borra bits 8-15

                    self.regs.set(regnr, self.regs.get(regnr) // 2)

                    # Ajustar los otros bits del status
                    self.regs.set_SR('V', False)                        # Siempre a 0
                    self.regs.set_SR('Z', self.regs.get(regnr) == 0)    # Según valor registro
                    self.regs.set_SR('N', cy)                           # Mismo estado que Carry

                except MemoryException as ex:
                    if str(ex) == "Lectura de memoria no inicializada":
                        self.mem.store_word_at(self.regs.get(regnr), 0xABCD)

                        print(self.mem.dump(self.regs.get(regnr), 32))

                        self.regs.set(regnr, self.mem.load_word_at(self.regs.get(regnr)))

                        # Mover el bit 0 del registro al CY
                        self.regs.set_SR(self.regs.get(regnr, 0), 'C')

                        cy = self.regs.get_SR('C')

                        if self.opc_Byte(opcode):
                            self.regs.clear_upper(regnr)                    # Cada operacion de byte
                                                                                # borra bits 8-15

                        self.regs.set(regnr, self.regs.get(regnr) // 2)

                        # Ajustar los otros bits del status
                        self.regs.set_SR('V', False)                        # Siempre a 0
                        self.regs.set_SR('Z', self.regs.get(regnr) == 0)    # Según valor registro
                        self.regs.set_SR('N', cy)                           # Mismo estado que Carry

                    else:
                        if "Direccion fuera de rango" in str(ex):
                            self.mem.store_word_at(self.mem.mem_start + self.regs.get(regnr), 0xABCD)

                            print(self.mem.dump(self.mem.mem_start + self.regs.get(regnr), 32))

                            self.regs.set(regnr, self.mem.load_word_at(self.mem.mem_start + self.regs.get(regnr)))

                            # Mover el bit 0 del registro al CY
                            self.regs.set_SR(self.regs.get(regnr, 0), 'C')

                            cy = self.regs.get_SR('C')

                            if self.opc_Byte(opcode):
                                self.regs.clear_upper(regnr)                    # Cada operacion de byte
                                                                                    # borra bits 8-15

                            self.regs.set(regnr, self.regs.get(regnr) // 2)

                            # Ajustar los otros bits del status
                            self.regs.set_SR('V', False)                        # Siempre a 0
                            self.regs.set_SR('Z', self.regs.get(regnr) == 0)    # Según valor registro
                            self.regs.set_SR('N', cy)                           # Mismo estado que Carry

            elif opcstr == 4: # Instruccion PUSH.w o PUSH.b

                try:
                    contenido_memoria = self.mem.load_word_at(self.regs.get(regnr))

                    print(self.mem.dump(self.regs.get(regnr), 32))

                    self.regs.set(regnr, self.mem.load_word_at(self.regs.get(regnr)))

                    sp = self.regs.get(1) - 0x0002
                    self.regs.set(1, sp)

                    if self.opc_Byte(opcode):
                        self.regs.clear_upper(regnr)                    # Cada operacion de byte
                                                                            # borra bits 8-15

                    #AGREGUE ESTO
                    self.mem.store_word_at(sp, self.regs.get(regnr))

                    print("SP: %x" % sp)
                    print(self.mem.dump(0xdff0, 32))

                except MemoryException as ex:
                    if str(ex) == "Lectura de memoria no inicializada":
                        self.mem.store_word_at(self.regs.get(regnr), 0xABCD)

                        print(self.mem.dump(self.regs.get(regnr), 32))

                        self.regs.set(regnr, self.mem.load_word_at(self.regs.get(regnr)))

                        sp = self.regs.get(1) - 0x0002
                        self.regs.set(1, sp)

                        if self.opc_Byte(opcode):
                            self.regs.clear_upper(regnr)                    # Cada operacion de byte
                                                                                # borra bits 8-15

                        #AGREGUE ESTO
                        self.mem.store_word_at(sp, self.regs.get(regnr))

                        print("SP: %x" % sp)
                        print(self.mem.dump(0xdff0, 32))

                    else:
                        if "Direccion fuera de rango" in str(ex):
                            self.mem.store_word_at(self.mem.mem_start + self.regs.get(regnr), 0xABCD)

                            print(self.mem.dump(self.mem.mem_start + self.regs.get(regnr), 32))

                            self.regs.set(regnr, self.mem.load_word_at(self.mem.mem_start + self.regs.get(regnr)))

                            sp = self.regs.get(1) - 0x0002
                            self.regs.set(1, sp)

                            if self.opc_Byte(opcode):
                                self.regs.clear_upper(regnr)                    # Cada operacion de byte
                                                                                    # borra bits 8-15

                            #AGREGUE ESTO
                            self.mem.store_word_at(sp, self.regs.get(regnr))

                            print("SP: %x" % sp)
                            print(self.mem.dump(0xdff0, 32))

            if self.mem.load_byte_at(addr) != None:
                return addr

        elif As== 3:                                            # modo indirecto autoincrementado

            if opcstr == 0: # Instruccion RRC.w o RRC.b

                try:
                    contenido_memoria = self.mem.load_word_at(self.regs.get(regnr))

                    #print(self.mem.dump(self.regs.get(regnr), 32))

                    self.regs.set(regnr, self.mem.load_word_at(self.regs.get(regnr)))

                    #~ # Mover el bit 0 del registro al CY
                    self.regs.set_SR(self.regs.get(regnr, 0), 'C')

                    cy = self.regs.get_SR('C')

                    # Hacer la operación de desplazamiento
                    self.regs.set(regnr, self.regs.get(regnr) >> 1)

                    # y setear el bit mas significativo con la memoria
                    if self.opc_Byte(opcode):
                        self.regs.clear_upper(regnr)                    # Cada operacion de byte
                                                                            # borra bits 8-15
                        self.regs.set(regnr, cy, 7)
                    else:
                        self.regs.set(regnr, cy, 15)

                    # Ajustar los otros bits del status
                    self.regs.set_SR('V', False)                        # Siempre a 0
                    self.regs.set_SR('Z', self.regs.get(regnr) == 0)    # Según valor registro
                    self.regs.set_SR('N', cy)                           # Mismo estado que Carry

                except MemoryException as ex:
                    if str(ex) == "Lectura de memoria no inicializada":
                        self.mem.store_word_at(self.regs.get(regnr), 0xABCD)

                        print(self.mem.dump(self.regs.get(regnr), 32))

                        self.regs.set(regnr, self.mem.load_word_at(self.regs.get(regnr)))

                        #~ # Mover el bit 0 del registro al CY
                        self.regs.set_SR(self.regs.get(regnr, 0), 'C')

                        cy = self.regs.get_SR('C')

                        # Hacer la operación de desplazamiento
                        self.regs.set(regnr, self.regs.get(regnr) >> 1)

                        # y setear el bit mas significativo con la memoria
                        if self.opc_Byte(opcode):
                            self.regs.clear_upper(regnr)                    # Cada operacion de byte
                                                                                # borra bits 8-15
                            self.regs.set(regnr, cy, 7)
                        else:
                            self.regs.set(regnr, cy, 15)

                        # Ajustar los otros bits del status
                        self.regs.set_SR('V', False)                        # Siempre a 0
                        self.regs.set_SR('Z', self.regs.get(regnr) == 0)    # Según valor registro
                        self.regs.set_SR('N', cy)                           # Mismo estado que Carry

                    else:
                        if "Direccion fuera de rango" in str(ex):
                            self.mem.store_word_at(self.mem.mem_start + self.regs.get(regnr), 0xABCD)

                            print(self.mem.dump(self.mem.mem_start + self.regs.get(regnr), 32))

                            self.regs.set(regnr, self.mem.load_word_at(self.mem.mem_start + self.regs.get(regnr)))

                            # Mover el bit 0 del registro al CY
                            self.regs.set_SR(self.regs.get(regnr, 0), 'C')

                            cy = self.regs.get_SR('C')

                            # Hacer la operación de desplazamiento
                            self.regs.set(regnr, self.regs.get(regnr) >> 1)

                            # y setear el bit mas significativo con la memoria
                            if self.opc_Byte(opcode):
                                self.regs.clear_upper(regnr)                    # Cada operacion de byte
                                                                                    # borra bits 8-15
                                self.regs.set(regnr, cy, 7)
                            else:
                                self.regs.set(regnr, cy, 15)

                            # Ajustar los otros bits del status
                            self.regs.set_SR('V', False)                        # Siempre a 0
                            self.regs.set_SR('Z', self.regs.get(regnr) == 0)    # Según valor registro
                            self.regs.set_SR('N', cy)                           # Mismo estado que Carry

                finally:
                    if self.opc_Byte(opcode):
                        self.regs.set(regnr, self.regs.get(regnr) + 0x0001)
                    else:
                        self.regs.set(regnr, self.regs.get(regnr) + 0x0002)

            elif opcstr == 2: # Instruccion RRA.w o RRA.b

                try:
                    contenido_memoria = self.mem.load_word_at(self.regs.get(regnr))

                    print(self.mem.dump(self.regs.get(regnr), 32))

                    self.regs.set(regnr, self.mem.load_word_at(self.regs.get(regnr)))

                    # Mover el bit 0 del registro al CY
                    self.regs.set_SR(self.regs.get(regnr, 0), 'C')

                    cy = self.regs.get_SR('C')

                    if self.opc_Byte(opcode):
                        self.regs.clear_upper(regnr)                    # Cada operacion de byte
                                                                            # borra bits 8-15

                    self.regs.set(regnr, self.regs.get(regnr) // 2)

                    # Ajustar los otros bits del status
                    self.regs.set_SR('V', False)                        # Siempre a 0
                    self.regs.set_SR('Z', self.regs.get(regnr) == 0)    # Según valor registro
                    self.regs.set_SR('N', cy)                           # Mismo estado que Carry

                except MemoryException as ex:
                    if str(ex) == "Lectura de memoria no inicializada":
                        self.mem.store_word_at(self.regs.get(regnr), 0xABCD)

                        print(self.mem.dump(self.regs.get(regnr), 32))

                        self.regs.set(regnr, self.mem.load_word_at(self.regs.get(regnr)))

                        # Mover el bit 0 del registro al CY
                        self.regs.set_SR(self.regs.get(regnr, 0), 'C')

                        cy = self.regs.get_SR('C')

                        if self.opc_Byte(opcode):
                            self.regs.clear_upper(regnr)                    # Cada operacion de byte
                                                                                # borra bits 8-15

                        self.regs.set(regnr, self.regs.get(regnr) // 2)

                        # Ajustar los otros bits del status
                        self.regs.set_SR('V', False)                        # Siempre a 0
                        self.regs.set_SR('Z', self.regs.get(regnr) == 0)    # Según valor registro
                        self.regs.set_SR('N', cy)                           # Mismo estado que Carry

                    else:
                        if "Direccion fuera de rango" in str(ex):
                            self.mem.store_word_at(self.mem.mem_start + self.regs.get(regnr), 0xABCD)

                            print(self.mem.dump(self.mem.mem_start + self.regs.get(regnr), 32))

                            self.regs.set(regnr, self.mem.load_word_at(self.mem.mem_start + self.regs.get(regnr)))

                            # Mover el bit 0 del registro al CY
                            self.regs.set_SR(self.regs.get(regnr, 0), 'C')

                            cy = self.regs.get_SR('C')

                            if self.opc_Byte(opcode):
                                self.regs.clear_upper(regnr)                    # Cada operacion de byte
                                                                                    # borra bits 8-15

                            self.regs.set(regnr, self.regs.get(regnr) // 2)

                            # Ajustar los otros bits del status
                            self.regs.set_SR('V', False)                        # Siempre a 0
                            self.regs.set_SR('Z', self.regs.get(regnr) == 0)    # Según valor registro
                            self.regs.set_SR('N', cy)                           # Mismo estado que Carry

                finally:
                    if self.opc_Byte(opcode):
                        self.regs.set(regnr, self.regs.get(regnr) + 0x0001)
                    else:
                        self.regs.set(regnr, self.regs.get(regnr) + 0x0002)

            elif opcstr == 4: # Instruccion PUSH.w o PUSH.b

                try:
                    contenido_memoria = self.mem.load_word_at(self.regs.get(regnr))

                    print(self.mem.dump(self.regs.get(regnr), 32))

                    self.regs.set(regnr, self.mem.load_word_at(self.regs.get(regnr)))

                    sp = self.regs.get(1) - 0x0002
                    self.regs.set(1, sp)

                    if self.opc_Byte(opcode):
                        self.regs.clear_upper(regnr)                    # Cada operacion de byte
                                                                            # borra bits 8-15

                    #AGREGUE ESTO
                    self.mem.store_word_at(sp, self.regs.get(regnr))

                    print("SP: %x" % sp)
                    print(self.mem.dump(0xdff0, 32))

                except MemoryException as ex:
                    if str(ex) == "Lectura de memoria no inicializada":
                        self.mem.store_word_at(self.regs.get(regnr), 0xABCD)

                        print(self.mem.dump(self.regs.get(regnr), 32))

                        self.regs.set(regnr, self.mem.load_word_at(self.regs.get(regnr)))

                        sp = self.regs.get(1) - 0x0002
                        self.regs.set(1, sp)

                        if self.opc_Byte(opcode):
                            self.regs.clear_upper(regnr)                    # Cada operacion de byte
                                                                                # borra bits 8-15

                        #AGREGUE ESTO
                        self.mem.store_word_at(sp, self.regs.get(regnr))

                        print("SP: %x" % sp)
                        print(self.mem.dump(0xdff0, 32))

                    else:
                        if "Direccion fuera de rango" in str(ex):
                            self.mem.store_word_at(self.mem.mem_start + self.regs.get(regnr), 0xABCD)

                            print(self.mem.dump(self.mem.mem_start + self.regs.get(regnr), 32))

                            self.regs.set(regnr, self.mem.load_word_at(self.mem.mem_start + self.regs.get(regnr)))

                            sp = self.regs.get(1) - 0x0002
                            self.regs.set(1, sp)

                            if self.opc_Byte(opcode):
                                self.regs.clear_upper(regnr)                    # Cada operacion de byte
                                                                                    # borra bits 8-15

                            #AGREGUE ESTO
                            self.mem.store_word_at(sp, self.regs.get(regnr))

                            print("SP: %x" % sp)
                            print(self.mem.dump(0xdff0, 32))

                finally:
                    if self.opc_Byte(opcode):
                        self.regs.set(regnr, self.regs.get(regnr) + 0x0001)
                    else:
                        self.regs.set(regnr, self.regs.get(regnr) + 0x0002)

            if self.mem.load_byte_at(addr) != None:
                return addr



    def opd_single_type2(self, addr, opcode, opcstr):
        """ Desensamblar instruccion SWPB, SXT, CALL """
        As = self.opc_As(opcode)

        # Abreviamos el numero de registro
        regnr = self.opc_register(opcode)

        # Acordarse del estado del CY en ST
        cy = self.regs.get_SR('C')

        if As == 0:                                             # modo por registro

            if opcstr == 1:     # INSTRUCCION SWPB
                lb = self.regs.get(regnr) & 0x00ff
                hb = self.regs.get(regnr) >> 8
                updated_reg = "0x{:02x}{:02x}".format(lb, hb) # nuevo valor del regnr, con los bytes intercambiados
                self.regs.set(regnr, int(updated_reg, 16) & 0xffff)

            elif opcstr == 3:   # INSTRUCCION SXT
                sb_lb = self.regs.get(regnr) & 0x0080 # extraigo el sign bit del low byte

                for pos in range(8,20,1):
                    self.regs.set(regnr, sb_lb, pos) # Seteo cada posicion desde bit 8.. 19 con el bit que estaba en sb_lb

                # Ajustar los otros bits del status
                self.regs.set_SR('Z', self.regs.get(regnr) == 0)    # Según valor registro
                self.regs.set_SR('C', self.regs.get(regnr) != 0)
                self.regs.set_SR('V', False)                        # Siempre a 0

                # Acordarse del estado del CY en ST
                cy = self.regs.get_SR('C')

                self.regs.set_SR('N', cy)                           # Mismo estado que Carry

            elif opcstr == 5:   # INSTRUCCION CALL
                tmp = self.regs.get(regnr) # guardo en tmp el contenido de regnr

                sp = self.regs.get(1) - 0x0002 # Decremento el registro SP en 2
                self.regs.set(1, sp) # Seteo el nuevo valor de SP

                self.mem.store_word_at(sp, self.regs.get(0) + 0x0002) # Seteo en la direccion que apunta el registro SP el valor de PC + 2
                print(self.mem.dump(0xdff0, 32))

                self.regs.set(0, tmp) # Seteo el PC con el valor de tmp, obtenido anteriormente

                return self.regs.get(0)

            return addr
        elif As == 1:                                           # modo indexado
            #pdb.set_trace()
            if opcstr == 1: # INSTRUCCION SWPB

                try:
                    contenido_memoria = self.a(self.regs.get(regnr) + self.mem.load_word_at(addr))
                    #print(self.mem.dump(self.regs.get(regnr) + 0x0019, 32))
                    self.regs.set(regnr, contenido_memoria)

                    lb = self.regs.get(regnr) & 0x00ff
                    hb = self.regs.get(regnr) >> 8
                    updated_reg = "0x{:02x}{:02x}".format(lb, hb) # nuevo valor del regnr, con los bytes intercambiados
                    self.regs.set(regnr, int(updated_reg, 16) & 0xffff)

                except MemoryException as ex:
                    if str(ex) == "Lectura de memoria no inicializada":
                        self.mem.store_word_at(self.a(self.regs.get(regnr) + self.mem.load_word_at(addr)), 0xABCD)
                        #print(self.mem.dump(self.a(self.regs.get(regnr) + 0x0019), 32))
                        self.regs.set(regnr, self.mem.load_word_at(self.a(self.regs.get(regnr) + self.mem.load_word_at(addr))))

                        lb = self.regs.get(regnr) & 0x00ff
                        hb = self.regs.get(regnr) >> 8
                        updated_reg = "0x{:02x}{:02x}".format(lb, hb) # nuevo valor del regnr, con los bytes intercambiados
                        self.regs.set(regnr, int(updated_reg, 16) & 0xffff)
                    else:
                        if "Direccion fuera de rango" in str(ex):
                            self.mem.store_word_at(self.a(self.mem.mem_start + self.regs.get(regnr) + self.mem.load_word_at(addr)), 0xABCD)

                            #print(self.mem.dump(self.a(self.mem.mem_start + self.regs.get(regnr) + 0x0019), 32))

                            self.regs.set(regnr, self.mem.load_word_at(self.a(self.mem.mem_start + self.regs.get(regnr) + self.mem.load_word_at(addr))))

                            lb = self.regs.get(regnr) & 0x00ff
                            hb = self.regs.get(regnr) >> 8
                            updated_reg = "0x{:02x}{:02x}".format(lb, hb) # nuevo valor del regnr, con los bytes intercambiados
                            self.regs.set(regnr, int(updated_reg, 16) & 0xffff)

            elif opcstr == 3: # INSTRUCCION SXT

                try:
                    contenido_memoria = self.a(self.regs.get(regnr) + self.mem.load_word_at(addr))

                    #print(self.mem.dump(self.a(self.regs.get(regnr)+0x0019), 32))

                    self.regs.set(regnr, contenido_memoria)

                    sb_lb = contenido_memoria & 0x0080 # extraigo el sign bit del low byte

                    for pos in range(8,16,1):
                        self.regs.set(regnr, sb_lb, pos) # Seteo cada posicion desde bit 8.. 15 con el bit que estaba en sb_lb

                    # Ajustar los otros bits del status
                    self.regs.set_SR('Z', self.regs.get(regnr) == 0)    # Según valor registro
                    self.regs.set_SR('C', self.regs.get(regnr) != 0)
                    self.regs.set_SR('V', False)                        # Siempre a 0

                    # Acordarse del estado del CY en ST
                    cy = self.regs.get_SR('C')

                    self.regs.set_SR('N', cy)                           # Mismo estado que Carry

                except MemoryException as ex:
                    if str(ex) == "Lectura de memoria no inicializada":
                        contenido_memoria = self.a(self.regs.get(regnr)+0x0019)

                        self.mem.store_word_at(contenido_memoria, 0xABCD)

                        #print(self.mem.dump(contenido_memoria, 32))

                        self.regs.set(regnr, contenido_memoria)

                        sb_lb = contenido_memoria & 0x0080 # extraigo el sign bit del low byte

                        for pos in range(8,16,1):
                            self.regs.set(regnr, sb_lb, pos) # Seteo cada posicion desde bit 8.. 15 con el bit que estaba en sb_lb

                        # Ajustar los otros bits del status
                        self.regs.set_SR('Z', self.regs.get(regnr) == 0)    # Según valor registro
                        self.regs.set_SR('C', self.regs.get(regnr) != 0)
                        self.regs.set_SR('V', False)                        # Siempre a 0

                        # Acordarse del estado del CY en ST
                        cy = self.regs.get_SR('C')

                        self.regs.set_SR('N', cy)                           # Mismo estado que Carry

                    else:
                        if "Direccion fuera de rango" in str(ex):
                            contenido_memoria = self.a(self.mem.mem_start + self.regs.get(regnr) + 0x0019)

                            self.mem.store_word_at(contenido_memoria, 0xABCD)

                            #print(self.mem.dump(contenido_memoria, 32))

                            self.regs.set(regnr, self.mem.load_word_at(contenido_memoria))

                            sb_lb = contenido_memoria & 0x0080 # extraigo el sign bit del low byte

                            for pos in range(8,16,1):
                                self.regs.set(regnr, sb_lb, pos) # Seteo cada posicion desde bit 8.. 15 con el bit que estaba en sb_lb

                            # Ajustar los otros bits del status
                            self.regs.set_SR('Z', self.regs.get(regnr) == 0)    # Según valor registro
                            self.regs.set_SR('C', self.regs.get(regnr) != 0)
                            self.regs.set_SR('V', False)                        # Siempre a 0

                            # Acordarse del estado del CY en ST
                            cy = self.regs.get_SR('C')

                            self.regs.set_SR('N', cy)                           # Mismo estado que Carry
            
            elif opcstr == 5: # INSTRUCCION CALL

                try:
                    contenido_memoria = self.a(self.regs.get(regnr)+0x0019)

                    print(self.mem.dump(contenido_memoria, 32))

                    self.regs.set(regnr, self.mem.load_word_at(contenido_memoria))

                    tmp = contenido_memoria # guardo en tmp el contenido de regnr

                    sp = self.regs.get(1) - 0x0002 # Decremento el registro SP en 2
                    self.regs.set(1, sp) # Seteo el nuevo valor de SP

                    self.mem.store_word_at(sp, self.regs.get(0) + 0x0002) # Seteo en la direccion que apunta el registro SP el valor de PC + 2
                    print(self.mem.dump(0xdff0, 32))

                    self.regs.set(0, tmp) # Seteo el PC con el valor de tmp, obtenido anteriormente

                    return self.regs.get(0)

                except MemoryException as ex:
                    if str(ex) == "Lectura de memoria no inicializada":
                        self.mem.store_word_at(contenido_memoria, 0xABCD)

                        print(self.mem.dump(contenido_memoria, 32))

                        self.regs.set(regnr, self.mem.load_word_at(contenido_memoria))

                        tmp = contenido_memoria # guardo en tmp el contenido de regnr

                        sp = self.regs.get(1) - 0x0002 # Decremento el registro SP en 2
                        self.regs.set(1, sp) # Seteo el nuevo valor de SP

                        self.mem.store_word_at(sp, self.regs.get(0) + 0x0002) # Seteo en la direccion que apunta el registro SP el valor de PC + 2
                        print(self.mem.dump(0xdff0, 32))

                        self.regs.set(0, tmp) # Seteo el PC con el valor de tmp, obtenido anteriormente

                        return self.regs.get(0)

                    else:
                        if "Direccion fuera de rango" in str(ex):
                            contenido_memoria = self.mem.mem_start + self.regs.get(regnr) + 0x0019
                            self.mem.store_word_at(contenido_memoria, 0xABCD)

                            print(self.mem.dump(contenido_memoria, 32))

                            self.regs.set(regnr, self.mem.load_word_at(contenido_memoria))

                            tmp = contenido_memoria # guardo en tmp el contenido de regnr

                            sp = self.regs.get(1) - 0x0002 # Decremento el registro SP en 2
                            self.regs.set(1, sp) # Seteo el nuevo valor de SP

                            self.mem.store_word_at(sp, self.regs.get(0) + 0x0002) # Seteo en la direccion que apunta el registro SP el valor de PC + 2
                            print(self.mem.dump(0xdff0, 32))

                            self.regs.set(0, tmp) # Seteo el PC con el valor de tmp, obtenido anteriormente

                            return self.regs.get(0)

            return addr+2
        elif As == 2:                                           # modo indirecto por registro

            if opcstr == 1: # INSTRUCCION SWPB

                try:
                    contenido_memoria = self.mem.load_word_at(self.regs.get(regnr))

                    # print(self.mem.dump(self.regs.get(regnr), 32))

                    self.regs.set(regnr, self.mem.load_word_at(self.regs.get(regnr)))

                    lb = self.regs.get(regnr) & 0x00ff
                    hb = self.regs.get(regnr) >> 8
                    updated_reg = "0x{:02x}{:02x}".format(lb, hb) # nuevo valor del regnr, con los bytes intercambiados
                    self.regs.set(regnr, int(updated_reg, 16) & 0xffff)

                except MemoryException as ex:
                    if str(ex) == "Lectura de memoria no inicializada":
                        self.mem.store_word_at(self.regs.get(regnr), 0xABCD)

                        print(self.mem.dump(self.regs.get(regnr), 32))

                        self.regs.set(regnr, self.mem.load_word_at(self.regs.get(regnr)))

                        lb = self.regs.get(regnr) & 0x00ff
                        hb = self.regs.get(regnr) >> 8
                        updated_reg = "0x{:02x}{:02x}".format(lb, hb) # nuevo valor del regnr, con los bytes intercambiados
                        self.regs.set(regnr, int(updated_reg, 16) & 0xffff)
                    else:
                        if "Direccion fuera de rango" in str(ex):
                            self.mem.store_word_at(self.mem.mem_start + self.regs.get(regnr), 0xABCD)

                            print(self.mem.dump(self.mem.mem_start + self.regs.get(regnr), 32))

                            self.regs.set(regnr, self.mem.load_word_at(self.mem.mem_start + self.regs.get(regnr)))

                            lb = self.regs.get(regnr) & 0x00ff
                            hb = self.regs.get(regnr) >> 8
                            updated_reg = "0x{:02x}{:02x}".format(lb, hb) # nuevo valor del regnr, con los bytes intercambiados
                            self.regs.set(regnr, int(updated_reg, 16) & 0xffff)

            elif opcstr == 3: # INSTRUCCION SXT

                try:
                    contenido_memoria = self.mem.load_word_at(self.regs.get(regnr))

                    print(self.mem.dump(self.regs.get(regnr), 32))

                    self.regs.set(regnr, self.mem.load_word_at(self.regs.get(regnr)))

                    sb_lb = self.regs.get(regnr) & 0x0080 # extraigo el sign bit del low byte

                    for pos in range(8,16,1):
                        self.regs.set(regnr, sb_lb, pos) # Seteo cada posicion desde bit 8.. 15 con el bit que estaba en sb_lb

                    # Ajustar los otros bits del status
                    self.regs.set_SR('Z', self.regs.get(regnr) == 0)    # Según valor registro
                    self.regs.set_SR('C', self.regs.get(regnr) != 0)
                    self.regs.set_SR('V', False)                        # Siempre a 0

                    # Acordarse del estado del CY en ST
                    cy = self.regs.get_SR('C')

                    self.regs.set_SR('N', cy)                           # Mismo estado que Carry

                except MemoryException as ex:
                    if str(ex) == "Lectura de memoria no inicializada":
                        self.mem.store_word_at(self.regs.get(regnr), 0xABCD)

                        print(self.mem.dump(self.regs.get(regnr), 32))

                        self.regs.set(regnr, self.mem.load_word_at(self.regs.get(regnr)))

                        sb_lb = self.regs.get(regnr) & 0x0080 # extraigo el sign bit del low byte

                        for pos in range(8,16,1):
                            self.regs.set(regnr, sb_lb, pos) # Seteo cada posicion desde bit 8.. 15 con el bit que estaba en sb_lb

                        # Ajustar los otros bits del status
                        self.regs.set_SR('Z', self.regs.get(regnr) == 0)    # Según valor registro
                        self.regs.set_SR('C', self.regs.get(regnr) != 0)
                        self.regs.set_SR('V', False)                        # Siempre a 0

                        # Acordarse del estado del CY en ST
                        cy = self.regs.get_SR('C')

                        self.regs.set_SR('N', cy)                           # Mismo estado que Carry

                    else:
                        if "Direccion fuera de rango" in str(ex):
                            self.mem.store_word_at(self.mem.mem_start + self.regs.get(regnr), 0xABCD)

                            print(self.mem.dump(self.mem.mem_start + self.regs.get(regnr), 32))

                            self.regs.set(regnr, self.mem.load_word_at(self.mem.mem_start + self.regs.get(regnr)))

                            sb_lb = self.regs.get(regnr) & 0x0080 # extraigo el sign bit del low byte

                            for pos in range(8,16,1):
                                self.regs.set(regnr, sb_lb, pos) # Seteo cada posicion desde bit 8.. 15 con el bit que estaba en sb_lb

                            # Ajustar los otros bits del status
                            self.regs.set_SR('Z', self.regs.get(regnr) == 0)    # Según valor registro
                            self.regs.set_SR('C', self.regs.get(regnr) != 0)
                            self.regs.set_SR('V', False)                        # Siempre a 0

                            # Acordarse del estado del CY en ST
                            cy = self.regs.get_SR('C')

                            self.regs.set_SR('N', cy)                           # Mismo estado que Carry

            elif opcstr == 5: # INSTRUCCION CALL

                try:
                    contenido_memoria = self.mem.load_word_at(self.regs.get(regnr))

                    print(self.mem.dump(self.regs.get(regnr), 32))

                    self.regs.set(regnr, self.mem.load_word_at(self.regs.get(regnr)))

                    tmp = self.regs.get(regnr) # guardo en tmp el contenido de regnr

                    sp = self.regs.get(1) - 0x0002 # Decremento el registro SP en 2
                    self.regs.set(1, sp) # Seteo el nuevo valor de SP

                    self.mem.store_word_at(sp, self.regs.get(0) + 0x0002) # Seteo en la direccion que apunta el registro SP el valor de PC + 2
                    print(self.mem.dump(0xdff0, 32))

                    self.regs.set(0, tmp) # Seteo el PC con el valor de tmp, obtenido anteriormente

                    return self.regs.get(0)

                except MemoryException as ex:
                    if str(ex) == "Lectura de memoria no inicializada":
                        self.mem.store_word_at(self.regs.get(regnr), 0xABCD)

                        print(self.mem.dump(self.regs.get(regnr), 32))

                        self.regs.set(regnr, self.mem.load_word_at(self.regs.get(regnr)))

                        tmp = self.regs.get(regnr) # guardo en tmp el contenido de regnr

                        sp = self.regs.get(1) - 0x0002 # Decremento el registro SP en 2
                        self.regs.set(1, sp) # Seteo el nuevo valor de SP

                        self.mem.store_word_at(sp, self.regs.get(0) + 0x0002) # Seteo en la direccion que apunta el registro SP el valor de PC + 2
                        print(self.mem.dump(0xdff0, 32))

                        self.regs.set(0, tmp) # Seteo el PC con el valor de tmp, obtenido anteriormente

                        return self.regs.get(0)

                    else:
                        if "Direccion fuera de rango" in str(ex):
                            self.mem.store_word_at(self.mem.mem_start + self.regs.get(regnr), 0xABCD)

                            print(self.mem.dump(self.mem.mem_start + self.regs.get(regnr), 32))

                            self.regs.set(regnr, self.mem.load_word_at(self.mem.mem_start + self.regs.get(regnr)))

                            tmp = self.regs.get(regnr) # guardo en tmp el contenido de regnr

                            sp = self.regs.get(1) - 0x0002 # Decremento el registro SP en 2
                            self.regs.set(1, sp) # Seteo el nuevo valor de SP

                            self.mem.store_word_at(sp, self.regs.get(0) + 0x0002) # Seteo en la direccion que apunta el registro SP el valor de PC + 2
                            print(self.mem.dump(0xdff0, 32))

                            self.regs.set(0, tmp) # Seteo el PC con el valor de tmp, obtenido anteriormente

                            return self.regs.get(0)

            return addr
        elif As == 3:                                           # modo indirecto autoincrementado

            if opcstr == 1: # INSTRUCCION SWPB

                try:
                    contenido_memoria = self.mem.load_word_at(self.regs.get(regnr))

                    # print(self.mem.dump(self.regs.get(regnr), 32))

                    self.regs.set(regnr, self.mem.load_word_at(self.regs.get(regnr)))

                    lb = self.regs.get(regnr) & 0x00ff
                    hb = self.regs.get(regnr) >> 8
                    updated_reg = "0x{:02x}{:02x}".format(lb, hb) # nuevo valor del regnr, con los bytes intercambiados
                    self.regs.set(regnr, int(updated_reg, 16) & 0xffff)

                except MemoryException as ex:
                    if str(ex) == "Lectura de memoria no inicializada":
                        self.mem.store_word_at(self.regs.get(regnr), 0xABCD)

                        print(self.mem.dump(self.regs.get(regnr), 32))

                        self.regs.set(regnr, self.mem.load_word_at(self.regs.get(regnr)))

                        lb = self.regs.get(regnr) & 0x00ff
                        hb = self.regs.get(regnr) >> 8
                        updated_reg = "0x{:02x}{:02x}".format(lb, hb) # nuevo valor del regnr, con los bytes intercambiados
                        self.regs.set(regnr, int(updated_reg, 16) & 0xffff)
                    else:
                        if "Direccion fuera de rango" in str(ex):
                            self.mem.store_word_at(self.mem.mem_start + self.regs.get(regnr), 0xABCD)

                            print(self.mem.dump(self.mem.mem_start + self.regs.get(regnr), 32))

                            self.regs.set(regnr, self.mem.load_word_at(self.mem.mem_start + self.regs.get(regnr)))

                            lb = self.regs.get(regnr) & 0x00ff
                            hb = self.regs.get(regnr) >> 8
                            updated_reg = "0x{:02x}{:02x}".format(lb, hb) # nuevo valor del regnr, con los bytes intercambiados
                            self.regs.set(regnr, int(updated_reg, 16) & 0xffff)

                finally:
                    if self.opc_Byte(opcode):
                        self.regs.set(regnr, self.regs.get(regnr) + 0x0001)
                    else:
                        self.regs.set(regnr, self.regs.get(regnr) + 0x0002)

            elif opcstr == 3: # INSTRUCCION SXT

                try:
                    contenido_memoria = self.mem.load_word_at(self.regs.get(regnr))

                    print(self.mem.dump(self.regs.get(regnr), 32))

                    self.regs.set(regnr, self.mem.load_word_at(self.regs.get(regnr)))

                    sb_lb = self.regs.get(regnr) & 0x0080 # extraigo el sign bit del low byte

                    for pos in range(8,16,1):
                        self.regs.set(regnr, sb_lb, pos) # Seteo cada posicion desde bit 8.. 15 con el bit que estaba en sb_lb

                    # Ajustar los otros bits del status
                    self.regs.set_SR('Z', self.regs.get(regnr) == 0)    # Según valor registro
                    self.regs.set_SR('C', self.regs.get(regnr) != 0)
                    self.regs.set_SR('V', False)                        # Siempre a 0

                    # Acordarse del estado del CY en ST
                    cy = self.regs.get_SR('C')

                    self.regs.set_SR('N', cy)                           # Mismo estado que Carry

                except MemoryException as ex:
                    if str(ex) == "Lectura de memoria no inicializada":
                        self.mem.store_word_at(self.regs.get(regnr), 0xABCD)

                        print(self.mem.dump(self.regs.get(regnr), 32))

                        self.regs.set(regnr, self.mem.load_word_at(self.regs.get(regnr)))

                        sb_lb = self.regs.get(regnr) & 0x0080 # extraigo el sign bit del low byte

                        for pos in range(8,16,1):
                            self.regs.set(regnr, sb_lb, pos) # Seteo cada posicion desde bit 8.. 15 con el bit que estaba en sb_lb

                        # Ajustar los otros bits del status
                        self.regs.set_SR('Z', self.regs.get(regnr) == 0)    # Según valor registro
                        self.regs.set_SR('C', self.regs.get(regnr) != 0)
                        self.regs.set_SR('V', False)                        # Siempre a 0

                        # Acordarse del estado del CY en ST
                        cy = self.regs.get_SR('C')

                        self.regs.set_SR('N', cy)                           # Mismo estado que Carry

                    else:
                        if "Direccion fuera de rango" in str(ex):
                            self.mem.store_word_at(self.mem.mem_start + self.regs.get(regnr), 0xABCD)

                            print(self.mem.dump(self.mem.mem_start + self.regs.get(regnr), 32))

                            self.regs.set(regnr, self.mem.load_word_at(self.mem.mem_start + self.regs.get(regnr)))

                            sb_lb = self.regs.get(regnr) & 0x0080 # extraigo el sign bit del low byte

                            for pos in range(8,16,1):
                                self.regs.set(regnr, sb_lb, pos) # Seteo cada posicion desde bit 8.. 15 con el bit que estaba en sb_lb

                            # Ajustar los otros bits del status
                            self.regs.set_SR('Z', self.regs.get(regnr) == 0)    # Según valor registro
                            self.regs.set_SR('C', self.regs.get(regnr) != 0)
                            self.regs.set_SR('V', False)                        # Siempre a 0

                            # Acordarse del estado del CY en ST
                            cy = self.regs.get_SR('C')

                            self.regs.set_SR('N', cy)                           # Mismo estado que Carry

                finally:
                    if self.opc_Byte(opcode):
                        self.regs.set(regnr, self.regs.get(regnr) + 0x0001)
                    else:
                        self.regs.set(regnr, self.regs.get(regnr) + 0x0002)

            elif opcstr == 5: # INSTRUCCION CALL

                try:
                    contenido_memoria = self.mem.load_word_at(self.regs.get(regnr))

                    print(self.mem.dump(self.regs.get(regnr), 32))

                    self.regs.set(regnr, self.mem.load_word_at(self.regs.get(regnr)))

                    tmp = self.regs.get(regnr) # guardo en tmp el contenido de regnr

                    sp = self.regs.get(1) - 0x0002 # Decremento el registro SP en 2
                    self.regs.set(1, sp) # Seteo el nuevo valor de SP

                    self.mem.store_word_at(sp, self.regs.get(0) + 0x0002) # Seteo en la direccion que apunta el registro SP el valor de PC + 2
                    print(self.mem.dump(0xdff0, 32))

                    self.regs.set(0, tmp) # Seteo el PC con el valor de tmp, obtenido anteriormente

                    return self.regs.get(0)

                except MemoryException as ex:
                    if str(ex) == "Lectura de memoria no inicializada":
                        self.mem.store_word_at(self.regs.get(regnr), 0xABCD)

                        print(self.mem.dump(self.regs.get(regnr), 32))

                        self.regs.set(regnr, self.mem.load_word_at(self.regs.get(regnr)))

                        tmp = self.regs.get(regnr) # guardo en tmp el contenido de regnr

                        sp = self.regs.get(1) - 0x0002 # Decremento el registro SP en 2
                        self.regs.set(1, sp) # Seteo el nuevo valor de SP

                        self.mem.store_word_at(sp, self.regs.get(0) + 0x0002) # Seteo en la direccion que apunta el registro SP el valor de PC + 2
                        print(self.mem.dump(0xdff0, 32))

                        self.regs.set(0, tmp) # Seteo el PC con el valor de tmp, obtenido anteriormente

                        return self.regs.get(0)

                    else:
                        if "Direccion fuera de rango" in str(ex):
                            self.mem.store_word_at(self.mem.mem_start + self.regs.get(regnr), 0xABCD)

                            print(self.mem.dump(self.mem.mem_start + self.regs.get(regnr), 32))

                            self.regs.set(regnr, self.mem.load_word_at(self.mem.mem_start + self.regs.get(regnr)))

                            tmp = self.regs.get(regnr) # guardo en tmp el contenido de regnr

                            sp = self.regs.get(1) - 0x0002 # Decremento el registro SP en 2
                            self.regs.set(1, sp) # Seteo el nuevo valor de SP

                            self.mem.store_word_at(sp, self.regs.get(0) + 0x0002) # Seteo en la direccion que apunta el registro SP el valor de PC + 2
                            print(self.mem.dump(0xdff0, 32))

                            self.regs.set(0, tmp) # Seteo el PC con el valor de tmp, obtenido anteriormente

                            return self.regs.get(0)

                finally:
                    if self.opc_Byte(opcode):
                        self.regs.set(regnr, self.regs.get(regnr) + 0x0001)
                    else:
                        self.regs.set(regnr, self.regs.get(regnr) + 0x0002)

            return addr



    def opd_single_reti(self, addr, opcode, opcstr):
        """ Desensamblar instruccion RETI """
        return "%-8s" % (opcstr)

    #
    #   Instrucciones de doble operando
    #

    def opd_double(self, addr, opcode, opcstr):
        pass
        """En grupos"""

    #
    #   Instrucciones de salto (condicional)
    #

    def opd_jump(self, addr, opcode, optype):
        """ Simular instrucciones de salto """

        offset = (opcode & 0x03ff) - 1    # salto se calcula desde la direccion
                                          # del opcode (addr ya fue incrementado!)
        if (offset & 0x0200) != 0:        # Positivo
            offset |= 0xfe00
        addr1 = (addr + 2*offset) & 0xffff

        if optype == self.JMP:
            return addr1

        elif optype == self.JNZ:
            return addr1 if not self.regs.get_SR('Z') else addr

        elif optype == self.JZ:
            return addr1 if self.regs.get_SR('Z') else addr

        elif optype == self.JC:
            return addr1 if self.regs.get_SR('C') else addr

        elif optype == self.JNC:
            return addr1 if not self.regs.get_SR('C') else addr

        elif optype == self.JN:
            return addr1 if self.regs.get_SR('N') else addr

        elif optype == self.JL:
            # La operacion != es el equivalente de una XOR
            if (self.regs.get_SR('N') != self.regs.get_SR('V')): return addr1
            else: return addr

        elif optype == self.JGE:
            # La operacion != es el equivalente de una XOR
            if not (self.regs.get_SR('N') != self.regs.get_SR('V')): return addr1
            else: return addr


    def disassemble(self, start, end):
        """ Desensamblar el bloque de memoria de <start> a <end>
        """
        pc = start
        while pc <= end:
            new_pc, s = self.one_opcode(pc)
            print("{:04x}  {:s}".format(pc, s))
            pc = new_pc


    def disassemble_all(self, handler):
        """ Desensamblar todos los lugares inicializados.
            El <handler> contiene la rutina que será llamada para hacer
            algo útil con <pc> y <s>  (<s> es el opcode desensamblado)
        """
        pc = self.mem.mem_start
        while pc < (self.mem.mem_start + self.mem.mem_size):
            if self.mem.load_word_at(pc) == None:
                pc += 2
                continue
            new_pc, s = self.one_opcode(pc)
            handler(pc, s)
            pc = new_pc


def main():
    from registers import Registers

    m = Memory(1024, mem_start = 0xfc00)
    r = Registers()
    s = Simulator(m, r)

    m.store_words_at(0xfd00, [
                0x3c55, 0x3e55,
                0x1005, 0x1015, 0x0019, 0x1026, 0x1037,
                0x1088, 0x1098, 0x001a, 0x10a9, 0x10b9,
                0x1105, 0x1196, 0x001b, 0x122b, 0x12bc,
                0x1300])

    m.store_word_at(0xfffe, 0xfd00)

    print(str(m))

    newpc = s.one_step(0xfffe)
    print("%04x" % newpc)

    newpc = s.one_step(newpc)
    print("%04x" % newpc)

    return 0

if __name__ == '__main__':
    main()