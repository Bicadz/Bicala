# ============================================================
# lex.py — Tokenizer for BImuila language
# Converts source code into token stream
# Imports: tok only (no circular deps, no cfg.py)
# ============================================================

from tok import (
    Token, is_keyword, is_builtin,
    KEYWORDS, BUILTINS, SYNTAX, resolve_syntax,
    TOKEN_NUMBER, TOKEN_STRING, TOKEN_IDENT, TOKEN_KEYWORD,
    TOKEN_OP, TOKEN_DOT, TOKEN_LPAREN, TOKEN_RPAREN, TOKEN_LBRACKET, TOKEN_RBRACKET,
    TOKEN_COMMA, TOKEN_COLON, TOKEN_SEMICOLON, TOKEN_PIPE, TOKEN_EOF,
    OPERATORS, MULTI_CHAR_OPERATORS, SINGLE_CHAR_OPERATORS,
    PUNCTUATION, COMMENT_MARKERS, COMPARISON_OPERATORS,
)
from err import BicalaLexerError

# ---------------------------------------------------------------------------
# Build combined operator list including .= (loose equality) so the lexer
# can match it before '.' is consumed as an accessor token.
# Sorted longest-first so compound operators are never split.
# ---------------------------------------------------------------------------
_EXTRA_OPERATORS = {'.='}  # Operators recognised by the lexer but not in tok.OPERATORS
_ALL_OP_STRINGS = set(OPERATORS.keys()) | _EXTRA_OPERATORS
_ALL_OPERATORS_SORTED = sorted(_ALL_OP_STRINGS, key=len, reverse=True)
_MULTI_CHAR_OPERATORS_SORTED = [op for op in _ALL_OPERATORS_SORTED if len(op) > 1]
_SINGLE_CHAR_OPERATORS_SORTED = [op for op in _ALL_OPERATORS_SORTED if len(op) == 1]

# Punctuation values for quick lookup (excluding '.', which needs special handling)
_PUNCT_VALUES = set(PUNCTUATION.values())


