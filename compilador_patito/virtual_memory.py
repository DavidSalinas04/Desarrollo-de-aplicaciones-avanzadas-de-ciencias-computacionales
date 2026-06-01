from semantic_cube import INT, FLOAT, BOOL

STRING = 'string'

SEGMENT_SIZE = 1000

BASES = {
    ('global', INT):    1000,
    ('global', FLOAT):  2000,
    ('local',  INT):    3000,
    ('local',  FLOAT):  4000,
    ('temp',   INT):    5000,
    ('temp',   FLOAT):  6000,
    ('temp',   BOOL):   7000,
    ('const',  INT):    8000,
    ('const',  FLOAT):  9000,
    ('const',  STRING): 10000,
}


def rango(segmento: str, tipo: str) -> tuple[int, int]:
    base = BASES[(segmento, tipo)]
    return (base, base + SEGMENT_SIZE - 1)


class VirtualMemory:
    def __init__(self):
        self.counters = {key: base for key, base in BASES.items()}
        self.const_to_addr: dict = {}    
        self.addr_to_const: dict = {}    
        self.addr_meta: dict = {}

    def reset_locals(self):
        self.counters[('local', INT)]   = BASES[('local', INT)]
        self.counters[('local', FLOAT)] = BASES[('local', FLOAT)]

    def reset_temps(self):
        self.counters[('temp', INT)]   = BASES[('temp', INT)]
        self.counters[('temp', FLOAT)] = BASES[('temp', FLOAT)]
        self.counters[('temp', BOOL)]  = BASES[('temp', BOOL)]


    def _alloc(self, segmento: str, tipo: str) -> int:
        key = (segmento, tipo)
        if key not in self.counters:
            raise ValueError(f"Segmento/tipo invalido: {segmento}/{tipo}")
        addr = self.counters[key]
        base = BASES[key]
        if addr >= base + SEGMENT_SIZE:
            raise MemoryError(
                f"Segmento agotado: {segmento}/{tipo} (limite {SEGMENT_SIZE})"
            )
        self.counters[key] += 1
        self.addr_meta[addr] = (segmento, tipo)
        return addr

    def alloc_global(self, tipo: str) -> int:
        return self._alloc('global', tipo)

    def alloc_local(self, tipo: str) -> int:
        return self._alloc('local', tipo)

    def alloc_temp(self, tipo: str) -> int:
        return self._alloc('temp', tipo)

    def alloc_const(self, valor, tipo: str) -> int:
        key = (tipo, valor)
        if key in self.const_to_addr:
            return self.const_to_addr[key]
        addr = self._alloc('const', tipo)
        self.const_to_addr[key] = addr
        self.addr_to_const[addr] = valor
        return addr


    def count(self, segmento: str, tipo: str) -> int:
        return self.counters[(segmento, tipo)] - BASES[(segmento, tipo)]

    def segment_of(self, addr: int) -> tuple[str, str]:
        return self.addr_meta.get(addr, (None, None))

    def is_address(self, x) -> bool:
        return isinstance(x, int) and x >= BASES[('global', INT)]