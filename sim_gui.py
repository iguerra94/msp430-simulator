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
#  This program ssis distributed in the hope that it will be useful,
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
from gi.repository import Gtk, Pango

from datetime import datetime, timedelta

from cpu import CPU
from registers import Registers
from main_menu import Sim_main_menu
from disasm import Disassembler
from memory import MemoryException
import pdb


class Word_editor(Gtk.EventBox):
    """ Editor para un valor:
            - Muestra al valor actual en hex
            - Al cliquear aparece un diálogo para editar el valor
                (puede ingresar decimal, 0x hex, 0o octal, 0b binario)
            - <Enter> o <Aceptar> aceptará al valor nuevo
        El método <update> es para actualizar el valor:
            - Actualizará el valor en pantalla
            - Llama a <callback> para actualizar el origen
    """
    def __init__(self, toplevel,
                    title, prompt,
                    value,
                    callback = None,
                    addr = None):
        super(Word_editor, self).__init__()
        self.connect("button-press-event", self.on_button_pressed)

        self.title = title              # Titulo para ventana de edición
        self.toplevel = toplevel
        self.prompt = prompt            # Texto para el campo de edición
        self.callback = callback        # Rutina para devolver resultado
        self.addr = addr                # Dirección (o número de registro)
        self.value = value              # Valor actual

        self.label = Gtk.Label(self.format_value(value))
        self.label.modify_font(Pango.FontDescription("Mono 10"));
        self.add(self.label)


    def format_value(self, value):
        """ Formatea los valores - para que todos tengan el mismo formato """
        if value < 0:
            return "0x...."
        else:
            return "0x{:04x}".format(value)


    def set(self, value):
        """ Setear self.value sin llamar al callback """
        self.value = value
        self.label.set_text(self.format_value(value))


    def update(self, value):
        self.set(value)
        if self.callback:
            self.callback(value, self.addr)


    def on_button_pressed(self, evbox, event):
        """ Cuando se cliquea sobre el campo del valor, inicia el diálogo
            de edición.
        """
        dlg_entry = Gtk.Entry(
                    width_chars = 10,
                    text = self.format_value(self.value))
        hbox = Gtk.HBox(
                    margin = 10,
                    spacing = 6)
        hbox.pack_start(Gtk.Label(
                    "{:s}: ".format(self.prompt)),
                    False,
                    False,
                    0)
        hbox.pack_start(dlg_entry, False, False, 0)
        hbox.show_all()

        dlg = Gtk.Dialog(
                    parent = self.toplevel,
                    title = self.title,
                    buttons = ("Cancelar", Gtk.ResponseType.CANCEL,
                               "Aceptar",  Gtk.ResponseType.ACCEPT))

        dlg.get_content_area().add(hbox)
        dlg_entry.connect("activate", lambda x: dlg.response(Gtk.ResponseType.ACCEPT))

        if dlg.run() == Gtk.ResponseType.ACCEPT:
            try:
                new_value = int(dlg_entry.get_text(), 0)
                self.update(new_value)
            except:
                pass

        dlg.destroy()



class Sim_registers(Gtk.Frame):
    """ Cuadro que contiene para editor todos los registros """
    def __init__(self, toplevel, regs):
        super(Sim_registers, self).__init__()
        self.set_label("Editor de registros")
        self.toplevel = toplevel
        self.regs = regs

        reg_grid = Gtk.Grid()
        sr_grid = Gtk.Grid(
                    column_spacing = 6)
        self.flag_btns = []
        self.edit_table = []

        # Mostrar los registros enteros
        for row in range(4):
            for col in range(4):
                reg_nr = row*4 + col
                lbl = Gtk.Label(" R{:02d}:".format(reg_nr))
                reg_grid.attach(lbl, col*2, row, 1, 1)

                reg_edit = Word_editor(
                            self.toplevel,
                            "Editor de registros",
                            "Registro {:d}",
                            self.regs[reg_nr],
                            self.callback,
                            reg_nr)
                self.edit_table.append(reg_edit)
                reg_grid.attach(reg_edit, col*2 + 1, row, 1, 1)

        # Mostrar los bits del STatus register separados
        sr = self.regs[Registers.SR]
        for i, name in enumerate(['V', 'SG1', 'SG0', 'OSC',
                                  'CPU', 'GIE', 'N', 'Z', 'C']):
            sr_grid.attach(Gtk.Label("  {:s}:".format(name)), i*2, 0, 1, 1)
            bitnr = 8 - i
            bit_is_set = (sr & (1 << bitnr)) != 0
            cbtn = Gtk.CheckButton(
                        active = bit_is_set,
                        hexpand = False)
            self.flag_btns.append(cbtn)
            sr_grid.attach(cbtn, i*2 + 1, 0, 1, 1)

        reg_grid.attach(sr_grid, 0, 4, 8, 1)

        self.add(reg_grid)


    def show_registers(self):
        """ Actualizar el display de los registros y del registro de Status """
        for row in range(4):
            for col in range(4):
                reg_nr = row*4 + col
                self.edit_table[reg_nr].update(self.regs[reg_nr])

        sr = self.regs[Registers.SR]
        for i, name in enumerate(['V', 'SG1', 'SG0', 'OSC',
                                  'CPU', 'GIE', 'N', 'Z', 'C']):
            bitnr = 8 - i
            bit_is_set = (sr & (1 << bitnr)) != 0
            self.flag_btns[i].set_active(bit_is_set)


    def callback(self, new_val, reg_nr = None):
        self.regs[reg_nr] = new_val



