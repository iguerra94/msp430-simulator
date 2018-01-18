#!/usr/bin/env python3

import pdb
from parser import Parser, Token, ParserException
from symbol_table import Symbol_table, SymtableException
from cpu import CPU
from memory import MemoryException
import sys

class Opcodes():
    SINGLE, SOURCE, DEST, JUMP, BR = range(5)
    OPC_TABLE = {
        'nop':      (0x0000, ()),
        'reti':     (0x1300, ()),

        'rrc':      (0x1000, (SINGLE, )),
        'rrc.b':    (0x1040, (SINGLE, )),
        'rrc.w':    (0x1000, (SINGLE, )),
        'swpb':     (0x1080, (SINGLE, )),
        'rra':      (0x1100, (SINGLE, )),
        'rra.b':    (0x1140, (SINGLE, )),
        'rra.w':    (0x1100, (SINGLE, )),
        'sxt':      (0x1180, (SINGLE, )),
        'push':     (0x1200, (SINGLE, )),
        'push.b':   (0x1240, (SINGLE, )),
        'push.w':   (0x1200, (SINGLE, )),
        'call':     (0x1280, (SINGLE, )),

        'jnz':      (0x2000, (JUMP, )),
        'jne':      (0x2000, (JUMP, )),
        'jz' :      (0x2400, (JUMP, )),
        'jeq':      (0x2400, (JUMP, )),
        'jnc':      (0x2800, (JUMP, )),
        'jlo':      (0x2800, (JUMP, )),
        'jc' :      (0x2c00, (JUMP, )),
        'jhs':      (0x2c00, (JUMP, )),
        'jn' :      (0x3000, (JUMP, )),
        'jge':      (0x3400, (JUMP, )),
        'jl' :      (0x3800, (JUMP, )),
        'jmp':      (0x3c00, (JUMP, )),

        'br':       (0x4000, (BR, )),

        'mov':      (0x4000, (SOURCE, DEST)),
        'mov.b':    (0x4040, (SOURCE, DEST)),
        'mov.w':    (0x4000, (SOURCE, DEST)),
        'add':      (0x5000, (SOURCE, DEST)),
        'add.b':    (0x5040, (SOURCE, DEST)),
        'add.w':    (0x5000, (SOURCE, DEST)),
        'addc':     (0x6000, (SOURCE, DEST)),
        'addc.b':   (0x6040, (SOURCE, DEST)),
        'addc.w':   (0x6000, (SOURCE, DEST)),
        'subc':     (0x7000, (SOURCE, DEST)),
        'subc.b':   (0x7040, (SOURCE, DEST)),
        'subc.w':   (0x7000, (SOURCE, DEST)),
        'sub':      (0x8000, (SOURCE, DEST)),
        'sub.b':    (0x8040, (SOURCE, DEST)),
        'sub.w':    (0x8000, (SOURCE, DEST)),
        'cmp':      (0x9000, (SOURCE, DEST)),
        'cmp.b':    (0x9040, (SOURCE, DEST)),
        'cmp.w':    (0x9000, (SOURCE, DEST)),
        'dadd':     (0xa000, (SOURCE, DEST)),
        'dadd.b':   (0xa040, (SOURCE, DEST)),
        'dadd.w':   (0xa000, (SOURCE, DEST)),
        'bit':      (0xb000, (SOURCE, DEST)),
        'bit.b':    (0xb040, (SOURCE, DEST)),
        'bit.w':    (0xb000, (SOURCE, DEST)),
        'bic':      (0xc000, (SOURCE, DEST)),
        'bic.b':    (0xc040, (SOURCE, DEST)),
        'bic.w':    (0xc000, (SOURCE, DEST)),
        'bis':      (0xd000, (SOURCE, DEST)),
        'bis.b':    (0xd040, (SOURCE, DEST)),
        'bis.w':    (0xd000, (SOURCE, DEST)),
        'xor':      (0xe000, (SOURCE, DEST)),
        'xor.b':    (0xe040, (SOURCE, DEST)),
        'xor.w':    (0xe000, (SOURCE, DEST)),
        'and':      (0xf000, (SOURCE, DEST)),
        'and.b':    (0xf040, (SOURCE, DEST)),
        'and.w':    (0xf000, (SOURCE, DEST))
    }

    ORG, END, EQU, WORD = range(4)
    PSEUDO_OPC_TABLE = {
        'org':      (ORG, ),
        'end':      (END, ),
        'equ':      (EQU, ),
        'word':     (WORD, ) }


    def __init__(self):
        pass

    def get_operands(self, opcode):
        if opcode in self.OPC_TABLE:
            return self.OPC_TABLE[opcode][1]
        else:
            return None


    def get_opc_base(self, opcode):
        if opcode in self.OPC_TABLE:
            return self.OPC_TABLE[opcode][0]
        else:
            return None


    def get_pseudo_opcode(self, ps_opc):
        if ps_opc in self.PSEUDO_OPC_TABLE:
            return self.PSEUDO_OPC_TABLE[ps_opc]
        else:
            return None


