class VariableTable:

    def __init__(self, scope_name: str):
        self.scope_name = scope_name
        self._table: dict = {}

    #agregar variables
    def add(self, name: str, tipo: str):
        
        if name in self._table:
            raise SemanticError(
                f"Variable doblemente declarada: '{name}' en scope '{self.scope_name}'"
            )
        self._table[name] = {'tipo': tipo}

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

    def __repr__(self):
        lines = [f"  VariableTable[{self.scope_name}]:"]
        if not self._table:
            lines.append("    (vacía)")
        for name, info in self._table.items():
            lines.append(f"    {name}: {info['tipo']}")
        return "\n".join(lines)


class FunctionDirectory:
    GLOBAL_SCOPE = '__global__'

    def __init__(self, program_name: str):
        self.program_name = program_name
        self._functions: dict = {}
        # Scope global para variables del programa principal
        self._global_vars = VariableTable(self.GLOBAL_SCOPE)

    # agrega variable global
    def add_global_var(self, name: str, tipo: str):
        self._global_vars.add(name, tipo)

    # busca variable global
    def lookup_global_var(self, name: str) -> dict | None:
        return self._global_vars.lookup(name)

    # agrega función con params
    def add_function(self, name: str, tipo: str, params: list):
        
        if name in self._functions:
            raise SemanticError(
                f"Función doblemente declarada: '{name}'"
            )
        var_table = VariableTable(name)
        # Los parámetros se agregan automáticamente a la tabla de variables local
        for param_name, param_tipo in params:
            var_table.add(param_name, param_tipo)

        self._functions[name] = {
            'tipo':      tipo,
            'params':    params,
            'var_table': var_table,
        }

    # agrega variable local a función
    def add_local_var(self, func_name: str, var_name: str, tipo: str):
        if func_name not in self._functions:
            raise SemanticError(f"Función no declarada: '{func_name}'")
        self._functions[func_name]['var_table'].add(var_name, tipo)

    # busca función
    def lookup_function(self, name: str) -> dict | None:
        return self._functions.get(name, None)

    # existe función
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

    def __repr__(self):
        lines = [f"FunctionDirectory[{self.program_name}]:"]
        lines.append(repr(self._global_vars))
        if not self._functions:
            lines.append("  (sin funciones)")
        for fname, finfo in self._functions.items():
            lines.append(f"  Función '{fname}' -> {finfo['tipo']}")
            params_str = ", ".join(f"{n}:{t}" for n, t in finfo['params'])
            lines.append(f"    params: ({params_str})")
            lines.append(repr(finfo['var_table']))
        return "\n".join(lines)


class SemanticError(Exception):
    # Excepción personalizada para errores semánticos
    pass