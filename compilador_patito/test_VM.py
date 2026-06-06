import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import io, contextlib
from VM import ejecutar_fuente

ok = 0
fail = 0

def check(nombre, cond):
    global ok, fail
    if cond:
        print(f"PASS - {nombre}"); ok += 1
    else:
        print(f"FAIL - {nombre}"); fail += 1

def corre(src):
    """Ejecuta y regresa la salida como una sola cadena (sin ruido en stdout)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        salida, errores = ejecutar_fuente(src)
    return "".join(salida), errores

print("\nMAQUINA VIRTUAL: EJECUCION")

s, e = corre('''programe p ;
variables x : ent ;
empieza { x = 3 + 2 * 5 ; di ( x ) ; }
termina''')
check("precedencia 3+2*5 = 13", s == "13" and not e)

s, e = corre('''programe p ;
variables x : ent ;
empieza { x = 13 ; si ( x > 10 ) { di ( "alto" ) ; } sino { di ( "bajo" ) ; } ; }
termina''')
check("condicional rama verdadera", s == "alto")

s, e = corre('''programe p ;
variables x : ent ;
empieza { x = 5 ; si ( x > 10 ) { di ( "alto" ) ; } sino { di ( "bajo" ) ; } ; }
termina''')
check("condicional rama falsa", s == "bajo")

s, e = corre('''programe p ;
variables i, suma : ent ;
empieza { i=0; suma=0; mientras (i<5) haz { suma=suma+i; i=i+1; }; di(suma); }
termina''')
check("ciclo suma 0..4 = 10", s == "10")

s, e = corre('''programe p ;
variables k : ent ;
empieza { k=1; mientras (k<4) haz { di(k); k=k+1; }; }
termina''')
check("ciclo imprime 123", s == "123")

s, e = corre('''programe p ;
variables r : dec ;
empieza { r = 7 / 2 ; di ( r ) ; }
termina''')
check("division 7/2 = 3.5", s == "3.5")

s, e = corre('''programe p ;
variables r : ent ;
ent doble ( n : ent ) { { regresa ( n * 2 ) ; } } ;
empieza { r = doble ( 5 ) + 1 ; di ( r ) ; }
termina''')
check("doble(5)+1 = 11", s == "11")

s, e = corre('''programe p ;
variables r : ent ;
ent suma ( a : ent , b : ent ) { { regresa ( a + b ) ; } } ;
empieza { r = suma ( 20 , 22 ) ; di ( r ) ; }
termina''')
check("suma(20,22) = 42", s == "42")

s, e = corre('''programe p ;
variables f : ent ;
ent fact ( n : ent ) {
  { si ( n < 2 ) { regresa ( 1 ) ; } sino { regresa ( n * fact ( n - 1 ) ) ; } ; }
} ;
empieza { f = fact ( 4 ) ; di ( f ) ; }
termina''')
check("factorial(4) = 24", s == "24")

s, e = corre('''programe p ;
variables k : ent ;
ent fib ( n : ent ) {
  { si ( n < 2 ) { regresa ( n ) ; } sino { regresa ( fib ( n - 1 ) + fib ( n - 2 ) ) ; } ; }
} ;
empieza { k = fib ( 10 ) ; di ( k ) ; }
termina''')
check("fibonacci(10) = 55", s == "55")

s, e = corre('''programe p ;
nil cuenta ( hasta : ent ) {
  variables k : ent ;
  { k=1; mientras (k<hasta) haz { di(k); k=k+1; }; }
} ;
empieza { cuenta ( 5 ) ; di ( "X" ) ; }
termina''')
check("procedimiento nula imprime 1234X", s == "1234X")

s, e = corre('''programe p ;
variables g : ent ;
ent inc ( x : ent ) { { regresa ( x + 1 ) ; } } ;
empieza { g = 10 ; g = inc ( g ) ; g = inc ( g ) ; di ( g ) ; }
termina''')
check("global tras dos llamadas = 12", s == "12")

s, e = corre('''programe p ;
nil f ( ) { { regresa ( 1 ) ; } } ;
empieza { f ( ) ; }
termina''')
check("regresa en funcion nula -> error", len(e) > 0)

err_div = False
try:
    corre('''programe p ;
variables r : dec ;
empieza { r = 5 / 0 ; di ( r ) ; }
termina''')
except Exception:
    err_div = True
check("division entre cero detectada", err_div)

print(f"\n{ok} passed, {fail} failed")