            .org    0xc200

backlabel   .equ    0xc200
RESET
            rrc     R4
            rrc     R5
            
fwdlabel    .equ    $
            .end