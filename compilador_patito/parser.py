import ply.yacc as yacc
from lexer import tokens

precedence = (
    ('left', 'IG', 'NIG', 'GT', 'LT'),
    ('left', 'MAS', 'MENOS'),
    ('left', 'MULT', 'DIVIDE'),
    ('right', 'UMINUS', 'UPLUS'),
)

def p_programa(p):
    '''programa : PROGRAMA ID SEMICOLON vars_opt funcs INICIO cuerpo FIN'''
    p[0] = ('programa', p[2], p[4], p[5], p[7])

def p_vars_opt_present(p):
    '''vars_opt : VARS vars_list'''
    p[0] = ('vars', p[2])

def p_vars_opt_empty(p):
    '''vars_opt : empty'''
    p[0] = None

def p_vars_list(p):
    '''vars_list : ids COLON tipo SEMICOLON vars_list
                 | ids COLON tipo SEMICOLON'''
    p[0] = ('decl', p[1], p[3]) if len(p) == 5 else ('decl', p[1], p[3], p[5])

def p_ids(p):
    '''ids : ID COMMA ids
           | ID'''
    p[0] = [p[1]] if len(p) == 2 else [p[1]] + p[3]

def p_tipo(p):
    '''tipo : ENTERO
            | FLOTANTE'''
    p[0] = p[1]

def p_funcs_many(p):
    '''funcs : func funcs'''
    p[0] = [p[1]] + p[2]

def p_funcs_empty(p):
    '''funcs : empty'''
    p[0] = []

def p_func_nula(p):
    '''func : NULA ID IPAREN params DPAREN IBRACE vars_opt cuerpo DBRACE SEMICOLON'''
    p[0] = ('func', 'nula', p[2], p[4], p[7], p[8])

def p_func_entero(p):
    '''func : ENTERO ID IPAREN params DPAREN IBRACE vars_opt cuerpo DBRACE SEMICOLON'''
    p[0] = ('func', 'entero', p[2], p[4], p[7], p[8])

def p_func_flotante(p):
    '''func : FLOTANTE ID IPAREN params DPAREN IBRACE vars_opt cuerpo DBRACE SEMICOLON'''
    p[0] = ('func', 'flotante', p[2], p[4], p[7], p[8])

def p_params_list(p):
    '''params : param_list'''
    p[0] = p[1]

def p_params_empty(p):
    '''params : empty'''
    p[0] = []

def p_param_list_multi(p):
    '''param_list : ID COLON tipo COMMA param_list'''
    p[0] = [(p[1], p[3])] + p[5]

def p_param_list_single(p):
    '''param_list : ID COLON tipo'''
    p[0] = [(p[1], p[3])]

def p_cuerpo(p):
    '''cuerpo : IBRACE estatutos DBRACE'''
    p[0] = ('cuerpo', p[2])

def p_estatutos_many(p):
    '''estatutos : estatuto estatutos'''
    p[0] = [p[1]] + p[2]

def p_estatutos_empty(p):
    '''estatutos : empty'''
    p[0] = []

def p_estatuto_asigna(p):
    '''estatuto : asigna'''
    p[0] = p[1]

def p_estatuto_condicion(p):
    '''estatuto : condicion'''
    p[0] = p[1]

def p_estatuto_ciclo(p):
    '''estatuto : ciclo'''
    p[0] = p[1]

def p_estatuto_llamada(p):
    '''estatuto : llamada SEMICOLON'''
    p[0] = p[1]

def p_estatuto_imprime(p):
    '''estatuto : imprime'''
    p[0] = p[1]

def p_estatuto_bloque(p):
    '''estatuto : IPAREN estatutos DPAREN'''
    p[0] = ('bloque', p[2])

def p_asigna(p):
    '''asigna : ID ASSIGN expresion SEMICOLON'''
    p[0] = ('asigna', p[1], p[3])

def p_imprime(p):
    '''imprime : ESCRIBE IPAREN print_args DPAREN SEMICOLON'''
    p[0] = ('imprime', p[3])