class Memory_editor(Gtk.Frame):
    """ Cuadro para editar el contenido de la memoria """
    def __init__(self, toplevel, mem):
        super(Memory_editor, self).__init__()

        self.set_label("Editor de memoria")
        self.toplevel = toplevel
        self.mem = mem
        self.grid = Gtk.Grid(
                    column_spacing = 8,
                    margin = 6)
        self.addr = 0xc200

        # Dirección base para mostra memoria
        addr_lbl = Gtk.Label("Inicio:")
        addr_edit = Word_editor(
                    self.toplevel,
                    "Cambiar desplazamiento",
                    "Inicio",
                    self.addr,
                    self.callback,
                    -1)                 # Valor = -1 indica que es la dirección

        self.grid.attach(addr_lbl, 0, 0, 1, 1)
        self.grid.attach(addr_edit, 0, 1, 1, 1)

        self.show_rom()

        self.add(self.grid)


    def show_rom(self):
        self.labels = []
        self.mem_locs = []
        for line in range(5):
            lbl = Gtk.Label("0x{:04x}".format(self.addr + line*16))
            self.grid.attach(lbl, 1, line, 1, 1)
            self.grid.attach(Gtk.Label("="), 2, line, 1, 1)
            self.labels.append(lbl)

            for w in range(8):
                self.ad = self.addr + line*16 + w*2
                try:
                    old_word = self.mem.load_word_at(self.ad)
                except MemoryException:
                    old_word = -1
                word_edit = Word_editor(
                            self.toplevel,
                            "Editar memoria",
                            "Contenido nuevo",
                            old_word,
                            self.callback,
                            line*16 + w*2)
                self.grid.attach(word_edit, 3 + w, line, 1, 1)
                self.mem_locs.append(word_edit)


    def update_rom(self):
        #~ pdb.set_trace()
        for lbl_nr, lbl in enumerate(self.labels):
            lbl.set_text("0x{:04x}".format(self.addr + lbl_nr*16))

        for offs, mem_loc in enumerate(self.mem_locs):
            phy_addr = self.addr + offs*2
            try:
                w = self.mem.load_word_at(phy_addr)
            except MemoryException:
                w = -1
            mem_loc.set(w)


    def callback(self, new_val, addr):
        if addr == -1:              # Editamos la direccion base
            self.addr = new_val
            self.update_rom()
        else:                       # Editamos contenido
            self.mem.store_word_at(self.addr + addr, new_val)


class ExecutionTime(Gtk.Frame):
    """ Muestra el tiempo de ejecucion en pasos del procesador
    """
    def __init__(self, toplevel):
        super(ExecutionTime, self).__init__()
        # self.connect("button-press-event", self.on_button_pressed)

        # Quito el borde del Gtk.Frame
        self.set_shadow_type(Gtk.ShadowType.NONE)

        self.toplevel = toplevel

        self.time_start = datetime.now()                                # Tiempo de inicio
        self.delta_time = datetime.now() - self.time_start              # Delta de tiempo entre el tiempo actual y el inicial

        self.label = Gtk.Label(self.format_value(self.delta_time.seconds))
        self.label.modify_font(Pango.FontDescription("Mono 10"));
        self.add(self.label)

    def format_value(self, delta_time_seconds):
        return 'Tiempo de ejecución: {}'.format(timedelta(seconds=delta_time_seconds))

    def get_time_start(self):
        return self.time_start

    def set_time_start(self):
        self.time_start = datetime.now()

    def get_delta_time(self):
        return self.delta_time

    def set_delta_time(self):
        self.delta_time = datetime.now() - self.get_time_start()

    def update_time(self, delta_time_seconds):
        self.label.set_text(self.format_value(delta_time_seconds))

    def reset_time(self):
        print("0")
        self.update_time(0)


class Tools(Gtk.Frame):
    """ Botones para hacer pasos, reset, etc """
    def __init__(self, toplevel, label):
        super(Tools, self).__init__()

        self.set_label(label)
        self.vbox = Gtk.VBox(
                    margin = 4,
                    spacing = 4)
        self.add(self.vbox)


    def append_button(self, icon, handler, tooltext):
        btn = Gtk.Button.new_from_icon_name(icon, Gtk.IconSize.BUTTON)
        btn.connect("clicked", handler)
        btn.set_tooltip_text(tooltext)
        self.vbox.pack_start(btn, False, False, 0)



