# ============================================================
# stmt.py — Statement & block parser
# Parse statements, control structures, and blocks
# ============================================================

from pars.base import (
    get_syntax, is_keyword,
    PUNCTUATION, COMMENT_MARKERS,
    ASSIGNMENT_OPERATORS,
    NumberNode, StringNode, VarNode, ArrayNode, CallNode, AttrNode,
    ExprStmtNode, AssignNode, CompoundAssignNode, IncDecNode,
    SayNode, InputNode, DebugNode, ErrorNode, ReturnNode, BreakNode, ContinueNode,
    BlockNode, IfNode, WhileNode,
    ForNode, DefNode, CommentNode, HelpNode, FromImportNode,
    CustomOperatorDef, SwitchNode, DelNode, PassNode,
    BicalaSyntaxError, BicalaIndentationError,
    _line_indent_level, _is_block_header, _split_statements, _find_block_range,
    BooleanNode, BinaryOpNode,
)
from ast import DeferNode, TryCatchNode
from pars.expr import parse_expression

import re


def parse_statement(line, line_num=1):
    """
    Parse a single line into a statement AST node.
    Returns None for empty/comment lines.
    """
    raw = line
    line = line.strip()
    
    if not line:
        return None
    
    # Check for standalone keywords that are not implemented as statements
    # This prevents unknown keywords from causing runtime R001 errors
    if is_keyword(line):
        # Known keywords that are allowed as standalone statements
        allowed_standalone = {get_syntax('BREAK'), get_syntax('CONTINUE'), get_syntax('PASS'), 
                              get_syntax('HELP'), get_syntax('DEBUG'), get_syntax('RETURN'),
                              get_syntax('DEFER')}
        if line not in allowed_standalone:
            raise BicalaSyntaxError(
                f"Unknown or unimplemented keyword '{line}' as a statement",
                code="S008",
                line=line_num,
                col=0,
                statement=line
            )
    
    # Comments
    if line.startswith(COMMENT_MARKERS['LINE']):
        return CommentNode(line, line_num, 0)
    
    if line.startswith(COMMENT_MARKERS['BLOCK_START']):
        return CommentNode(line, line_num, 0)
    
    # Control flow
    if line == get_syntax('BREAK'):
        return BreakNode(line_num, 0)
    
    if line == get_syntax('CONTINUE'):
        return ContinueNode(line_num, 0)
    
    if line == get_syntax('PASS'):
        return PassNode(line_num, 0)
    
    # Delete statement: del identifier
    kw_del = get_syntax('DEL')
    if line.startswith(kw_del + ' ') and len(line) > len(kw_del) + 1:
        identifier = line[len(kw_del)+1:].strip()
        if not re.match(r'^[A-Za-z_]\w*$', identifier):
            raise BicalaSyntaxError(
                code="S002",
                line=line_num,
                col=len(kw_del) + 1,
                kw=kw_del,
                identifier=identifier
            )
        return DelNode(VarNode(identifier, line_num, 0), line_num, 0)
    
    if line == get_syntax('HELP'):
        return HelpNode(None, line_num, 0)
    
    if line.endswith(' /help'):
        topic = line[:-len(' /help')].strip()
        return HelpNode(topic, line_num, 0)
    
    # From import: from math import sqrt, sin
    # From import with alias: from math as m import sqrt, sin
    # From import with function aliases: from math import sqrt as square_root
    kw_from = get_syntax('FROM')
    kw_import = get_syntax('IMPORT')
    kw_as = get_syntax('AS')
    if line.startswith(kw_from + ' '):
        # Extract parts after 'from'
        parts = line[len(kw_from)+1:].strip().split()

        if not parts:
            raise BicalaSyntaxError(
                code="S033",
                line=line_num,
                col=len(kw_from) + 1,
                kw=kw_from,
                kw_import=kw_import
            )
        
        module = parts[0]
        
        # Check if line has 'import' keyword
        has_import = f' {kw_import} ' in line or line.endswith(f' {kw_import}')
        has_as = f' {kw_as} ' in line

        if not has_import and not has_as:
            raise BicalaSyntaxError(
                code="S034",
                line=line_num,
                col=len(kw_from) + len(module) + 1,
                kw_import=kw_import,
                kw_as=kw_as
            )
        
        from_match = re.match(
            rf'^{re.escape(kw_from)}\s+(\w+)(?:\s+{re.escape(kw_as)}\s+(\w+))?(?:\s+{re.escape(kw_import)}\s*(.*))?$',
            line
        )
        if not from_match:
            raise BicalaSyntaxError(
                code="S033",
                line=line_num,
                col=len(kw_from) + 1,
                kw=kw_from
            )
        
        module = from_match.group(1)
        alias = from_match.group(2)
        names_str = from_match.group(3)
        
        if names_str is not None:
            name_aliases = {}
            names = []
            
            for name_part in names_str.split(','):
                name_part = name_part.strip()
                if not name_part:
                    continue
                
                if f' {kw_as} ' in name_part:
                    orig_name, alias_name = name_part.split(f' {kw_as} ', 1)
                    orig_name = orig_name.strip()
                    alias_name = alias_name.strip()

                    if not alias_name:
                        raise BicalaSyntaxError(
                            code="S036",
                            line=line_num,
                            col=0,
                            kw_as=kw_as
                        )
                    
                    # Check if alias_name is a reserved keyword
                    if is_keyword(alias_name):
                        raise BicalaSyntaxError(
                            f"Cannot use reserved keyword '{alias_name}' as an identifier",
                            code="S041", line=line_num,
                            expected="valid identifier", got=f"'{alias_name}'",
                            hint=f"'{alias_name}' is a reserved keyword and cannot be used as an import alias"
                        )
                    
                    name_aliases[orig_name] = alias_name
                    names.append(orig_name)
                elif name_part.endswith(f' {kw_as}'):
                    orig_name = name_part[:-len(f' {kw_as}')].strip()
                    raise BicalaSyntaxError(
                        code="S036",
                        line=line_num,
                        col=0,
                        kw_as=kw_as
                    )
                else:
                    names.append(name_part)
            
            if not names:
                raise BicalaSyntaxError(
                    code="S035",
                    line=line_num,
                    col=0,
                    kw_import=kw_import
                )
            
            if alias:
                # Check if alias is a reserved keyword
                if is_keyword(alias):
                    raise BicalaSyntaxError(
                        f"Cannot use reserved keyword '{alias}' as an identifier",
                        code="S041", line=line_num,
                        expected="valid identifier", got=f"'{alias}'",
                        hint=f"'{alias}' is a reserved keyword and cannot be used as an import alias"
                    )
                return FromImportNode(module, names, line_num, 0, alias, name_aliases)
            else:
                return FromImportNode(module, names, line_num, 0, None, name_aliases)
        elif alias:
            # Check if alias is a reserved keyword
            if is_keyword(alias):
                raise BicalaSyntaxError(
                    f"Cannot use reserved keyword '{alias}' as an identifier",
                    code="S041", line=line_num,
                    expected="valid identifier", got=f"'{alias}'",
                    hint=f"'{alias}' is a reserved keyword and cannot be used as an import alias"
                )
            import_call = CallNode('import', [StringNode(module, line_num, 0)], line_num, 0)
            return AssignNode(VarNode(alias, line_num, 0), import_call, line_num, 0)
        else:
            raise BicalaSyntaxError(
                code="S034",
                line=line_num,
                col=len(kw_from) + len(module) + 1,
                kw_import=kw_import,
                kw_as=kw_as
            )
    
    # Import: import module or import module as alias
    if line.startswith(kw_import + ' '):
        rest = line[len(kw_import)+1:].strip()
        if f' {kw_as} ' in rest:
            module_part, alias = rest.split(f' {kw_as} ', 1)
            module = module_part.strip()
        else:
            module = rest
            alias = module
        
        # Check if alias is a reserved keyword
        if is_keyword(alias.strip()):
            raise BicalaSyntaxError(
                f"Cannot use reserved keyword '{alias.strip()}' as an identifier",
                code="S041", line=line_num,
                expected="valid identifier", got=f"'{alias.strip()}'",
                hint=f"'{alias.strip()}' is a reserved keyword and cannot be used as an import alias"
            )
        
        import_call = CallNode('import', [StringNode(module, line_num, 0)], line_num, 0)
        return AssignNode(VarNode(alias.strip(), line_num, 0), import_call, line_num, 0)
    
    # Say (requires space: say expr)
    kw_print = get_syntax('PRINT')
    if line.startswith(kw_print + ' ') and len(line) > len(kw_print) + 1:
        expr_text = line[len(kw_print)+1:].strip()
        expr_ast = parse_expression(expr_text, line_num, len(kw_print)+1)
        return SayNode(expr_ast, line_num, 0)
    
    # Say with no arguments (standalone)
    if line == kw_print:
        return SayNode(StringNode("", line_num, 0), line_num, 0)
    
    # Input (requires space: input "prompt")
    kw_input = get_syntax('INPUT')
    if line == kw_input:
        return InputNode(None, line_num, 0)
    
    if line.startswith(kw_input + ' ') and len(line) > len(kw_input) + 1:
        expr_text = line[len(kw_input)+1:].strip()
        prompt_ast = parse_expression(expr_text, line_num, len(kw_input)+1)
        return InputNode(prompt_ast, line_num, 0)
    
    # Debug
    kw_debug = get_syntax('DEBUG')
    if line == kw_debug or line == kw_debug + ' all':
        return DebugNode(None, line_num, 0)
    
    if line.startswith(kw_debug + ' ') and len(line) > len(kw_debug) + 1:
        var_name = line[len(kw_debug)+1:].strip()
        return DebugNode(var_name, line_num, 0)
    
    # Error
    kw_error = get_syntax('ERROR')
    if line.startswith(kw_error + ' ') and len(line) > len(kw_error) + 1:
        expr_text = line[len(kw_error)+1:].strip()
        expr_ast = parse_expression(expr_text, line_num, len(kw_error)+1)
        return ErrorNode(expr_ast, line_num, 0)
    
    # Return
    kw_return = get_syntax('RETURN')
    if line == kw_return:
        return ReturnNode(None, line_num, 0)
    
    if line.startswith(kw_return + ' ') and len(line) > len(kw_return) + 1:
        expr_text = line[len(kw_return)+1:].strip()
        expr_ast = parse_expression(expr_text, line_num, len(kw_return)+1)
        return ReturnNode(expr_ast, line_num, 0)
    
    # Defer one-liner: defer statement
    kw_defer = get_syntax('DEFER')
    if line.startswith(kw_defer + ' ') and len(line) > len(kw_defer) + 1:
        stmt_text = line[len(kw_defer)+1:].strip()
        stmt_ast = parse_statement(stmt_text, line_num)
        if stmt_ast:
            return DeferNode(stmt_ast, line_num, 0)
    
    # Constant declaration: const <identifier> = <expression>
    kw_const = get_syntax('CONST')
    const_match = re.match(rf'^{re.escape(kw_const)}\s+([a-zA-Z_]\w*)\s*=\s*(.+)$', line)
    if const_match:
        var = const_match.group(1)
        
        # Check if variable name is a reserved keyword
        if is_keyword(var):
            raise BicalaSyntaxError(
                f"Cannot use reserved keyword '{var}' as an identifier",
                code="S041", line=line_num,
                expected="valid identifier", got=f"'{var}'",
                hint=f"'{var}' is a reserved keyword and cannot be used as a variable name"
            )
        
        expr_str = const_match.group(2)
        expr_ast = parse_expression(expr_str.strip(), line_num, line.index('=') + 1)
        return AssignNode(VarNode(var, line_num, 0), expr_ast, line_num, 0, is_const=True)
    
    # Type-constrained variable: <type> <identifier> = <expression>
    # Supported types: int, string, bool, float, array
    type_match = re.match(r'^(int|string|bool|float|array)\s+([a-zA-Z_]\w*)\s*=\s*(.+)$', line)
    if type_match:
        var_type = type_match.group(1)
        var = type_match.group(2)
        
        # Check if variable name is a reserved keyword
        if is_keyword(var):
            raise BicalaSyntaxError(
                f"Cannot use reserved keyword '{var}' as an identifier",
                code="S041", line=line_num,
                expected="valid identifier", got=f"'{var}'",
                hint=f"'{var}' is a reserved keyword and cannot be used as a variable name"
            )
        
        expr_str = type_match.group(3)
        expr_ast = parse_expression(expr_str.strip(), line_num, line.index('=') + 1)
        return AssignNode(VarNode(var, line_num, 0), expr_ast, line_num, 0, declared_type=var_type)
    
    # Combined: const <type> <identifier> = <expression>
    const_type_match = re.match(rf'^{re.escape(kw_const)}\s+(int|string|bool|float|array)\s+([a-zA-Z_]\w*)\s*=\s*(.+)$', line)
    if const_type_match:
        var_type = const_type_match.group(1)
        var = const_type_match.group(2)
        
        # Check if variable name is a reserved keyword
        if is_keyword(var):
            raise BicalaSyntaxError(
                f"Cannot use reserved keyword '{var}' as an identifier",
                code="S041", line=line_num,
                expected="valid identifier", got=f"'{var}'",
                hint=f"'{var}' is a reserved keyword and cannot be used as a variable name"
            )
        
        expr_str = const_type_match.group(3)
        expr_ast = parse_expression(expr_str.strip(), line_num, line.index('=') + 1)
        return AssignNode(VarNode(var, line_num, 0), expr_ast, line_num, 0, is_const=True, declared_type=var_type)
    
    # Assignment with =: var = expr
    eq_assign_match = re.match(r'^([a-zA-Z_]\w*)\s*=\s*(.+)$', line)
    if eq_assign_match:
        var = eq_assign_match.group(1)
        
        # Check if variable name is a reserved keyword
        if is_keyword(var):
            raise BicalaSyntaxError(
                f"Cannot use reserved keyword '{var}' as an identifier",
                code="S041", line=line_num,
                expected="valid identifier", got=f"'{var}'",
                hint=f"'{var}' is a reserved keyword and cannot be used as a variable name"
            )
        
        expr_str = eq_assign_match.group(2)
        expr_ast = parse_expression(expr_str.strip(), line_num, line.index('=') + 1)
        return AssignNode(VarNode(var, line_num, 0), expr_ast, line_num, 0)
    
    # Compound assignments
    compound_ops = list(ASSIGNMENT_OPERATORS.values())
    for op in compound_ops:
        if line.endswith(op) or (f' {op} ' in line):
            var, val_expr = line.split(op, 1)
            var = var.strip()
            
            # Check if variable name is a reserved keyword
            if is_keyword(var):
                raise BicalaSyntaxError(
                    f"Cannot use reserved keyword '{var}' as an identifier",
                    code="S041", line=line_num,
                    expected="valid identifier", got=f"'{var}'",
                    hint=f"'{var}' is a reserved keyword and cannot be used as a variable name"
                )
            
            val_ast = parse_expression(val_expr.strip(), line_num, line.index(op) + len(op))
            return CompoundAssignNode(VarNode(var, line_num, 0), op, val_ast, line_num, 0)
    
    # Increment/Decrement
    if line.endswith('++') and '+:' not in line:
        var = line[:-2].strip()
        
        # Check if variable name is a reserved keyword
        if is_keyword(var):
            raise BicalaSyntaxError(
                f"Cannot use reserved keyword '{var}' as an identifier",
                code="S041", line=line_num,
                expected="valid identifier", got=f"'{var}'",
                hint=f"'{var}' is a reserved keyword and cannot be used as a variable name"
            )
        
        return IncDecNode(VarNode(var, line_num, 0), '++', line_num, 0)
    
    if line.endswith('--') and '-:' not in line:
        var = line[:-2].strip()
        
        # Check if variable name is a reserved keyword
        if is_keyword(var):
            raise BicalaSyntaxError(
                f"Cannot use reserved keyword '{var}' as an identifier",
                code="S041", line=line_num,
                expected="valid identifier", got=f"'{var}'",
                hint=f"'{var}' is a reserved keyword and cannot be used as a variable name"
            )
        
        return IncDecNode(VarNode(var, line_num, 0), '--', line_num, 0)
    
    # Bare function call: funcName arg1, arg2 or module.func arg1, arg2
    bare_call_match = re.match(r'^([a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*)*)\s+(.+)$', line)
    if bare_call_match:
        func_path = bare_call_match.group(1)
        args_str = bare_call_match.group(2).strip()
        # Make sure first part is not a keyword
        first_part = func_path.split('.')[0]
        if not is_keyword(first_part):
            try:
                arg_exprs = [parse_expression(a.strip(), line_num, 0) for a in args_str.split(',') if a.strip()]
                if '.' in func_path:
                    parts = func_path.split('.')
                    callee = VarNode(parts[0], line_num, 0)
                    for attr in parts[1:]:
                        callee = AttrNode(callee, attr, line_num, 0)
                    return ExprStmtNode(CallNode(callee, arg_exprs, line_num, 0), line_num, 0)
                else:
                    return ExprStmtNode(CallNode(func_path, arg_exprs, line_num, 0), line_num, 0)
            except (BicalaSyntaxError, SyntaxError):
                pass  # Fall through to expression parsing
    
    # Expression as statement (function call, etc.)
    try:
        expr_ast = parse_expression(line, line_num, 0)
        return ExprStmtNode(expr_ast, line_num, 0)
    except (BicalaSyntaxError, SyntaxError):
        pass
    
    raise BicalaSyntaxError(
        code="S008",
        line=line_num,
        col=0,
        statement=line[:50]
    )


