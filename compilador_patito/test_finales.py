from VM import ejecutar_fuente


fibonacci_ciclico = '''
programe fibCicMain ;
variables n, i, a, b, t : ent ;
empieza {
  n = 10 ;
  a = 0 ;
  b = 1 ;
  i = 0 ;
  mientras ( i < n ) haz {
    t = a + b ;
    a = b ;
    b = t ;
    i = i + 1 ;
  } ;
  di ( "fib(" , n , ") = " , a) ;
}
termina
'''

fibonacci_recursivo = '''
programe fibRec ;
variables r : ent ;
ent fib ( n : ent ) {
  {
    si ( n < 2 ) { regresa ( n ) ; }
    sino { regresa ( fib ( n - 1 ) + fib ( n - 2 ) ) ; } ;
  }
} ;
empieza {
  r = fib ( 10 ) ;
  di ( "fib(10) = " , r ) ;
}
termina
'''
factorial_ciclico = '''
programe factCicMain ;
variables n, i, fact : ent ;
empieza {
  n = 6 ;
  fact = 1 ;
  i = 1 ;
  mientras ( i < n ) haz {
    i = i + 1 ;
    fact = fact * i ;
  } ;
  di ( "fact(" , n , ") = " , fact ) ;
}
termina
'''

factorial_recursivo = '''
programe factRec ;
variables r : ent ;
ent factorial ( n : ent ) {
  {
    si ( n < 2 ) { regresa ( 1 ) ; }
    sino { regresa ( n * factorial ( n - 1 ) ) ; } ;
  }
} ;
empieza {
  r = factorial ( 6 ) ;
  di ( "fact(6) = " , r ) ;
}
termina
'''

print("\nfibonacci recursivo")
s, e = ejecutar_fuente(fibonacci_recursivo)

print("\nfibonacci ciclico")
s, e = ejecutar_fuente(fibonacci_ciclico)

print("\nfactorial recursivo")
s, e = ejecutar_fuente(factorial_recursivo)

print("\nfactorial ciclico")
s, e = ejecutar_fuente(factorial_ciclico)