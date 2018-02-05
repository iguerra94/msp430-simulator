#!/usr/bin/python3
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
from instructions_table import Instructions_table
import pdb

# class 

class ValueNegativeOrZeroException(Exception): pass

class Memory_editor_words_dialog(Gtk.Dialog):
    """
    Cuadro de dialogo que permite ingresar las "n" palabras en 
    el editor de memoria.
    Los datos a ingresar son:
        - Formato de instrucción:
            - Hexadecimal
            - Codigo Fuente
        - Tipo de instrucción:
            - Por registro
            - Indexado
            - Indirecto por registro
            - Indirecto autoincrementado
            - Palabra de memoria
        - Contenido de la palabra:
            Si el formato es hex:
                Se muestra un campo de texto para ingresar el comtenido 
                con el valor inicial '0x....' 
            Sino:
                - Se muestra a la izquierda un combobox con las instrucciones 
                en codigo fuente (rrc, rra, sxt, swpb, etc..)
                - A la derecha un campo de texto para completar la instruccion con el registro
    """
    def __init__(self, toplevel, title, loc, value, current_num_word, num_words, buttons):
        super(Memory_editor_words_dialog, self).__init__(
            parent = toplevel,
            title = title,
            buttons = buttons
        )

        self.loc = loc
        self.toplevel = toplevel
        self.value_hex = value
        self.current_num_word = current_num_word
        self.num_words = num_words
        self.buttons = buttons
        self.modified = False
        self.is_memory_word_only = False
        
        # print("VALUE: ", self.value_hex)

        self.instr_table = Instructions_table()


        self.memory_instruction = [None] * 4
        self.instruction_selected = None
        self.addressing_type_selected = None
        self.source_register_selected = None


        if self.value_hex == "0x....":
            self.instruction_selected = self.get_instructions_list()[0]
            self.addressing_type_selected = self.get_addressing_types_list()[0]
            self.source_register_selected = self.get_source_registers_list()[0]

            self.memory_instruction = [
                self.addressing_type_selected,
                self.instruction_selected,
                self.source_register_selected,
                None
            ]

            self.value = self.instr_table.get_instruction_opcode(self.memory_instruction[0], self.memory_instruction[1]) | self.memory_instruction[2]
            self.value_hex = hex(int(hex(self.instr_table.get_instruction_opcode(self.memory_instruction[0], self.memory_instruction[1])), 0) | self.memory_instruction[2])

            self.modified = True
        else:
            self.value = int(self.value_hex, 16)

        vbox = Gtk.VBox(margin = 10, spacing = 6)

        vbox.pack_start(Gtk.Label(
                            "PALABRA N°{:d}/{:d}".format(
                                self.current_num_word,
                                self.num_words)),
                            True,
                            True,
                            0)

        separator = Gtk.Separator(orientation = Gtk.Orientation.HORIZONTAL)
        vbox.pack_start(separator, True, True, 0)

        # hbox_instruction_format = self.instruction_format_box(
        #                             "Formato de instrucción",
        #                             self.get_instruction_formats_list()
        #                         )

        # vbox.pack_start(hbox_instruction_format, True, True, 0)

        hbox_instruction = self.instruction_box(
                                    "Instrucción",
                                    self.get_instructions_list()
                                )

        vbox.pack_start(hbox_instruction, True, True, 0)

        hbox_addressing_type = self.addressing_type_box(
                                    "Modo de direccionamiento",
                                    self.get_addressing_types_list()
                                )

        vbox.pack_start(hbox_addressing_type, True, True, 0)

        self.hbox_instruction_offset = self.instruction_offset_box("Offset (Formato decimal)", 25)
        
        vbox.pack_start(self.hbox_instruction_offset, True, True, 0)        

        hbox_source_register = self.source_register_box(
                                 "Registro fuente",
                                 self.get_source_registers_list()
                               )

        vbox.pack_start(hbox_source_register, True, True, 0)

        hbox_instruction_content = self.instruction_content_box("Contenido", self.value_hex)

        vbox.pack_start(hbox_instruction_content, True, True, 0)

        vbox.show_all()

        self.get_content_area().add(vbox)

    # Getters

    def get_instruction(self):
        return self.value

    def get_is_memory_word_only(self):
        return self.is_memory_word_only

    def get_instruction_offset(self):
        return self.memory_instruction[3]

    def get_label_location(self):
        return self.loc

    def get_buttons_text(self):
        return self.buttons[0]

    def is_modified(self):
        return self.modified

    # INSTRUCTION

    def on_instruction_combo_changed(self, combo):
        tree_iter = combo.get_active_iter()
        if tree_iter != None:
            model = combo.get_model()
            self.instruction_selected = model[tree_iter][0]

            self.memory_instruction[1] = self.instruction_selected
            self.value = self.instr_table.get_instruction_opcode(self.memory_instruction[0], self.memory_instruction[1]) | self.memory_instruction[2]
            self.value_hex = hex(int(hex(self.instr_table.get_instruction_opcode(self.memory_instruction[0], self.memory_instruction[1])), 0) | self.memory_instruction[2])
            self.instr_content_entry.set_text(self.value_hex)

            if (self.addressing_type_selected == "Indexado"):
                value = int(self.instr_offset_entry.get_text(), 10)
                self.memory_instruction[3] = value
            
            self.modified = True
            print(self.memory_instruction)

    # TODO: No parsear a hexadecimal la instruccion y el offset en caso que no sea None
    def get_instructions_list(self):
        return [
            "RRC",
            "RRC.b",
            "SWPB",
            "RRA",
            "RRA.b",
            "SXT",
            "PUSH",
            "PUSH.b",
            "CALL"
        ]

    def on_memory_word_check_button_toggled(self, checkbtn, data=None):
        option = ("OFF", "ON")[checkbtn.get_active()]

        if option == "ON":
            self.instruction_combo.set_sensitive(False)
            self.addressing_types_combo.set_sensitive(False)
            self.instr_offset_entry.set_sensitive(False)
            self.source_register_combo.set_sensitive(False)
            self.instr_content_entry.set_editable(True)
            self.instr_content_entry.set_text("25")
            
            value = self.instr_content_entry.get_text()

            self.value = int(value, 10)
            self.modified = True
            self.is_memory_word_only = True
        
        if option == "OFF":
            self.instruction_combo.set_sensitive(True)
            self.addressing_types_combo.set_sensitive(True)
            self.source_register_combo.set_sensitive(True)
            self.instr_content_entry.set_text("0x1004")
            self.instr_content_entry.set_editable(False)

            value = self.instr_content_entry.get_text()
            self.value = int(value, 16)
            print(self.value)
            self.modified = True
            self.is_memory_word_only = False


    def instruction_box(self, prompt, instructions_list):
        if not self.instruction_selected:
            self.instruction_selected = instructions_list[0]
            self.memory_instruction[1] = self.instruction_selected


        hbox = Gtk.HBox(
                    margin = 10,
                    spacing = 6)

        hbox.pack_start(Gtk.Label(
                            "{:s}: ".format(prompt)),
                            False,
                            False,
                            0)

        instruction_store = Gtk.ListStore(str)
        
        for instr in instructions_list:
            instruction_store.append([instr])

        self.instruction_combo = Gtk.ComboBox.new_with_model(instruction_store)
        self.instruction_combo.set_active(0)
        self.instruction_combo.connect("changed", self.on_instruction_combo_changed)
        renderer_text = Gtk.CellRendererText()
        self.instruction_combo.pack_start(renderer_text, True)
        self.instruction_combo.add_attribute(renderer_text, "text", 0)

        hbox.pack_start(self.instruction_combo, True, True, 0)

        separator = Gtk.Separator(orientation = Gtk.Orientation.VERTICAL)
        hbox.pack_start(separator, True, True, 0)

        memory_word_check_button = Gtk.CheckButton("Palabra de memoria")
        memory_word_check_button.connect("toggled", self.on_memory_word_check_button_toggled, "toggle button memory word check button")

        hbox.pack_start(memory_word_check_button, True, True, 4)

        hbox.show_all()

        return hbox

    # ADDRESSING TYPE

    def on_addressing_types_combo_changed(self, combo):
        tree_iter = combo.get_active_iter()
        if tree_iter != None:
            model = combo.get_model()
            
            self.addressing_type_selected = model[tree_iter][0]

            self.memory_instruction[0] = self.addressing_type_selected
            self.value = self.instr_table.get_instruction_opcode(self.memory_instruction[0], self.memory_instruction[1]) | self.memory_instruction[2]
            self.value_hex = hex(int(hex(self.instr_table.get_instruction_opcode(self.memory_instruction[0], self.memory_instruction[1])), 0) | self.memory_instruction[2])
            self.instr_content_entry.set_text(self.value_hex)

            if (self.addressing_type_selected == "Indexado"):
                self.instr_offset_entry.set_sensitive(True)
                value = int(self.instr_offset_entry.get_text(), 10)
                self.memory_instruction[3] = value
            else:
                self.instr_offset_entry.set_sensitive(False)
                self.memory_instruction[3] = None

            self.modified = True

            print(self.memory_instruction)


    def get_addressing_types_list(self):
        return [
            "Por registro",
            "Indexado",
            "Indirecto por registro",
            "Indirecto autoincrementado"
        ]


    def addressing_type_box(self, prompt, addressing_types_list):
        if not self.addressing_type_selected:
            self.addressing_type_selected = addressing_types_list[0]
            self.memory_instruction[0] = self.addressing_type_selected


        hbox = Gtk.HBox(
                    margin = 10,
                    spacing = 6)

        hbox.pack_start(Gtk.Label(
                            "{:s}: ".format(prompt)),
                            False,
                            False,
                            0)

        addressing_types_store = Gtk.ListStore(str)
        
        for addr_type in addressing_types_list:
            addressing_types_store.append([addr_type])

        self.addressing_types_combo = Gtk.ComboBox.new_with_model(addressing_types_store)
        self.addressing_types_combo.set_active(0)
        self.addressing_types_combo.connect("changed", self.on_addressing_types_combo_changed)
        renderer_text = Gtk.CellRendererText()
        self.addressing_types_combo.pack_start(renderer_text, True)
        self.addressing_types_combo.add_attribute(renderer_text, "text", 0)

        hbox.pack_start(self.addressing_types_combo, True, True, 0)
        hbox.show_all()

        return hbox

    # INSTRUCTION CONTENT

    def on_instr_offset_entry_changed(self, entry):

        try:
            value = int(entry.get_text(), 10)
            print("0x{:04x}".format(value))

            if value <= 0:
                raise ValueNegativeOrZeroException("El offset debe ser mayor a 0 (cero).")
            self.memory_instruction[3] = value

            self.modified = True
        except ValueError:

            hbox = Gtk.HBox(
                    margin = 10,
                    spacing = 6)

            hbox.pack_start(Gtk.Label(
                        "{:s}".format("Debe ingresar un numero valido en el campo de offset.")),
                        False,
                        False,
                        0)

            hbox.show_all()

            dlgError = Gtk.Dialog(
                    parent = self,
                    title = "Error",
                    buttons = ("Aceptar",  Gtk.ResponseType.ACCEPT))

            dlgError.get_content_area().add(hbox)

            if dlgError.run() == Gtk.ResponseType.ACCEPT:
                entry.set_text("25")
                dlgError.destroy()
        except ValueNegativeOrZeroException as err:

            hbox = Gtk.HBox(
                    margin = 10,
                    spacing = 6)

            hbox.pack_start(Gtk.Label(err),
                            False,
                            False,
                            0)

            hbox.show_all()

            dlgError = Gtk.Dialog(
                    parent = self,
                    title = "Error",
                    buttons = ("Aceptar",  Gtk.ResponseType.ACCEPT))

            dlgError.get_content_area().add(hbox)

            if dlgError.run() == Gtk.ResponseType.ACCEPT:
                entry.set_text("25")
                dlgError.destroy()


    def instruction_offset_box(self, prompt, value):
        hbox = Gtk.HBox(
                    margin = 10,
                    spacing = 6)

        hbox.pack_start(Gtk.Label(
                            "{:s}: ".format(prompt)),
                            False,
                            False,
                            0)

        self.instr_offset_entry = Gtk.Entry(
                    width_chars = 10,
                    text = value)
        self.instr_offset_entry.connect('changed', self.on_instr_offset_entry_changed)
        self.instr_offset_entry.set_sensitive(False)
        hbox.pack_start(self.instr_offset_entry, True, True, 0)

        hbox.show_all()

        return hbox

    # SOURCE REGISTER

    def on_source_register_combo_changed(self, combo):
        tree_iter = combo.get_active_iter()
        if tree_iter != None:
            model = combo.get_model()
            self.source_register_selected = model[tree_iter][0]

            self.memory_instruction[2] = self.source_register_selected
            self.value = self.instr_table.get_instruction_opcode(self.memory_instruction[0], self.memory_instruction[1]) | self.memory_instruction[2]
            self.value_hex = hex(int(hex(self.instr_table.get_instruction_opcode(self.memory_instruction[0], self.memory_instruction[1])), 0) | self.memory_instruction[2])
            self.instr_content_entry.set_text(self.value_hex)

            if (self.addressing_type_selected == "Indexado"):
                self.instr_offset_entry.set_sensitive(True)
                value = int(self.instr_offset_entry.get_text(), 10)
                self.memory_instruction[3] = value
            else:
                self.instr_offset_entry.set_sensitive(False)
                self.memory_instruction[3] = None

            self.modified = True

            print(self.memory_instruction)


    def get_source_registers_list(self):
        return [
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11,
            12,
            13,
            14,
            15
        ]


    def source_register_box(self, prompt, source_registers_list):
        if not self.source_register_selected:
            self.source_register_selected = source_registers_list[0]
            self.memory_instruction[2] = self.source_register_selected

        hbox = Gtk.HBox(
                    margin = 10,
                    spacing = 6)

        hbox.pack_start(Gtk.Label(
                            "{:s}: ".format(prompt)),
                            False,
                            False,
                            0)

        source_register_store = Gtk.ListStore(int)
        
        for src_reg in source_registers_list:
            source_register_store.append([src_reg])

        self.source_register_combo = Gtk.ComboBox.new_with_model(source_register_store)
        self.source_register_combo.set_active(0)
        self.source_register_combo.connect("changed", self.on_source_register_combo_changed)
        renderer_text = Gtk.CellRendererText()
        self.source_register_combo.pack_start(renderer_text, True)
        self.source_register_combo.add_attribute(renderer_text, "text", 0)

        hbox.pack_start(self.source_register_combo, True, True, 0)
        hbox.show_all()

        return hbox

    # INSTRUCTION CONTENT

    def on_instr_content_entry_changed(self, entry):
        # print("CONTENIDO: {:s}".format(entry.get_text()))
        if self.is_memory_word_only:
            try:
                value = int(entry.get_text())
                print("0x{:04x}".format(value))
                self.value = "0x{:04x}".format(value)
                self.modified = True
            except ValueError:
                try:
                    self.value = int(entry.get_text(), 16)
                    self.modified = True
                except ValueError:
                    entry.set_text("0xc200")
                    self.value = int(entry.get_text(), 16)
                    self.modified = True
        else:
            self.value_hex = entry.get_text()


    def instruction_content_box(self, prompt, value):
        hbox = Gtk.HBox(
                    margin = 10,
                    spacing = 6)

        hbox.pack_start(Gtk.Label(
                            "{:s}: ".format(prompt)),
                            False,
                            False,
                            0)

        self.instr_content_entry = Gtk.Entry(
                    width_chars = 10,
                    text = self.value_hex)
        self.instr_content_entry.set_editable(False)
        self.instr_content_entry.connect('changed', self.on_instr_content_entry_changed)

        hbox.pack_start(self.instr_content_entry, True, True, 0)

        hbox.show_all()

        return hbox



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

    def update_at(self, pos, value, memory_word_only=False):

        if type(value) is int:
            # print("2,", value, pos)
            self.toplevel.memedit.mem_locs[pos].label.set_text(self.format_value(value))
            self.callback(value, pos, memory_word_only)
        if type(value) is str:
            # print("3, ", int(value, 16))
            self.toplevel.memedit.mem_locs[pos].label.set_text(value)
            self.callback(int(value, 16), pos, memory_word_only)
        

    def on_num_words_combo_changed(self, combo):
        tree_iter = combo.get_active_iter()
        if tree_iter != None:
            model = combo.get_model()
            self.num_words = model[tree_iter][0]


    def on_button_pressed(self, evbox, event):
        """ Cuando se cliquea sobre el campo del valor, inicia el diálogo
            de edición.
        """
        hbox = Gtk.HBox(
                    margin = 10,
                    spacing = 6)
        hbox.pack_start(Gtk.Label(
                    "{:s}: ".format(self.prompt)),
                    False,
                    False,
                    0)

        if self.title in ("Editor de registros", "Cambiar desplazamiento"):            
            dlg_entry = Gtk.Entry(
                            width_chars = 10,
                            text = self.format_value(self.value))

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
                    self.toplevel.memedit.base_addr = new_value
                    self.update(new_value)
                except Exception as err:
                    print(err)
            else:
                pass
            dlg.destroy()
        else:
            num_words_store = Gtk.ListStore(int)
            num_words = [1, 2, 3, 4, 5]
            for num in num_words:
                num_words_store.append([num])

            num_words_combo = Gtk.ComboBox.new_with_model(num_words_store)
            num_words_combo.set_active(0)
            num_words_combo.connect("changed", self.on_num_words_combo_changed)
            renderer_text = Gtk.CellRendererText()
            num_words_combo.pack_start(renderer_text, True)
            num_words_combo.add_attribute(renderer_text, "text", 0)

            hbox.pack_start(num_words_combo, False, False, 0)
            hbox.show_all()

            self.num_words = num_words[0]

            dlg = Gtk.Dialog(
                    parent = self.toplevel,
                    title = self.title,
                    buttons = ("Cancelar", Gtk.ResponseType.CANCEL,
                               "Continuar",  Gtk.ResponseType.ACCEPT)
                )

            dlg.get_content_area().add(hbox)
            # dlg_entry.connect("activate", lambda x: dlg.response(Gtk.ResponseType.ACCEPT))

            if dlg.run() == Gtk.ResponseType.ACCEPT:
                dlg.destroy()
                for num_word in range(0, self.num_words):
                    ad = self.toplevel.cpu.ROM.mem_start + self.addr + num_word*2
                    try:
                        self.content = self.toplevel.cpu.ROM.load_word_at(ad)
                    except MemoryException:
                        self.content = -1
                        
                    dlg_words = None

                    # Label location
                    loc = int(self.addr/2) + num_word

                    if (num_word +1 < self.num_words):
                        dlg_words = Memory_editor_words_dialog(
                            self.toplevel,
                            self.title,
                            loc,
                            self.format_value(self.content),
                            num_word +1,
                            self.num_words,
                            ("Continuar",  Gtk.ResponseType.ACCEPT)
                        )
                    else:                    
                        dlg_words = Memory_editor_words_dialog(
                            self.toplevel,
                            self.title,
                            loc,
                            self.format_value(self.content),
                            self.num_words,
                            self.num_words,
                            ("Finalizar",  Gtk.ResponseType.ACCEPT)
                        )

                    if dlg_words.run() == Gtk.ResponseType.ACCEPT:

                        if dlg_words.is_modified():
                            
                            if dlg_words.get_is_memory_word_only():
                                try:
                                    value = dlg_words.get_instruction()
                                    pos = dlg_words.get_label_location()

                                    if type(value) is str:
                                        value = int(value, 16)
                                    self.toplevel.memedit.get_memory_words().append({ "LOCATION": self.toplevel.memedit.base_addr + pos*2, "CONTENT": value })
                                except Exception as err:
                                    pass
                            else:
                                if loc +1 > len(self.toplevel.memedit.get_memory_instruction_words()):
                                    if dlg_words.get_instruction() >= int("0x1000", 16) and dlg_words.get_instruction() <= int("0x12B0", 16):
                                        value = dlg_words.get_instruction()
                                        pos = dlg_words.get_label_location()
 
                                        if (dlg_words.get_instruction_offset() != None):
                                            offset = dlg_words.get_instruction_offset()
                                            
                                            self.toplevel.memedit.get_memory_instruction_words().append({ "LOCATION": self.toplevel.memedit.base_addr + pos*2, "CONTENT": value, "OFFSET_LOCATION": self.toplevel.memedit.base_addr + (pos+1)*2, "OFFSET": offset })
                                            # print(self.toplevel.memedit.get_memory_instruction_words())
                                        else:
                                            self.toplevel.memedit.get_memory_instruction_words().append({ "LOCATION": self.toplevel.memedit.base_addr + pos*2, "CONTENT": value, "OFFSET_LOCATION": None, "OFFSET": None })
                                            # print(self.toplevel.memedit.get_memory_instruction_words())
                                else:
                                    if dlg_words.get_instruction() >= int("0x1000", 16) and dlg_words.get_instruction() <= int("0x12B0", 16):
                                        value = dlg_words.get_instruction()
                                        pos = dlg_words.get_label_location()

                                        self.toplevel.memedit.memory_instruction_words_insert_at(loc, dlg_words.get_instruction())
                                        # print(self.toplevel.memedit.get_memory_instruction_words())
                                        if (dlg_words.get_instruction_offset() != None):
                                            self.toplevel.memedit.get_memory_instruction_words().insert(loc+1, dlg_words.get_instruction_offset())
                                            # print(self.toplevel.memedit.get_memory_instruction_words())

                            if dlg_words.get_buttons_text() == "Finalizar":
                                # print("ANTES => M", self.toplevel.memedit.get_memory_words())
                                # print("ANTES => I", self.toplevel.memedit.get_memory_instruction_words())
                                self.toplevel.memedit.mem.store_to_intel_with_words_list("input_main.hex", self.toplevel.memedit.get_memory_instruction_words(), self.toplevel.memedit.get_memory_words())
                                self.toplevel.memedit.toplevel.open_intel_file_without_dialog("input_main.hex")

                        dlg_words.destroy()
                    else:
                        dlg_words.destroy()
                        break

            else:
                dlg.destroy()
                pass



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
                                "Registro N°{:d}".format(reg_nr),
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



