#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
##  symbol_table.py
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

class SymtableException(Exception): pass

class Symbol_table():
    
    def __init__(self):
        """ Metodo Constructor de la clase Symbol_table

            Atributos: 
            symbols: Tabla de simbolos 
        """
        self.symbols = {}


    def defined(self, sym):
        """ Retorna un valor booleano dependiendo si el simbolo <sym> esta definido en la lista de simbolos:
            Si <sym> esta definido en self.symbols:
                retorna True
            Sino:
                retorna False
        """
        return sym in self.symbols


    def define(self, sym, value = None, equ = False):
        """ Define un simbolo y su respectivo valor en la lista de simbolos:
            Si <sym> esta definido en la lista de simbolos:
                Si el valor de <sym> en la lista de simbolos es None:
                    Define el valor del simbolo en la lista de simbolos
                Sino:
                    Si el valor de <sym> en la lista de simbolos es distinto al valor pasado como parametro:
                        Si el parametro <equ> es False:
                            Se lanza una excepcion de que el simbolo ya definido con otro valor
                        Sino:
                            Define el valor del simbolo en la lista de simbolos
                    Sino:
                        Retorna sin errores
            Sino:
                Define el simbolo y su respectivo valor en la lista de simbolos
        """

        if self.defined(sym):
            if self.symbols[sym] == None:       # Simbolo en tabla pero sin valor
                self.symbols[sym] = value
                return

            else:                               # Simbolo en la tabla con valor!
                if self.symbols[sym] != value:  # El nuevo valor no coincide
                    if not equ:
                        raise SymtableException("Simbolo ya definido con otro valor")
                    self.symbols[sym] = value

                else:                           # Sí coincide -> no hay error
                    return

        else:
            self.symbols[sym] = value           # Simbolo aún no declarado


    def lookup(self, sym):
        """ Retorna el valor que contiene el simbolo <sym> en la lista de simbolos:
            Si el simbolo <sym> no tiene definido ningun valor:
                retorna None
            Sino:
                retorna el valor del simbolo <sym> en la lista de simbolos
        """
        return self.symbols[sym]


    def dump(self):
        """ Retorna una representacion en cadena de caracteres de la lista de simbolos:
            A la izquierda se muestra el simbolo.
            A la derecha se muestra el valor del simbolo:
                Si el valor del simbolo es None:
                    Se imprime "No esta definido"
                Sino:
                    Se imprime el valor del simbolo
            
            Al final se muestra un mensaje de la cantidad de simbolos en la tabla y cuantos de ellos 
            no tienen valores definidos.
        """
        undefined = 0
        print("")
        print("Tabla de símbolos")
        print("")
        print("{:25s} {:s}".format("Símbolo", "Valor"))

        for sym in sorted(self.symbols):
            if self.symbols[sym] == None:
                print("{:25s} No definido".format(sym))
                undefined += 1
            else:
                print("{0:25s} 0x{1:04x} ({1:d})".format(sym, self.symbols[sym]))

        print("")
        print("{:d} símbolo(s) en la tabla, {:d} símbolo(s) sin definir".format(
                    len(self.symbols), undefined))


    def undefined(self):
        """ Retorna un valor booleano dependiendo si el valor de algun simbolo no esta definido en la lista de simbolos:
            Si el valor de algun simbolo no esta definido en la lista de simbolos:
                retorna True
            Sino:
                retorna False
        """        
        for key in self.symbols:
            if self.symbols[key] == None:
                return True

        return False



def main():
    st = Symbol_table()

    if st.defined("Hola"):
        print("Simbolo no definido detectado")
    st.define("Hola", 0x1234)
    if not st.defined("Hola"):
        print("Simbolo definidos no encontrado")
    else:
        print("Encontre valor: ", st.lookup("Hola"))

    st.define("Vacio")
    print("Vacio devuelve valor:", st.lookup("Vacio"))

    st.dump()

    return 0

if __name__ == '__main__':
    main()