class SyntaxException(Exception): pass


class Syntax_analyser():
    def __init__(self, mem):
        self.parser = Parser()
        self.table = Opcodes()
        self.regnames = {"r%d" % i: i for i in range(16)}   # Registros r0..r15
        self.regnames['pc'] = 0
        self.regnames['st'] = 1
        self.regnames['cg1'] = 2
        self.regnames['cg2'] = 3
        self.mem = mem
        self.symtable = Symbol_table()
        self.pc = 0


    def save_opcode(self, words):
        for w in words:
            self.mem.store_word_at(self.pc, w)
            self.pc += 2


    def is_register(self, s):
        return s.lower() in self.regnames


    def reg_nr(self, s):
        return self.regnames[s.lower()]


    def at_line_end(self, token):
        return token.is_a(Token.EOL) or token.is_a(Token.SYMBOL, ';')


    def analyse_jump(self, tokens, base):
        token = tokens.next_token()
        if token.is_not_a(Token.BLANK):
            raise SyntaxException("Esperaba un espacio")

        token = tokens.next_token()
        if token.is_a(Token.IDENT):
            if self.symtable.defined(token.val):
                value = self.symtable.lookup(token.val)
            else:
                self.symtable.define(token.val, None)
                value = None

        elif token.is_a(Token.NUMBER):
            value = Token.val

        else:
            raise SyntaxException("Esperaba un valor")

        if value != None:
            offs = value - (self.pc + 2)
            if offs >= 0x0400 or offs < -0x0400:
                raise SyntaxException("Distancia excesiva para JUMP")

            self.save_opcode([base | (offs & 0x03ff)])


    def analyse(self, line):
        #pdb.set_trace()
        tokens = self.parser.parse(line)

        if tokens.empty():
            return

        token = tokens.next_token()
        if self.at_line_end(token):
            return

        elif token.is_a(Token.IDENT):                   # Es una etiqueta
            self.symtable.define(token.val, self.pc)
            token = tokens.next_token()

        if self.at_line_end(token):
            return

        if token.is_a(Token.BLANK):
            token = tokens.next_token()

            if self.at_line_end(token):
                return

            elif token.is_a(Token.IDENT):               # Tendria que ser opcode
                # Identificar el opcode y ver cuantos operandos
                opds = self.table.get_operands(token.val)
                base = self.table.get_opc_base(token.val)

                if opds == ():                          # Opcode sin operandos
                    base = self.table.get_opc_base(token.val)
                    self.save_opcode([base])

                elif opds == (Opcodes.SINGLE, ):        # Solo operando
                    token = tokens.next_token()
                    if not token.is_a(Token.BLANK):
                        raise SyntaxException("Esperaba un blanco")

                    token = tokens.next_token()
                    if token.is_a(Token.IDENT):
                        if self.is_register(token.val):
                            reg = self.reg_nr(token.val)
                            self.save_opcode([base | reg] )
                        else:
                            raise SyntaxException("No es un registro valido")

                    elif token.is_a(Token.NUMBER):
                        value = token.val
                        token = tokens.next_token()

                        if token.is_a(Token.SYMBOL, '('):
                            token = tokens.next_token()
                            if token.is_a(Token.IDENT):
                                if self.is_register(token.val):
                                    reg = self.reg_nr(token.val)

                                    token = tokens.next_token()
                                    if token.is_a(Token.SYMBOL, ')'):
                                        self.save_opcode([base | reg | 0x0010, value] )
                                    else:
                                        raise SyntaxException("Esperaba un parentesis ")

                                else:
                                    raise SyntaxException("No es un registro valido")

                        else:
                            self.save_opcode([base | reg] )

                    elif token.is_a(Token.SYMBOL, '@'):
                        token = tokens.next_token()
                        if token.is_a(Token.IDENT):
                            if self.is_register(token.val):
                                reg = self.reg_nr(token.val)
                                self.save_opcode([base | reg | 0x0020] )
                        else:
                            raise SyntaxException("Esperaba un registro luego de @")

                elif opds == (Opcodes.JUMP,):
                    self.analyse_jump(tokens, base)

                elif opds == (Opcodes.SOURCE, Opcodes.DEST):    #Doble operando
                    token = tokens.next_token()
                    if not token.is_a(Token.BLANK):
                        raise SyntaxException("Esperaba un blanco")

                    token = tokens.next_token()

                    if token.is_a(Token.IDENT):
                        if self.is_register(token.val):
                            base |= self.reg_nr(token.val) << 8

                            token = tokens.next_token()
                            if token.is_a(Token.SYMBOL, ','):
                                token = tokens.next_token()
                                if token.is_a(Token.BLANK):
                                    token = tokens.next_token()

                                if token.is_a(Token.IDENT) and self.is_register(token.val):
                                    self.save_opcode( [base | self.reg_nr(token.val)] )

                                    token = tokens.next_token()
                                    if token.is_a(Token.EOL):
                                        return

                                elif token.is_a(Token.NUMBER):
                                    value = token.val

                                    token = tokens.next_token()
                                    if token.is_a(Token.SYMBOL, '('):
                                        token = tokens.next_token()
                                        if token.is_a(Token.IDENT):
                                            if self.is_register(token.val):
                                                base |= self.reg_nr(token.val) | 0x0080

                                                token = tokens.next_token()
                                                if token.is_not_a(Token.SYMBOL, ')'):
                                                    raise SyntaxException("Esperaba un parentesis ")
                                                self.save_opcode( [base, value] )

                                            else:
                                                raise SyntaxException("No es un registro valido")
                                        else:
                                            raise SyntaxException("No es un registro valido")

                                    else:
                                        raise SyntaxException("Esperaba un parentesis ")


                                else:
                                    raise SyntaxException("No es un registro valido")

                        else:
                            raise SyntaxException("No es un registro valido")

                    elif token.is_a(Token.NUMBER):
                        value = token.val

                        token = tokens.next_token()
                        if token.is_a(Token.SYMBOL, '('):
                            token = tokens.next_token()
                            if token.is_a(Token.IDENT):
                                if self.is_register(token.val):
                                    base |= self.reg_nr(token.val) << 8 | 0x0010

                                    token = tokens.next_token()
                                    if token.is_not_a(Token.SYMBOL, ')'):
                                        raise SyntaxException("Esperaba un parentesis ")
                                    token = tokens.next_token()
                                    if  token.is_not_a(Token.SYMBOL, ','):
                                        raise SyntaxException("Esperaba una ,")
                                    token = tokens.next_token()

                                    if token.is_a(Token.BLANK):
                                        token = tokens.next_token()

                                    if token.is_a(Token.SYMBOL,'&'):
                                        token = tokens.next_token()
                                        if token.is_not_a(Token.NUMBER):
                                            raise SyntaxException("Esperaba un numero luego de &")

                                        self.save_opcode( [base | 0x0002, token.val] )

                                    elif token.is_a(Token.NUMBER):
                                        value = token.val

                                        token = tokens.next_token()
                                        if token.is_a(Token.SYMBOL, '('):
                                            token = tokens.next_token()
                                            if token.is_a(Token.IDENT):
                                                if self.is_register(token.val):
                                                    base |= self.reg_nr(token.val) | 0x0080

                                                    token = tokens.next_token()
                                                    if token.is_not_a(Token.SYMBOL, ')'):
                                                        raise SyntaxException("Esperaba un parentesis ")
                                                    self.save_opcode( [base, value] )

                                                else:
                                                    raise SyntaxException("No es un registro valido")

                                    elif token.is_a(Token.IDENT) and self.is_register(token.val):
                                        base |= self.reg_nr(token.val)
                                        self.save_opcode( [base, value] )
                                    else:
                                        raise SyntaxException("Esperaba un registro")


                        elif token.is_a(Token.SYMBOL, ','):
                            token = tokens.next_token()
                            if token.is_a(Token.BLANK):
                                token = tokens.next_token()

                            if token.is_a(Token.NUMBER):
                                value2 = token.val

                                token = tokens.next_token()
                                if token.is_a(Token.SYMBOL, '('):
                                    token = tokens.next_token()
                                    if token.is_a(Token.IDENT):
                                        if self.is_register(token.val):
                                            base |= self.reg_nr(token.val) | 0x0080

                                            token = tokens.next_token()
                                            if token.is_not_a(Token.SYMBOL, ')'):
                                                raise SyntaxException("Esperaba un parentesis ")
                                            self.save_opcode( [base, value, value2] )

                                        else:
                                            raise SyntaxException("No es un registro valido")

                            elif token.is_a(Token.IDENT) and self.is_register(token.val):
                                self.save_opcode( [base, value] )
                                token = tokens.next_token()
                                if token.is_a(Token.EOL):
                                    return

                            else:
                                raise SyntaxException("No es un registro valido")

                    elif token.is_a(Token.SYMBOL, '@'):
                        token = tokens.next_token()
                        if token.is_a(Token.IDENT):
                            if self.is_register(token.val):
                                value = self.reg_nr(token.val)
                                token = tokens.next_token()
                                if token.is_a(Token.SYMBOL, '+'):
                                    base |= value << 8 | 0x0030
                                    token = tokens.next_token()
                                else:
                                    base |= value << 8 | 0x0020
                                if  token.is_not_a(Token.SYMBOL, ','):
                                    raise SyntaxException("Esperaba una ,")
                                token = tokens.next_token()

                                if token.is_a(Token.BLANK):
                                    token = tokens.next_token()

                                if token.is_a(Token.SYMBOL,'&'):
                                    token = tokens.next_token()
                                    if token.is_not_a(Token.NUMBER):
                                        raise SyntaxException("Esperaba un numero luego de &")

                                    self.save_opcode( [base | 0x0002, token.val] )

                                elif token.is_a(Token.NUMBER):
                                    value = token.val

                                    token = tokens.next_token()
                                    if token.is_a(Token.SYMBOL, '('):
                                        token = tokens.next_token()
                                        if token.is_a(Token.IDENT):
                                            if self.is_register(token.val):
                                                base |= self.reg_nr(token.val) | 0x0080

                                                token = tokens.next_token()
                                                if token.is_not_a(Token.SYMBOL, ')'):
                                                    raise SyntaxException("Esperaba un parentesis ")
                                                self.save_opcode( [base, value] )

                                            else:
                                                raise SyntaxException("No es un registro valido")

                                elif token.is_a(Token.IDENT) and self.is_register(token.val):
                                    base |= self.reg_nr(token.val)
                                    self.save_opcode( [base, value] )
                                else:
                                    raise SyntaxException("Esperaba un registro")



                        else:
                            raise SyntaxException("Esperaba un numero luego de @")

            elif token.is_a(Token.SYMBOL, '.'):
                token = tokens.next_token()
                if not token.is_a(Token.IDENT):
                    raise SyntaxException("Esperaba un identificador despues de .")

                else:
                    opds = self.table.get_pseudo_opcode(token.val)
                    if opds == None:
                        raise SyntaxException("Seudo-opcode no encontrado")

                    if opds[0] == Opcodes.ORG:
                        token = tokens.next_token()
                        if token.is_not_a(Token.BLANK):
                            raise SyntaxException("Esperaba un blanco")

                        token = tokens.next_token()
                        if token.is_not_a(Token.NUMBER):
                            raise SyntaxException("Esperaba un número")

                        self.pc = token.val

                    elif opds[0] == Opcodes.EQU:
                        token1 = tokens.tokens[0]
                        if token1.is_not_a(Token.IDENT):
                            raise SyntaxException(".equ necesita una etiqueta")

                        if tokens.next_token().is_not_a(Token.BLANK):
                            raise SyntaxException("Esperaba un blanco")

                        token = tokens.next_token()
                        if token.is_a(Token.SYMBOL, '$'):
                            value = self.pc
                        elif token.is_a(Token.NUMBER):
                            value = token.val
                        else:
                            raise SyntaxException("Esperaba un número")

                        self.symtable.define(token1.val, value, equ = True)

                    elif opds[0] == Opcodes.WORD:
                        token = tokens.next_token()
                        if token.is_not_a(Token.BLANK):
                            raise SyntaxException("Esperaba un blanco")

                        token = tokens.next_token()
                        while True:
                            if token.is_a(Token.NUMBER):
                                print(token)
                                self.save_opcode([token.val])

                            print(token)
                            token = tokens.next_token()
                            if token.is_not_a(Token.SYMBOL, ','):
                                break

                            token = tokens.next_token()
                            if token.is_a(Token.BLANK):
                                token = tokens.next_token()

                    elif opds[0] == Opcodes.END:
                        return Opcodes.END

                    else:
                        raise SyntaxException("Seudo-opcode no reconocido")


