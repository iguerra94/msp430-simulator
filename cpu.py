#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
##  cpu.py
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

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from registers import Registers
from memory import Memory, MemoryException
from simulator import Simulator

class CPU():                    #   ROM    RAM
    CPU_TABLE = {"MSP430FR2000": (  512,   512),
                 "MSP430FR2100": ( 1024,   512),
                 "MSP430FR2110": ( 2048,  1024),
                 "MSP430FR2111": ( 4096,  1024),
                 "MSP430iua"   : (15872,  1024)}

    def __init__(self, part = "MSP430iua"):
        assert part in CPU.CPU_TABLE

        # Memoria de programa: Termina en el final del espacio de 65kB,
        # y se reserva hacia abajo.
        self.ROM = Memory(mem_size  = self.CPU_TABLE[part][0],
                          mem_start = 2**16 - self.CPU_TABLE[part][0],
                          readonly  = True)
        self.ROM.store_word_at(65534, self.ROM.mem_start)

        # RAM inicia siempre en 0x200
        self.RAM = Memory(mem_size  = self.CPU_TABLE[part][1],
                          mem_start = 0x0200,
                          readonly  = False)
        self.reg = Registers()
        self.sim = Simulator(self.ROM, self.reg)

    def __str__(self):
        return (str(self.reg) + "\n" +
                str(self.RAM) + "\n" +
                str(self.ROM) + "\n")

    def reset(self):
        # pc = self.ROM.load_word_at(0xfffe)
        # self.reg.set_PC(pc)
        self.reg.set_PC(0xfffe)
        self.reg.set_SR(0)



    def step(self, toplevel):
        """ Ejecutar un paso desde el PC actual, luego actualizar el PC """
        # self.reg.set_PC(self.sim.one_step(self.reg.get_PC()))

        try:
            self.reg.set_PC(self.sim.one_step(self.reg.get_PC()))
            print(self.reg.get_PC())
            if self.reg.get_PC() == None:
                raise MemoryException()

        except MemoryException:
            dlg = Gtk.Dialog(
                    parent = toplevel,
                    title = "Fin del programa",
                    buttons = ("Cancelar", Gtk.ResponseType.CANCEL,
                                "Aceptar",  Gtk.ResponseType.ACCEPT))

            dlg.set_size_request(250, 50)

            hbox = Gtk.HBox(
                    margin = 10,
                    spacing = 6)
        
            hbox.pack_start(Gtk.Label(
                        "¿Desea reiniciar el programa?"),
                        True,
                        False,
                        0)

            hbox.show_all()

            dlg.get_content_area().add(hbox)                            

            if dlg.run() == Gtk.ResponseType.ACCEPT:
                toplevel.source.reset()

            dlg.destroy()



def main():
    c = CPU()
    print(str(c))
    return 0


if __name__ == '__main__':
    main()