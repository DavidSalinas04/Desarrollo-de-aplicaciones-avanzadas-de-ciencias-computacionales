import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from symbols_table import FunctionDirectory, VariableTable, SemanticError
from semantic_cube import get_result_type, INT, FLOAT, BOOL, ERROR


class SemanticChecker:

    def __init__(self):
        self.func_dir: FunctionDirectory | None = None
        self.current_scope: str | None = None   # scope activo al analizar
        self.errors: list[str] = []

    # punto de entrada principal
    def check_programa(self, ast):
        # ast: ('programa', nombre, vars_opt, [funcs], cuerpo)
        
        _, nombre, vars_opt, funcs, cuerpo = ast
        self.func_dir = FunctionDirectory(nombre)

        # PN-1: variables globales
        if vars_opt:
            self._process_vars(vars_opt, scope=None)

        # PN-2: declaración de funciones
        for func in funcs:
            self._process_func(func)

        # PN-3: cuerpo principal (scope global)
        self.current_scope = None
        self._process_cuerpo(cuerpo)

    # declaración de variables
    def _process_vars(self, vars_node, scope: str | None):
        if vars_node is None:
            return
        # vars_node = ('vars', decl_chain)
        decl = vars_node[1]
        self._process_decl(decl, scope)

    def _process_decl(self, decl, scope: str | None):
        if decl is None:
            return
        ids   = decl[1]
        tipo  = decl[2]
        resto = decl[3] if len(decl) > 3 else None

        for var_name in ids:
            try:
                if scope is None:
                    # Variable global
                    self.func_dir.add_global_var(var_name, tipo)
                else:
                    # Variable local a una función
                    self.func_dir.add_local_var(scope, var_name, tipo)
            except SemanticError as e:
                self._report_error(str(e))

        # Procesar el siguiente grupo de declaraciones (lista encadenada)
        if resto:
            self._process_decl(resto, scope)

    # declaración de funciones
    def _process_func(self, func_node):
        # func_node = ('func', tipo_ret, nombre, params, vars_opt, cuerpo)
        _, tipo_ret, nombre, params, vars_opt, cuerpo = func_node

        try:
            self.func_dir.add_function(nombre, tipo_ret, params)
        except SemanticError as e:
            self._report_error(str(e))
            return

        self.current_scope = nombre

        if vars_opt:
            self._process_vars(vars_opt, scope=nombre)

        self._process_cuerpo(cuerpo)

        self.current_scope = None

    # procesamiento de cuerpo y estatutos
    def _process_cuerpo(self, cuerpo):
        if cuerpo is None:
            return
        # cuerpo = ('cuerpo', [estatutos])
        _, estatutos = cuerpo
        for estatuto in estatutos:
            self._process_estatuto(estatuto)

    def _process_estatuto(self, estatuto):
        if estatuto is None:
            return
        kind = estatuto[0]

        if kind == 'asigna':
            self._check_asigna(estatuto)
        elif kind == 'condicion':
            self._check_condicion(estatuto)
        elif kind == 'ciclo':
            self._check_ciclo(estatuto)
        elif kind == 'imprime':
            self._check_imprime(estatuto)
        elif kind == 'llamada':
            self._check_llamada(estatuto)
        elif kind == 'bloque':
            for s in estatuto[1]:
                self._process_estatuto(s)

    # asignación: validar variable y tipo de expresión
    def _check_asigna(self, node):
        
        _, var_name, expr = node
        var_tipo = self.func_dir.get_var_type(var_name, self.current_scope)
        if var_tipo is None:
            self._report_error(
                f"Variable no declarada: '{var_name}' en scope '{self._scope_label()}'"
            )
            return
        expr_tipo = self._check_expresion(expr)
        if expr_tipo == ERROR:
            return  # el error ya fue reportado dentro de _check_expresion
        if not self._tipos_compatibles(var_tipo, expr_tipo):
            self._report_error(
                f"Tipo incompatible en asignación: '{var_name}' es '{var_tipo}' "
                f"pero la expresión es '{expr_tipo}'"
            )

    # validar tipos en expresiones, llamadas, condiciones, etc.
    def _check_expresion(self, node) -> str:
    
        if node is None:
            return ERROR

        kind = node[0]

        # Operadores relacionales y aritméticos
        if kind in ('+', '-', '*', '/', '>', '<', '==', '!='):
            tipo_izq = self._check_expresion(node[1])
            tipo_der = self._check_expresion(node[2])
            resultado = get_result_type(tipo_izq, tipo_der, kind)
            if resultado == ERROR:
                self._report_error(
                    f"Operación inválida: '{tipo_izq}' {kind} '{tipo_der}'"
                )
            return resultado

        # Negación / signo
        if kind in ('neg', 'pos'):
            return self._check_expresion(node[1])

        # Constante entera
        if kind == 'cte':
            val = node[1]
            return INT if isinstance(val, int) else FLOAT

        # Identificador
        if kind == 'id':
            var_name = node[1]
            tipo = self.func_dir.get_var_type(var_name, self.current_scope)
            if tipo is None:
                self._report_error(
                    f"Variable no declarada: '{var_name}' en scope '{self._scope_label()}'"
                )
                return ERROR
            return tipo

        # Llamada a función
        if kind == 'llamada':
            return self._check_llamada(node)

        # Letrero (cadena literal) — no operable aritméticamente
        if kind == 'letrero':
            return 'letrero'

        return ERROR

    # validar llamada a función: existencia, número de argumentos, tipos de argumentos
    def _check_llamada(self, node) -> str:
        _, func_name, args = node
        func_info = self.func_dir.lookup_function(func_name)
        if func_info is None:
            self._report_error(f"Función no declarada: '{func_name}'")
            return ERROR

        params = func_info['params']
        if len(args) != len(params):
            self._report_error(
                f"Función '{func_name}': se esperaban {len(params)} argumento(s), "
                f"se recibieron {len(args)}"
            )
            return func_info['tipo']

        for i, (arg, (param_name, param_tipo)) in enumerate(zip(args, params)):
            arg_tipo = self._check_expresion(arg)
            if not self._tipos_compatibles(param_tipo, arg_tipo):
                self._report_error(
                    f"Función '{func_name}', argumento {i+1} '{param_name}': "
                    f"se esperaba '{param_tipo}', se recibió '{arg_tipo}'"
                )

        return func_info['tipo']

    # validar condiciones de 'si' y 'mientras'
    def _check_condicion(self, node):
        _, expr, cuerpo_true, cuerpo_false = node
        tipo_cond = self._check_expresion(expr)
        if tipo_cond not in (BOOL, ERROR):
            self._report_error(
                f"La condición del 'si' debe ser booleana, se obtuvo '{tipo_cond}'"
            )
        self._process_cuerpo(cuerpo_true)
        if cuerpo_false:
            self._process_cuerpo(cuerpo_false)

    def _check_ciclo(self, node):
        _, expr, cuerpo = node
        tipo_cond = self._check_expresion(expr)
        if tipo_cond not in (BOOL, ERROR):
            self._report_error(
                f"La condición del 'mientras' debe ser booleana, se obtuvo '{tipo_cond}'"
            )
        self._process_cuerpo(cuerpo)

    def _check_imprime(self, node):
        """node: ('imprime', [items])"""
        _, items = node
        for item in items:
            if isinstance(item, tuple) and item[0] == 'letrero':
                continue  # strings literales siempre son válidos
            self._check_expresion(item)

    # Validar que el tipo de la expresión en 'di' sea compatible con el tipo esperado (ent o dec)
    def _tipos_compatibles(self, esperado: str, recibido: str) -> bool:
        if esperado == recibido:
            return True
        if esperado in (INT, FLOAT) and recibido in (INT, FLOAT):
            return True
        return False

    def _scope_label(self) -> str:
        return self.current_scope if self.current_scope else 'global'

    def _report_error(self, msg: str):
        full_msg = f"[SemanticError] {msg}"
        self.errors.append(full_msg)
        print(full_msg)

    def has_errors(self) -> bool:
        return len(self.errors) > 0


# Función de utilidad para correr el análisis semántico desde un string de código fuente
def analyze(source: str) -> tuple[FunctionDirectory | None, list[str]]:
    """
    Recibe código fuente de Patito, lo parsea y ejecuta el análisis semántico.
    Regresa (func_dir, errores).
    """
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))
    from parser import parse

    ast = parse(source)
    if ast is None:
        return None, ["[SyntaxError] El parser no pudo procesar el código"]

    checker = SemanticChecker()
    checker.check_programa(ast)
    return checker.func_dir, checker.errors