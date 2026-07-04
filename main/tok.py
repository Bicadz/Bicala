# ============================================================
# tok.py — Single source of truth for all token definitions,
# syntax configuration, operators, and keyword mappings.
# No internal project imports allowed (base module).
# ============================================================

# ============================================================
# DYNAMIC SYNTAX OVERRIDES
# Users may remap Bicala keywords by editing these dictionaries.
# Internal code references the uppercase key; the value is the
# actual keyword string recognised by the lexer / parser.
# ============================================================

# Group-based keyword dictionaries for better maintainability
_LOGICAL = {
    'AND':       'and',
    'OR':        'or',
    'NOT':       'not',
    'IN':        'in',
}

_CONTROL_FLOW = {
    'IF':        'if',
    'ELIF':      'elif',
    'ELSE':      'else',
    'WHILE':     'while',
    'FOR':       'for',
    'REPEAT':    'repeat',
    'FOREVER':   'forever',
    'TRY':       'try',
    'CATCH':     'catch',
    'FINALLY':   'finally',
    'SWITCH':    'switch',
    'DEFAULT':   'default',
    'DEFER':     'defer',
}

_FUNCTIONS = {
    'DEF':       'def',
    'RETURN':    'return',
    'DEFINE':    'define',
    'INFIX':     'infix',
    'INFIX_L':   'infixl',
    'INFIX_R':   'infixr',
    'PREFIX':    'prefix',
    'POSTFIX':   'postfix',
    'LAMBDA':    'fn',
}

_DECLARATIONS = {
    'CONST':     'const',
}

_LOOP_CONTROL = {
    'BREAK':     'break',
    'CONTINUE':  'continue',
    'DEL':       'del',
    'PASS':      'pass',
}

_LITERALS = {
    'TRUE':      'true',
    'FALSE':     'false',
    'NONE':      'none',
    'NAN':       'nan',
}

_IO = {
    'INPUT':     'input',
    'PRINT':     'say',       # Maps 'say' dynamically to internal PRINT token
}

_BUILTINS = {
    'DEBUG':     'debug',
    'HELP':      'help',
    'ERROR':     'error',
    'TYPE':      'type',
}

_MODULE = {
    'IMPORT':    'import',
    'FROM':      'from',
    'AS':        'as',
}

# Merge all groups into global SYNTAX dictionary using dictionary unpacking
SYNTAX = {
    **_LOGICAL,
    **_CONTROL_FLOW,
    **_FUNCTIONS,
    **_DECLARATIONS,
    **_LOOP_CONTROL,
    **_LITERALS,
    **_IO,
    **_BUILTINS,
    **_MODULE,
}

# Keys within SYNTAX that are treated as syntax-level keywords
# Dynamically derived from group keys to avoid manual errors
_KEYWORD_KEYS = frozenset(
    _LOGICAL.keys() |
    _CONTROL_FLOW.keys() |
    _FUNCTIONS.keys() |
    _DECLARATIONS.keys() |
    _LOOP_CONTROL.keys() |
    _LITERALS.keys()
)

# Keys within SYNTAX that are treated as built-in functions
# Dynamically derived from group keys to avoid manual errors
_BUILTIN_KEYS = frozenset(
    _IO.keys() |
    _BUILTINS.keys() |
    _MODULE.keys()
)


def _build_keyword_set():
    """Derive the active keyword set from SYNTAX overrides."""
    return {SYNTAX[k] for k in _KEYWORD_KEYS if k in SYNTAX}


def _build_builtin_set():
    """Derive the active built-in set from SYNTAX overrides."""
    return {SYNTAX[k] for k in _BUILTIN_KEYS if k in SYNTAX}


# Active keyword / built-in sets (re-compute after mutating SYNTAX)
KEYWORDS = _build_keyword_set()
BUILTINS = _build_builtin_set()


def refresh_syntax():
    """Re-derive KEYWORDS, BUILTINS, and OPERATORS after SYNTAX or operator dictionaries have been mutated.

    Call this once after bulk-editing SYNTAX or operator dictionaries at startup:
        SYNTAX['PRINT'] = 'noi'
        SYNTAX['INPUT'] = 'nhap'
        COMPARISON_OPERATORS['LOOSE_EQ'] = '.='
        refresh_syntax()
    """
    global KEYWORDS, BUILTINS, OPERATORS, ALL_OPERATORS, MULTI_CHAR_OPERATORS, SINGLE_CHAR_OPERATORS
    KEYWORDS = _build_keyword_set()
    BUILTINS = _build_builtin_set()
    OPERATORS = _build_operators()
    ALL_OPERATORS = _build_all_operators()
    MULTI_CHAR_OPERATORS = _build_multi_char_operators()
    SINGLE_CHAR_OPERATORS = _build_single_char_operators()


