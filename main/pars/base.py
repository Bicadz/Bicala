# ============================================================
# base.py — Parser core & helpers
# Imports, constants, and helper functions for parsing
# ============================================================

from tok import (
    Token, TOKEN_NUMBER, TOKEN_STRING, TOKEN_IDENT, TOKEN_KEYWORD,
    TOKEN_OP, TOKEN_DOT, TOKEN_LPAREN, TOKEN_RPAREN, TOKEN_LBRACKET, TOKEN_RBRACKET,
    TOKEN_COMMA, TOKEN_COLON, TOKEN_SEMICOLON, TOKEN_PIPE, TOKEN_QUESTION, TOKEN_EOF,
    KEYWORDS, BUILTINS, SYNTAX, get_syntax, is_keyword, is_builtin,
    PUNCTUATION, COMMENT_MARKERS,
    ASSIGNMENT_OPERATORS, COMPARISON_OPERATORS, ARITHMETIC_OPERATORS,
    LOGICAL_OPERATORS,
)
from ast import (
    NumberNode, BooleanNode, StringNode, VarNode, ArrayNode, UnaryOpNode, BinaryOpNode,
    CompareNode, CallNode, IndexNode, SliceNode, TernaryNode, InlineIfNode, AttrNode, LambdaNode, TypeNode,
    NoneNode, NaNNode,
    ExprStmtNode, AssignNode, CompoundAssignNode, IncDecNode,
    SayNode, InputNode, DebugNode, ErrorNode, ReturnNode, BreakNode, ContinueNode,
    BlockNode, IfNode, WhileNode,
    ForNode, DefNode, CommentNode, HelpNode, ImportNode, FromImportNode,
    CustomOperatorDef, CustomOperatorCall, SwitchNode, DelNode, PassNode
)
from lex import tokenize
from err import BicalaSyntaxError, BicalaIndentationError

import re

# ---------------------------------------------------------------------------
# Precompute operator sets from tok.py dictionaries so we never index a list.
# ---------------------------------------------------------------------------
_COMPARISON_OPS = set(COMPARISON_OPERATORS.values()) | {'.='}
_ADD_OPS = {ARITHMETIC_OPERATORS['ADD'], ARITHMETIC_OPERATORS['SUB']}            # {'+', '-'}
_MUL_OPS = {ARITHMETIC_OPERATORS['MUL'], ARITHMETIC_OPERATORS['DIV'],
            ARITHMETIC_OPERATORS['FLOOR_DIV'], ARITHMETIC_OPERATORS['MOD']}      # {'*','/','//', '%'}
_POW_OPS = {ARITHMETIC_OPERATORS['POW'], ARITHMETIC_OPERATORS['CARET']}          # {'**', '^'}
_KW_AND = LOGICAL_OPERATORS['AND']    # 'and'
_KW_OR  = LOGICAL_OPERATORS['OR']     # 'or'
_KW_NOT = LOGICAL_OPERATORS['NOT']    # 'not'


def _line_indent(raw_line):
    """Count leading spaces (4-space tabs)."""
    expanded = raw_line.replace('\t', '    ')
    return len(expanded) - len(expanded.lstrip(' '))


def _line_indent_level(raw_line, line_num=0):
    """Get indentation level (0-based)."""
    spaces = _line_indent(raw_line)
    if spaces % 4 != 0:
        raise BicalaIndentationError(
            code="S014",
            line=line_num,
            col=0,
            spaces=spaces
        )
    return spaces // 4