def parse_control_statement(lines, i, line_num_offset=0):
    """
    Parse control flow statements (for, while, if, repeat, def) with their blocks.
    Returns: (stmt_node, next_idx)
    """
    raw = lines[i]
    line = raw.strip()
    base_indent = _line_indent_level(raw)
    line_num = i + 1 + line_num_offset
    
    kw_for = get_syntax('FOR')
    kw_while = get_syntax('WHILE')
    kw_repeat = get_syntax('REPEAT')
    kw_forever = get_syntax('FOREVER')
    kw_if = get_syntax('IF')
    kw_elif = get_syntax('ELIF')
    kw_else = get_syntax('ELSE')
    kw_def = get_syntax('DEF')
    kw_define = get_syntax('DEFINE')
    kw_switch = get_syntax('SWITCH')
    kw_default = get_syntax('DEFAULT')
    kw_defer = get_syntax('DEFER')
    
    # For loop: for i in 10 or for i in 0,10 or for i in 0,10,2 or for i in 0,10:pass
    if line.startswith(kw_for + ' '):
        rest = line[len(kw_for)+1:].strip()
        match = re.match(r'(\w+)\s+in\s+(.+)', rest)
        if not match:
            raise BicalaSyntaxError(
                code="S009",
                line=line_num,
                col=0,
                kw=kw_for
            )
        
        var = match.group(1)
        
        # Check if variable name is a reserved keyword
        if is_keyword(var):
            raise BicalaSyntaxError(
                f"Cannot use reserved keyword '{var}' as an identifier",
                code="S041", line=line_num,
                expected="valid identifier", got=f"'{var}'",
                hint=f"'{var}' is a reserved keyword and cannot be used as a loop variable"
            )
        
        range_expr = match.group(2).strip()
        
        colon = PUNCTUATION['BLOCK_HEADER']
        
        # Support 'with' as an alternative inline body delimiter:
        # "for i in 1,10 with body" is equivalent to "for i in 1,10: body"
        with_sep = ' with '
        if with_sep in range_expr:
            with_idx = range_expr.index(with_sep)
            range_part_str = range_expr[:with_idx].strip()
            inline_body = range_expr[with_idx + len(with_sep):].strip()
        else:
            range_part_str = range_expr
            inline_body = None  # Determined further below if colons are present
        
        # --- Token-based lookahead parsing for the range portion ---
        # This fixes the colon ambiguity by using token lookahead instead of string splitting
        # We explicitly look for the pattern: expr , expr (range) and consume the first comma
        # Only then do we look for the colon (or newline) for the block body
        
        from lex import tokenize as lex_tokenize
        from pars.expr import parse_expression_to_ast
        
        start = end = step = iterable = None
        
        # Tokenize the range expression for proper lookahead
        tokens = lex_tokenize(range_part_str, line_num, len(kw_for) + len(var) + 4)
        # Remove EOF token
        tokens = [t for t in tokens if t.type != 'EOF']
        
        if not tokens:
            raise BicalaSyntaxError(
                code="S010",
                line=line_num,
                col=0,
                range_expr=range_part_str
            )
        
        # Helper: find comma position in tokens for range separation
        def find_comma_pos(tok_list):
            for idx, tok in enumerate(tok_list):
                if tok.type == 'COMMA':
                    return idx
            return -1
        
        # Helper: find colon position in tokens for block header
        def find_colon_pos(tok_list):
            for idx, tok in enumerate(tok_list):
                if tok.type == 'COLON':
                    return idx
            return -1
        
        first_comma_pos = find_comma_pos(tokens)
        
        if first_comma_pos == -1:
            # No comma: "for i in 10" or "for i in arr"
            # Parse entire range_part_str as a single expression
            try:
                expr = parse_expression(range_part_str, line_num, 0)
            except Exception:
                raise BicalaSyntaxError(
                    code="S010",
                    line=line_num,
                    col=0,
                    range_expr=range_part_str
                )
            
            if isinstance(expr, (ArrayNode, VarNode)):
                iterable = expr
            else:
                start = NumberNode(0, line_num, 0)
                end = expr
                step = NumberNode(1, line_num, 0)
        
        else:
            # There is at least one comma
            # Parse the first expression (before the first comma)
            first_expr_str = range_part_str[:tokens[first_comma_pos].col - 1 - (len(kw_for) + len(var) + 4)].strip()
            try:
                first_expr = parse_expression(first_expr_str, line_num, 0)
            except Exception:
                raise BicalaSyntaxError(
                    code="S010",
                    line=line_num,
                    col=0,
                    range_expr=range_part_str
                )
            
            # Look for a second comma (for step)
            second_comma_pos = find_comma_pos(tokens[first_comma_pos + 1:])
            if second_comma_pos == -1:
                # Only one comma: "start,end" (no step)
                # The first comma is the range separator, so we have start,end
                second_expr_str = range_part_str[tokens[first_comma_pos].col - 1 - (len(kw_for) + len(var) + 4) + 1:].strip()
                try:
                    second_expr = parse_expression(second_expr_str, line_num, 0)
                except Exception:
                    raise BicalaSyntaxError(
                        code="S010",
                        line=line_num,
                        col=0,
                        range_expr=range_part_str
                    )
                # Both parts are valid expressions → "start,end" range
                start = first_expr
                end = second_expr
                step = NumberNode(1, line_num, 0)
            else:
                # Two commas found: "start,end,step"
                second_comma_pos = first_comma_pos + 1 + second_comma_pos
                
                # Parse the second expression (between first and second comma)
                second_expr_start = tokens[first_comma_pos].col - 1 - (len(kw_for) + len(var) + 4) + 1
                second_expr_end = tokens[second_comma_pos].col - 1 - (len(kw_for) + len(var) + 4)
                second_expr_str = range_part_str[second_expr_start:second_expr_end].strip()
                try:
                    second_expr = parse_expression(second_expr_str, line_num, 0)
                except Exception:
                    raise BicalaSyntaxError(
                        code="S010",
                        line=line_num,
                        col=0,
                        range_expr=range_part_str
                    )
                
                # Parse the third expression (after second comma)
                third_expr_str = range_part_str[tokens[second_comma_pos].col - 1 - (len(kw_for) + len(var) + 4) + 1:].strip()
                try:
                    third_expr = parse_expression(third_expr_str, line_num, 0)
                    # All three parts are valid expressions → "start,end,step" range
                    start = first_expr
                    end = second_expr
                    step = third_expr
                except Exception:
                    raise BicalaSyntaxError(
                        code="S010",
                        line=line_num,
                        col=0,
                        range_expr=range_part_str
                    )
        
        # Check for block header colon (for block body)
        colon_pos = find_colon_pos(tokens)
        if colon_pos != -1:
            # There's a colon - check if it's for inline body or block header
            # If inline_body is already set via 'with', ignore the colon
            if inline_body is None:
                # Extract inline body after colon
                body_start = tokens[colon_pos].col - 1 - (len(kw_for) + len(var) + 4) + 1
                inline_body = range_part_str[body_start:].strip()
        
        # Create ForNode
        if iterable is not None:
            node = ForNode(var, iterable, None, line_num, 0)
        else:
            node = ForNode(var, (start, end, step), None, line_num, 0)
        
        # Determine if inline or multi-line
        if inline_body is not None and inline_body:
            # Inline case: body on same line
            stmts = []
            for stmt_str in _split_statements(inline_body):
                stmt = parse_statement(stmt_str, line_num)
                if stmt:
                    stmts.append(stmt)
            body_block = BlockNode(stmts, line_num, 0)
            return ForNode(var, start, end, step, iterable, body_block, line_num, 0), i + 1
        else:
            # Multi-line case: expect indented block on following lines
            body_start, body_end = _find_block_range(lines, i, base_indent)
            if body_start < 0:
                raise BicalaSyntaxError(
                    code="S011",
                    line=line_num,
                    col=0
                )
            body_block, _ = parse_block(lines, body_start, base_indent + 1, line_num_offset)
            return ForNode(var, start, end, step, iterable, body_block, line_num, 0), body_end
    
    # While loop
    if line.startswith(kw_while + ' '):
        rest = line[len(kw_while)+1:].strip()
        
        # Check if there's a colon in the line
        has_colon = PUNCTUATION['BLOCK_HEADER'] in rest
        
        # Split by colon to separate condition from inline body
        if has_colon:
            parts = rest.split(PUNCTUATION['BLOCK_HEADER'], 1)
            cond_expr = parts[0].strip()
            inline_body = parts[1].strip() if len(parts) > 1 else None
        else:
            cond_expr = rest
            inline_body = None
        
        # Check for inline content without colon (ERROR S005)
        # If there's no colon, we need to detect if there's content after the condition
        # by checking if the raw line has more than just the condition expression
        if not has_colon:
            # Tokenize to see if there are tokens that look like a statement after the condition
            from lex import tokenize as lex_tokenize
            try:
                tokens = lex_tokenize(rest, line_num, len(kw_while)+1)
                # Remove EOF token
                tokens = [t for t in tokens if t.type != 'EOF']
                # If there are tokens, try to parse the condition
                # If parsing succeeds but there are leftover tokens, it's inline without colon
                # For simplicity, we'll check if the line contains statement-like patterns
                # A heuristic: if the line has keywords like 'say', 'return', etc. after the condition
                # it's likely inline content without colon
                kw_print = get_syntax('PRINT')
                kw_return = get_syntax('RETURN')
                kw_break = get_syntax('BREAK')
                kw_continue = get_syntax('CONTINUE')
                statement_keywords = [kw_print, kw_return, kw_break, kw_continue]
                
                # Check if any statement keyword appears in the rest (after condition)
                for stmt_kw in statement_keywords:
                    if stmt_kw in rest and rest.index(stmt_kw) > len(cond_expr):
                        raise BicalaSyntaxError(
                            code="S005",
                            line=line_num,
                            col=0
                        )
            except BicalaSyntaxError:
                raise
            except:
                pass
        
        # Parse condition
        cond_ast = parse_expression(cond_expr, line_num, len(kw_while)+1)
        
        # Determine if inline or multi-line
        if inline_body is not None and inline_body:
            # Inline case: body on same line - colon is required
            # Parse the inline body as statements (may have multiple separated by ;)
            stmts = []
            for stmt_str in _split_statements(inline_body):
                stmt = parse_statement(stmt_str, line_num)
                if stmt:
                    stmts.append(stmt)
            body_block = BlockNode(stmts, line_num, 0)
            return WhileNode(cond_ast, body_block, line_num, 0), i + 1
        else:
            # Multi-line case: colon is optional, expect indented block
            body_start, body_end = _find_block_range(lines, i, base_indent)
            if body_start < 0:
                raise BicalaSyntaxError(
                    code="S011",
                    line=line_num,
                    col=0
                )
            
            body_block, _ = parse_block(lines, body_start, base_indent + 1, line_num_offset)
            return WhileNode(cond_ast, body_block, line_num, 0), body_end
    
    # Repeat
    if line.startswith(kw_repeat):
        # Check if repeat has inline body
        has_colon = PUNCTUATION['BLOCK_HEADER'] in line
        if has_colon:
            parts = line.split(PUNCTUATION['BLOCK_HEADER'], 1)
            count_expr = parts[0][len(kw_repeat):].strip() if len(parts[0]) > len(kw_repeat) else '1'
            repeat_inline_body = parts[1].strip() if len(parts) > 1 else None
        else:
            count_expr = line[len(kw_repeat):].strip() if len(line) > len(kw_repeat) else '1'
            repeat_inline_body = None
        
        count_ast = parse_expression(count_expr, line_num, len(kw_repeat))
        
        if repeat_inline_body is not None and repeat_inline_body:
            # Inline case: body on same line
            stmts = []
            for stmt_str in _split_statements(repeat_inline_body):
                stmt = parse_statement(stmt_str, line_num)
                if stmt:
                    stmts.append(stmt)
            body_block = BlockNode(stmts, line_num, 0)
            # Subtract 1 from count to make it exclusive (repeat 3 should execute 3 times, not 4)
            adjusted_end = BinaryOpNode('-', count_ast, NumberNode(1, line_num, 0), line_num, 0)
            return ForNode(None, NumberNode(0, line_num, 0), adjusted_end, NumberNode(1, line_num, 0), None, body_block, line_num, 0), i + 1
        else:
            # Multi-line case: expect indented block
            body_start, body_end = _find_block_range(lines, i, base_indent)
            if body_start < 0:
                raise BicalaSyntaxError(
                    code="S011",
                    line=line_num,
                    col=0
                )
            
            body_block, _ = parse_block(lines, body_start, base_indent + 1, line_num_offset)
            # Subtract 1 from count to make it exclusive (repeat 3 should execute 3 times, not 4)
            adjusted_end = BinaryOpNode('-', count_ast, NumberNode(1, line_num, 0), line_num, 0)
            return ForNode(None, NumberNode(0, line_num, 0), adjusted_end, NumberNode(1, line_num, 0), None, body_block, line_num, 0), body_end
    
    # Forever
    if line == kw_forever or (line.startswith(kw_forever) and PUNCTUATION['BLOCK_HEADER'] in line):
        # Check if forever has inline body
        has_colon = PUNCTUATION['BLOCK_HEADER'] in line
        if has_colon:
            parts = line.split(PUNCTUATION['BLOCK_HEADER'], 1)
            forever_inline_body = parts[1].strip() if len(parts) > 1 else None
        else:
            forever_inline_body = None
        
        if forever_inline_body is not None and forever_inline_body:
            # Inline case: body on same line - colon is required
            stmts = []
            for stmt_str in _split_statements(forever_inline_body):
                stmt = parse_statement(stmt_str, line_num)
                if stmt:
                    stmts.append(stmt)
            body_block = BlockNode(stmts, line_num, 0)
            return WhileNode(BooleanNode(True, line_num, 0), body_block, line_num, 0), i + 1
        else:
            # Multi-line case: colon is optional, expect indented block
            body_start, body_end = _find_block_range(lines, i, base_indent)
            if body_start < 0:
                raise BicalaSyntaxError(
                    code="S011",
                    line=line_num,
                    col=0
                )
            
            body_block, _ = parse_block(lines, body_start, base_indent + 1, line_num_offset)
            return WhileNode(BooleanNode(True, line_num, 0), body_block, line_num, 0), body_end
    
    # Try/Catch/Finally
    kw_try = get_syntax('TRY')
    kw_catch = get_syntax('CATCH')
    kw_finally = get_syntax('FINALLY')
    
    if line == kw_try or (line.startswith(kw_try) and PUNCTUATION['BLOCK_HEADER'] in line):
        # Parse try block
        try_body_start, try_body_end = _find_block_range(lines, i, base_indent)
        if try_body_start < 0:
            raise BicalaSyntaxError(
                code="S011",
                line=line_num,
                col=0,
                expected="indented block after 'try'",
                got="no block found"
            )
        
        try_body, next_i = parse_block(lines, try_body_start, base_indent + 1, line_num_offset)
        
        # Look for catch and/or finally blocks
        catch_param = None
        catch_body = None
        finally_body = None
        current_i = try_body_end
        
        # Check for catch block
        if current_i < len(lines):
            next_line = lines[current_i].strip()
            if next_line.startswith(kw_catch):
                # Parse catch parameter: catch (param_name)
                catch_line = next_line[len(kw_catch):].strip()
                if catch_line.startswith('(') and ')' in catch_line:
                    param_start = catch_line.index('(') + 1
                    param_end = catch_line.index(')')
                    catch_param = catch_line[param_start:param_end].strip()
                    if not catch_param or not catch_param.replace('_', '').isalnum():
                        raise BicalaSyntaxError(
                            code="S043",
                            line=current_i + 1 + line_num_offset,
                            col=0,
                            expected="valid identifier in catch()",
                            got=catch_param if catch_param else "empty"
                        )
                else:
                    raise BicalaSyntaxError(
                        code="S043",
                        line=current_i + 1 + line_num_offset,
                        col=0,
                        expected="catch(param_name)",
                        got=catch_line
                    )
                
                # Parse catch body
                catch_body_start, catch_body_end = _find_block_range(lines, current_i, base_indent)
                if catch_body_start < 0:
                    raise BicalaSyntaxError(
                        code="S011",
                        line=current_i + 1 + line_num_offset,
                        col=0,
                        expected="indented block after 'catch'",
                        got="no block found"
                    )
                
                catch_body, current_i = parse_block(lines, catch_body_start, base_indent + 1, line_num_offset)
        
        # Check for finally block
        if current_i < len(lines):
            next_line = lines[current_i].strip()
            if next_line.startswith(kw_finally):
                # Parse finally body
                finally_body_start, finally_body_end = _find_block_range(lines, current_i, base_indent)
                if finally_body_start < 0:
                    raise BicalaSyntaxError(
                        code="S011",
                        line=current_i + 1 + line_num_offset,
                        col=0,
                        expected="indented block after 'finally'",
                        got="no block found"
                    )
                
                finally_body, current_i = parse_block(lines, finally_body_start, base_indent + 1, line_num_offset)
        
        # Enforce strict rule: try must be followed by catch or finally
        if catch_body is None and finally_body is None:
            raise BicalaSyntaxError(
                code="S044",
                line=line_num,
                col=0,
                expected="'try' block must be followed by 'catch' or 'finally'",
                got="standalone 'try' block"
            )
        
        return TryCatchNode(try_body, catch_param, catch_body, finally_body, line_num, 0), current_i
    
    # If/elif/else chain
    if line.startswith(kw_if + ' '):
        rest = line[len(kw_if)+1:].strip()
        
        # Check if there's a colon in the line
        has_colon = PUNCTUATION['BLOCK_HEADER'] in rest
        
        # Split by colon to separate condition from inline body
        if has_colon:
            parts = rest.split(PUNCTUATION['BLOCK_HEADER'], 1)
            cond_expr = parts[0].strip()
            inline_body = parts[1].strip() if len(parts) > 1 else None
        else:
            cond_expr = rest
            inline_body = None
        
        # Check for inline content without colon (ERROR S005)
        if not has_colon:
            kw_print = get_syntax('PRINT')
            kw_return = get_syntax('RETURN')
            kw_break = get_syntax('BREAK')
            kw_continue = get_syntax('CONTINUE')
            statement_keywords = [kw_print, kw_return, kw_break, kw_continue]
            
            for stmt_kw in statement_keywords:
                if stmt_kw in rest and rest.index(stmt_kw) > len(cond_expr):
                    raise BicalaSyntaxError(
                        code="S005",
                        line=line_num,
                        col=0
                    )
        
        # Parse condition
        cond_ast = parse_expression(cond_expr, line_num, len(kw_if)+1)
        
        # Determine if inline or multi-line
        if inline_body is not None and inline_body:
            # Inline case: body on same line - colon is required
            # Parse the inline body as statements (may have multiple separated by ;)
            stmts = []
            for stmt_str in _split_statements(inline_body):
                stmt = parse_statement(stmt_str, line_num)
                if stmt:
                    stmts.append(stmt)
            then_block = BlockNode(stmts, line_num, 0)
            # For inline if, we don't support elif/else chains
            return IfNode(cond_ast, then_block, [], None, line_num, 0), i + 1
        else:
            # Multi-line case: colon is optional, expect indented block
            body_start, body_end = _find_block_range(lines, i, base_indent)
            if body_start < 0:
                raise BicalaSyntaxError(
                    code="S011",
                    line=line_num,
                    col=0
                )
            
            then_block, _ = parse_block(lines, body_start, base_indent + 1, line_num_offset)
        
        elif_blocks = []
        else_block = None
        j = body_end
        while j < len(lines):
            raw_next = lines[j]
            next_line = raw_next.strip()
            
            if not next_line:
                j += 1
                continue
            
            try:
                next_indent = _line_indent_level(raw_next, j + 1 + line_num_offset)
            except BicalaIndentationError:
                raise
            
            if next_indent != base_indent:
                break

            if next_line.startswith(kw_elif + ' ') or next_line.startswith(kw_else + ' ' + kw_if + ' '):
                if j == i:
                    pass
                elif next_indent != base_indent:
                    raise BicalaSyntaxError(
                        code="S026",
                        line=j + 1,
                        col=0
                    )
                
                if next_line.startswith(kw_elif + ' '):
                    elif_rest = next_line[len(kw_elif)+1:].strip()
                else:
                    elif_rest = next_line[len(kw_else)+1+len(kw_if)+1:].strip()
                
                # Check if there's a colon in the line
                elif_has_colon = PUNCTUATION['BLOCK_HEADER'] in elif_rest
                
                # Split by colon to separate condition from inline body
                if elif_has_colon:
                    elif_parts = elif_rest.split(PUNCTUATION['BLOCK_HEADER'], 1)
                    elif_expr = elif_parts[0].strip()
                    elif_inline_body = elif_parts[1].strip() if len(elif_parts) > 1 else None
                else:
                    elif_expr = elif_rest
                    elif_inline_body = None
                
                # Check for inline content without colon (ERROR S005)
                if not elif_has_colon:
                    kw_print = get_syntax('PRINT')
                    kw_return = get_syntax('RETURN')
                    kw_break = get_syntax('BREAK')
                    kw_continue = get_syntax('CONTINUE')
                    statement_keywords = [kw_print, kw_return, kw_break, kw_continue]
                    
                    for stmt_kw in statement_keywords:
                        if stmt_kw in elif_rest and elif_rest.index(stmt_kw) > len(elif_expr):
                            raise BicalaSyntaxError(
                                code="S005",
                                line=j + 1 + line_num_offset,
                                col=0
                            )
                
                elif_ast = parse_expression(elif_expr, j + 1 + line_num_offset, 0)
                
                # Determine if inline or multi-line for elif
                if elif_inline_body is not None and elif_inline_body:
                    # Inline case: body on same line - colon is required
                    # Parse the inline body as statements (may have multiple separated by ;)
                    elif_stmts = []
                    for stmt_str in _split_statements(elif_inline_body):
                        stmt = parse_statement(stmt_str, j + 1 + line_num_offset)
                        if stmt:
                            elif_stmts.append(stmt)
                    elif_block = BlockNode(elif_stmts, j + 1 + line_num_offset, 0)
                    elif_blocks.append((elif_ast, elif_block))
                    j += 1
                    continue
                else:
                    # Multi-line case: colon is optional, expect indented block
                    elif_body_start, elif_body_end = _find_block_range(lines, j, base_indent)
                    if elif_body_start < 0:
                        raise BicalaSyntaxError(
                            code="S011",
                            line=j + 1,
                            col=0
                        )
                    elif_block, _ = parse_block(lines, elif_body_start, base_indent + 1, line_num_offset)
                    
                    elif_blocks.append((elif_ast, elif_block))
                    j = elif_body_end
                    continue
            
            elif next_line == kw_else or next_line.startswith(kw_else + PUNCTUATION["BLOCK_HEADER"]):
                if j == i:
                    pass
                elif next_indent != base_indent:
                    raise BicalaSyntaxError(
                        code="S025",
                        line=j + 1,
                        col=0
                    )
                
                # Check if else has inline body
                has_colon = PUNCTUATION['BLOCK_HEADER'] in next_line
                if has_colon:
                    parts = next_line.split(PUNCTUATION['BLOCK_HEADER'], 1)
                    else_inline_body = parts[1].strip() if len(parts) > 1 else None
                else:
                    else_inline_body = None
                
                if else_inline_body is not None and else_inline_body:
                    # Inline case: body on same line - colon is required
                    else_stmts = []
                    for stmt_str in _split_statements(else_inline_body):
                        stmt = parse_statement(stmt_str, j + 1 + line_num_offset)
                        if stmt:
                            else_stmts.append(stmt)
                    else_block = BlockNode(else_stmts, j + 1 + line_num_offset, 0)
                    j += 1
                    break
                else:
                    # Multi-line case: colon is optional, expect indented block
                    else_body_start, else_body_end = _find_block_range(lines, j, base_indent)
                    if else_body_start < 0:
                        raise BicalaSyntaxError(
                            code="S011",
                            line=j + 1,
                            col=0
                        )
                    else_block, _ = parse_block(lines, else_body_start, base_indent + 1, line_num_offset)
                    j = else_body_end
                    break
            
            else:
                break
        
        return IfNode(cond_ast, then_block, elif_blocks, else_block, line_num, 0), j
    
    # Switch statement
    if line.startswith(kw_switch + ' '):
        value_expr = line[len(kw_switch)+1:].strip()
        if value_expr.endswith(PUNCTUATION['BLOCK_HEADER']):
            value_expr = value_expr[:-len(PUNCTUATION['BLOCK_HEADER'])].strip()
        value_ast = parse_expression(value_expr, line_num, len(kw_switch)+1)
        
        # Parse case blocks - collect all case labels and their bodies
        cases = []
        default_block = None
        j = i + 1
        
        # First, find the end of the entire switch block
        switch_end = i + 1
        while switch_end < len(lines):
            raw = lines[switch_end]
            line_stripped = raw.strip()
            if not line_stripped or line_stripped.startswith('#'):
                switch_end += 1
                continue
            try:
                indent = _line_indent_level(raw, switch_end + 1 + line_num_offset)
            except BicalaIndentationError:
                raise
            # Allow default: at same indent level as switch
            if indent <= base_indent and not (line_stripped == kw_default or line_stripped == f'{kw_default}{PUNCTUATION["BLOCK_HEADER"]}'):
                break
            switch_end += 1
        
        # Now parse case blocks within the switch block
        k = i + 1
        while k < switch_end:
            raw = lines[k]
            next_line = raw.strip()
            
            if not next_line or next_line.startswith('#'):
                k += 1
                continue
            
            try:
                next_indent = _line_indent_level(raw, k + 1 + line_num_offset)
            except BicalaIndentationError:
                raise
            
            # Check for default block (must be at same indent level as switch)
            if next_line == kw_default or next_line == f'{kw_default}{PUNCTUATION["BLOCK_HEADER"]}':
                if next_indent != base_indent:
                    raise BicalaSyntaxError(
                        f"{kw_default} must be at the same indent level as {kw_switch}",
                        code="S041", line=k + 1 + line_num_offset,
                        expected=f"indent level {base_indent}", got=f"indent level {next_indent}",
                        hint=f"Move {kw_default} to the same indent level as the corresponding {kw_switch}"
                    )
                if default_block is not None:
                    raise BicalaSyntaxError(
                        f"Only one {kw_default} block is allowed",
                        code="S039", line=k + 1 + line_num_offset,
                        expected="at most one default block", got="multiple default blocks",
                        hint=f"Remove the extra {kw_default} block"
                    )
                
                # Find default body (lines indented more than base_indent)
                default_body_start = k + 1
                default_body_end = default_body_start
                while default_body_end < switch_end:
                    raw_body = lines[default_body_end]
                    body_line = raw_body.strip()
                    if not body_line or body_line.startswith('#'):
                        default_body_end += 1
                        continue
                    try:
                        body_indent = _line_indent_level(raw_body, default_body_end + 1 + line_num_offset)
                    except BicalaIndentationError:
                        raise
                    if body_indent <= base_indent:
                        break
                    default_body_end += 1
                
                # Parse default body statements
                default_statements = []
                for stmt_idx in range(default_body_start, default_body_end):
                    raw_stmt = lines[stmt_idx]
                    stmt_line = raw_stmt.strip()
                    if not stmt_line or stmt_line.startswith('#'):
                        continue
                    stmt = parse_statement(raw_stmt, stmt_idx + 1 + line_num_offset)
                    if stmt:
                        default_statements.append(stmt)
                
                default_block = BlockNode(default_statements, k + 1 + line_num_offset, 0)
                k = default_body_end
                continue
            
            # Only process case labels at base_indent + 1
            if next_indent != base_indent + 1:
                k += 1
                continue
            
            # Parse case value (expression followed by colon)
            if PUNCTUATION['BLOCK_HEADER'] in next_line:
                case_parts = next_line.split(PUNCTUATION['BLOCK_HEADER'], 1)
                case_value_expr = case_parts[0].strip()
                
                if not case_value_expr:
                    raise BicalaSyntaxError(
                        f"Expected case value before ':'",
                        code="S040", line=k + 1 + line_num_offset,
                        expected="case value expression", got="nothing",
                        hint=f"Example: 1: or 'hello':"
                    )
                
                case_value_ast = parse_expression(case_value_expr, k + 1 + line_num_offset, 0)
                
                # Find case body
                case_body_start = k + 1
                case_body_end = case_body_start
                while case_body_end < switch_end:
                    raw_body = lines[case_body_end]
                    body_line = raw_body.strip()
                    if not body_line or body_line.startswith('#'):
                        case_body_end += 1
                        continue
                    try:
                        body_indent = _line_indent_level(raw_body, case_body_end + 1 + line_num_offset)
                    except BicalaIndentationError:
                        raise
                    if body_indent <= base_indent + 1:
                        break
                    case_body_end += 1
                
                # Parse case body statements
                case_statements = []
                for stmt_idx in range(case_body_start, case_body_end):
                    raw_stmt = lines[stmt_idx]
                    stmt_line = raw_stmt.strip()
                    if not stmt_line or stmt_line.startswith('#'):
                        continue
                    stmt = parse_statement(raw_stmt, stmt_idx + 1 + line_num_offset)
                    if stmt:
                        case_statements.append(stmt)
                
                case_block = BlockNode(case_statements, k + 1 + line_num_offset, 0)
                cases.append((case_value_ast, case_block))
                k = case_body_end
            else:
                k += 1
        
        if not cases:
            raise BicalaSyntaxError(
                f"Switch statement must have at least one case",
                code="S042", line=line_num,
                expected="at least one case", got="no cases",
                hint=f"Add at least one case block after '{kw_switch}'"
            )
        
        return SwitchNode(value_ast, cases, default_block, line_num, 0), switch_end
    
    # Defer statement with block
    if line.startswith(kw_defer):
        # Check if there's a colon in the line
        has_colon = PUNCTUATION['BLOCK_HEADER'] in line
        
        if has_colon:
            # defer: statement (inline) or defer: (multi-line)
            parts = line.split(PUNCTUATION['BLOCK_HEADER'], 1)
            defer_inline_body = parts[1].strip() if len(parts) > 1 else None
            
            if defer_inline_body:
                # Parse the inline body as a statement
                stmt = parse_statement(defer_inline_body, line_num)
                if stmt:
                    return DeferNode(stmt, line_num, 0), i + 1
            else:
                # defer: (empty inline) - treat as multi-line
                body_start, body_end = _find_block_range(lines, i, base_indent)
                if body_start < 0:
                    raise BicalaSyntaxError(
                        f"Expected indented block after '{kw_defer}:'",
                        code="S011", line=line_num,
                        expected="indented block", got="no block found",
                        hint=f"Add an indented line (4 spaces) after '{kw_defer}:'"
                    )
                
                body_block, _ = parse_block(lines, body_start, base_indent + 1, line_num_offset)
                return DeferNode(body_block, line_num, 0), body_end
        else:
            # defer (without colon) - must be multi-line block
            body_start, body_end = _find_block_range(lines, i, base_indent)
            if body_start < 0:
                raise BicalaSyntaxError(
                    f"Expected indented block after '{kw_defer}'",
                    code="S011", line=line_num,
                    expected="indented block", got="no block found",
                    hint=f"Add an indented line (4 spaces) after '{kw_defer}'"
                )
            
            body_block, _ = parse_block(lines, body_start, base_indent + 1, line_num_offset)
            return DeferNode(body_block, line_num, 0), body_end
    
    # Def / Define (function definition)
    if line.startswith(kw_def + ' ') or line.startswith(kw_define + ' '):
        rest = line[len(kw_def)+1:].strip()
        
        # Check for operator definition: def infixl/infixr/infix prec symbol params
        # Check for prefix/postfix definition: def prefix/postfix prec symbol param
        # FIXED: Changed from ([^A-Za-z0-9_\s]+) to (\S+) to support alphanumeric operators
        # Use SYNTAX keys for operator type keywords
        kw_infixl = get_syntax('INFIX_L')
        kw_infixr = get_syntax('INFIX_R')
        kw_infix = get_syntax('INFIX')
        kw_prefix = get_syntax('PREFIX')
        kw_postfix = get_syntax('POSTFIX')
        op_match = re.match(rf'^({kw_infixl}|{kw_infixr}|{kw_infix}|{kw_prefix}|{kw_postfix})\s+(\d+)\s+(\S+)\s+([^:]+)(?::\s*(.*))?$', rest)
        if op_match:
            op_type, prec_str, symbol, params_str, body_expr = op_match.groups()
            precedence = int(prec_str)
            
            # Enforce precedence constraint: must be positive integer 1-99
            if not (1 <= precedence <= 99):
                raise BicalaSyntaxError(
                    f"Precedence must be between 1 and 99, got {precedence}",
                    code="S035", line=line_num,
                    expected="precedence 1-99", got=f"{precedence}",
                    hint="Use a positive integer between 1 and 99 for operator precedence"
                )
            
            params = [p.strip() for p in params_str.split(',') if p.strip()]
            
            # Enforce parameter count based on operator type
            if op_type in (kw_infixl, kw_infixr, kw_infix):
                # Infix operators require exactly 2 parameters
                if len(params) != 2:
                    raise BicalaSyntaxError(
                        f"Infix operators require exactly two parameters, got {len(params)}",
                        code="S036", line=line_num,
                        expected="exactly 2 parameters", got=f"{len(params)}",
                        hint=f"Example: {kw_infixl} 10 add x,y: x+y"
                    )
            elif op_type in (kw_prefix, kw_postfix):
                # Prefix/postfix operators require exactly 1 parameter
                if len(params) != 1:
                    raise BicalaSyntaxError(
                        f"{op_type.capitalize()} operators require exactly one parameter, got {len(params)}",
                        code="S036", line=line_num,
                        expected="exactly 1 parameter", got=f"{len(params)}",
                        hint=f"Example: {kw_prefix} 8 ! x: fac(x)"
                    )
            
            for param in params:
                if not re.match(r'^[A-Za-z_]\w*$', param):
                    raise BicalaSyntaxError(
                        f"Invalid parameter name '{param}'",
                        code="S013", line=line_num,
                        expected="valid name", got=f"'{param}'",
                        hint="Use letters, digits, underscore (no leading digit)"
                    )
                
                # Check if parameter is a reserved keyword
                if is_keyword(param):
                    raise BicalaSyntaxError(
                        f"Cannot use reserved keyword '{param}' as an identifier",
                        code="S041", line=line_num,
                        expected="valid identifier", got=f"'{param}'",
                        hint=f"'{param}' is a reserved keyword and cannot be used as a parameter name"
                    )
            
            if body_expr is not None and body_expr.strip():
                body_ast = parse_expression(body_expr.strip(), line_num, 0)
                return CustomOperatorDef(symbol, op_type, precedence, params, body_ast, line_num, 0), i + 1
            else:
                body_start, body_end = _find_block_range(lines, i, base_indent)
                if body_start < 0:
                    raise BicalaSyntaxError(
                        "Expected indented block after operator definition",
                        code="S011", line=line_num,
                        expected="indented block", got="no block found",
                        hint=f"Add an indented line (4 spaces) after '{kw_def}'"
                    )
                
                body_block, _ = parse_block(lines, body_start, base_indent + 1, line_num_offset)
                return CustomOperatorDef(symbol, op_type, precedence, params, body_block, line_num, 0), body_end
        
        # Regular function definition: def name param1, param2: body
        if PUNCTUATION['BLOCK_HEADER'] in rest:
            parts = rest.split(PUNCTUATION['BLOCK_HEADER'], 1)
            header = parts[0].strip()
            body_expr = parts[1].strip() if len(parts) > 1 else None
        else:
            header = rest
            body_expr = None
        
        header_parts = header.split(None, 1)
        name = header_parts[0].strip()
        if not re.match(r'^[A-Za-z_]\w*$', name):
            raise BicalaSyntaxError(
                f"Invalid function name '{name}'",
                code="S012", line=line_num,
                expected="valid name", got=f"'{name}'",
                hint="Use letters, digits, underscore (no leading digit)"
            )
        
        # Check if name is a reserved keyword
        if is_keyword(name):
            raise BicalaSyntaxError(
                f"Cannot use reserved keyword '{name}' as an identifier",
                code="S041", line=line_num,
                expected="valid identifier", got=f"'{name}'",
                hint=f"'{name}' is a reserved keyword and cannot be used as a function name"
            )
        
        if len(header_parts) > 1 and header_parts[1].strip():
            params = [p.strip() for p in header_parts[1].split(',') if p.strip()]
        else:
            params = []
        
        for param in params:
            if not re.match(r'^[A-Za-z_]\w*$', param):
                raise BicalaSyntaxError(
                    f"Invalid parameter name '{param}'",
                    code="S013", line=line_num,
                    expected="valid name", got=f"'{param}'",
                    hint="Use letters, digits, underscore (no leading digit)"
                )
            
            # Check if parameter is a reserved keyword
            if is_keyword(param):
                raise BicalaSyntaxError(
                    f"Cannot use reserved keyword '{param}' as an identifier",
                    code="S041", line=line_num,
                    expected="valid identifier", got=f"'{param}'",
                    hint=f"'{param}' is a reserved keyword and cannot be used as a parameter name"
                )
        
        if body_expr is not None and body_expr:
            body_ast = parse_expression(body_expr, line_num, 0)
            return DefNode(name, params, BlockNode([ReturnNode(body_ast, line_num, 0)], line_num, 0), line_num, 0), i + 1
        else:
            body_start, body_end = _find_block_range(lines, i, base_indent)
            if body_start < 0:
                raise BicalaSyntaxError(
                    f"Expected indented block after '{kw_def}'",
                    code="S011", line=line_num,
                    expected="indented block", got="no block found",
                    hint=f"Add an indented line (4 spaces) after '{kw_def}'"
                )
            
            body_block, _ = parse_block(lines, body_start, base_indent + 1, line_num_offset)
            return DefNode(name, params, body_block, line_num, 0), body_end
    
    raise BicalaSyntaxError(
        f"Unknown block header '{line}'",
        code="S014", line=line_num,
        expected="block keyword with ':'", got=f"'{line[:30]}'",
        hint="Block headers must be: if/while/for/def/repeat <expr>:"
    )