def get_syntax(key):
    """Return the active keyword string for an internal token name."""
    return SYNTAX[key]


def resolve_syntax(text):
    """Return the internal token name for a user-facing keyword, or None."""
    for key, val in SYNTAX.items():
        if val == text:
            return key
    return None


# ============================================================
# SYNTAX CONFIGURATION
# Operators, punctuation, comments, precedence
# ============================================================

# Arithmetic operators
ARITHMETIC_OPERATORS = {
    'ADD': '+',
    'SUB': '-',
    'MUL': '*',
    'DIV': '/',
    'FLOOR_DIV': '//',
    'MOD': '%',
    'POW': '**',
    'CARET': '^',  # Custom power operator (user-definable)
}

# Assignment operators
ASSIGNMENT_OPERATORS = {
    'ADD': '+=',
    'SUB': '-=',
    'MUL': '*=',
    'DIV': '/=',
    'FLOOR_DIV': '//=',
    'MOD': '%=',
    'POW': '**=',
}



# Comparison operators
COMPARISON_OPERATORS = {
    'LOOSE_EQ': '.=',
    'STRICT_EQ': '==',
    'IDENTITY_EQ': '===',
    'LOOSE_NE': '!=',
    'STRICT_NE': '!==',
    'IDENTITY_NE': '!===',
    'LT': '<',
    'GT': '>',
    'LTE': '<=',
    'GTE': '>=',
    'IN': 'in',
}

# Logical operators
LOGICAL_OPERATORS = {
    'AND': 'and',
    'OR': 'or',
    'NOT': 'not',
}

# Punctuation characters (organised by function)
PUNCTUATION = {
    # Function call syntax
    'CALL_END': ';',       # Semicolon ends function call (function terminator)

    # Separators
    'STMT_SEP': '|',       # Pipe separates statements on same line
    'EXPR_SEP': ',',       # Comma separates expressions/parameters

    # Object/property access
    'ACCESSOR': '.',       # Dot accesses object properties (obj.property)

    # Grouping
    'GROUP_START': '(',    # Parenthesis start
    'GROUP_END': ')',      # Parenthesis end

    # Arrays/slices
    'ARRAY_START': '[',    # Bracket start (array literal or index)
    'ARRAY_END': ']',      # Bracket end

    # Objects/dictionaries
    'OBJ_START': '{',      # Brace start (object literal)
    'OBJ_END': '}',        # Brace end

    # Control flow
    'BLOCK_HEADER': ':',   # Colon ends control flow headers (if/while/def:)
}

# Comment markers
COMMENT_MARKERS = {
    'LINE': '#',
    'BLOCK_START': '###',
    'BLOCK_END': '###',
}

# Operator precedence (higher number = higher precedence)
# Scale: 0-1000 for flexible custom operator insertion
OPERATOR_PRECEDENCE = {
    'COMMA': 50,
    'ASSIGN': 100,           # Standard assignment (=)
    'COMPOUND_ASSIGN': 150,  # Compound assignment (+=, -=, etc.)
    'TERNARY': 200,
    'OR': 300,
    'AND': 400,
    'NOT': 500,
    'CMP': 600,              # Comparison operators
    'ADD': 700,              # Addition/subtraction
    'MUL': 800,              # Multiplication/division
    'POW': 900,              # Power/exponentiation
    'UNARY': 950,            # Unary operators
    'PAREN': 1000,           # Parentheses (highest)
}

# ============================================================
# TOKEN DEFINITIONS
# ============================================================

# Token types
TOKEN_NUMBER = "NUMBER"
TOKEN_STRING = "STRING"
TOKEN_IDENT = "IDENT"
TOKEN_KEYWORD = "KEYWORD"
TOKEN_OP = "OP"
TOKEN_DOT = "DOT"
TOKEN_LPAREN = "LPAREN"
TOKEN_RPAREN = "RPAREN"
TOKEN_LBRACKET = "LBRACKET"
TOKEN_RBRACKET = "RBRACKET"
TOKEN_COMMA = "COMMA"
TOKEN_COLON = "COLON"
TOKEN_SEMICOLON = "SEMICOLON"
TOKEN_PIPE = "PIPE"
TOKEN_QUESTION = "QUESTION"
TOKEN_EOF = "EOF"


# ============================================================
# TOKEN CLASS
# ============================================================

