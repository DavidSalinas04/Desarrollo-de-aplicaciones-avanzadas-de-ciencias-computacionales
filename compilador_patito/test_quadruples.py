import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from quadruples import QuadrupleGenerator, compile_to_quads, MAIN_SCOPE
from virtual_memory import BASES, SEGMENT_SIZE
from semantic_cube import INT, FLOAT, BOOL

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

def disp(g, val, scope=MAIN_SCOPE):
    return g._disp(val, scope)

def en_segmento(addr, segmento, tipo):
    base = BASES[(segmento, tipo)]
    return isinstance(addr, int) and base <= addr < base + SEGMENT_SIZE

def ops_de(q):
    return [x[0] for x in q]


ast1 = ('programa', 'p', ('vars', ('decl', ['x'], 'ent')), [],
        ('cuerpo', [('asigna', 'x', ('cte', 5))]))
g = run(ast1)
q = g.cuadruplos.items()
check("[1] inicia con GOTO al main",        q[0][0] == 'GOTO')
asg = q[1]
check("[1] emite '='",                      asg[0] == '=')
check("[1] arg1 es la constante 5",         disp(g, asg[1]) == '5')
check("[1] constante en segmento const-ent", en_segmento(asg[1], 'const', INT))
check("[1] arg2 vacio",                     asg[2] is None)
check("[1] destino es x",                   disp(g, asg[3]) == 'x')
check("[1] x en segmento global-ent",       en_segmento(asg[3], 'global', INT))
check("[1] ultimo cuadruplo es END",        q[-1][0] == 'END')


ast2 = ('programa', 'p', ('vars', ('decl', ['r'], 'ent')), [],
        ('cuerpo', [('asigna', 'r', ('+', ('cte', 3), ('*', ('cte', 2), ('cte', 5))))]))
g = run(ast2)
q = g.cuadruplos.items()
mult = q[1]; suma = q[2]; asg = q[3]
check("[2] primero la multiplicacion",      mult[0] == '*' and disp(g, mult[1]) == '2' and disp(g, mult[2]) == '5')
check("[2] temporal de mult en temp-ent",   en_segmento(mult[3], 'temp', INT))
check("[2] luego la suma usa el temporal",  suma[0] == '+' and disp(g, suma[1]) == '3' and suma[2] == mult[3])
check("[2] asignacion r = temp",            asg[0] == '=' and asg[1] == suma[3] and disp(g, asg[3]) == 'r')


ast3 = ('programa', 'p', ('vars', ('decl', ['x'], 'ent')), [],
        ('cuerpo', [('condicion', ('>', ('id', 'x'), ('cte', 3)),
            ('cuerpo', [('asigna', 'x', ('cte', 0))]), None)]))
g = run(ast3)
q = g.cuadruplos.items()
cmp_ = q[1]; gotof = q[2]; asg = q[3]
check("[3] comparacion >",                  cmp_[0] == '>' and disp(g, cmp_[1]) == 'x' and disp(g, cmp_[2]) == '3')
check("[3] resultado relacional en temp-bool", en_segmento(cmp_[3], 'temp', BOOL))
check("[3] GOTOF usa la condicion",         gotof[0] == 'GOTOF' and gotof[1] == cmp_[3])
check("[3] GOTOF salta despues del cuerpo", gotof[3] == 4)
check("[3] asignacion dentro del si",       asg[0] == '=' and disp(g, asg[3]) == 'x')



ast4 = ('programa', 'p', ('vars', ('decl', ['x'], 'ent')), [],
        ('cuerpo', [('condicion', ('!=', ('id', 'x'), ('cte', 0)),
            ('cuerpo', [('asigna', 'x', ('cte', 1))]),
            ('cuerpo', [('asigna', 'x', ('cte', 0))]))]))
g = run(ast4)
q = g.cuadruplos.items()
check("[4] comparacion !=",                 q[1][0] == '!=')
check("[4] GOTOF salta al sino",            q[2][0] == 'GOTOF' and q[2][3] == 5)
check("[4] cuerpo verdadero x = 1",         q[3][0] == '=' and disp(g, q[3][1]) == '1' and disp(g, q[3][3]) == 'x')
check("[4] GOTO salta al final",            q[4][0] == 'GOTO' and q[4][3] == 6)
check("[4] cuerpo falso x = 0",             q[5][0] == '=' and disp(g, q[5][1]) == '0' and disp(g, q[5][3]) == 'x')


ast5 = ('programa', 'p', ('vars', ('decl', ['i'], 'ent')), [],
        ('cuerpo', [('ciclo', ('<', ('id', 'i'), ('cte', 10)),
            ('cuerpo', [('asigna', 'i', ('+', ('id', 'i'), ('cte', 1)))]))]))
