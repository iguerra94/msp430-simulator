#!/usr/bin/env python3

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

VERSION = "Sim_gui v0.1beta"

class Sim_main_menu(Gtk.MenuBar):
    def __init__(self, toplevel):
        super(Sim_main_menu, self).__init__()
        self.main_menu = {}
        self.toplevel = toplevel

        for key in ["File", "Edit", "Tools", "Help"]:
            item = Gtk.MenuItem(key)
            self.main_menu[key] = Gtk.Menu()
            item.set_submenu(self.main_menu[key])
            self.add(item)

        self.add_items_to("File", (("Quit", lambda x: Gtk.main_quit()), ))
        self.add_items_to("Help", (("About", self.on_about_activated), ))

    def add_items_to(self, main_item, items):
        for item, handler in items:
            if item == None:
                it = Gtk.SeparatorMenuItem()
            else:
                it = Gtk.ImageMenuItem(item)
                it.connect("activate", handler)
            self.main_menu[main_item].insert(it, 0)

    def on_about_activated(self, menuitem):
        #pxb = GdkPixbuf.Pixbuf.new_from_file("picide.png")
        dlg = Gtk.AboutDialog(version = VERSION,program_name = "PixIDE",
                              license_type = Gtk.License.GPL_3_0)
        dlg.set_transient_for(self.toplevel)
        dlg.run()
        dlg.destroy()