class Token:
    """Token class for lexical analysis."""

    __slots__ = ("type", "value", "line", "col", "length")

    def __init__(self, type_, value=None, line=0, col=0, length=None):
        self.type = type_
        self.value = value
        self.line = line
        self.col = col
        self.length = length if length is not None else 1

    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, l={self.line}, c={self.col})"

    def __eq__(self, other):
        if not isinstance(other, Token):
            return False
        return self.type == other.type and self.value == other.value


# ============================================================
# KEYWORD / BUILT-IN HELPERS
# ============================================================

def is_keyword(text):
    """Check whether *text* is an active keyword (respects SYNTAX overrides)."""
    return text in KEYWORDS


def is_builtin(text):
    """Check whether *text* is an active built-in (respects SYNTAX overrides)."""
    return text in BUILTINS


# ============================================================
# OPERATOR TABLE - DYNAMIC
# ============================================================

# Operator precedence and associativity mapping
# This defines which operators from each dictionary get which precedence/associativity
# Levels map directly to OPERATOR_PRECEDENCE dictionary (Single Source of Truth)
_OPERATOR_CONFIG = {
    # Arithmetic operators
    'ARITHMETIC': {
        'POW': (lambda: OPERATOR_PRECEDENCE['POW'], "right"),
        'CARET': (lambda: OPERATOR_PRECEDENCE['POW'], "left"),
        'MUL': (lambda: OPERATOR_PRECEDENCE['MUL'], "left"),
        'DIV': (lambda: OPERATOR_PRECEDENCE['MUL'], "left"),
        'FLOOR_DIV': (lambda: OPERATOR_PRECEDENCE['MUL'], "left"),
        'MOD': (lambda: OPERATOR_PRECEDENCE['MUL'], "left"),
        'ADD': (lambda: OPERATOR_PRECEDENCE['ADD'], "left"),
        'SUB': (lambda: OPERATOR_PRECEDENCE['ADD'], "left"),
    },
    # Comparison operators
    'COMPARISON': {
        'LOOSE_EQ': (lambda: OPERATOR_PRECEDENCE['CMP'], "left"),
        'STRICT_EQ': (lambda: OPERATOR_PRECEDENCE['CMP'], "left"),
        'IDENTITY_EQ': (lambda: OPERATOR_PRECEDENCE['CMP'], "left"),
        'LOOSE_NE': (lambda: OPERATOR_PRECEDENCE['CMP'], "left"),
        'STRICT_NE': (lambda: OPERATOR_PRECEDENCE['CMP'], "left"),
        'IDENTITY_NE': (lambda: OPERATOR_PRECEDENCE['CMP'], "left"),
        'LT': (lambda: OPERATOR_PRECEDENCE['CMP'], "left"),
        'GT': (lambda: OPERATOR_PRECEDENCE['CMP'], "left"),
        'LTE': (lambda: OPERATOR_PRECEDENCE['CMP'], "left"),
        'GTE': (lambda: OPERATOR_PRECEDENCE['CMP'], "left"),
        'IN': (lambda: OPERATOR_PRECEDENCE['CMP'], "left"),
    },
    # Assignment operators (compound assignments)
    'ASSIGNMENT': {
        'ADD': (lambda: OPERATOR_PRECEDENCE['COMPOUND_ASSIGN'], "right"),
        'SUB': (lambda: OPERATOR_PRECEDENCE['COMPOUND_ASSIGN'], "right"),
        'MUL': (lambda: OPERATOR_PRECEDENCE['COMPOUND_ASSIGN'], "right"),
        'DIV': (lambda: OPERATOR_PRECEDENCE['COMPOUND_ASSIGN'], "right"),
        'FLOOR_DIV': (lambda: OPERATOR_PRECEDENCE['COMPOUND_ASSIGN'], "right"),
        'MOD': (lambda: OPERATOR_PRECEDENCE['COMPOUND_ASSIGN'], "right"),
        'POW': (lambda: OPERATOR_PRECEDENCE['COMPOUND_ASSIGN'], "right"),
    },
    # Custom operators (user-definable) - these are added separately
    'CUSTOM': {
        # These will be added dynamically from a separate config
    },
}

# Additional custom operators that aren't in the main dictionaries
# Aligned with 0-1000 precedence scale
_CUSTOM_OPERATORS = {
    "^": (OPERATOR_PRECEDENCE['POW'], "left"),
    "~>": (OPERATOR_PRECEDENCE['ADD'], "right"),
    "<~": (OPERATOR_PRECEDENCE['ADD'], "left"),
    "@@": (OPERATOR_PRECEDENCE['MUL'], "left"),
    "++": (OPERATOR_PRECEDENCE['ADD'], "left"),
}


