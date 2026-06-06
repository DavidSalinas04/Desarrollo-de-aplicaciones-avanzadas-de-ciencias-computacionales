GLOBAL_INI, GLOBAL_FIN = 1000, 2999
LOCAL_INI,  TEMP_FIN   = 3000, 7999
CONST_INI,  CONST_FIN  = 8000, 10999


class Memoria:
    def __init__(self, nombre="memoria"):
        self.nombre = nombre
        self.celdas: dict = {}

    def get(self, direccion):
        return self.celdas.get(direccion)

    def set(self, direccion, valor):
        self.celdas[direccion] = valor

    def tiene(self, direccion) -> bool:
        return direccion in self.celdas

    def __repr__(self):
        cuerpo = ", ".join(f"{d}={v!r}" for d, v in sorted(self.celdas.items()))
        return f"{self.nombre}{{{cuerpo}}}"


class RegistroActivacion(Memoria):
    def __init__(self, nombre_funcion: str):
        super().__init__(f"AR[{nombre_funcion}]")
        self.nombre_funcion = nombre_funcion


class RuntimeErrorPatito(Exception):
    pass


class MaquinaVirtual:
    def __init__(self, codigo: dict):
        self.cuadruplos = codigo['cuadruplos']
        self.global_mem = Memoria("GLOBAL")
        self.const_mem = Memoria("CONST")
        for direccion, valor in codigo.get('constantes', {}).items():
            self.const_mem.set(direccion, valor)
        self.pila_llamadas = [RegistroActivacion("__main__")]
        self.pila_retorno: list[int] = []
        self.ar_pendiente: RegistroActivacion | None = None
        self.ip = 0
        self.salida: list[str] = []

    @property
    def ar_actual(self) -> RegistroActivacion:
        return self.pila_llamadas[-1]

    def _segmento(self, direccion: int) -> Memoria:
        if GLOBAL_INI <= direccion <= GLOBAL_FIN:
            return self.global_mem
        if CONST_INI <= direccion <= CONST_FIN:
            return self.const_mem
        if LOCAL_INI <= direccion <= TEMP_FIN:
            return self.ar_actual
        raise RuntimeErrorPatito(f"Direccion fuera de rango: {direccion}")

    def get(self, direccion):
        if direccion is None:
            return None
        mem = self._segmento(direccion)
        if not mem.tiene(direccion):
            raise RuntimeErrorPatito(
                f"Lectura de direccion no inicializada: {direccion} en {mem.nombre}"
            )
        return mem.get(direccion)

    def set(self, direccion, valor):
        self._segmento(direccion).set(direccion, valor)

    def ejecutar(self, traza=False) -> list:
        n = len(self.cuadruplos)
        pasos = 0
        while 0 <= self.ip < n:
            op, a1, a2, res = self.cuadruplos[self.ip]
            if traza:
                print(f"  ip={self.ip:>3} {op:<8} {a1} {a2} {res}")
            metodo = getattr(self, f"_op_{self._nombre_op(op)}", None)
            if metodo is None:
                raise RuntimeErrorPatito(f"Codigo de operacion desconocido: {op}")
            siguiente = metodo(a1, a2, res)
            self.ip = siguiente if siguiente is not None else self.ip + 1
            pasos += 1
            if pasos > 1_000_000:
                raise RuntimeErrorPatito("Limite de ejecucion excedido (posible ciclo infinito)")
        return self.salida

    @staticmethod
    def _nombre_op(op: str) -> str:
        tabla = {
            '=': 'asigna', '+': 'suma', '-': 'resta', '*': 'mult', '/': 'div',
            '>': 'gt', '<': 'lt', '==': 'eq', '!=': 'neq',
            'NEG': 'neg', 'print': 'print',
            'GOTO': 'goto', 'GOTOF': 'gotof',
            'ERA': 'era', 'PARAM': 'param', 'GOSUB': 'gosub',
            'ENDFUNC': 'endfunc', 'RETURN': 'return', 'END': 'end',
        }
        return tabla[op]

    def _op_asigna(self, a1, a2, res):
        self.set(res, self.get(a1))

    def _op_suma(self, a1, a2, res):
        self.set(res, self.get(a1) + self.get(a2))

    def _op_resta(self, a1, a2, res):
        self.set(res, self.get(a1) - self.get(a2))

    def _op_mult(self, a1, a2, res):
        self.set(res, self.get(a1) * self.get(a2))

    def _op_div(self, a1, a2, res):
        divisor = self.get(a2)
        if divisor == 0:
            raise RuntimeErrorPatito("Division entre cero")
        self.set(res, self.get(a1) / divisor)

    def _op_neg(self, a1, a2, res):
        self.set(res, -self.get(a1))

    def _op_gt(self, a1, a2, res):
        self.set(res, self.get(a1) > self.get(a2))

    def _op_lt(self, a1, a2, res):
        self.set(res, self.get(a1) < self.get(a2))

    def _op_eq(self, a1, a2, res):
        self.set(res, self.get(a1) == self.get(a2))

    def _op_neq(self, a1, a2, res):
        self.set(res, self.get(a1) != self.get(a2))

    def _op_print(self, a1, a2, res):
        valor = self.get(res)
        if isinstance(valor, str) and len(valor) >= 2 and valor[0] == '"' and valor[-1] == '"':
            valor = valor[1:-1]               # quita comillas del letrero
        texto = self._fmt(valor)
        self.salida.append(texto)
        print(texto, end="")

    @staticmethod
    def _fmt(v):
        if isinstance(v, bool):
            return "verdadero" if v else "falso"
        return str(v)

    def _op_goto(self, a1, a2, res):
        return res

    def _op_gotof(self, a1, a2, res):
        if not self.get(a1):
            return res
        return None

    def _op_era(self, a1, a2, res):
        self.ar_pendiente = RegistroActivacion(a1)

    def _op_param(self, a1, a2, res):
        valor = self.get(a1)
        self.ar_pendiente.set(res, valor)

    def _op_gosub(self, a1, a2, res):
        self.pila_retorno.append(self.ip + 1)
        self.pila_llamadas.append(self.ar_pendiente)
        self.ar_pendiente = None
        return res

    def _op_return(self, a1, a2, res):
        valor = self.get(a1)
        self.global_mem.set(res, valor) 
        self.pila_llamadas.pop()
        return self.pila_retorno.pop()

    def _op_endfunc(self, a1, a2, res):
        self.pila_llamadas.pop()
        return self.pila_retorno.pop()

    def _op_end(self, a1, a2, res):
        return len(self.cuadruplos)


def ejecutar_fuente(source: str, traza=False) -> tuple[list, list]:
    from quadruples import compile_to_quads
    gen = compile_to_quads(source)
    if gen is None:
        return [], ["[Error] El parser no pudo procesar el codigo"]
    if gen.errors:
        return [], gen.errors
    mv = MaquinaVirtual(gen.exportar())
    salida = mv.ejecutar(traza=traza)
    return salida, []