def parse_block(lines, start_idx, parent_indent, line_num_offset=0):
    """
    Parse a block of indented statements.
    Returns: (BlockNode, next_idx)
    """
    statements = []
    i = start_idx
    has_content = False
    
    while i < len(lines):
        raw = lines[i]
        line = raw.strip()
        
        if not line or line.startswith('#'):
            i += 1
            continue
        
        try:
            indent = _line_indent_level(raw, i + 1 + line_num_offset)
        except BicalaIndentationError:
            raise
        
        if indent < parent_indent:
            break
        
        # Check for block headers (for, while, if, etc.) in nested blocks
        if _is_block_header(line):
            stmt, i = parse_control_statement(lines, i, line_num_offset)
            if stmt:
                statements.append(stmt)
                has_content = True
            continue
        
        # Simple statement — split by | and ; (statement separators)
        try:
            if ('|' in raw or ';' in raw) and not _is_block_header(line):
                parts = _split_statements(raw)
                for part in parts:
                    if part.strip():
                        stmt = parse_statement(part.strip(), i + 1 + line_num_offset)
                        if stmt:
                            statements.append(stmt)
                            has_content = True
            else:
                stmt = parse_statement(raw, i + 1 + line_num_offset)
                if stmt:
                    statements.append(stmt)
                    has_content = True
        except (BicalaSyntaxError, BicalaIndentationError) as e:
            raise
        i += 1
    
    # Check for empty block
    if not has_content and statements:
        raise BicalaSyntaxError(
            "Empty block",
            code="S022", line=start_idx + 1 + line_num_offset,
            expected="at least one statement", got="empty block",
            hint="Add at least one statement to the block"
        )
    
    return BlockNode(statements, line_num_offset + start_idx, 0), i


def parse_program(lines, line_num_offset=0):
    """
    Parse entire program into AST.
    Returns: BlockNode containing all statements.
    """
    statements = []
    i = 0
    
    while i < len(lines):
        raw = lines[i]
        line = raw.strip()
        
        if not line or line.startswith('#'):
            i += 1
            continue
        
        # Check for block headers (for, while, if, repeat, def)
        if _is_block_header(line):
            stmt, i = parse_control_statement(lines, i, line_num_offset)
            if stmt:
                statements.append(stmt)
            continue
        
        # Simple statement — split by | and ; (statement separators)
        try:
            if ('|' in raw or ';' in raw) and not _is_block_header(line):
                parts = _split_statements(raw)
                for part in parts:
                    if part.strip():
                        stmt = parse_statement(part.strip(), i + 1 + line_num_offset)
                        if stmt:
                            statements.append(stmt)
            else:
                stmt = parse_statement(raw, i + 1 + line_num_offset)
                if stmt:
                    statements.append(stmt)
        except (BicalaSyntaxError, BicalaIndentationError) as e:
            raise
        
        i += 1
    
    return BlockNode(statements, 0, 0)
