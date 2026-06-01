from semantic_cube import get_result_type, INT, FLOAT, BOOL, ERROR
from symbols_table import FunctionDirectory, SemanticError
from virtual_memory import VirtualMemory, STRING


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

MAIN_SCOPE = '__main__'


RET_TIPO = {
    'entero': INT, 'flotante': FLOAT, 'nula': 'nula', 'nil': 'nula',
    INT: INT, FLOAT: FLOAT,
}


def normaliza_tipo_ret(tipo_ret: str) -> str:
    return RET_TIPO.get(tipo_ret, 'nula')


class QuadrupleGenerator:
    def __init__(self):
        self.pila_operandos = Stack('PilaOperandos')   # ahora guarda DIRECCIONES
        self.pila_operadores = Stack('PilaOperadores')
        self.pila_tipos = Stack('PilaTipos')
        self.pila_saltos = Stack('PilaSaltos')
        self.cuadruplos = Queue('Cuadruplos')

        self.func_dir: FunctionDirectory | None = None
        self.current_scope: str | None = None

        # Administrador de memoria virtual
        self.vm = VirtualMemory()

        # Contador global de temporales (etiqueta legible unica t1, t2, ...)
        self._temp_counter = 0

        # --- Mapas para impresion legible (direccion -> nombre) ---
        self.global_display: dict = {}              # globales + slots de retorno
        self.scope_local_display: dict = {}         # scope -> {dir -> nombre} (locales/params/temps)
        self.quad_scope: list = []                  # scope activo al emitir cada cuadruplo
        self.quad_result_label: dict = {}           # idx -> etiqueta legible del campo RES (para PARAM)

        # GOSUB pendientes de backpatch (llamadas a funciones aun sin start_quad)
        self.pending_gosubs: list = []

        self.errors: list[str] = []


    def _cur_scope_label(self) -> str:
        return self.current_scope if self.current_scope is not None else MAIN_SCOPE

    def _local_display_map(self, scope_label: str) -> dict:
        return self.scope_local_display.setdefault(scope_label, {})

    def _alloc_temp(self, tipo: str) -> int:
        seg_tipo = tipo if tipo in (INT, FLOAT, BOOL) else INT
        addr = self.vm.alloc_temp(seg_tipo)
        self._temp_counter += 1
        self._local_display_map(self._cur_scope_label())[addr] = f"t{self._temp_counter}"
        return addr

    def _const_addr(self, valor, tipo: str) -> int:
        return self.vm.alloc_const(valor, tipo)

    def _emit(self, op: str, arg1, arg2, res) -> int:
        self.cuadruplos.enqueue((op, arg1, arg2, res))
        self.quad_scope.append(self._cur_scope_label())
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

        idx_goto_main = self._emit('GOTO', None, None, None)

        if vars_opt:
            self._registrar_vars(vars_opt, scope=None)

        for func in funcs:
            self._registrar_func(func)

        for func in funcs:
            nombre_f = func[2]
            if not self.func_dir.exists_function(nombre_f):
                continue
            self.current_scope = nombre_f
            self.vm.reset_temps()
            self.func_dir.set_start_quad(nombre_f, self.cuadruplos.size())
            self._gen_cuerpo(func[5])
            self.func_dir.set_temp_counts(nombre_f, {
                INT:  self.vm.count('temp', INT),
                FLOAT: self.vm.count('temp', FLOAT),
                BOOL: self.vm.count('temp', BOOL),
            })
            self._emit('ENDFUNC', None, None, None)

        self._patch(idx_goto_main, self.cuadruplos.size())

        self.current_scope = None
        self.vm.reset_temps()
        self._gen_cuerpo(cuerpo)

        self._emit('END', None, None, None)

        for idx, fname in self.pending_gosubs:
            info = self.func_dir.lookup_function(fname)
            if info is not None and info['start_quad'] is not None:
                self._patch(idx, info['start_quad'])

        return self.cuadruplos


    def _registrar_vars(self, vars_node, scope):
        if vars_node is None:
            return
        self._registrar_decl(vars_node[1], scope)

    def _registrar_decl(self, decl, scope):
        if decl is None:
            return
        ids = decl[1]
        tipo = decl[2]
        resto = decl[3] if len(decl) > 3 else None
        for var in ids:
            try:
                if scope is None:
                    addr = self.vm.alloc_global(tipo)
                    self.func_dir.add_global_var(var, tipo, addr)
                    self.global_display[addr] = var
                else:
                    addr = self.vm.alloc_local(tipo)
                    self.func_dir.add_local_var(scope, var, tipo, addr)
                    self._local_display_map(scope)[addr] = var
            except SemanticError as e:
                self._report(str(e))
        if resto:
            self._registrar_decl(resto, scope)

    def _registrar_func(self, func_node):
        _, tipo_ret, nombre, params, vars_opt, _cuerpo = func_node
        tipo_ret = normaliza_tipo_ret(tipo_ret)

        self.vm.reset_locals()

        param_dirs = []
        for _pname, ptipo in params:
            param_dirs.append(self.vm.alloc_local(ptipo))

        try:
            self.func_dir.add_function(nombre, tipo_ret, params, param_dirs)
        except SemanticError as e:
            self._report(str(e))
            return

        for (pname, _ptipo), paddr in zip(params, param_dirs):
            self._local_display_map(nombre)[paddr] = pname

        if vars_opt:
            self._registrar_vars(vars_opt, scope=nombre)

        if tipo_ret in (INT, FLOAT):
            raddr = self.vm.alloc_global(tipo_ret)
            self.func_dir.set_return_dir(nombre, raddr)
            self.global_display[raddr] = f"ret_{nombre}"

        self.func_dir.set_local_counts(nombre, {
            INT:  self.vm.count('local', INT),
            FLOAT: self.vm.count('local', FLOAT),
        })


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
            self._procesar_llamada(est)
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
        var_dir = self.func_dir.get_var_dir(var, self.current_scope)
        self._emit('=', valor, None, var_dir)

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
                addr = self._const_addr(item[1], STRING)
                self._emit('print', None, None, addr)
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
            self.pila_saltos.pop()
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


    def _procesar_llamada(self, node):
        _, nombre, args = node
        info = self.func_dir.lookup_function(nombre)
        if info is None:
            self._report(f"Funcion no declarada: '{nombre}'")
            return None

        params = info['params']
        param_dirs = info['param_dirs']
        if len(args) != len(params):
            self._report(
                f"Funcion '{nombre}': se esperaban {len(params)} argumento(s), "
                f"se recibieron {len(args)}"
            )

        self._emit('ERA', nombre, None, None)

        for i, a in enumerate(args):
            self._gen_expresion(a)
            if self.pila_operandos.is_empty():
                continue
            arg_addr = self.pila_operandos.pop()
            self.pila_tipos.pop()
            pdir = param_dirs[i] if i < len(param_dirs) else None
            idx = self._emit('PARAM', arg_addr, None, pdir)
            if i < len(params):
                self.quad_result_label[idx] = f"{nombre}.{params[i][0]}"

        start = info['start_quad']
        idx = self._emit('GOSUB', nombre, None, start)
        if start is None:
            self.pending_gosubs.append((idx, nombre))
        return info


    def _gen_expresion(self, node):
        if node is None:
            return
        kind = node[0]

        if kind == 'cte':
            val = node[1]
            tipo = INT if isinstance(val, int) else FLOAT
            addr = self._const_addr(val, tipo)
            self.pila_operandos.push(addr)
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
            addr = self.func_dir.get_var_dir(name, self.current_scope)
            self.pila_operandos.push(addr)
            self.pila_tipos.push(tipo)
            return

        if kind == 'neg':
            self._gen_expresion(node[1])
            if self.pila_operandos.is_empty():
                return
            op = self.pila_operandos.pop()
            t = self.pila_tipos.pop()
            temp = self._alloc_temp(t)
            self._emit('NEG', op, None, temp)
            self.pila_operandos.push(temp)
            self.pila_tipos.push(t)
            return

        if kind == 'pos':
            self._gen_expresion(node[1])
            return

        if kind == 'llamada':
            info = self._procesar_llamada(node)
            if info is None:
                self.pila_operandos.push(node[1])
                self.pila_tipos.push(ERROR)
                return
            tipo_ret = info['tipo']
            if tipo_ret in (INT, FLOAT):
                rdir = info['return_dir']
                temp = self._alloc_temp(tipo_ret)
                self._emit('=', rdir, None, temp)
                self.pila_operandos.push(temp)
                self.pila_tipos.push(tipo_ret)
            else:
                self._report(
                    f"La funcion '{node[1]}' es nula y no puede usarse en una expresion"
                )
                self.pila_operandos.push(node[1])
                self.pila_tipos.push(ERROR)
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
                self._report(f"Operacion invalida: '{t_izq}' {op} '{t_der}'")
                temp = self._alloc_temp(INT)
                self._emit(op, izq, der, temp)
                self.pila_operandos.push(temp)
                self.pila_tipos.push(ERROR)
                return
            temp = self._alloc_temp(t_res)
            self._emit(op, izq, der, temp)
            self.pila_operandos.push(temp)
            self.pila_tipos.push(t_res)
            return


    def _disp(self, x, scope_label: str) -> str:
        if x is None:
            return '_'
        if isinstance(x, str):
            return x
        if isinstance(x, int):
            if x in self.vm.addr_to_const:
                v = self.vm.addr_to_const[x]
                return v if isinstance(v, str) else str(v)
            if x in self.global_display:
                return self.global_display[x]
            m = self.scope_local_display.get(scope_label, {})
            if x in m:
                return m[x]
            if x >= 1000:
                return f"@{x}"
            return str(x)
        return str(x)

    def imprimir_cuadruplos(self):
        items = self.cuadruplos.items()
        print(f"\n=== Cuadruplos (direcciones virtuales) ({len(items)}) ===")
        print(f"{'#':>3}  {'OP':<8} {'ARG1':<8} {'ARG2':<8} {'RES':<8}")
        print("-" * 44)
        for i, q in enumerate(items):
            op, a1, a2, r = q
            print(f"{i:>3}  {str(op):<8} {str(a1):<8} {str(a2):<8} {str(r):<8}")

        print(f"\n=== Cuadruplos (forma legible) ===")
        print(f"{'#':>3}  {'OP':<8} {'ARG1':<10} {'ARG2':<10} {'RES':<10}")
        print("-" * 50)
        for i, q in enumerate(items):
            op, a1, a2, r = q
            sc = self.quad_scope[i]
            d1 = self._disp(a1, sc)
            d2 = self._disp(a2, sc)
            dr = self.quad_result_label.get(i) or self._disp(r, sc)
            print(f"{i:>3}  {str(op):<8} {d1:<10} {d2:<10} {dr:<10}")
        print()

    def imprimir_memoria(self):
        print("\n=== Distribucion de Memoria Virtual usada ===")
        segs = [
            ('global', INT), ('global', FLOAT),
            ('local', INT), ('local', FLOAT),
            ('temp', INT), ('temp', FLOAT), ('temp', BOOL),
            ('const', INT), ('const', FLOAT), ('const', STRING),
        ]
        from virtual_memory import rango
        print(f"{'SEGMENTO':<9} {'TIPO':<7} {'RANGO':<14} {'USADAS':<6}")
        print("-" * 40)
        for seg, tipo in segs:
            ini, fin = rango(seg, tipo)
            usadas = self.vm.count(seg, tipo) if seg in ('global', 'const') else '-'
            print(f"{seg:<9} {tipo:<7} {f'{ini}-{fin}':<14} {str(usadas):<6}")
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