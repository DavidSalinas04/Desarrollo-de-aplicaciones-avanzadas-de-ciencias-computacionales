from semantic_cube import get_result_type, INT, FLOAT, BOOL, ERROR
from symbols_table import FunctionDirectory, SemanticError


class Stack:
    def __init__(self, nombre: str = 'stack'):
        self.nombre = nombre
        self._data: list = []

    def push(self, item):
        self._data.append(item)

    def pop(self):
        if not self._data:
            raise IndexError(f"pop() en pila vacia: {self.nombre}")
        return self._data.pop()

    def top(self):
        if not self._data:
            return None
        return self._data[-1]

    def is_empty(self) -> bool:
        return len(self._data) == 0

    def size(self) -> int:
        return len(self._data)

    def __repr__(self):
        return f"{self.nombre}={self._data}"


class Queue:
    def __init__(self, nombre: str = 'queue'):
        self.nombre = nombre
        self._data: list = []

    def enqueue(self, item):
        self._data.append(item)

    def get(self, idx: int):
        return self._data[idx]

    def set(self, idx: int, item):
        self._data[idx] = item

    def size(self) -> int:
        return len(self._data)

    def items(self) -> list:
        return list(self._data)

    def __iter__(self):
        return iter(self._data)

JERARQUIA = {
    '(':  0,
    '=':  1,
    '>':  2, '<': 2, '==': 2, '!=': 2,
    '+':  3, '-': 3,
    '*':  4, '/': 4,
}


