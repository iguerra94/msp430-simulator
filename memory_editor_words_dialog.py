import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Pango

from instructions_table import Instructions_table


class ValueNegativeOrZeroException(Exception): pass


class ValueIsInstructionError(Exception): pass


class Memory_editor_words_dialog(Gtk.Dialog):
    def __init__(self, 
        toplevel, title, 
        loc, 
        value, 
        current_num_word, num_words, 
        buttons):
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

    # Getters

    def get_instruction(self):
        return self.value

    def get_label_location(self):
        return self.loc

    def get_buttons_text(self):
        return self.buttons[0]

    def is_modified(self):
        return self.modified


class Memory_editor_instruction_word_dialog(Memory_editor_words_dialog):
    def __init__(self, 
        toplevel, title, 
        loc, 
        value, 
        current_num_word, num_words, 
        buttons):
        super(Memory_editor_instruction_word_dialog, self).__init__(
            toplevel, title, 
            loc, 
            value, 
            current_num_word, num_words, 
            buttons
        )
    
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

        self.instr_content_entry.set_editable(False)

        vbox.pack_start(hbox_instruction_content, True, True, 0)

        vbox.show_all()

        self.get_content_area().add(vbox)


    def get_instruction_offset(self):
      return self.memory_instruction[3]

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

    # INSTRUCTION OFFSET

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
            else:
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
        self.instr_content_entry.connect('changed', self.on_instr_content_entry_changed)

        hbox.pack_start(self.instr_content_entry, True, True, 0)

        hbox.show_all()

        return hbox



class Memory_editor_memory_word_dialog(Memory_editor_words_dialog):
    def __init__(self, 
        toplevel, title, 
        loc, 
        value, 
        current_num_word, num_words, 
        buttons):
        super(Memory_editor_memory_word_dialog, self).__init__(
            toplevel, title, 
            loc, 
            value, 
            current_num_word, num_words, 
            buttons
        )
    
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

        hbox_instruction_content = self.instruction_content_box("Contenido", self.value_hex)

        vbox.pack_start(hbox_instruction_content, True, True, 0)

        vbox.show_all()

        self.get_content_area().add(vbox)

    def on_instr_content_entry_changed(self, entry):
        try:
            value = entry.get_text()

            if len(value) < 2:
                raise ValueError()
            
            if int(entry.get_text(), 16) >= int("0x1000", 16) and int(entry.get_text(), 16) <= int("0x12B0", 16):
                raise ValueIsInstructionError()
                
            self.value = int(entry.get_text(), 0)
            self.modified = True
        except ValueError:
            try:
                value = entry.get_text()
                if len(value) < 2:
                    raise ValueError()

            except ValueError:                
                entry.set_text("0xabcd")
                self.value = int(entry.get_text(), 0)
                self.modified = True
        except ValueIsInstructionError:
            hbox = Gtk.HBox(
                    margin = 10,
                    spacing = 6)

            hbox.pack_start(Gtk.Label(
                        "{:s}".format("El formato ingresado corresponde a una instruccion.\nDebe ingresar una palabra de memoria en este rango de direcciones.")),
                        False,
                        False,
                        0)

            hbox.show_all()

            dlgError = Gtk.Dialog(
                    parent = self.toplevel,
                    title = "Error",
                    buttons = ("Aceptar",  Gtk.ResponseType.ACCEPT))

            dlgError.get_content_area().add(hbox)

            if dlgError.run() == Gtk.ResponseType.ACCEPT:
                entry.set_text("0xabcd")
                self.value = int(entry.get_text(), 0)
                self.modified = True
                dlgError.destroy()
            else:
                entry.set_text("0xabcd")
                self.value = int(entry.get_text(), 0)
                self.modified = True
                dlgError.destroy()
            



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
        self.instr_content_entry.connect('changed', self.on_instr_content_entry_changed)

        hbox.pack_start(self.instr_content_entry, True, True, 0)

        hbox.show_all()

        return hbox
