import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from quadruples import QuadrupleGenerator

ok = 0
fail = 0

def check(nombre, cond):
    global ok, fail
    if cond:
        print(f"PASS - {nombre}")
        ok += 1
    else:
        print(f"FAIL - {nombre}")
        fail += 1


def run(ast):
    gen = QuadrupleGenerator()
    gen.generar(ast)
    return gen


ast1 = (
    'programa', 'p',
    ('vars', ('decl', ['x'], 'ent')),
    [],
    ('cuerpo', [
        ('asigna', 'x', ('cte', 5))
    ])
)
g = run(ast1)
g.imprimir_cuadruplos()
quads = g.cuadruplos.items()
check("emite '=' al final",                quads[0][0] == '=')
check("operando es 5",                     quads[0][1] == 5)
check("espacio vacio",                     quads[0][2] is None)
check("destino es x",                      quads[0][3] == 'x')
check("ultimo cuadruplo es END",           quads[-1][0] == 'END')


ast2 = (
    'programa', 'p',
    ('vars', ('decl', ['r'], 'ent')),
    [],
    ('cuerpo', [
        ('asigna', 'r',
            ('+', ('cte', 3), ('*', ('cte', 2), ('cte', 5))))
    ])
)
g = run(ast2)
g.imprimir_cuadruplos()
q = g.cuadruplos.items()
check("primero la multiplicacion",         q[0][0] == '*' and q[0][1] == 2 and q[0][2] == 5)
check("luego la suma usando t1",           q[1][0] == '+' and q[1][1] == 3 and q[1][2] == 't1')
check("hace la asignacion r = t2",           q[2][0] == '=' and q[2][1] == 't2' and q[2][3] == 'r')


ast3 = (
    'programa', 'p',
    ('vars', ('decl', ['x'], 'ent')),
    [],
    ('cuerpo', [
        ('condicion',
            ('>', ('id', 'x'), ('cte', 3)),
            ('cuerpo', [('asigna', 'x', ('cte', 0))]),
            None)
    ])
)
g = run(ast3)
g.imprimir_cuadruplos()
q = g.cuadruplos.items()
check("comparacion",     q[0][0] == '>' and q[0][1] == 'x' and q[0][2] == 3)
check("GOTOF ",    q[1][0] == 'GOTOF' and q[1][3] == 3)
check("asigna",  q[2][0] == '=' and q[2][3] == 'x')


ast4 = (
    'programa', 'p',
    ('vars', ('decl', ['x'], 'ent')),
    [],
    ('cuerpo', [
        ('condicion',
            ('!=', ('id', 'x'), ('cte', 0)),
            ('cuerpo', [('asigna', 'x', ('cte', 1))]),
            ('cuerpo', [('asigna', 'x', ('cte', 0))]))
    ])
)
g = run(ast4)
g.imprimir_cuadruplos()
q = g.cuadruplos.items()
check("comparacion",       q[0][0] == '!=')
check("GOTOF",  q[1][0] == 'GOTOF' and q[1][3] == 4)
check("cuerpo true",          q[2] == ('=', 1, None, 'x'))
check("GOTO al fin",          q[3][0] == 'GOTO' and q[3][3] == 5)
check("cuerpo false",         q[4] == ('=', 0, None, 'x'))


ast5 = (
    'programa', 'p',
    ('vars', ('decl', ['i'], 'ent')),
    [],
    ('cuerpo', [
        ('ciclo',
            ('<', ('id', 'i'), ('cte', 10)),
            ('cuerpo', [
                ('asigna', 'i', ('+', ('id', 'i'), ('cte', 1)))
            ]))
    ])
)
g = run(ast5)
g.imprimir_cuadruplos()
q = g.cuadruplos.items()
check("comparacion",        q[0][0] == '<')
check("GOTOF al fin",         q[1][0] == 'GOTOF' and q[1][3] == 5)
check("suma",      q[2][0] == '+')
check("asignacion i ",    q[3][0] == '=' and q[3][3] == 'i')
check("GOTO al inicio",   q[4][0] == 'GOTO' and q[4][3] == 0)


ast6 = (
    'programa', 'p',
    ('vars', ('decl', ['x'], 'ent')),
    [],
    ('cuerpo', [
        ('imprime', [('id', 'x'), ('letrero', '"hola"')])
    ])
)
g = run(ast6)
g.imprimir_cuadruplos()
q = g.cuadruplos.items()
check("variable",    q[0] == ('print', None, None, 'x'))
check("letrero",     q[1] == ('print', None, None, '"hola"'))


ast7 = (
    'programa', 'p',
    ('vars', ('decl', ['x', 'y'], 'ent')),
    [],
    ('cuerpo', [
        ('asigna', 'x', ('+', ('neg', ('id', 'y')), ('cte', 1)))
    ])
)
g = run(ast7)
g.imprimir_cuadruplos()
q = g.cuadruplos.items()
check("NEG y",                q[0][0] == 'NEG' and q[0][1] == 'y')
check("suma",          q[1][0] == '+' and q[1][1] == 't1')


ast8 = (
    'programa', 'p',
    ('vars', ('decl', ['r'], 'ent')),
    [],
    ('cuerpo', [
        ('asigna', 'r',
            ('*', ('+', ('cte', 3), ('cte', 2)), ('cte', 5)))
    ])
)
g = run(ast8)
g.imprimir_cuadruplos()
q = g.cuadruplos.items()
check("suma",      q[0][0] == '+' and q[0][1] == 3 and q[0][2] == 2)
check("multiplicacion ",       q[1][0] == '*' and q[1][1] == 't1' and q[1][2] == 5)


print(f"\n{ok} passed, {fail} failed")