            .org    0xc200

backlabel   .equ    0xc200
RESET
            rrc     R4
            rrc     25(R4)
            
fwdlabel    .equ    $
            .end