# RRC INSTRUCTION

def simulate_rrc_instruction(toplevel, regnr, opcode):

    # Hacer la operación de desplazamiento
    toplevel.regs.set(regnr, toplevel.regs.get(regnr) >> 1)

    # Mover el bit 0 del registro al CY
    toplevel.regs.set_SR(toplevel.regs.get(regnr, 0), 'C')

    # Acordarse del estado del CY en ST
    cy = toplevel.regs.get_SR('C')

    # y setear el bit mas significativo con la memoria
    if toplevel.opc_Byte(opcode):
        toplevel.regs.set(regnr, cy, 7)
        toplevel.regs.clear_upper(regnr)                    # Cada operacion de byte borra bits 8-15
    else:
        toplevel.regs.set(regnr, cy, 15)

    # Ajustar los otros bits del status
    toplevel.regs.set_SR('V', False)                        # Siempre a 0
    toplevel.regs.set_SR('Z', toplevel.regs.get(regnr) == 0)    # Según valor registro
    toplevel.regs.set_SR('N', cy)                           # Mismo estado que Carry

# RRA INSTRUCTION

def simulate_rra_instruction(toplevel, regnr, opcode):
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

# PUSH INSTRUCTION

def simulate_push_instruction(toplevel, regnr, opcode):
    sp = self.regs.get(1) - 0x0002
    self.regs.set(1, sp)

    if self.opc_Byte(opcode):
        self.regs.clear_upper(regnr)                    # Cada operacion de byte borra bits 8-15

    self.mem.store_word_at(sp, self.regs.get(regnr))

# SWPB INSTRUCTION

def simulate_swpb_instruction(toplevel, regnr):
    lb = toplevel.regs.get(regnr) & 0x00ff
    hb = toplevel.regs.get(regnr) >> 8
    updated_reg = "0x{:02x}{:02x}".format(lb, hb) # nuevo valor del regnr, con los bytes intercambiados
    toplevel.regs.set(regnr, int(updated_reg, 16) & 0xffff)

# SXT INSTRUCTION

def simulate_sxt_instruction(toplevel, regnr, is_register_mode = False):
    sb_lb = toplevel.regs.get(regnr) & 0x0080 # extraigo el sign bit del low byte

    if is_register_mode:
        for pos in range(8,20,1):
            toplevel.regs.set(regnr, sb_lb, pos) # Seteo cada posicion desde bit 8.. 19 con el bit que estaba en sb_lb
    else:
        for pos in range(8,16,1):
            self.regs.set(regnr, sb_lb, pos) # Seteo cada posicion desde bit 8.. 15 con el bit que estaba en sb_lb

    # Ajustar los otros bits del status
    toplevel.regs.set_SR('Z', toplevel.regs.get(regnr) == 0)    # Según valor registro
    toplevel.regs.set_SR('C', toplevel.regs.get(regnr) != 0)
    toplevel.regs.set_SR('V', False)                        # Siempre a 0

    # Acordarse del estado del CY en ST
    cy = toplevel.regs.get_SR('C')

    toplevel.regs.set_SR('N', cy)                           # Mismo estado que Carry

# CALL INSTRUCTION

def simulate_call_instruction(toplevel, regnr):
    tmp = toplevel.regs.get(regnr) # guardo en tmp el contenido de regnr

    sp = toplevel.regs.get(1) - 0x0002 # Decremento el registro SP en 2
    toplevel.regs.set(1, sp) # Seteo el nuevo valor de SP

    toplevel.mem.store_word_at(sp, toplevel.regs.get(0) + 0x0002) # Seteo en la direccion que apunta el registro SP el valor de PC + 2
    
    toplevel.regs.set(0, tmp) # Seteo el PC con el valor de tmp, obtenido anteriormente