def test_line(an, linenr, line):
    print("{:5d} {:30s}\nTesting: ".format(linenr, line), end = '')

    try:
        ret_code = an.analyse(line)
        print("Ok")

    except SyntaxException:
        print("Error de sintaxis en línea {:d}".format(linenr))

    except ParserException:
        print("Error del parser en línea {:d}".format(linenr))

    except SymtableException:
        print("Error en la tabla de símbolos en línea {:d}".format(linenr))

    except MemoryException:
        print("Error de memoria en línea {:d}".format(linenr))
    except:         # Ninguna de las capturas anteriores
        print("Excepción no reconocida", sys.exc_info()[0])

    finally:
        return

    return ret_code


SRC_FILE = "main.asm" # "source1.asm"

def main():
    cpu = CPU()
    syntax = Syntax_analyser(cpu.ROM)

    with open(SRC_FILE, "r") as srcf:
        for linenr, line in enumerate(srcf):
            ret_code = test_line(syntax, linenr+1, line.rstrip('\n'))
            if ret_code == Opcodes.END:
                break

    syntax.symtable.dump()
    print(syntax.mem.dump(0xc200, 200))
    cpu.ROM.store_word_at(0xfffe, syntax.mem.mem_start)
    print(syntax.mem.dump(0xffe0, 32))
    syntax.mem.store_to_intel("analyser_test.hex")


if __name__ == '__main__':
    main()
