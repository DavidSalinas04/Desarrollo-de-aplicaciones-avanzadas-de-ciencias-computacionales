import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from lexer import tokenize
from parser import parse

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

def toks(src):
    return [t for t, *_ in tokenize(src)]

# ---- LEXER ----
print("\n-- LEXER --")

check("id simple", toks("abc") == ["ID"])
check("id con digitos", toks("x1y2") == ["ID"])
check("keyword programe", toks("programe") == ["PROGRAMA"])
check("keyword variables", toks("variables") == ["VARS"])
check("keyword empieza", toks("empieza") == ["INICIO"])
check("keyword termina", toks("termina") == ["FIN"])
check("keyword ent", toks("ent") == ["ENTERO"])
check("keyword dec", toks("dec") == ["FLOTANTE"])
check("keyword nil", toks("nil") == ["NULA"])
check("keyword di", toks("di") == ["ESCRIBE"])
check("keyword si", toks("si") == ["SI"])
check("keyword sino", toks("sino") == ["SINO"])
check("keyword mientras", toks("mientras") == ["MIENTRAS"])
check("keyword haz", toks("haz") == ["HAZ"])
check("entero", toks("42") == ["CTE_ENT"])
check("flotante", toks("3.14") == ["CTE_FLOT"])
check("letrero", toks('"hola"') == ["LETRERO"])
check("igual ==", toks("==") == ["IG"])
check("diferente !=", toks("!=") == ["NIG"])
check("mayor >", toks(">") == ["GT"])
check("menor <", toks("<") == ["LT"])
check("suma +", toks("+") == ["MAS"])
check("resta -", toks("-") == ["MENOS"])
check("mult *", toks("*") == ["MULT"])
check("division /", toks("/") == ["DIVIDE"])
check("asignacion =", toks("=") == ["ASSIGN"])
check("punto y coma", toks(";") == ["SEMICOLON"])
check("dos puntos", toks(":") == ["COLON"])
check("coma", toks(",") == ["COMMA"])
check("paren izq", toks("(") == ["IPAREN"])
check("paren der", toks(")") == ["DPAREN"])
check("llave izq", toks("{") == ["IBRACE"])
check("llave der", toks("}") == ["DBRACE"])

# ---- PARSER ----
print("\n-- PARSER --")

check("programa minimo", parse("""
programe p ;
empieza { }
termina
""") is not None)

check("declaracion variable", parse("""
programe p ;
variables x : ent ;
empieza { }
termina
""") is not None)

check("declaracion multiple", parse("""
programe p ;
variables a, b, c : dec ;
empieza { }
termina
""") is not None)

check("asignacion", parse("""
programe p ;
variables x : ent ;
empieza { x = 10 ; }
termina
""") is not None)

check("expresion aritmetica", parse("""
programe p ;
variables r : dec ;
empieza { r = 3.0 + 2.0 * 5.0 ; }
termina
""") is not None)

check("si sin sino", parse("""
programe p ;
variables x : ent ;
empieza { si ( x > 3 ) { x = 0 ; } ; }
termina
""") is not None)

check("si con sino", parse("""
programe p ;
variables x : ent ;
empieza { si ( x != 0 ) { x = 1 ; } sino { x = 0 ; } ; }
termina
""") is not None)

check("ciclo mientras", parse("""
programe p ;
variables i : ent ;
empieza { mientras ( i < 5 ) haz { i = i + 1 ; } ; }
termina
""") is not None)

check("di con letrero", parse("""
programe p ;
variables x : ent ;
empieza { di ( x , "hola" ) ; }
termina
""") is not None)

check("funcion nil", parse("""
programe p ;
nil f ( ) { { di ( "x" ) ; } } ;
empieza { f ( ) ; }
termina
""") is not None)

check("funcion ent con params", parse("""
programe p ;
ent suma ( a : ent , b : ent ) { { a = a + b ; } } ;
empieza { suma ( 1 , 2 ) ; }
termina
""") is not None)

check("llamada en expresion", parse("""
programe p ;
variables r : ent ;
ent doble ( n : ent ) { { n = n * 2 ; } } ;
empieza { r = doble ( 5 ) + 1 ; }
termina
""") is not None)

# ---- ERRORES ----
print("\n-- ERRORES (deben fallar) --")

import io, contextlib

def falla(src):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        return parse(src) is None

check("falta termina", falla("programe p ; empieza { }"))
check("falta punto y coma", falla("programe p ; variables x : ent ; empieza { x = 1 } termina"))
check("letrero en expresion", falla('programe p ; variables x : ent ; empieza { x = "hola" + 1 ; } termina'))

# ---- RESUMEN ----
print(f"\n{ok} passed, {fail} failed")