class QuadrupleGenerator:
    def __init__(self):
        self.pila_operandos = Stack('PilaOperandos')
        self.pila_operadores = Stack('PilaOperadores')
        self.pila_tipos = Stack('PilaTipos')
        self.pila_saltos = Stack('PilaSaltos')
        self.cuadruplos = Queue('Cuadruplos')

        self.func_dir: FunctionDirectory | None = None
        self.current_scope: str | None = None

        self._temp_counter = 0

        self.errors: list[str] = []

    def _new_temp(self) -> str:
        self._temp_counter += 1
        return f"t{self._temp_counter}"

    def _emit(self, op: str, arg1, arg2, res) -> int:
        self.cuadruplos.enqueue((op, arg1, arg2, res))
        return self.cuadruplos.size() - 1

    def _patch(self, idx: int, destino: int):
        op, a1, a2, _ = self.cuadruplos.get(idx)
        self.cuadruplos.set(idx, (op, a1, a2, destino))

    def _report(self, msg: str):
        full = f"[SemanticError] {msg}"
        self.errors.append(full)
        print(full)

    
    def generar(self, ast) -> Queue:
        if ast is None or ast[0] != 'programa':
            self._report("AST invalido o programa nulo")
            return self.cuadruplos

        _, nombre, vars_opt, funcs, cuerpo = ast
        self.func_dir = FunctionDirectory(nombre)

        if vars_opt:
            self._registrar_vars(vars_opt, scope=None)

        for func in funcs:
            self._registrar_func(func)

        self.current_scope = None
        self._gen_cuerpo(cuerpo)

        self._emit('END', None, None, None)

        return self.cuadruplos

    
    def _registrar_vars(self, vars_node, scope):
        if vars_node is None:
            return
        decl = vars_node[1]
        self._registrar_decl(decl, scope)

    def _registrar_decl(self, decl, scope):
        if decl is None:
            return
        ids = decl[1]
        tipo = decl[2]
        resto = decl[3] if len(decl) > 3 else None
        for var in ids:
            try:
                if scope is None:
                    self.func_dir.add_global_var(var, tipo)
                else:
                    self.func_dir.add_local_var(scope, var, tipo)
            except SemanticError as e:
                self._report(str(e))
        if resto:
            self._registrar_decl(resto, scope)

    def _registrar_func(self, func_node):
        _, tipo_ret, nombre, params, vars_opt, _cuerpo = func_node
        try:
            self.func_dir.add_function(nombre, tipo_ret, params)
        except SemanticError as e:
            self._report(str(e))
            return
        if vars_opt:
            self._registrar_vars(vars_opt, scope=nombre)

    
    def _gen_cuerpo(self, cuerpo):
        if cuerpo is None:
            return
        _, estatutos = cuerpo
        for est in estatutos:
            self._gen_estatuto(est)

    def _gen_estatuto(self, est):
        if est is None:
            return
        kind = est[0]
        if kind == 'asigna':
            self._gen_asigna(est)
        elif kind == 'imprime':
            self._gen_imprime(est)
        elif kind == 'condicion':
            self._gen_condicion(est)
        elif kind == 'ciclo':
            self._gen_ciclo(est)
        elif kind == 'llamada':
            self._gen_llamada_min(est)
        elif kind == 'bloque':
            for s in est[1]:
                self._gen_estatuto(s)

    def _gen_asigna(self, est):
        _, var, expr = est
        var_tipo = self.func_dir.get_var_type(var, self.current_scope)
        if var_tipo is None:
            self._report(f"Variable no declarada: '{var}'")
            return

        self._gen_expresion(expr)
        if self.pila_operandos.is_empty():
            return

        valor = self.pila_operandos.pop()
        tipo_val = self.pila_tipos.pop()
        if get_result_type(var_tipo, tipo_val, '=') == ERROR and \
           not self._compatible(var_tipo, tipo_val):
            self._report(
                f"Tipo incompatible en asignacion a '{var}': "
                f"se esperaba '{var_tipo}', se recibio '{tipo_val}'"
            )
            return
        self._emit('=', valor, None, var)

    def _compatible(self, esperado: str, recibido: str) -> bool:
        if esperado == recibido:
            return True
        if esperado in (INT, FLOAT) and recibido in (INT, FLOAT):
            return True
        return False

    
    def _gen_imprime(self, est):
        _, items = est
        for item in items:
            if isinstance(item, tuple) and item[0] == 'letrero':
                self._emit('print', None, None, item[1])
            else:
                self._gen_expresion(item)
                if self.pila_operandos.is_empty():
                    continue
                val = self.pila_operandos.pop()
                self.pila_tipos.pop()
                self._emit('print', None, None, val)

    
    def _gen_condicion(self, est):
        _, expr, cuerpo_true, cuerpo_false = est

        self._gen_expresion(expr)
        if self.pila_operandos.is_empty():
            return
        cond = self.pila_operandos.pop()
        t_cond = self.pila_tipos.pop()
        if t_cond != BOOL:
            self._report(
                f"La condicion del 'si' debe ser booleana, se obtuvo '{t_cond}'"
            )
            return

        idx_gotof = self._emit('GOTOF', cond, None, None)
        self.pila_saltos.push(idx_gotof)

        
        self._gen_cuerpo(cuerpo_true)

        if cuerpo_false is not None:
            idx_goto = self._emit('GOTO', None, None, None)
            falso = self.pila_saltos.pop()
            self._patch(falso, self.cuadruplos.size())
            self.pila_saltos.push(idx_goto)

            self._gen_cuerpo(cuerpo_false)

        pend = self.pila_saltos.pop()
        self._patch(pend, self.cuadruplos.size())

    
    def _gen_ciclo(self, est):
        _, expr, cuerpo = est

        retorno = self.cuadruplos.size()
        self.pila_saltos.push(retorno)

        self._gen_expresion(expr)
        if self.pila_operandos.is_empty():
            self.pila_saltos.pop()  # cleanup
            return
        cond = self.pila_operandos.pop()
        t_cond = self.pila_tipos.pop()
        if t_cond != BOOL:
            self._report(
                f"La condicion del 'mientras' debe ser booleana, se obtuvo '{t_cond}'"
            )
            self.pila_saltos.pop()
            return

        idx_gotof = self._emit('GOTOF', cond, None, None)
        self.pila_saltos.push(idx_gotof)

        self._gen_cuerpo(cuerpo)

        falso = self.pila_saltos.pop()
        ret = self.pila_saltos.pop()
        self._emit('GOTO', None, None, ret)
        self._patch(falso, self.cuadruplos.size())

    def _gen_llamada_min(self, est):
        _, nombre, args = est
        if not self.func_dir.exists_function(nombre):
            self._report(f"Funcion no declarada: '{nombre}'")
            return
        for a in args:
            self._gen_expresion(a)
            if not self.pila_operandos.is_empty():
                self.pila_operandos.pop()
                self.pila_tipos.pop()
        self._emit('CALL', nombre, len(args), None)

    
    def _gen_expresion(self, node):
        if node is None:
            return
        kind = node[0]

        if kind == 'cte':
            val = node[1]
            tipo = INT if isinstance(val, int) else FLOAT
            self.pila_operandos.push(val)
            self.pila_tipos.push(tipo)
            return

        if kind == 'id':
            name = node[1]
            tipo = self.func_dir.get_var_type(name, self.current_scope)
            if tipo is None:
                self._report(f"Variable no declarada: '{name}'")
                self.pila_operandos.push(name)
                self.pila_tipos.push(ERROR)
                return
            self.pila_operandos.push(name)
            self.pila_tipos.push(tipo)
            return

        if kind == 'neg':
            self._gen_expresion(node[1])
            if self.pila_operandos.is_empty():
                return
            op = self.pila_operandos.pop()
            t = self.pila_tipos.pop()
            temp = self._new_temp()
            self._emit('NEG', op, None, temp)
            self.pila_operandos.push(temp)
            self.pila_tipos.push(t)
            return
        if kind == 'pos':
            self._gen_expresion(node[1])
            return

        if kind == 'llamada':
            self._gen_llamada_min(node)
            nombre = node[1]
            info = self.func_dir.lookup_function(nombre)
            if info is not None:
                tipo_ret = info['tipo']
                if tipo_ret in (INT, FLOAT):
                    temp = self._new_temp()
                    self._emit('RET_VAL', nombre, None, temp)
                    self.pila_operandos.push(temp)
                    self.pila_tipos.push(tipo_ret)
            return

        if kind in ('+', '-', '*', '/', '>', '<', '==', '!='):
            self._gen_expresion(node[1])
            self.pila_operadores.push(kind)
            self._gen_expresion(node[2])
            if self.pila_operadores.is_empty():
                return
            op = self.pila_operadores.pop()
            if self.pila_operandos.size() < 2:
                return
            der = self.pila_operandos.pop()
            izq = self.pila_operandos.pop()
            t_der = self.pila_tipos.pop()
            t_izq = self.pila_tipos.pop()
            t_res = get_result_type(t_izq, t_der, op)
            if t_res == ERROR:
                self._report(
                    f"Operacion invalida: '{t_izq}' {op} '{t_der}'"
                )
                temp = self._new_temp()
                self._emit(op, izq, der, temp)
                self.pila_operandos.push(temp)
                self.pila_tipos.push(ERROR)
                return
            temp = self._new_temp()
            self._emit(op, izq, der, temp)
            self.pila_operandos.push(temp)
            self.pila_tipos.push(t_res)
            return

    def imprimir_cuadruplos(self):
        print(f"\n=== Cuadruplos generados ({self.cuadruplos.size()}) ===")
        print(f"{'#':>3}  {'OP':<8} {'ARG1':<10} {'ARG2':<10} {'RES':<10}")
        print("-" * 50)
        for i, q in enumerate(self.cuadruplos.items()):
            op, a1, a2, r = q
            print(f"{i:>3}  {str(op):<8} {str(a1):<10} {str(a2):<10} {str(r):<10}")
        print()



def compile_to_quads(source: str) -> QuadrupleGenerator:
    """Parsea + genera cuadruplos. Devuelve el generador con todo dentro."""
    from parser import parse
    ast = parse(source)
    if ast is None:
        print("[Error] El parser no pudo procesar el codigo")
        return None
    gen = QuadrupleGenerator()
    gen.generar(ast)
    return gen