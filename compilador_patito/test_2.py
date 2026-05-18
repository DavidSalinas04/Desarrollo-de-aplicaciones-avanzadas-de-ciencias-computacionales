import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from semantic_cube import get_result_type, INT, FLOAT, BOOL, ERROR
from symbols_table import VariableTable, FunctionDirectory, SemanticError
from test_semantic import SemanticChecker

ok = 0
fail = 0

def check(nombre, resultado):
    global ok, fail
    if resultado:
        print(f"PASS - {nombre}")
        ok += 1
    else:
        print(f"FAIL - {nombre}")
        fail += 1

def run_checker(ast):
    import io, contextlib
    checker = SemanticChecker()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        checker.check_programa(ast)
    return checker.func_dir, checker.errors

# CUBO SEMÁNTICO
print("\n-- CUBO SEMÁNTICO --")

check("ent + ent = ent",       get_result_type(INT, INT, '+')    == INT)
check("dec + ent = dec",       get_result_type(FLOAT, INT, '+')  == FLOAT)
check("ent > ent = bool",      get_result_type(INT, INT, '>')    == BOOL)
check("ent + bool = error",    get_result_type(INT, BOOL, '+')   == ERROR)

# TABLA DE VARIABLES
print("\n-- TABLA DE VARIABLES --")

vt = VariableTable('test')
vt.add('x', INT)
vt.add('y', FLOAT)

check("add y lookup x",         vt.lookup('x') == {'tipo': INT})
check("lookup no existente",    vt.lookup('z') is None)

err_doble = False
try:
    vt.add('x', FLOAT)
except SemanticError:
    err_doble = True
check("variable doblemente declarada lanza SemanticError", err_doble)

# DIRECTORIO DE FUNCIONES
print("\n-- DIRECTORIO DE FUNCIONES --")

fd = FunctionDirectory('miPrograma')
fd.add_global_var('g', INT)
check("variable global agregada",       fd.lookup_global_var('g') == {'tipo': INT})

fd.add_function('suma', INT, [('a', INT), ('b', INT)])
check("función registrada",             fd.exists_function('suma'))
check("params en var_table",           fd.lookup_function('suma')['var_table'].exists('a'))

fd.add_local_var('suma', 'temp', FLOAT)
check("variable local agregada",        fd.lookup_function('suma')['var_table'].exists('temp'))

err_func_doble = False
try:
    fd.add_function('suma', FLOAT, [])
except SemanticError:
    err_func_doble = True
check("función doblemente declarada lanza SemanticError", err_func_doble)

# Prioridad local > global
fd2 = FunctionDirectory('p')
fd2.add_global_var('x', INT)
fd2.add_function('f', 'nil', [])
fd2.add_local_var('f', 'x', FLOAT)
check("local tiene prioridad sobre global", fd2.get_var_type('x', 'f') == FLOAT)

# SEMANTIC CHECKER
print("\n-- SEMANTIC CHECKER --")

# Programa mínimo sin errores
ast_minimo = ('programa', 'p', None, [], ('cuerpo', []))
fd, errs = run_checker(ast_minimo)
check("programa mínimo sin errores", fd is not None and len(errs) == 0)

# Variable global declarada y usada correctamente
ast_asigna_ok = (
    'programa', 'p',
    ('vars', ('decl', ['x'], INT)),   # variables x : ent
    [],
    ('cuerpo', [
        ('asigna', 'x', ('cte', 5))   # x = 5
    ])
)
fd, errs = run_checker(ast_asigna_ok)
check("asignación válida sin errores", len(errs) == 0)

# Variable no declarada en asignación
ast_var_no_decl = (
    'programa', 'p', None, [],
    ('cuerpo', [('asigna', 'noExiste', ('cte', 1))])
)
fd, errs = run_checker(ast_var_no_decl)
check("variable no declarada detectada", len(errs) > 0)

# Variable doblemente declarada
ast_doble_var = (
    'programa', 'p',
    ('vars', ('decl', ['x'], INT, ('decl', ['x'], FLOAT))),
    [], ('cuerpo', [])
)
fd, errs = run_checker(ast_doble_var)
check("variable global doblemente declarada detectada", len(errs) > 0)

# Función declarada correctamente
ast_func_ok = (
    'programa', 'p', None,
    [('func', INT, 'doble', [('n', INT)], None,
      ('cuerpo', [('asigna', 'n', ('*', ('id', 'n'), ('cte', 2)))]))],
    ('cuerpo', [])
)
fd, errs = run_checker(ast_func_ok)
check("función registrada correctamente", fd.exists_function('doble'))

# Función doblemente declarada
ast_func_doble = (
    'programa', 'p', None,
    [
        ('func', 'nil', 'f', [], None, ('cuerpo', [])),
        ('func', 'nil', 'f', [], None, ('cuerpo', [])),
    ],
    ('cuerpo', [])
)
fd, errs = run_checker(ast_func_doble)
check("función doblemente declarada detectada", len(errs) > 0)

# Llamada a función no declarada
ast_llamada_no_decl = (
    'programa', 'p', None, [],
    ('cuerpo', [('llamada', 'fantasma', [])])
)
fd, errs = run_checker(ast_llamada_no_decl)
check("función no declarada en llamada detectada", len(errs) > 0)

# Número incorrecto de argumentos
ast_args_incorrectos = (
    'programa', 'p', None,
    [('func', INT, 'suma', [('a', INT), ('b', INT)], None,
      ('cuerpo', []))],
    ('cuerpo', [('llamada', 'suma', [('cte', 1)])])  # solo 1 arg, se necesitan 2
)
fd, errs = run_checker(ast_args_incorrectos)
check("número incorrecto de argumentos detectado", len(errs) > 0)

# Tipo incompatible: asignar bool a ent
ast_bool_a_ent = (
    'programa', 'p',
    ('vars', ('decl', ['x'], INT)), [],
    ('cuerpo', [
        ('asigna', 'x', ('>', ('cte', 3), ('cte', 2)))  # x = 3 > 2 → bool
    ])
)
fd, errs = run_checker(ast_bool_a_ent)
check("asignación de bool a ent detectada como error", len(errs) > 0)



# Ciclo con condición booleana válida
ast_ciclo = (
    'programa', 'p',
    ('vars', ('decl', ['i'], INT)), [],
    ('cuerpo', [
        ('ciclo',
         ('<', ('id', 'i'), ('cte', 10)),   # i < 10 → bool ✓
         ('cuerpo', [('asigna', 'i', ('+', ('id', 'i'), ('cte', 1)))]))
        ]
    )
)
fd, errs = run_checker(ast_ciclo)
check("ciclo con condición booleana válido", len(errs) == 0)

# resumen
print(f"\n{ok} passed, {fail} failed")