# TODO: Add the possibility to insert more than one word in the Word_Editor
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
        self.base_addr = int(str(self.addr), 0)
        self.memory_instruction_words = []
        self.memory_words = []

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

    def memory_instruction_words_clear(self):
        self.memory_instruction_words = []

    def set_memory_instruction_words(self, instruction_words=[]):
        self.memory_instruction_words = instruction_words

    def get_memory_instruction_words(self):
        return self.memory_instruction_words

    def memory_instruction_words_insert_at(self, index, word):
        self.memory_instruction_words[index] = word

    def memory_words_clear(self):
        self.memory_words = []

    def get_memory_words(self):
        return self.memory_words

    def set_memory_words(self, memory_words=[]):
        self.memory_words = memory_words

    def memory_words_insert_at(self, index, word):
        self.memory_words[index] = word

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
                            "Cantidad de palabras a ingresar",
                            old_word,
                            self.callback,
                            line*16 + w*2)
                # word_edit = Word_editor(
                #             self.toplevel,
                #             "Editar memoria",
                #             "Contenido nuevo",
                #             old_word,
                #             self.callback,
                #             line*16 + w*2)
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



    def callback(self, new_val, addr, memory_word_only=False):
        if addr == -1:              # Editamos la direccion base
            self.addr = new_val
            self.update_rom()
        else:                       # Editamos contenido
            # print(new_val, self.addr, addr)
            self.mem.store_word_at(self.addr + addr, new_val, memory_word_only)
            # self.update_rom()
        #     print(self.mem.dump(0xc200, 256))

        #     self.toplevel.source.clear()
        #     dis = Disassembler(self.mem)

        #     dis_all = dis.disassemble_all()
        #     for pc, _, s in dis_all:
        #         if pc != 0xfffe:
        #             self.toplevel.source.append(pc, s)

        # self.toplevel.source.reset()