def p_print_args_multi(p):
    '''print_args : print_item COMMA print_args'''
    p[0] = [p[1]] + p[3]

def p_print_args_single(p):
    '''print_args : print_item'''
    p[0] = [p[1]]

def p_print_item_expr(p):
    '''print_item : expresion'''
    p[0] = p[1]

def p_print_item_letrero(p):
    '''print_item : LETRERO'''
    p[0] = ('letrero', p[1])

def p_ciclo(p):
    '''ciclo : MIENTRAS IPAREN expresion DPAREN HAZ cuerpo SEMICOLON'''
    p[0] = ('ciclo', p[3], p[6])

def p_condicion_sino(p):
    '''condicion : SI IPAREN expresion DPAREN cuerpo SINO cuerpo SEMICOLON'''
    p[0] = ('condicion', p[3], p[5], p[7])

def p_condicion(p):
    '''condicion : SI IPAREN expresion DPAREN cuerpo SEMICOLON'''
    p[0] = ('condicion', p[3], p[5], None)

def p_expresion_gt(p):
    '''expresion : exp GT exp'''
    p[0] = ('>', p[1], p[3])

def p_expresion_lt(p):
    '''expresion : exp LT exp'''
    p[0] = ('<', p[1], p[3])

def p_expresion_neq(p):
    '''expresion : exp NIG exp'''
    p[0] = ('!=', p[1], p[3])

def p_expresion_eq(p):
    '''expresion : exp IG exp'''
    p[0] = ('==', p[1], p[3])

def p_expresion_exp(p):
    '''expresion : exp'''
    p[0] = p[1]

def p_exp_add(p):
    '''exp : exp MAS termino'''
    p[0] = ('+', p[1], p[3])

def p_exp_sub(p):
    '''exp : exp MENOS termino'''
    p[0] = ('-', p[1], p[3])

def p_exp_termino(p):
    '''exp : termino'''
    p[0] = p[1]

def p_termino_mul(p):
    '''termino : termino MULT factor'''
    p[0] = ('*', p[1], p[3])

def p_termino_div(p):
    '''termino : termino DIVIDE factor'''
    p[0] = ('/', p[1], p[3])

def p_termino_factor(p):
    '''termino : factor'''
    p[0] = p[1]

def p_factor_paren(p):
    '''factor : IPAREN expresion DPAREN'''
    p[0] = p[2]

def p_factor_uminus(p):
    '''factor : MENOS factor %prec UMINUS'''
    p[0] = ('neg', p[2])

def p_factor_uplus(p):
    '''factor : MAS factor %prec UPLUS'''
    p[0] = ('pos', p[2])

def p_factor_id(p):
    '''factor : ID'''
    p[0] = ('id', p[1])

def p_factor_cte_ent(p):
    '''factor : CTE_ENT'''
    p[0] = ('cte', p[1])

def p_factor_cte_flot(p):
    '''factor : CTE_FLOT'''
    p[0] = ('cte', p[1])

def p_factor_llamada(p):
    '''factor : llamada'''
    p[0] = p[1]

def p_llamada(p):
    '''llamada : ID IPAREN call_args DPAREN'''
    p[0] = ('llamada', p[1], p[3])

def p_call_args_multi(p):
    '''call_args : expresion COMMA call_args'''
    p[0] = [p[1]] + p[3]

def p_call_args_single(p):
    '''call_args : expresion'''
    p[0] = [p[1]]

def p_call_args_empty(p):
    '''call_args : empty'''
    p[0] = []

def p_empty(p):
    '''empty :'''
    p[0] = None

def p_error(p):
    if p:
        print(f"[Parser] Error sintáctico en token '{p.value}' (tipo {p.type}) línea {p.lineno}")
    else:
        print("[Parser] Error sintáctico: fin de archivo inesperado")

parser = yacc.yacc(start='programa', debug=False, write_tables=False)

def parse(source: str):
    from lexer import lexer as _lex
    _lex.lineno = 1
    return parser.parse(source, lexer=_lex)