class Source_code(Gtk.Frame):
    """ Maneja el cuadro de código fuente y provee las herramientas:
            clear()         Para borrar todo el cuadro
            append()        Agrega una línea en la pantalla
            select_at_pc()  Selecciona la linea correspondiente al PC
            step()          Ejecutar un paso del programa
            reset()         Resetear al procesador
    """
    def __init__(self, toplevel):
        super(Source_code, self).__init__()
        self.set_label("Codigo fuente")
        self.toplevel = toplevel

        scroller = Gtk.ScrolledWindow()
        self.store = Gtk.ListStore(str, str, str, str)
        self.editor = Gtk.TreeView(
                    model = self.store,
                    margin = 4)

        renderer = Gtk.CellRendererText()
        for c, hdr in ((0, "PC"),
                       (1, "Dir"),
                       (2, "Label"),
                       (3, "Instruction")):
            col = Gtk.TreeViewColumn(hdr, renderer, text = c)
            self.editor.append_column(col)

        self.editor.modify_font(Pango.FontDescription("Mono 10"));

        scroller.add(self.editor)
        self.add(scroller)
        self.index = {}


    def clear(self):
        """ Borrar el listado del código """
        self.store.clear()


    def append(self, pc, s):
        """ Agrega una linea a la pantalla """
        self.store.append( ("",
                            "{:04x}".format(pc),
                            "",
                            "{:s}".format(s)) )


    def select_at_pc(self, pc):
        """ Modifica el treeview para mostrar la proxima instrucción """
        pcs = "{:04x}".format(pc)
        for row in self.store:
            row[0] = "▶" if (row[1] == pcs) else ""


    def step(self, btn):
        """ Ejecutar un paso de simulación """
        
        self.select_at_pc(0xfd16)
        self.toplevel.cpu.step(self.toplevel)
        self.toplevel.registers.show_registers()

        self.select_at_pc(self.toplevel.cpu.reg.get_PC())

        self.toplevel.exectime.set_delta_time()
        self.toplevel.exectime.update_time(self.toplevel.exectime.get_delta_time().seconds)
        self.toplevel.exectime.set_time_start()


    def reset(self, btn):
        """ Ejecutar un 'reset': PC buscará vector de inicio en 0xfffe """
        self.toplevel.cpu.reset()
        self.toplevel.registers.show_registers()
        self.select_at_pc(self.toplevel.cpu.reg.get_PC())

        self.toplevel.exectime.reset_time()



class MainWindow(Gtk.Window):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.connect("destroy", lambda x: Gtk.main_quit())
        self.set_size_request(400, 500)

        self.cpu = CPU("MSP430iua")             # Modelo CPU
                                                # ROM: 0xc200..0xffff
        main_menu = Sim_main_menu(self)
        main_menu.add_items_to("File", ((None, None),
                                        ("Open", self.open_intel_file)))
        self.registers = Sim_registers(self, self.cpu.reg.get_registers())
        self.source = Source_code(self)
        self.memedit = Memory_editor(self, self.cpu.ROM)
        self.tools = Tools(self, "Tools")

        self.exectime = ExecutionTime(self)

        self.create_buttons()

        center_hbox = Gtk.HBox(spacing = 4, margin = 6)
        center_hbox.pack_start(self.tools, False, False, 0)
        center_hbox.pack_start(self.source, True, True, 0)

        bottom_nb = Gtk.Notebook(margin = 6)
        bottom_nb.append_page(self.registers, Gtk.Label("Registros"))
        bottom_nb.append_page(self.memedit, Gtk.Label("Memoria"))

        exectime_hbox = Gtk.HBox(spacing = 4, margin = 6)
        exectime_hbox.pack_end(self.exectime, False, False, 0)

        vbox = Gtk.VBox()
        vbox.pack_start(main_menu, False, False, 0)
        vbox.pack_start(center_hbox, True, True, 0)
        vbox.pack_start(exectime_hbox, False, True, 0)
        vbox.pack_start(bottom_nb, False, False, 0)

        self.add(vbox)
        self.show_all()


    def run(self):
        Gtk.main()


    def create_buttons(self):
        for icon, handler, tooltext in (
                    ("media-playback-start", self.source.step, "Step"),
                    ("media-seek-backward", self.source.reset, "Reset")):

            self.tools.append_button(icon, handler, tooltext)



    def open_intel_file(self, menuitem):
        fc = Gtk.FileChooserDialog(
                    parent = self,
                    action = Gtk.FileChooserAction.OPEN,
                    local_only = True,
                    buttons = ("Cancel", Gtk.ResponseType.CANCEL,
                               "Open", Gtk.ResponseType.ACCEPT))

        if fc.run() == Gtk.ResponseType.ACCEPT:
            self.source.clear()                     # Borrar la 'pantalla'
            fname = fc.get_filename()
            self.cpu.ROM.load_from_intel(fname)     # Carga el archivo en ROM
            print(self.cpu.ROM.dump(0xc200, 1024))
            dis = Disassembler(self.cpu.ROM)

            dis_all = dis.disassemble_all()
            for pc, _, s in dis_all:
                if pc != 0xfffe:
                    self.source.append(pc, s)

        fc.destroy()



def main():
    mw = MainWindow()
    mw.run()
    return 0



if __name__ == '__main__':
    main()