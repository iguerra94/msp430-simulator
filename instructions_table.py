class Instructions_table():
    INSTRUCTIONS_TABLE = {
      "Por registro": {
        'RRC':      (0x1000),
        'RRC.b':    (0x1040),
        'SWPB':     (0x1080),
        'RRA':      (0x1100),
        'RRA.b':    (0x1140),
        'SXT':      (0x1180),
        'PUSH':     (0x1200),
        'PUSH.b':   (0x1240),
        'CALL':     (0x1280)
      },
      "Indexado": {
        'RRC':      (0x1010),
        'RRC.b':    (0x1050),
        'SWPB':     (0x1090),
        'RRA':      (0x1110),
        'RRA.b':    (0x1150),
        'SXT':      (0x1190),
        'PUSH':     (0x1210),
        'PUSH.b':   (0x1250),
        'CALL':     (0x1290)
      },
      "Indirecto por registro": {
        'RRC':      (0x1020),
        'RRC.b':    (0x1060),
        'SWPB':     (0x10A0),
        'RRA':      (0x1120),
        'RRA.b':    (0x1160),
        'SXT':      (0x11A0),
        'PUSH':     (0x1220),
        'PUSH.b':   (0x1260),
        'CALL':     (0x12A0)
      },
      "Indirecto autoincrementado": {
        'RRC':      (0x1030),
        'RRC.b':    (0x1070),
        'SWPB':     (0x10B0),
        'RRA':      (0x1130),
        'RRA.b':    (0x1170),
        'SXT':      (0x11B0),
        'PUSH':     (0x1230),
        'PUSH.b':   (0x1270),
        'CALL':     (0x12B0)
      }
    }

    def __init__(self):
        pass

    def get_instruction_opcode(self, addr_mode, instr):
        if instr in self.INSTRUCTIONS_TABLE[addr_mode]:
            return self.INSTRUCTIONS_TABLE[addr_mode][instr]
        else:
            return None