class ExecutionTime(Gtk.Frame):
    """ Muestra el tiempo de ejecucion en pasos del procesador
    """
    def __init__(self, toplevel):
        super(ExecutionTime, self).__init__()
        # self.connect("button-press-event", self.on_button_pressed)

        # Quito el borde del Gtk.Frame
        self.set_shadow_type(Gtk.ShadowType.NONE)

        self.toplevel = toplevel

        self.time_start = datetime.now()                            # Tiempo de inicio
        self.delta_time = datetime.now() - self.time_start          # Delta de tiempo entre el tiempo actual y el inicial
        self.accumulated = 0
        self.is_reset = False

        self.label = Gtk.Label(self.format_value(self.delta_time.seconds))
        self.label.modify_font(Pango.FontDescription("Mono 10"))
        self.add(self.label)

    def format_value(self, delta_time_seconds):
        self.accumulated += delta_time_seconds
        return 'Tiempo de ejecución: {}'.format(timedelta(seconds=self.accumulated))
 
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

        if self.is_reset:
            self.is_reset = False

    def reset_time(self):
        self.accumulated = 0
        self.is_reset = True



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
        
        if (self.toplevel.cpu.reg.get_PC() != self.toplevel.cpu.ROM.mem_start):
            self.toplevel.exectime.set_time_start()

        self.toplevel.cpu.step(self.toplevel)
        self.toplevel.registers.show_registers()
        self.select_at_pc(self.toplevel.cpu.reg.get_PC())

        if (self.toplevel.cpu.reg.get_PC() != self.toplevel.cpu.ROM.mem_start):
            self.toplevel.exectime.set_delta_time()
            # print("START: ", self.toplevel.exectime.get_time_start())
            # print("DELTA_TIME: ", self.toplevel.exectime.get_delta_time())
            self.toplevel.exectime.update_time(self.toplevel.exectime.get_delta_time().seconds)



    def reset(self, btn = None):
        """ Ejecutar un 'reset': PC buscará vector de inicio en 0xfffe """
        self.toplevel.cpu.reset()
        self.toplevel.registers.show_registers()
        self.select_at_pc("0xfffe")

        self.toplevel.exectime.reset_time()
        self.toplevel.exectime.update_time(0)
        self.toplevel.exectime.set_time_start()
    


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
            # Refrescar el contenido del Codigo Fuente
            self.source.clear()                     # Borrar la 'pantalla'
            fname = fc.get_filename()
            self.cpu.ROM.load_from_intel(fname)     # Carga el archivo en ROM

            instruction_words_list = self.cpu.ROM.get_instruction_words()
            memory_words_list = self.cpu.ROM.get_memory_words()

            self.memedit.memory_instruction_words_clear()
            self.memedit.memory_words_clear()

            self.memedit.set_memory_instruction_words(instruction_words_list)
            self.memedit.set_memory_words(memory_words_list)

            # print("INSTR", self.memedit.get_memory_instruction_words())
            # print("MEMORY", self.memedit.get_memory_words())

            dis = Disassembler(self.cpu.ROM)

            instructions_and_offsets_list = []    
            for word in self.memedit.get_memory_instruction_words():
                instructions_and_offsets_list.append(word["CONTENT"])
                if word["OFFSET"] != None:
                    instructions_and_offsets_list.append(word["OFFSET"])

            dis_all = dis.disassemble_all()

            for pc, _, s in dis_all:
                if pc != int("0xfffe", 16) and s.strip() != 'nop' and self.cpu.ROM.load_word_at(pc) in instructions_and_offsets_list:
                    self.source.append(pc, s)

            self.memedit.update_rom()

        fc.destroy()


    def open_intel_file_without_dialog(self, fname):

        # Refrescar el contenido del Codigo Fuente
        self.source.clear()                     # Borrar la 'pantalla'

        self.cpu.ROM.load_from_intel(fname)     # Carga el archivo en ROM
        # print(self.cpu.ROM.dump(0xc200, 1024))
        dis = Disassembler(self.cpu.ROM)

        instruction_words_list = self.cpu.ROM.get_instruction_words()
        memory_words_list = self.cpu.ROM.get_memory_words()

        self.memedit.memory_instruction_words_clear()
        self.memedit.memory_words_clear()

        self.memedit.set_memory_instruction_words(instruction_words_list)
        self.memedit.set_memory_words(memory_words_list)

        instructions_and_offsets_list = []    
        for word in self.memedit.get_memory_instruction_words():
            instructions_and_offsets_list.append(word["CONTENT"])
            if word["OFFSET"] != None:
                instructions_and_offsets_list.append(word["OFFSET"])
                
        dis_all = dis.disassemble_all()
        for pc, _, s in dis_all:
            if pc != int("0xfffe", 16) and s.strip() != 'nop' and self.cpu.ROM.load_word_at(pc) in instructions_and_offsets_list:
                # print(s.strip(), len(s.strip()))
                self.source.append(pc, s)

        self.memedit.update_rom()



def main():
    mw = MainWindow()
    mw.run()
    return 0



if __name__ == '__main__':
    main()