def _is_block_header(line):
    """Check if line starts a block structure."""
    normalized = line.strip()
    if normalized.endswith(PUNCTUATION['BLOCK_HEADER']):
        normalized = normalized[:-len(PUNCTUATION['BLOCK_HEADER'])].strip()
    kw_if = get_syntax('IF')
    kw_while = get_syntax('WHILE')
    kw_forever = get_syntax('FOREVER')
    kw_repeat = get_syntax('REPEAT')
    kw_for = get_syntax('FOR')
    kw_def = get_syntax('DEF')
    kw_switch = get_syntax('SWITCH')
    kw_elif = get_syntax('ELIF')
    kw_else = get_syntax('ELSE')
    kw_defer = get_syntax('DEFER')
    kw_try = get_syntax('TRY')
    kw_catch = get_syntax('CATCH')
    kw_finally = get_syntax('FINALLY')
    return (
        normalized.startswith(kw_if + ' ') or
        normalized.startswith(kw_while + ' ') or
        normalized == kw_forever or
        normalized.startswith(kw_forever + PUNCTUATION['BLOCK_HEADER']) or
        normalized.startswith(kw_repeat) or
        normalized.startswith(kw_for + ' ') or
        normalized.startswith(kw_def + ' ') or
        normalized.startswith(kw_switch + ' ') or
        normalized == kw_defer or
        normalized.startswith(kw_defer + PUNCTUATION['BLOCK_HEADER']) or
        normalized.startswith(kw_try) or
        normalized.startswith(kw_catch) or
        normalized.startswith(kw_finally)
    )


def _split_statements(line):
    """
    Split a line by statement separators (| and ;) at top level only.
    Does not split inside parentheses, brackets, or strings.
    """
    parts = []
    current_chars = []
    paren_depth = 0
    bracket_depth = 0
    in_string = None
    
    i = 0
    while i < len(line):
        ch = line[i]
        
        # Track string state
        if in_string is not None:
            current_chars.append(ch)
            if ch == '\\' and i + 1 < len(line):
                current_chars.append(line[i + 1])
                i += 2
                continue
            if ch == in_string:
                in_string = None
            i += 1
            continue
        
        if ch in ('"', "'"):
            in_string = ch
            current_chars.append(ch)
            i += 1
            continue
        
        if ch == '(':
            paren_depth += 1
            current_chars.append(ch)
        elif ch == ')':
            paren_depth -= 1
            current_chars.append(ch)
        elif ch == '[':
            bracket_depth += 1
            current_chars.append(ch)
        elif ch == ']':
            bracket_depth -= 1
            current_chars.append(ch)
        elif (ch == PUNCTUATION['STMT_SEP'] or ch == PUNCTUATION['CALL_END']) and paren_depth == 0 and bracket_depth == 0:
            # Pipe or semicolon at top level — split here
            parts.append(''.join(current_chars))
            current_chars = []
        else:
            current_chars.append(ch)
        i += 1
    
    # Add the last part
    if current_chars:
        parts.append(''.join(current_chars))
    
    return [p for p in parts if p.strip()]


def _find_block_range(lines, start_idx, base_indent):
    """
    Find the range of a block (indented lines after header).
    Returns: (block_start_idx, next_idx_after_block) or (-1, -1) if no block found.
    """
    i = start_idx + 1
    block_start = -1
    
    while i < len(lines):
        raw = lines[i]
        line = raw.strip()
        
        if not line or line.startswith(COMMENT_MARKERS['LINE']):
            i += 1
            continue
        
        try:
            indent = _line_indent_level(raw, i + 1)
        except BicalaIndentationError:
            raise
        
        if indent > base_indent:
            block_start = i
            break
        else:
            raise BicalaIndentationError(
                code="S011",
                line=i + 1,
                col=0,
                expected=base_indent + 1,
                got=indent
            )
        
        i += 1
    
    if block_start < 0:
        return -1, start_idx + 1
    
    # Find end of block
    while i < len(lines):
        raw = lines[i]
        line = raw.strip()
        
        if not line or line.startswith('#'):
            i += 1
            continue
        
        try:
            indent = _line_indent_level(raw, i + 1)
        except BicalaIndentationError:
            raise
        
        if indent <= base_indent:
            break
        
        i += 1
    
    return block_start, i
