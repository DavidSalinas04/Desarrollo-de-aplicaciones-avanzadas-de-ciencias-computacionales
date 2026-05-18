
INT   = 'ent'
FLOAT = 'dec'
BOOL  = 'bool'
ERROR = 'error'

semantic_cube = {
    INT: {
        INT: {
            '+':  INT,
            '-':  INT,
            '*':  INT,
            '/':  FLOAT,
            '>':  BOOL,
            '<':  BOOL,
            '==': BOOL,
            '!=': BOOL,
        },
        FLOAT: {
            '+':  FLOAT,
            '-':  FLOAT,
            '*':  FLOAT,
            '/':  FLOAT,
            '>':  BOOL,
            '<':  BOOL,
            '==': BOOL,
            '!=': BOOL,
        },
    },
    FLOAT: {
        INT: {
            '+':  FLOAT,
            '-':  FLOAT,
            '*':  FLOAT,
            '/':  FLOAT,
            '>':  BOOL,
            '<':  BOOL,
            '==': BOOL,
            '!=': BOOL,
        },
        FLOAT: {
            '+':  FLOAT,
            '-':  FLOAT,
            '*':  FLOAT,
            '/':  FLOAT,
            '>':  BOOL,
            '<':  BOOL,
            '==': BOOL,
            '!=': BOOL,
        },
    },
    BOOL: {
        BOOL: {
            '==': BOOL,
            '!=': BOOL,
        },
    },
}


def get_result_type(tipo_izq: str, tipo_der: str, operador: str) -> str:
    try:
        return semantic_cube[tipo_izq][tipo_der][operador]
    except KeyError:
        return ERROR


def is_valid_operation(tipo_izq: str, tipo_der: str, operador: str) -> bool:
    return get_result_type(tipo_izq, tipo_der, operador) != ERROR