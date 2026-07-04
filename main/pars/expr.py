# ============================================================
# expr.py — Expression parser
# Recursive descent with precedence climbing
# ============================================================

from pars.base import (
    get_syntax,
    NumberNode, BooleanNode, StringNode, VarNode, ArrayNode, UnaryOpNode, BinaryOpNode,
    CompareNode, CallNode, IndexNode, SliceNode, InlineIfNode, AttrNode, LambdaNode, TypeNode,
    NoneNode, NaNNode,
    BicalaSyntaxError,
    _COMPARISON_OPS, _ADD_OPS, _MUL_OPS, _POW_OPS, _KW_AND, _KW_OR, _KW_NOT,
    Token, TOKEN_NUMBER, TOKEN_STRING, TOKEN_IDENT, TOKEN_KEYWORD,
    TOKEN_OP, TOKEN_DOT, TOKEN_LPAREN, TOKEN_RPAREN, TOKEN_LBRACKET, TOKEN_RBRACKET,
    TOKEN_COMMA, TOKEN_COLON, TOKEN_SEMICOLON, TOKEN_PIPE, TOKEN_EOF,
)
from lex import tokenize
from env import get_custom_operator


def parse_expression_to_ast(tokens):
    """
    Parse expression tokens into AST.
    Uses recursive descent with precedence climbing.
    """
    pos = [0]
    last_was_semicolon = [False]  # Track if last expression ended with semicolon
    
    def current():
        return tokens[pos[0]] if pos[0] < len(tokens) else Token(TOKEN_EOF, None)
    
    def advance():
        tok = current()
        pos[0] += 1
        return tok

    def dotted_name_to_ast(name, line=0, col=0):
        parts = name.split('.')
        base = VarNode(parts[0], line, col)
        for attr in parts[1:]:
            base = AttrNode(base, attr, line, col)
        return base
    
    # Context-aware error hints for common expected tokens
    _HINTS = {
        TOKEN_RPAREN: "Expected ')' to close expression",
        TOKEN_RBRACKET: "Expected ']' to close array/index",
        TOKEN_NUMBER: "Expected a number",
        TOKEN_STRING: "Expected a string (quoted text)",
        TOKEN_IDENT: "Expected a name/identifier",
        TOKEN_LPAREN: "Expected '('",
    }
    
    def consume(expected_type, expected_value=None):
        tok = current()
        if tok.type != expected_type:
            hint = _HINTS.get(expected_type, f"Expected {expected_type}")
            got = tok.value if tok.value else tok.type

            # Specific bracket error codes
            if expected_type == TOKEN_RPAREN:
                raise BicalaSyntaxError(
                    code="S015",
                    line=tok.line,
                    col=tok.col,
                    expected="')'",
                    got=got,
                    length=tok.length
                )
            if expected_type == TOKEN_RBRACKET:
                raise BicalaSyntaxError(
                    code="S015",
                    line=tok.line,
                    col=tok.col,
                    expected="']'",
                    got=got,
                    length=tok.length
                )

            # Use specific error codes based on expected type
            if expected_type == TOKEN_IDENT:
                raise BicalaSyntaxError(
                    code="S002",
                    line=tok.line,
                    col=tok.col,
                    got=got,
                    length=tok.length
                )
            raise BicalaSyntaxError(
                code="S001",
                line=tok.line,
                col=tok.col,
                got=got,
                length=tok.length
            )
        if expected_value is not None and tok.value != expected_value:
            # Use S005 for missing colon after block header
            if expected_value == ':':
                raise BicalaSyntaxError(
                    code="S005",
                    line=tok.line,
                    col=tok.col,
                    expected="':'",
                    got=tok.value,
                    length=tok.length
                )
            raise BicalaSyntaxError(
                code="S002",
                line=tok.line,
                col=tok.col,
                expected=expected_value,
                got=tok.value,
                length=tok.length
            )
        return advance()
    
    def is_expr_start(tok):
        """Check if token can start an expression."""
        return tok.type in {TOKEN_NUMBER, TOKEN_STRING, TOKEN_IDENT, TOKEN_LPAREN, 
                           TOKEN_LBRACKET, TOKEN_OP} or (
            tok.type == TOKEN_KEYWORD and tok.value in {'true', 'false'})
    
    def is_arg_start(tok):
        """Check if token can start a function call argument (more restrictive)."""
        if tok.type in {TOKEN_NUMBER, TOKEN_STRING, TOKEN_IDENT, TOKEN_LPAREN, TOKEN_LBRACKET}:
            return True
        if tok.type == TOKEN_KEYWORD and tok.value in {'true', 'false'}:
            return True
        return False
    
    # Precedence levels (lowest to highest)
    def parse_comma():
        """Comma/concatenation (lowest precedence)."""
        left = parse_inline_if()
        while current().type == TOKEN_COMMA:
            tok = advance()
            right = parse_inline_if()
            left = BinaryOpNode(',', left, right, tok.line, tok.col)
        return left
    
    def parse_inline_if():
        """Inline if: if cond: true_expr { elif cond: expr } else: false_expr"""
        # Check if we're at the start of an inline if expression
        if current().type == TOKEN_KEYWORD and current().value == get_syntax('IF'):
            tok = advance()
            # Parse condition
            cond = parse_or()
            # Expect colon after condition
            if current().type != TOKEN_COLON:
                raise BicalaSyntaxError(
                    code="S005",
                    line=current().line,
                    col=current().col,
                    expected=":",
                    got=current().value
                )
            advance()  # consume colon
            # Parse true expression
            true_expr = parse_or()
            
            # Parse optional elif branches
            elif_branches = []
            while current().type == TOKEN_KEYWORD and current().value == get_syntax('ELIF'):
                elif_tok = advance()
                # Parse elif condition
                elif_cond = parse_or()
                # Expect colon after elif condition
                if current().type != TOKEN_COLON:
                    raise BicalaSyntaxError(
                        code="S005",
                        line=current().line,
                        col=current().col,
                        expected=":",
                        got=current().value
                    )
                advance()  # consume colon
                # Parse elif expression
                elif_expr = parse_or()
                elif_branches.append((elif_cond, elif_expr))
            
            # Expect 'else' keyword
            if current().type != TOKEN_KEYWORD or current().value != get_syntax('ELSE'):
                raise BicalaSyntaxError(
                    code="S025",
                    line=current().line,
                    col=current().col,
                    expected="else",
                    got=current().value
                )
            advance()  # consume else
            # Expect colon after else
            if current().type != TOKEN_COLON:
                raise BicalaSyntaxError(
                    code="S005",
                    line=current().line,
                    col=current().col,
                    expected=":",
                    got=current().value
                )
            advance()  # consume colon
            # Parse false expression
            false_expr = parse_or()
            return InlineIfNode(cond, true_expr, elif_branches, false_expr, tok.line, tok.col)
        # Not an inline if, parse as regular expression
        return parse_or()
    
    def parse_or():
        left = parse_and()
        while current().type == TOKEN_KEYWORD and current().value == _KW_OR:
            tok = advance()
            right = parse_and()
            left = BinaryOpNode(tok.value, left, right, tok.line, tok.col)
        return left
    
    def parse_and():
        left = parse_not()
        while current().type == TOKEN_KEYWORD and current().value == _KW_AND:
            tok = advance()
            right = parse_not()
            left = BinaryOpNode(tok.value, left, right, tok.line, tok.col)
        return left
    
    def parse_not():
        if current().type == TOKEN_KEYWORD and current().value == _KW_NOT:
            tok = advance()
            operand = parse_not()
            return UnaryOpNode(tok.value, operand, tok.line, tok.col)
        return parse_comparison()
    
    def parse_comparison():
        left = parse_add()
        tok = current()
        if tok.type == TOKEN_OP and tok.value in _COMPARISON_OPS:
            op_tok = advance()
            op = op_tok.value
            right = parse_add()
            return CompareNode(op, left, right, tok.line, tok.col)
        return left
    
    def parse_add():
        left = parse_mul()
        while current().type == TOKEN_OP and current().value in _ADD_OPS:
            tok = advance()
            op = tok.value
            if not is_expr_start(current()):
                raise BicalaSyntaxError(
                    code="S003",
                    line=tok.line,
                    col=tok.col,
                    op=op,
                    length=tok.length
                )
            right = parse_mul()
            left = BinaryOpNode(op, left, right, tok.line, tok.col)
        return left
    
    def parse_mul():
        left = parse_power()
        while current().type == TOKEN_OP and current().value in _MUL_OPS:
            tok = advance()
            op = tok.value
            if not is_expr_start(current()):
                raise BicalaSyntaxError(
                    code="S003",
                    line=tok.line,
                    col=tok.col,
                    op=op,
                    length=tok.length
                )
            right = parse_power()
            left = BinaryOpNode(op, left, right, tok.line, tok.col)
        return left
    
    def parse_power():
        """Exponentiation - right associative."""
        left = parse_unary()
        if current().type == TOKEN_OP and current().value in _POW_OPS:
            tok = advance()
            right = parse_power()  # Right recursive
            return BinaryOpNode(tok.value, left, right, tok.line, tok.col)
        return left
    
    def parse_unary():
        if current().type == TOKEN_OP and current().value in _ADD_OPS:
            op_tok = advance()
            operand = parse_unary()
            return UnaryOpNode(op_tok.value, operand, op_tok.line, op_tok.col)
        # Handle custom prefix operators
        if current().type == TOKEN_OP:
            op_tok = current()
            custom_op = get_custom_operator(op_tok.value)
            if custom_op and custom_op["type"] == "prefix":
                advance()  # consume the operator
                operand = parse_unary()
                # Create CustomOperatorCall for prefix operator
                from main.ast import CustomOperatorCall
                return CustomOperatorCall(op_tok.value, "prefix", [operand], op_tok.line, op_tok.col)
            # Handle custom multi-character prefix operators (legacy fallback)
            if len(op_tok.value) > 1:
                advance()
                operand = parse_unary()
                return UnaryOpNode(op_tok.value, operand, op_tok.line, op_tok.col)
        return parse_primary()
    
    def parse_postfix_on_node(base_node):
        """Handle postfix operators on any node."""
        while True:
            # Handle custom postfix operators
            if current().type == TOKEN_OP:
                op_tok = current()
                custom_op = get_custom_operator(op_tok.value)
                if custom_op and custom_op["type"] == "postfix":
                    advance()  # consume the operator
                    # Create CustomOperatorCall for postfix operator
                    from main.ast import CustomOperatorCall
                    base_node = CustomOperatorCall(op_tok.value, "postfix", [base_node], op_tok.line, op_tok.col)
                    continue
            break
        return base_node
    
    def parse_primary():
        tok = current()
        
        # Number literal
        if tok.type == TOKEN_NUMBER:
            advance()
            node = NumberNode(tok.value, tok.line, tok.col)
            # Handle postfix operators after number literals
            return parse_postfix_on_node(node)
        
        # String literal
        if tok.type == TOKEN_STRING:
            advance()
            node = StringNode(tok.value, tok.line, tok.col)
            # Handle postfix operators after string literals
            return parse_postfix_on_node(node)

        if tok.type == TOKEN_KEYWORD and tok.value in {get_syntax('TRUE'), get_syntax('FALSE')}:
            advance()
            node = BooleanNode(tok.value == get_syntax('TRUE'), tok.line, tok.col)
            return parse_postfix_on_node(node)
        
        # None literal
        if tok.type == TOKEN_KEYWORD and tok.value == get_syntax('NONE'):
            advance()
            node = NoneNode(tok.line, tok.col)
            return parse_postfix_on_node(node)
        
        # NaN literal
        if tok.type == TOKEN_KEYWORD and tok.value == get_syntax('NAN'):
            advance()
            node = NaNNode(tok.line, tok.col)
            return parse_postfix_on_node(node)
        
        # Lambda: fn arg: expr
        if tok.type == TOKEN_KEYWORD and tok.value == get_syntax('LAMBDA'):
            advance()
            # Parse parameter (must be identifier)
            param_tok = current()
            if param_tok.type != TOKEN_IDENT:
                raise BicalaSyntaxError(
                    code="S002",
                    line=param_tok.line,
                    col=param_tok.col,
                    got=param_tok.value
                )
            param = param_tok.value
            
            # Check if parameter is a reserved keyword
            from tok import is_keyword
            if is_keyword(param):
                raise BicalaSyntaxError(
                    f"Cannot use reserved keyword '{param}' as an identifier",
                    code="S041", line=param_tok.line,
                    expected="valid identifier", got=f"'{param}'",
                    hint=f"'{param}' is a reserved keyword and cannot be used as a lambda parameter"
                )
            
            advance()
            
            # Expect colon
            if current().type != TOKEN_COLON:
                raise BicalaSyntaxError(
                    code="S005",
                    line=current().line,
                    col=current().col,
                    expected=":",
                    got=current().value
                )
            advance()
            
            # Parse body expression
            body = parse_inline_if()
            node = LambdaNode(param, body, tok.line, tok.col)
            return parse_postfix_on_node(node)
        
        # Input keyword as function call (for use in expressions like x: input "prompt")
        if tok.type == TOKEN_KEYWORD and tok.value == get_syntax('INPUT'):
            advance()
            # Parse arguments if present
            if is_arg_start(current()):
                args = [parse_add()]
                while current().type == TOKEN_COMMA:
                    advance()
                    args.append(parse_add())
                node = CallNode(VarNode('input', tok.line, tok.col), args, tok.line, tok.col)
                return parse_postfix_on_node(node)
            else:
                # No arguments - call with empty string prompt
                node = CallNode(VarNode('input', tok.line, tok.col), [StringNode("", tok.line, tok.col)], tok.line, tok.col)
                return parse_postfix_on_node(node)
        
        # Type keyword as function call (for type checking)
        if tok.type == TOKEN_KEYWORD and tok.value == get_syntax('TYPE'):
            advance()
            # Parse argument (required)
            if is_arg_start(current()):
                value = parse_inline_if()
                node = TypeNode(value, tok.line, tok.col)
                return parse_postfix_on_node(node)
            else:
                raise BicalaSyntaxError(
                    code="S003",
                    line=tok.line,
                    col=tok.col
                )
        
        # Identifier or function call
        if tok.type == TOKEN_IDENT:
            name = tok.value
            advance()
            base = dotted_name_to_ast(name, tok.line, tok.col)

            def parse_postfix_chain(base_node, nested_depth=0):
                """Parse postfix operators with uniform precedence: DOT/CALL/INDEX/POSTFIX.
                
                Args:
                    base_node: The base expression node
                    nested_depth: Depth of nested function calls (for semicolon validation)
                """
                while True:
                    if current().type == TOKEN_DOT:
                        dot_tok = advance()
                        attr_tok = current()
                        if attr_tok.type != TOKEN_IDENT:
                            got = attr_tok.value if attr_tok.value is not None else attr_tok.type
                            raise BicalaSyntaxError(
                                code="S004",
                                line=dot_tok.line,
                                col=dot_tok.col,
                                got=got
                            )
                        advance()
                        base_node = AttrNode(base_node, attr_tok.value, dot_tok.line, dot_tok.col)
                        continue

                    if current().type == TOKEN_LPAREN:
                        call_tok = advance()
                        args = []
                        if current().type != TOKEN_RPAREN:
                            args.append(parse_inline_if())
                            while current().type == TOKEN_COMMA:
                                advance()
                                args.append(parse_inline_if())
                        consume(TOKEN_RPAREN)
                        base_node = CallNode(base_node, args, call_tok.line, call_tok.col)
                        continue

                    if current().type == TOKEN_LBRACKET:
                        bracket_tok = advance()
                        if current().type == TOKEN_COLON:
                            # [:end] slice
                            advance()
                            if current().type == TOKEN_RBRACKET:
                                consume(TOKEN_RBRACKET)
                                base_node = SliceNode(base_node, NumberNode(0), None, bracket_tok.line, bracket_tok.col)
                            else:
                                end = parse_comma()
                                consume(TOKEN_RBRACKET)
                                base_node = SliceNode(base_node, NumberNode(0), end, bracket_tok.line, bracket_tok.col)
                            continue

                        index_or_start = parse_comma()
                        if current().type == TOKEN_COLON:
                            advance()
                            if current().type == TOKEN_RBRACKET:
                                # [start:]
                                consume(TOKEN_RBRACKET)
                                base_node = SliceNode(base_node, index_or_start, None, bracket_tok.line, bracket_tok.col)
                            else:
                                # [start:end]
                                end = parse_comma()
                                consume(TOKEN_RBRACKET)
                                base_node = SliceNode(base_node, index_or_start, end, bracket_tok.line, bracket_tok.col)
                        else:
                            # [index]
                            consume(TOKEN_RBRACKET)
                            base_node = IndexNode(base_node, index_or_start, bracket_tok.line, bracket_tok.col)
                        continue

                    # Handle custom postfix operators
                    if current().type == TOKEN_OP:
                        op_tok = current()
                        custom_op = get_custom_operator(op_tok.value)
                        if custom_op and custom_op["type"] == "postfix":
                            advance()  # consume the operator
                            # Create CustomOperatorCall for postfix operator
                            from main.ast import CustomOperatorCall
                            base_node = CustomOperatorCall(op_tok.value, "postfix", [base_node], op_tok.line, op_tok.col)
                            continue

                    # Space-call postfix: callee arg1, arg2
                    if is_arg_start(current()):
                        call_line = getattr(base_node, "line", tok.line)
                        call_col = getattr(base_node, "col", tok.col)
                        args = [parse_add()]
                        
                        # Check for semicolon terminator (function terminator)
                        if current().type == TOKEN_SEMICOLON:
                            advance()  # consume the semicolon
                            base_node = CallNode(base_node, args, call_line, call_col)
                            continue
                        
                        while current().type == TOKEN_COMMA:
                            advance()
                            # Parse next argument
                            next_arg = parse_add()
                            args.append(next_arg)
                            
                            # Check for semicolon after comma
                            if current().type == TOKEN_SEMICOLON:
                                advance()  # consume the semicolon
                                base_node = CallNode(base_node, args, call_line, call_col)
                                continue
                        
                        base_node = CallNode(base_node, args, call_line, call_col)
                        continue

                    break
                return base_node

            base = parse_postfix_chain(base)
            
            return base
        
        # Parenthesized expression
        if tok.type == TOKEN_LPAREN:
            advance()
            value = parse_comma()
            consume(TOKEN_RPAREN)
            return parse_postfix_on_node(value)
        
        # Array literal
        if tok.type == TOKEN_LBRACKET:
            bracket_tok = advance()
            items = []
            if current().type != TOKEN_RBRACKET:
                items.append(parse_inline_if())
                while current().type == TOKEN_COMMA:
                    advance()
                    items.append(parse_inline_if())
            consume(TOKEN_RBRACKET)
            node = ArrayNode(items, bracket_tok.line, bracket_tok.col)
            return parse_postfix_on_node(node)
        
        # Use S001 for expected expression
        raise BicalaSyntaxError(
            code="S001",
            line=tok.line,
            col=tok.col,
            got=tok.value,
            length=tok.length
        )
    
    result = parse_comma()
    # Allow semicolon at end of expression (statement separator)
    if current().type == TOKEN_SEMICOLON:
        advance()
    # Allow pipe at end of expression (statement separator)
    if current().type == TOKEN_PIPE:
        advance()
    if current().type != TOKEN_EOF:
        # Check for extra closing brackets
        if current().type == TOKEN_RPAREN:
            raise BicalaSyntaxError(
                code="S018",
                line=current().line,
                col=current().col,
                expected="expression",
                got="')'",
                length=current().length
            )
        if current().type == TOKEN_RBRACKET:
            raise BicalaSyntaxError(
                code="S018",
                line=current().line,
                col=current().col,
                expected="expression",
                got="']'",
                length=current().length
            )
        raise BicalaSyntaxError(
            code="S006",
            line=current().line,
            col=current().col,
            got=current().value,
            length=current().length
        )
    return result


def parse_expression(expr_text, line_num=1, base_col=0):
    """Parse expression string into AST."""
    tokens = tokenize(expr_text, line_num, base_col)
    return parse_expression_to_ast(tokens)