def tokenize(expr, line_num=1, base_col=0):
    """
    Tokenize expression into list of tokens.
    
    :param expr: Source string to tokenize
    :param line_num: Starting line number for error reporting
    :param base_col: 0-based column offset for the first character
    :return: List of Token objects
    """
    tokens = []
    i = 0
    length = len(expr)
    # Internal column is 0-based; emitted token/error columns are 1-based.
    col = base_col
    
    while i < length:
        ch = expr[i]
        start_col = col + 1
        
        # Skip whitespace
        if ch.isspace():
            if ch == '\n':
                line_num += 1
                col = 0
            else:
                col += 1
            i += 1
            continue
        
        # ---- Block comment (###...###) ----
        block_start = COMMENT_MARKERS['BLOCK_START']
        block_end = COMMENT_MARKERS['BLOCK_END']
        if expr.startswith(block_start, i):
            i += len(block_start)
            col += len(block_start)
            block_start_line = line_num
            while i < length:
                if expr.startswith(block_end, i):
                    i += len(block_end)
                    col += len(block_end)
                    break
                if expr[i] == '\n':
                    line_num += 1
                    col = 0
                else:
                    col += 1
                i += 1
            else:
                raise BicalaLexerError(
                    code="L006",
                    line=block_start_line,
                    col=col - 2
                )
            continue

        # ---- Single-line comment ----
        line_comment = COMMENT_MARKERS['LINE']
        if ch == line_comment:
            while i < length and expr[i] != '\n':
                i += 1
                col += 1
            continue
        
        # ---- Multi-character operators (longest-first, BEFORE punctuation) ----
        # This ensures compound operators like .=, **:, ==, !==, etc.
        # are matched completely and never split.
        found_multi = False
        for op in _MULTI_CHAR_OPERATORS_SORTED:
            if expr.startswith(op, i):
                tokens.append(Token(TOKEN_OP, op, line_num, start_col))
                i += len(op)
                col += len(op)
                found_multi = True
                break
        if found_multi:
            continue
        
        # ---- Punctuation (single-char structural tokens) ----
        if ch in _PUNCT_VALUES:
            if ch == PUNCTUATION['GROUP_START']:
                tokens.append(Token(TOKEN_LPAREN, ch, line_num, start_col))
            elif ch == PUNCTUATION['GROUP_END']:
                tokens.append(Token(TOKEN_RPAREN, ch, line_num, start_col))
            elif ch == PUNCTUATION['ARRAY_START']:
                tokens.append(Token(TOKEN_LBRACKET, ch, line_num, start_col))
            elif ch == PUNCTUATION['ARRAY_END']:
                tokens.append(Token(TOKEN_RBRACKET, ch, line_num, start_col))
            elif ch == PUNCTUATION['EXPR_SEP']:
                tokens.append(Token(TOKEN_COMMA, ch, line_num, start_col))
            elif ch == PUNCTUATION['CALL_END']:
                tokens.append(Token(TOKEN_SEMICOLON, ch, line_num, start_col))
            elif ch == PUNCTUATION['STMT_SEP']:
                tokens.append(Token(TOKEN_PIPE, ch, line_num, start_col))
            elif ch == PUNCTUATION['BLOCK_HEADER']:
                tokens.append(Token(TOKEN_COLON, ch, line_num, start_col))
            elif ch == PUNCTUATION['ACCESSOR']:
                # Dot: emit as TOKEN_DOT (property access)
                # (compound '.=' already caught above in multi-char pass)
                tokens.append(Token(TOKEN_DOT, ch, line_num, start_col))
            # OBJ_START / OBJ_END — currently unused in lexer but safe to skip
            i += 1
            col += 1
            continue
        
        # ---- String literals ----
        if ch == '"' or ch == "'":
            quote = ch
            i += 1
            col += 1
            string_parts = []  # List of (is_literal, value) tuples
            current_literal = []
            string_start = start_col
            in_interpolation = False
            interpolation_start = 0
            
            while i < length:
                if expr[i] == '\\' and i + 1 < length:
                    # Handle escape sequences
                    escape_col = col + 1
                    next_char = expr[i + 1]
                    if next_char == 'n':
                        current_literal.append('\n')
                    elif next_char == 't':
                        current_literal.append('\t')
                    elif next_char == 'r':
                        current_literal.append('\r')
                    elif next_char == '\\':
                        current_literal.append('\\')
                    elif next_char == '"' or next_char == "'":
                        current_literal.append(next_char)
                    elif next_char == '{':
                        current_literal.append('{')
                    elif next_char == '}':
                        current_literal.append('}')
                    else:
                        raise BicalaLexerError(
                            code="L003",
                            line=line_num,
                            col=escape_col,
                            char=next_char
                        )
                    i += 2
                    col += 2
                    continue
                
                if expr[i] == '\n':
                    raise BicalaLexerError(
                        code="L004",
                        line=line_num,
                        col=col + 1
                    )
                
                if expr[i] == quote:
                    # End of string
                    if in_interpolation:
                        raise BicalaLexerError(
                            code="L007",
                            line=line_num,
                            col=col + 1
                        )
                    # Flush any remaining literal
                    if current_literal:
                        string_parts.append((True, ''.join(current_literal)))
                    break
                
                # Handle interpolation {variable}
                if expr[i] == '{' and not in_interpolation:
                    # Save current literal part
                    if current_literal:
                        string_parts.append((True, ''.join(current_literal)))
                        current_literal = []
                    # Start interpolation
                    in_interpolation = True
                    interpolation_start = col + 1
                    i += 1
                    col += 1
                    continue
                
                if expr[i] == '}' and in_interpolation:
                    # End interpolation
                    var_name = ''.join(current_literal)
                    if not var_name:
                        raise BicalaLexerError(
                            code="L008",
                            line=line_num,
                            col=interpolation_start
                        )
                    string_parts.append((False, var_name))
                    current_literal = []
                    in_interpolation = False
                    i += 1
                    col += 1
                    continue
                
                # Regular character
                current_literal.append(expr[i])
                i += 1
                col += 1
            
            if i >= length or expr[i] != quote:
                if in_interpolation:
                    raise BicalaLexerError(
                        code="L007",
                        line=line_num,
                        col=col + 1
                    )
                raise BicalaLexerError(
                    code="L001",
                    line=line_num,
                    col=string_start
                )
            
            i += 1  # Skip closing quote
            col += 1
            
            # Store string as either simple string or interpolated string
            # If no interpolation, store as simple string for backward compatibility
            has_interpolation = any(not is_literal for is_literal, _ in string_parts)
            if has_interpolation:
                # Store as tuple: ('INTERPOLATED', parts_list)
                tokens.append(Token(TOKEN_STRING, ('INTERPOLATED', string_parts), line_num, string_start))
            else:
                # Simple string - store as before
                string_value = string_parts[0][1] if string_parts else ''
                tokens.append(Token(TOKEN_STRING, string_value, line_num, string_start))
            continue
        
        # ---- Numbers (integers and floats) ----
        if ch.isdigit() or (ch == '.' and i + 1 < length and expr[i + 1].isdigit()):
            num_chars = []
            num_start = start_col
            
            if ch == '.':
                num_chars.append(ch)
                i += 1
                col += 1
                while i < length and expr[i].isdigit():
                    num_chars.append(expr[i])
                    i += 1
                    col += 1
            else:
                while i < length and expr[i].isdigit():
                    num_chars.append(expr[i])
                    i += 1
                    col += 1
                
                if i < length and expr[i] == '.':
                    num_chars.append('.')
                    i += 1
                    col += 1
                    while i < length and expr[i].isdigit():
                        num_chars.append(expr[i])
                        i += 1
                        col += 1
            
            num_str = ''.join(num_chars)
            # Convert to int or float
            if '.' in num_str:
                value = float(num_str)
            else:
                value = int(num_str)

            if i < length and (expr[i].isalpha() or expr[i] == '_'):
                bad_tail = expr[i]
                raise BicalaLexerError(
                    code="L005",
                    line=line_num,
                    col=col + 1,
                    char=bad_tail
                )
            
            tokens.append(Token(TOKEN_NUMBER, value, line_num, num_start))
            continue
        
        # ---- Identifiers and keywords ----
        if ch.isalpha() or ch == '_':
            ident_chars = []
            ident_start = start_col
            while i < length and (expr[i].isalnum() or expr[i] == '_'):
                ident_chars.append(expr[i])
                i += 1
                col += 1
            
            ident = ''.join(ident_chars)

            # Dynamic keyword check via SYNTAX-derived KEYWORDS set
            if is_keyword(ident) or is_builtin(ident):
                tokens.append(Token(TOKEN_KEYWORD, ident, line_num, ident_start))
            else:
                # Check if it resolves through SYNTAX (user-remapped keyword)
                internal = resolve_syntax(ident)
                if internal is not None:
                    tokens.append(Token(TOKEN_KEYWORD, ident, line_num, ident_start))
                else:
                    tokens.append(Token(TOKEN_IDENT, ident, line_num, ident_start))
            continue

        # ---- Single-character operators ----
        if ch in _SINGLE_CHAR_OPERATORS_SORTED:
            tokens.append(Token(TOKEN_OP, ch, line_num, start_col))
            i += 1
            col += 1
            continue

        # ---- Handle remaining operator-like character sequences ----
        if not ch.isalnum() and not ch.isspace():
            op_start = i
            while i < length and not expr[i].isalnum() and not expr[i].isspace() and expr[i] not in _PUNCT_VALUES:
                i += 1
                col += 1
            if i > op_start:
                op = expr[op_start:i]
                tokens.append(Token(TOKEN_OP, op, line_num, start_col))
                continue
            i = op_start
            col = start_col - 1
        
        # ---- Unknown character ----
        raise BicalaLexerError(
            code="L002",
            line=line_num,
            col=start_col,
            char=ch
        )
    
    # Add EOF token
    tokens.append(Token(TOKEN_EOF, None, line_num, col + 1))
    return tokens