g = run(ast5)
q = g.cuadruplos.items()
check("[5] comparacion <",                  q[1][0] == '<')
check("[5] GOTOF al final del ciclo",       q[2][0] == 'GOTOF' and q[2][3] == 6)
check("[5] suma i + 1",                     q[3][0] == '+' and disp(g, q[3][1]) == 'i')
check("[5] asignacion a i",                 q[4][0] == '=' and disp(g, q[4][3]) == 'i')
check("[5] GOTO regresa a la condicion",    q[5][0] == 'GOTO' and q[5][3] == 1)


ast6 = ('programa', 'p', ('vars', ('decl', ['x'], 'ent')), [],
        ('cuerpo', [('imprime', [('id', 'x'), ('letrero', '"hola"')])]))
g = run(ast6)
q = g.cuadruplos.items()
check("[6] imprime variable x",             q[1][0] == 'print' and disp(g, q[1][3]) == 'x')
check("[6] imprime letrero",                q[2][0] == 'print' and disp(g, q[2][3]) == '"hola"')
check("[6] letrero en segmento const-string", en_segmento(q[2][3], 'const', 'string'))


ast7 = ('programa', 'p', ('vars', ('decl', ['x', 'y'], 'ent')), [],
        ('cuerpo', [('asigna', 'x', ('+', ('neg', ('id', 'y')), ('cte', 1)))]))
g = run(ast7)
q = g.cuadruplos.items()
check("[7] NEG sobre y",                    q[1][0] == 'NEG' and disp(g, q[1][1]) == 'y')
check("[7] suma usa el temporal de NEG",    q[2][0] == '+' and q[2][1] == q[1][3])


src_void = """
programe p ;
nil saluda ( ) { { di ( "hola" ) ; } } ;
empieza { saluda ( ) ; }
termina
"""
g = compile_to_quads(src_void)
q = g.cuadruplos.items()
ops = ops_de(q)
check("[8] sin errores semanticos",         g.errors == [])
check("[8] existe ENDFUNC",                 'ENDFUNC' in ops)
check("[8] existe ERA",                     'ERA' in ops)
check("[8] existe GOSUB",                   'GOSUB' in ops)
check("[8] ERA antes de GOSUB",             ops.index('ERA') < ops.index('GOSUB'))
info = g.func_dir.lookup_function('saluda')
gosub = [x for x in q if x[0] == 'GOSUB'][0]
check("[8] GOSUB apunta al inicio de la funcion", gosub[1] == 'saluda' and gosub[3] == info['start_quad'])
check("[8] start_quad registrado",          isinstance(info['start_quad'], int))


src_fn = """
programe p ;
variables r : ent ;
ent doble ( n : ent ) { { n = n * 2 ; } } ;
empieza { r = doble ( 5 ) + 1 ; }
termina
"""
g = compile_to_quads(src_fn)
q = g.cuadruplos.items()
check("[9] sin errores semanticos",         g.errors == [])
era = [x for x in q if x[0] == 'ERA'][0]
check("[9] ERA de doble",                   era[1] == 'doble')
param = [x for x in q if x[0] == 'PARAM'][0]
check("[9] PARAM pasa la constante 5",      disp(g, param[1]) == '5')
check("[9] PARAM destino en segmento local-ent", en_segmento(param[3], 'local', INT))
info = g.func_dir.lookup_function('doble')
rdir = info['return_dir']
check("[9] slot de retorno en global-ent",  en_segmento(rdir, 'global', INT))
retcopy = [x for x in q if x[0] == '=' and x[1] == rdir]
check("[9] copia del valor de retorno a temporal", len(retcopy) == 1)
suma = [x for x in q if x[0] == '+'][0]
check("[9] suma usa el temporal del retorno", suma[1] == retcopy[0][3])


src_rangos = """
programe p ;
variables a : ent ; b : dec ;
empieza {
  a = 2 + 3 ;
  b = 1.5 * 2.0 ;
  si ( a > 1 ) { di ( "ok" ) ; } ;
}
termina
"""
g = compile_to_quads(src_rangos)
q = g.cuadruplos.items()
check("[10] sin errores",                   g.errors == [])
check("[10] global-ent usado (a)",          g.vm.count('global', INT) == 1)
check("[10] global-dec usado (b)",          g.vm.count('global', FLOAT) == 1)
check("[10] const-ent usadas",              g.vm.count('const', INT) >= 1)
check("[10] const-dec usadas",              g.vm.count('const', FLOAT) >= 1)
check("[10] const-string usada (\"ok\")",   g.vm.count('const', 'string') == 1)


temp_ent = [x for x in q if x[0] == '+' ][0][3]
temp_dec = [x for x in q if x[0] == '*' ][0][3]
temp_bool = [x for x in q if x[0] == '>' ][0][3]
check("[10] temporal de suma en temp-ent",  en_segmento(temp_ent, 'temp', INT))
check("[10] temporal de mult en temp-dec",  en_segmento(temp_dec, 'temp', FLOAT))
check("[10] temporal de comparacion en temp-bool", en_segmento(temp_bool, 'temp', BOOL))

print(f"\n{ok} passed, {fail} failed")