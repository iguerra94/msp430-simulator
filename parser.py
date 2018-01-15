#!/usr/bin/env python3

import pdb
import re

class ParserException(Exception): pass

class Token():
    IDENT, BLANK, NUMBER, SYMBOL, EOL, EOF = range(6)
    name = ("Identifier", "Blank", "Number", "Symbol", "EOL", "EOF")

    def __init__(self, kind, val = None):
        self.kind = kind
        self.val = val

    def __str__(self):
        if isinstance(self.val, str):
            return "{:s}: '{:s}'".format(self.name[self.kind],  str(self.val))
        else:
            return "{:s}: {:s}".format(self.name[self.kind], str(self.val))


    def is_a(self, kind, spec = None):
        if spec == None:
            return self.kind == kind
        else:
            return (self.kind == kind) and (self.val == spec)


    def is_not_a(self, kind, spec = None):
        if spec == None:
            return self.kind != kind
        else:
            return (self.kind != kind) or (self.val != spec)



class TokenList():
    def __init__(self):
        self.tokens = []
        self.ptoken = 0


    def __str__(self):
        return ', '.join([str(token) for token in self.tokens])


    def append(self, token):
        self.tokens.append(token)


    def empty(self):
        return len(self.tokens) == 0


    def next_token(self):
        if self.ptoken >= len(self.tokens):
            return None

        tkn = self.tokens[self.ptoken]
        self.ptoken += 1
        return tkn



class Parser():

    def __init__(self):
        pass


    def parse(self, line):
        tokens = TokenList()
        ident = []
        pline = 0

        while True:
            if pline >= len(line):
                break
                
            #print(line[pline])

            if line[pline].isalpha():
                ident = line[pline]
                pline += 1
                while (pline < len(line)):
                    if not line[pline].isalnum() and (line[pline] not in '_.'):
                        break
                    ident += line[pline]
                    pline += 1
                tokens.append( Token(Token.IDENT, ident) )

            elif line[pline] == '0':
                pline += 1
                ident = ""
                if pline >= len(line):
                    raise ParserException("Fin de linea inesperado")

                if line[pline] in 'xX':         # Numero hexadecimal?
                    pline += 1
                    if pline >= len(line):
                        raise ParserException("Fin de linea inesperado")

                    while pline < len(line):
                        r = re.match("[0-9a-fA-F]", line[pline])
                        if r != None:
                            ident += line[pline]
                        else:
                            break
                        pline += 1

                    tokens.append( Token(Token.NUMBER, int(ident, 16)) )

                elif line[pline] in 'bB':       # Numero binario?
                    pline += 1
                    if pline >= len(line):
                        raise ParserException("Fin de linea inesperado")

                    while pline < len(line):
                        if line[pline] in '01':
                            ident += line[pline]
                        else:
                            break
                        pline += 1

                    tokens.append( Token(Token.NUMBER, int(ident, 2)) )

                elif line[pline] in 'qQ':       # Numero octal?
                    pline += 1
                    if pline >= len(line):
                        raise ParserException("Fin de linea inesperado")

                    while pline < len(line):
                        r = re.match("[0-7]", line[pline])
                        if r != None:
                            ident += line[pline]
                        else:
                            break
                        pline += 1

                    tokens.append( Token(Token.NUMBER, int(ident, 8)) )

            elif line[pline].isdigit():
                ident = line[pline]
                pline += 1
                while (pline < len(line)):
                    if not line[pline].isdigit():
                        break
                    ident += line[pline]
                    pline += 1
                tokens.append( Token(Token.NUMBER, int(ident)) )

            elif line[pline] in ".,=+-():;*/#&$@\"":
                tokens.append( Token(Token.SYMBOL, line[pline]) )
                if line[pline] == ';':
                    break
                pline += 1

            elif line[pline].isspace():
                pline += 1
                while (pline < len(line)):
                    if not line[pline].isspace():
                        break
                    pline += 1
                tokens.append( Token(Token.BLANK) )

        tokens.append( Token(Token.EOL) )
        return tokens



def main():
    p = Parser()

    #~ pdb.set_trace()
    print(p.parse("		; mov	r5, uno	INVALID"))

    print(p.parse(''))
    #pdb.set_trace()
    print(p.parse('identificador'))
    # Prueba de espacio en blanco
    print(p.parse('   \t'))
    print(p.parse('identi    ficador'))
    # Prueba de deteccion de numeros decimales
    print(p.parse('identi    ficador 123'))

    # Pruebas con simbolos
    print(p.parse('identi, ficador'))

    tokenlist = p.parse(',')
    print("Tokens: {:s}".format(str(tokenlist)))
    token = tokenlist.next_token()
    print(token.is_a(Token.SYMBOL, ','))
    print(token.is_a(Token.SYMBOL, '+'))

    # Prueba de numeros hexadecimales
    print(p.parse('identi    ficador 0x123'))
    print(p.parse('iden 0x123a ti    ficador'))

    # Prueba de numeros binarios
    print(p.parse('ident 0b10001000a ti   0B11111111 ficador'))

    # Prueba de numeros octales
    print(p.parse('iden 0q123a ti  0q377  ficador'))
    print(p.parse('identi    rrc.b'))

if __name__ == '__main__':
    main()