def register_custom_operator(op_symbol, precedence, associativity="left"):
    """Register a custom operator at runtime.

    Args:
        op_symbol: The operator symbol (e.g., '^', '~~', '>>>')
        precedence: Precedence level (0-1000, where 1000 is highest)
        associativity: "left" or "right" (default: "left")

    Raises:
        SyntaxError: If precedence is outside the valid range (0-1000)

    Example:
        register_custom_operator('~~', 750, "right")
        refresh_syntax()
    """
    if precedence < 0 or precedence > 1000:
        raise BicalaValueError(
            code="V007",
            line=0,
            col=0,
            precedence=precedence
        )
    global _CUSTOM_OPERATORS
    _CUSTOM_OPERATORS[op_symbol] = (precedence, associativity)


def unregister_custom_operator(op_symbol):
    """Unregister a custom operator at runtime.

    Args:
        op_symbol: The operator symbol to remove

    Example:
        unregister_custom_operator('~~')
        refresh_syntax()
    """
    global _CUSTOM_OPERATORS
    if op_symbol in _CUSTOM_OPERATORS:
        del _CUSTOM_OPERATORS[op_symbol]


def _build_operators():
    """Dynamically build OPERATORS dictionary from operator configuration."""
    operators = {}
    
    # Build from arithmetic operators
    for key, (prec_fn, assoc) in _OPERATOR_CONFIG['ARITHMETIC'].items():
        if key in ARITHMETIC_OPERATORS:
            op = ARITHMETIC_OPERATORS[key]
            operators[op] = (prec_fn(), assoc)
    
    # Build from comparison operators
    for key, (prec_fn, assoc) in _OPERATOR_CONFIG['COMPARISON'].items():
        if key in COMPARISON_OPERATORS:
            op = COMPARISON_OPERATORS[key]
            operators[op] = (prec_fn(), assoc)
    
    # Build from assignment operators
    for key, (prec_fn, assoc) in _OPERATOR_CONFIG['ASSIGNMENT'].items():
        if key in ASSIGNMENT_OPERATORS:
            op = ASSIGNMENT_OPERATORS[key]
            operators[op] = (prec_fn(), assoc)
    
    # Add custom operators
    operators.update(_CUSTOM_OPERATORS)
    
    return operators


def _build_all_operators():
    """Build longest-first list for lexer matching."""
    return sorted(OPERATORS.keys(), key=len, reverse=True)


def _build_multi_char_operators():
    """Build list of multi-character operators."""
    return [op for op in ALL_OPERATORS if len(op) > 1]


def _build_single_char_operators():
    """Build list of single-character operators."""
    return [op for op in ALL_OPERATORS if len(op) == 1]


# Dynamic operator tables (will be rebuilt by refresh_syntax())
OPERATORS = _build_operators()
ALL_OPERATORS = _build_all_operators()
MULTI_CHAR_OPERATORS = _build_multi_char_operators()
SINGLE_CHAR_OPERATORS = _build_single_char_operators()


def is_operator(op):
    return op in OPERATORS


def get_precedence(op):
    return OPERATORS[op][0]


def get_associativity(op):
    return OPERATORS[op][1]


def is_right_associative(op):
    return OPERATORS[op][1] == "right"


# ============================================================
# SYNTAX CONFIG (merged from cfg.py)
# Singleton providing convenient property access to all
# syntax definitions above.
# ============================================================

class SyntaxConfig:
    """Singleton accessor for the syntax tables defined in tok.py."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def assignment_operators(self):
        """All assignment operators as list."""
        return list(ASSIGNMENT_OPERATORS.values())

    @property
    def assignment_operators_dict(self):
        """All assignment operators as dictionary (for key access)."""
        return ASSIGNMENT_OPERATORS

    @property
    def comparison_operators(self):
        """All comparison operators as list."""
        return list(COMPARISON_OPERATORS.values())

    @property
    def arithmetic_operators(self):
        """All arithmetic operators."""
        return list(ARITHMETIC_OPERATORS.values())

    @property
    def logical_operators(self):
        """All logical operators."""
        return list(LOGICAL_OPERATORS.values())

    @property
    def punctuation(self):
        """All punctuation characters as dict."""
        return PUNCTUATION

    @property
    def keywords(self):
        """All active keywords as set (respects SYNTAX overrides)."""
        return KEYWORDS

    @property
    def comment_markers(self):
        """Comment markers."""
        return COMMENT_MARKERS

    @property
    def operator_precedence(self):
        """Operator precedence mapping."""
        return OPERATOR_PRECEDENCE


# Global singleton — drop-in replacement for the old cfg.config
config = SyntaxConfig()
