"""Códigos de comando: valores de `NumbersAndOperatorsEnum` (CalculatorApp.ViewModel.winmd), que o VM repassa ao
motor sem tradução, salvo as exceções do CalculatorManager (01 §5, §6.4)."""
from enum import IntEnum


class C(IntEnum):
    NEGATE = 80
    CLEAR = 81
    CLEARENTRY = 82
    BACKSPACE = 83
    DECIMAL = 84
    AND = 86
    OR = 87
    XOR = 88
    LSH = 89
    RSH = 90
    DIVIDE = 91
    MULTIPLY = 92
    ADD = 93
    SUBTRACT = 94
    MOD = 95
    YROOT = 96
    POW = 97
    INT = 98
    ROL = 99
    ROR = 100
    NOT = 101
    SIN = 102
    COS = 103
    TAN = 104
    SINH = 105
    COSH = 106
    TANH = 107
    LN = 108
    LOG = 109
    SQRT = 110
    SQR = 111
    CUBE = 112
    FACT = 113
    INVERT = 114
    DMS = 115
    CUBEROOT = 116
    POW10 = 117
    PERCENT = 118
    FTOE = 119
    PI = 120
    EQUALS = 121
    MC = 122
    MR = 123
    MS = 124
    MPLUS = 125
    MMINUS = 126
    EXP = 127
    OPENP = 128
    CLOSEP = 129
    ZERO = 130
    INV = 146          # no motor = INV; na UI o mesmo valor é `Memory` (MS), interceptado pelo VM (01 §6.4)
    STANDARD = 200
    SCIENTIFIC = 201
    INVSIN = 202
    INVCOS = 203
    INVTAN = 204
    EPOWX = 205
    INVSINH = 206
    INVCOSH = 207
    INVTANH = 208
    PROGRAMMER = 209
    HEX = 313
    DEC = 314
    OCT = 315
    BIN = 316
    QWORD = 317
    DWORD = 318
    WORD = 319
    BYTE = 320
    DEG = 321
    RAD = 322
    GRAD = 323
    DEGREES = 324
    SEC = 400
    INVSEC = 401
    CSC = 402
    INVCSC = 403
    COT = 404
    INVCOT = 405
    SECH = 406
    INVSECH = 407
    CSCH = 408
    INVCSCH = 409
    COTH = 410
    INVCOTH = 411
    TWOPOWX = 412
    ABS = 413
    FLOOR = 414
    CEIL = 415
    ROLC = 416
    RORC = 417
    LOGBASEY = 500
    NAND = 501
    NOR = 502
    RSHL = 505
    RAND = 600
    EULER = 601
    BINPOS0 = 700


def digito(n):
    return C.ZERO + n  # 0–9 = 130–139, A–F = 140–145


BINARIOS = set(range(86, 98)) | {500, 501, 502, 505}          # 0x56–0x61 e 500–505 (02d §3.7)
UNARIOS = set(range(98, 119)) | set(range(400, 418)) | {324}  # 0x62–0x76, 400–417, 0x144
UNARIOS_H3 = set(range(98, 119)) | set(range(400, 412)) | {80}  # "último comando unário" de H3/H4 (02b §4.1)
DIGITOS = set(range(130, 146))
BINPOS = set(range(700, 764))

# Precedência (02c §3.11): Or/Xor 0; And/Nand/Nor 1; + − 2; × ÷ Mod Lsh Rsh RshL 3; yroot ^ logᵧx 4
PRECEDENCIA = {C.OR: 0, C.XOR: 0, C.AND: 1, C.NAND: 1, C.NOR: 1, C.ADD: 2, C.SUBTRACT: 2,
               C.MULTIPLY: 3, C.DIVIDE: 3, C.MOD: 3, C.LSH: 3, C.RSH: 3, C.RSHL: 3,
               C.YROOT: 4, C.POW: 4, C.LOGBASEY: 4}

# Inversas: o CalculatorManager manda INV (146) e depois a função direta (01 §6.4)
INVERSAS = {C.INVSIN: C.SIN, C.INVCOS: C.COS, C.INVTAN: C.TAN, C.EPOWX: C.LN,
            C.INVSINH: C.SINH, C.INVCOSH: C.COSH, C.INVTANH: C.TANH,
            C.INVSEC: C.SEC, C.INVCSC: C.CSC, C.INVCOT: C.COT,
            C.INVSECH: C.SECH, C.INVCSCH: C.CSCH, C.INVCOTH: C.COTH}
