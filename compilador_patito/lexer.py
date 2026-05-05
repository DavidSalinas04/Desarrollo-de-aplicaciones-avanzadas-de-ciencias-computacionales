import ply.lex as lex
 

reserved = {
    'programe' : 'PROGRAMA',
    'variables'     : 'VARS',
    'empieza'   : 'INICIO',
    'termina'      : 'FIN',
    'ent'   : 'ENTERO',
    'dec'  : 'FLOTANTE',
    'nil'     : 'NULA',
    'si'       : 'SI',
    'sino'     : 'SINO',
    'mientras' : 'MIENTRAS',
    'haz'      : 'HAZ',
    'di'  : 'ESCRIBE',
}
 

tokens = [
    # Identificadores y constantes
    'ID', 'CTE_ENT', 'CTE_FLOT', 'LETRERO',
    # Operadores relacionales
    'IG', 'NIG', 'GT', 'LT',
    # Operadores aritméticos
    'MAS', 'MENOS', 'MULT', 'DIVIDE',
    # Asignación
    'ASSIGN',
    # Delimitadores
    'SEMICOLON', 'COLON', 'COMMA',
    'IPAREN', 'DPAREN',
    'IBRACE', 'DBRACE',
] + list(reserved.values())

t_IG        = r'=='
t_NIG       = r'!='
t_GT        = r'>'
t_LT        = r'<'
t_MAS      = r'\+'
t_MENOS     = r'-'
t_MULT     = r'\*'
t_DIVIDE    = r'/'
t_ASSIGN    = r'='
t_SEMICOLON = r';'
t_COLON     = r':'
t_COMMA     = r','
t_IPAREN    = r'\('
t_DPAREN    = r'\)'
t_IBRACE    = r'\{'
t_DBRACE    = r'\}'
 

 
def t_LETRERO(t):
    r'"[^"\n]*"'
    return t
 
def t_CTE_FLOT(t):
    r'[0-9]+\.[0-9]+'
    t.value = float(t.value)
    return t
 
def t_CTE_ENT(t):
    r'[0-9]+'
    t.value = int(t.value)
    return t
 
def t_ID(t):
    r'[a-zA-Z][a-zA-Z0-9]*'
    t.type = reserved.get(t.value, 'ID')
    return t

# nueva linea
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)
 
# Espacios y tabs ignorados
t_ignore = ' \t\r'
 
def t_error(t):
    print(f"[Lexer] Carácter ilegal '{t.value[0]}' en línea {t.lineno}")
    t.lexer.skip(1)
 

lexer = lex.lex()
 
def tokenize(source: str):
    """Devuelve lista de (tipo, valor, línea) para el código fuente dado."""
    lexer.input(source)
    result = []
    for tok in lexer:
        result.append((tok.type, tok.value, tok.lineno))
    return result
 