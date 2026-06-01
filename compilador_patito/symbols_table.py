class VariableTable:

    def __init__(self, scope_name: str):
        self.scope_name = scope_name
        self._table: dict = {}

    def add(self, name: str, tipo: str, direccion=None):
        if name in self._table:
            raise SemanticError(
                f"Variable doblemente declarada: '{name}' en scope '{self.scope_name}'"
            )
        self._table[name] = {'tipo': tipo, 'dir': direccion}

    # buscar variables
    def lookup(self, name: str) -> dict | None:
        return self._table.get(name, None)

    # existe variable
    def exists(self, name: str) -> bool:
        return name in self._table

    # tipo de variable
    def get_type(self, name: str) -> str | None:
        entry = self.lookup(name)
        return entry['tipo'] if entry else None

    # direccion virtual de variable
    def get_dir(self, name: str):
        entry = self.lookup(name)
        return entry['dir'] if entry else None

    def set_dir(self, name: str, direccion):
        if name in self._table:
            self._table[name]['dir'] = direccion

    def __repr__(self):
        lines = [f"  VariableTable[{self.scope_name}]:"]
        if not self._table:
            lines.append("    (vacia)")
        for name, info in self._table.items():
            lines.append(f"    {name}: {info['tipo']} @ {info.get('dir')}")
        return "\n".join(lines)


class FunctionDirectory:
    GLOBAL_SCOPE = '__global__'

    def __init__(self, program_name: str):
        self.program_name = program_name
        self._functions: dict = {}
        # Scope global para variables del programa principal
        self._global_vars = VariableTable(self.GLOBAL_SCOPE)

    # agrega variable global (con direccion virtual opcional)
    def add_global_var(self, name: str, tipo: str, direccion=None):
        self._global_vars.add(name, tipo, direccion)

    # busca variable global
    def lookup_global_var(self, name: str) -> dict | None:
        return self._global_vars.lookup(name)

    # agrega funcion con params
    def add_function(self, name: str, tipo: str, params: list, param_dirs=None):
        if name in self._functions:
            raise SemanticError(
                f"Funcion doblemente declarada: '{name}'"
            )
        var_table = VariableTable(name)
        # Los parametros se agregan automaticamente a la tabla de variables local
        if param_dirs is None:
            param_dirs = [None] * len(params)
        for (param_name, param_tipo), pdir in zip(params, param_dirs):
            var_table.add(param_name, param_tipo, pdir)

        self._functions[name] = {
            'tipo':        tipo,
            'params':      params,
            'param_dirs':  list(param_dirs),
            'var_table':   var_table,
            'start_quad':  None,   # indice del primer cuadruplo del cuerpo
            'return_dir':  None,   # direccion global del valor de retorno
            'local_counts': {},    # recursos locales
            'temp_counts':  {},    # recursos temporales
        }

    # agrega variable local a funcion
    def add_local_var(self, func_name: str, var_name: str, tipo: str, direccion=None):
        if func_name not in self._functions:
            raise SemanticError(f"Funcion no declarada: '{func_name}'")
        self._functions[func_name]['var_table'].add(var_name, tipo, direccion)

    # busca funcion
    def lookup_function(self, name: str) -> dict | None:
        return self._functions.get(name, None)

    # existe funcion
    def exists_function(self, name: str) -> bool:
        return name in self._functions

    def lookup_var(self, var_name: str, scope: str | None = None) -> dict | None:
        # Buscar en scope local primero
        if scope and scope in self._functions:
            entry = self._functions[scope]['var_table'].lookup(var_name)
            if entry:
                return entry
        # Luego en global
        return self._global_vars.lookup(var_name)

    # obtener tipo de variable considerando scopes
    def get_var_type(self, var_name: str, scope: str | None = None) -> str | None:
        entry = self.lookup_var(var_name, scope)
        return entry['tipo'] if entry else None

    # obtener direccion virtual de variable considerando scopes
    def get_var_dir(self, var_name: str, scope: str | None = None):
        entry = self.lookup_var(var_name, scope)
        return entry['dir'] if entry else None

    #setters de metadatos de generacion de codigo
    def set_start_quad(self, func_name: str, quad_idx: int):
        self._functions[func_name]['start_quad'] = quad_idx

    def set_return_dir(self, func_name: str, direccion):
        self._functions[func_name]['return_dir'] = direccion

    def set_local_counts(self, func_name: str, counts: dict):
        self._functions[func_name]['local_counts'] = dict(counts)

    def set_temp_counts(self, func_name: str, counts: dict):
        self._functions[func_name]['temp_counts'] = dict(counts)

    def __repr__(self):
        lines = [f"FunctionDirectory[{self.program_name}]:"]
        lines.append(repr(self._global_vars))
        if not self._functions:
            lines.append("  (sin funciones)")
        for fname, finfo in self._functions.items():
            lines.append(f"  Funcion '{fname}' -> {finfo['tipo']} "
                         f"(inicio={finfo['start_quad']}, ret={finfo['return_dir']})")
            params_str = ", ".join(f"{n}:{t}" for n, t in finfo['params'])
            lines.append(f"    params: ({params_str})")
            lines.append(repr(finfo['var_table']))
        return "\n".join(lines)


class SemanticError(Exception):
    # Excepcion personalizada para errores semanticos
    pass