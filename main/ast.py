# ============================================================
# BICALA_AST NODES - Expression and Statement node classes
# Pure data structures - NO logic/eval methods here
# No imports allowed here (base module)
# Renamed from ast.py to avoid shadowing Python's built-in ast module
# ============================================================

def _node_repr(node, **fields):
    parts = []
    for name, value in fields.items():
        parts.append(f"{name}={_repr_value(value)}")
    parts.append(f"line={getattr(node, 'line', 0)}")
    parts.append(f"col={getattr(node, 'col', 0)}")
    return f"{type(node).__name__}({', '.join(parts)})"

def _repr_value(value):
    if isinstance(value, ASTNode):
        return f"{type(value).__name__}(line={getattr(value, 'line', 0)}, col={getattr(value, 'col', 0)})"
    if isinstance(value, list):
        items = ", ".join(_repr_value(item) for item in value[:3])
        suffix = ", ..." if len(value) > 3 else ""
        return f"[{items}{suffix}]"
    if isinstance(value, tuple):
        return "(" + ", ".join(_repr_value(item) for item in value) + ")"
    return repr(value)


class ASTNode:
    """Base class for all AST nodes."""
    
    def dump_tree(self, indent=0):
        """Recursively dump the AST tree with indentation for debugging."""
        lines = []
        prefix = "  " * indent
        lines.append(f"{prefix}{type(self).__name__}(line={getattr(self, 'line', 0)}, col={getattr(self, 'col', 0)})")
        
        for slot in getattr(self.__class__, '__slots__', []):
            if slot in ('line', 'col'):
                continue
            value = getattr(self, slot, None)
            if value is None:
                continue
            lines.append(f"{prefix}  {slot}:")
            if isinstance(value, ASTNode):
                lines.append(value.dump_tree(indent + 2))
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, ASTNode):
                        lines.append(item.dump_tree(indent + 2))
                    else:
                        lines.append(f"{prefix}    {repr(item)}")
            else:
                lines.append(f"{prefix}    {repr(value)}")
        
        return "\n".join(lines)


# ============================================================
# EXPRESSION NODES
# ============================================================

class ExprNode(ASTNode):
    """Base class for all expression nodes."""
    pass


class NumberNode(ExprNode):
    __slots__ = ['value', 'line', 'col']
    
    def __init__(self, value, line=0, col=0):
        if not isinstance(value, (int, float)):
            raise TypeError(f"NumberNode value must be int or float, got {type(value).__name__}")
        self.value = value
        self.line = line
        self.col = col
    
    def __repr__(self):
        return _node_repr(self, value=self.value)


class BooleanNode(ExprNode):
    __slots__ = ['value', 'line', 'col']
    
    def __init__(self, value, line=0, col=0):
        if type(value) is not bool:
            raise TypeError("BooleanNode value must be bool")
        self.line = line
        self.col = col
        self.value = value
    
    def __repr__(self):
        return _node_repr(self, value=self.value)


class NoneNode(ExprNode):
    __slots__ = ['line', 'col']
    
    def __init__(self, line=0, col=0):
        self.line = line
        self.col = col
    
    def __repr__(self):
        return _node_repr(self)


class NaNNode(ExprNode):
    __slots__ = ['line', 'col']
    
    def __init__(self, line=0, col=0):
        self.line = line
        self.col = col
    
    def __repr__(self):
        return _node_repr(self)


class StringNode(ExprNode):
    __slots__ = ['value', 'line', 'col']
    
    def __init__(self, value, line=0, col=0):
        # value can be either a plain string or a tuple ('INTERPOLATED', parts_list)
        # parts_list is a list of (is_literal, value) tuples
        if not isinstance(value, (str, tuple)):
            raise TypeError(f"StringNode value must be str or tuple, got {type(value).__name__}")
        self.value = value
        self.line = line
        self.col = col
    
    def __repr__(self):
        if isinstance(self.value, tuple) and self.value[0] == 'INTERPOLATED':
            return _node_repr(self, value=f"<interpolated with {len(self.value[1])} parts>")
        return _node_repr(self, value=self.value)


class VarNode(ExprNode):
    __slots__ = ['name', 'line', 'col']
    
    def __init__(self, name, line=0, col=0):
        if not isinstance(name, str):
            raise TypeError(f"VarNode name must be str, got {type(name).__name__}")
        if '.' in name:
            raise ValueError("VarNode cannot contain dotted names; use AttrNode chains")
        self.name = name
        self.line = line
        self.col = col
    
    def __repr__(self):
        return _node_repr(self, name=self.name)


class ArrayNode(ExprNode):
    __slots__ = ['items', 'line', 'col']
    
    def __init__(self, items, line=0, col=0):
        self.items = items
        self.line = line
        self.col = col
    
    def __repr__(self):
        return _node_repr(self, items=self.items)


class UnaryOpNode(ExprNode):
    __slots__ = ['op', 'operand', 'line', 'col']
    
    def __init__(self, op, operand, line=0, col=0):
        self.op = op
        self.operand = operand
        self.line = line
        self.col = col
    
    def __repr__(self):
        return _node_repr(self, op=self.op, operand=self.operand)


class BinaryOpNode(ExprNode):
    __slots__ = ['op', 'left', 'right', 'line', 'col']
    
    def __init__(self, op, left, right, line=0, col=0):
        self.op = op
        self.left = left
        self.right = right
        self.line = line
        self.col = col
    
    def __repr__(self):
        return _node_repr(self, op=self.op, left=self.left, right=self.right)


class CompareNode(ExprNode):
    __slots__ = ['op', 'left', 'right', 'line', 'col']
    
    def __init__(self, op, left, right, line=0, col=0):
        self.op = op
        self.left = left
        self.right = right
        self.line = line
        self.col = col
    
    def __repr__(self):
        return _node_repr(self, op=self.op, left=self.left, right=self.right)


class CallNode(ExprNode):
    __slots__ = ['callee', 'args', 'line', 'col']
    
    def __init__(self, callee, args, line=0, col=0):
        self.callee = VarNode(callee, line, col) if isinstance(callee, str) else callee
        self.args = args
        self.line = line
        self.col = col

    @property
    def name(self):
        """Compatibility shim for older code that expected CallNode(name, args)."""
        if isinstance(self.callee, VarNode):
            return self.callee.name
        return None
    
    def __repr__(self):
        return _node_repr(self, callee=self.callee, args=self.args)


class LambdaNode(ExprNode):
    __slots__ = ['param', 'body', 'line', 'col']
    
    def __init__(self, param, body, line=0, col=0):
        self.param = param
        self.body = body
        self.line = line
        self.col = col
    
    def __repr__(self):
        return _node_repr(self, param=self.param, body=self.body)


class IndexNode(ExprNode):
    __slots__ = ['base', 'index', 'line', 'col']
    
    def __init__(self, base, index, line=0, col=0):
        self.base = base
        self.index = index
        self.line = line
        self.col = col
    
    def __repr__(self):
        return _node_repr(self, base=self.base, index=self.index)


class SliceNode(ExprNode):
    __slots__ = ['base', 'start', 'end', 'line', 'col']
    
    def __init__(self, base, start, end, line=0, col=0):
        self.base = base
        self.start = start
        self.end = end
        self.line = line
        self.col = col
    
    def __repr__(self):
        return _node_repr(self, base=self.base, start=self.start, end=self.end)


class InlineIfNode(ExprNode):
    __slots__ = ['condition', 'true_expr', 'elif_branches', 'false_expr', 'line', 'col']
    
    def __init__(self, condition, true_expr, elif_branches=None, false_expr=None, line=0, col=0):
        self.condition = condition
        self.true_expr = true_expr
        self.elif_branches = elif_branches if elif_branches is not None else []
        self.false_expr = false_expr
        self.line = line
        self.col = col
    
    def __repr__(self):
        return _node_repr(self, condition=self.condition, true_expr=self.true_expr, elif_branches=self.elif_branches, false_expr=self.false_expr)


class TernaryNode(ExprNode):
    __slots__ = ['condition', 'true_expr', 'false_expr', 'line', 'col']
    
    def __init__(self, condition, true_expr, false_expr, line=0, col=0):
        self.condition = condition
        self.true_expr = true_expr
        self.false_expr = false_expr
        self.line = line
        self.col = col
    
    def __repr__(self):
        return _node_repr(self, condition=self.condition, true_expr=self.true_expr, false_expr=self.false_expr)


class AttrNode(ExprNode):
    """Attribute access: obj.attr (e.g., math.sqrt)"""
    __slots__ = ['obj', 'attr', 'line', 'col']
    
    def __init__(self, obj, attr, line=0, col=0):
        self.obj = obj    # Expression (e.g., VarNode("math"))
        self.attr = attr  # String name (e.g., "sqrt")
        self.line = line
        self.col = col
    
    def __repr__(self):
        return _node_repr(self, obj=self.obj, attr=self.attr)


# ============================================================
# STATEMENT NODES
# ============================================================

class StmtNode(ASTNode):
    """Base class for all statement nodes."""
    pass


class ExprStmtNode(StmtNode):
    """Expression as statement (e.g., function call)."""
    __slots__ = ['expr', 'line', 'col']
    
    def __init__(self, expr, line=0, col=0):
        self.expr = expr
        self.line = line
        self.col = col
    
    def __repr__(self):
        return _node_repr(self, expr=self.expr)


class AssignNode(StmtNode):
    __slots__ = ['target', 'value', 'line', 'col', 'is_const', 'declared_type']
    
    def __init__(self, target, value, line=0, col=0, is_const=False, declared_type=None):
        # Validate target is a valid l-value (can be assigned to)
        valid_targets = (VarNode, IndexNode, AttrNode)
        if not isinstance(target, valid_targets):
            raise TypeError(f"AssignNode target must be VarNode, IndexNode, or AttrNode, got {type(target).__name__}")
        self.target = target
        self.value = value
        self.line = line
        self.col = col
        self.is_const = is_const
        self.declared_type = declared_type
    
    def __repr__(self):
        return _node_repr(self, target=self.target, value=self.value, is_const=self.is_const, declared_type=self.declared_type)


class CompoundAssignNode(StmtNode):
    __slots__ = ['target', 'op', 'value', 'line', 'col']
    
    def __init__(self, target, op, value, line=0, col=0):
        # Validate target is a valid l-value (can be assigned to)
        valid_targets = (VarNode, IndexNode, AttrNode)
        if not isinstance(target, valid_targets):
            raise TypeError(f"CompoundAssignNode target must be VarNode, IndexNode, or AttrNode, got {type(target).__name__}")
        self.target = target
        self.op = op
        self.value = value
        self.line = line
        self.col = col
    
    def __repr__(self):
        return _node_repr(self, target=self.target, op=self.op, value=self.value)


class IncDecNode(StmtNode):
    __slots__ = ['target', 'op', 'line', 'col']
    
    def __init__(self, target, op, line=0, col=0):
        # Validate target is a valid l-value (can be assigned to)
        valid_targets = (VarNode, IndexNode, AttrNode)
        if not isinstance(target, valid_targets):
            raise TypeError(f"IncDecNode target must be VarNode, IndexNode, or AttrNode, got {type(target).__name__}")
        self.target = target
        self.op = op
        self.line = line
        self.col = col
    
    def __repr__(self):
        return _node_repr(self, target=self.target, op=self.op)


class SayNode(StmtNode):
    __slots__ = ['expr', 'line', 'col']
    
    def __init__(self, expr, line=0, col=0):
        self.expr = expr
        self.line = line
        self.col = col
    
    def __repr__(self):
        return _node_repr(self, expr=self.expr)


class InputNode(StmtNode):
    __slots__ = ['prompt', 'line', 'col']
    
    def __init__(self, prompt=None, line=0, col=0):
        self.prompt = prompt
        self.line = line
        self.col = col
    
    def __repr__(self):
        return _node_repr(self, prompt=self.prompt)


class DebugNode(StmtNode):
    __slots__ = ['var_name', 'line', 'col']
    
    def __init__(self, var_name=None, line=0, col=0):
        self.var_name = var_name
        self.line = line
        self.col = col
    
    def __repr__(self):
        return _node_repr(self, var_name=self.var_name)


class ErrorNode(StmtNode):
    __slots__ = ['message', 'line', 'col']
    
    def __init__(self, message, line=0, col=0):
        self.message = message
        self.line = line
        self.col = col
    
    def __repr__(self):
        return _node_repr(self, message=self.message)


class TypeNode(ExprNode):
    __slots__ = ['value', 'line', 'col']
    
    def __init__(self, value, line=0, col=0):
        self.value = value
        self.line = line
        self.col = col
    
    def __repr__(self):
        return _node_repr(self, value=self.value)


class ReturnNode(StmtNode):
    __slots__ = ['value', 'line', 'col']
    
    def __init__(self, value=None, line=0, col=0):
        self.value = value
        self.line = line
        self.col = col
    
    def __repr__(self):
        return _node_repr(self, value=self.value)


class BreakNode(StmtNode):
    __slots__ = ['line', 'col']
    
    def __init__(self, line=0, col=0):
        self.line = line
        self.col = col
    
    def __repr__(self):
        return _node_repr(self)


class ContinueNode(StmtNode):
    __slots__ = ['line', 'col']
    
    def __init__(self, line=0, col=0):
        self.line = line
        self.col = col
    
    def __repr__(self):
        return _node_repr(self)


class BlockNode(StmtNode):
    __slots__ = ['statements', 'line', 'col']
    
    def __init__(self, statements, line=0, col=0):
        self.statements = statements
        self.line = line
        self.col = col
    
    def __repr__(self):
        return _node_repr(self, statements=self.statements)


class IfNode(StmtNode):
    __slots__ = ['condition', 'then_block', 'elif_blocks', 'else_block', 'line', 'col']
    
    def __init__(self, condition, then_block, elif_blocks=None, else_block=None, line=0, col=0):
        if elif_blocks is not None and not isinstance(elif_blocks, list):
            raise TypeError("IfNode elif_blocks must be a list or None")
        self.condition = condition
        self.then_block = then_block
        self.elif_blocks = elif_blocks or []
        self.else_block = else_block
        self.line = line
        self.col = col
    
    def __repr__(self):
        return _node_repr(
            self,
            condition=self.condition,
            then_block=self.then_block,
            elif_blocks=self.elif_blocks,
            else_block=self.else_block,
        )


class WhileNode(StmtNode):
    __slots__ = ['condition', 'body', 'line', 'col']
    
    def __init__(self, condition, body, line=0, col=0):
        self.condition = condition
        self.body = body
        self.line = line
        self.col = col
    
    def __repr__(self):
        return _node_repr(self, condition=self.condition, body=self.body)


class ForNode(StmtNode):
    __slots__ = ['var', 'start', 'end', 'step', 'iterable', 'body', 'line', 'col']
    
    def __init__(self, var, start=None, end=None, step=None, iterable=None, body=None, line=0, col=0):
        self.var = var
        self.start = start
        self.end = end
        self.step = step
        self.iterable = iterable  # For array iteration (e.g., for item in arr)
        self.body = body
        self.line = line
        self.col = col
    
    def __repr__(self):
        if self.iterable is not None:
            return _node_repr(self, var=self.var, iterable=self.iterable, body=self.body)
        else:
            return _node_repr(self, var=self.var, start=self.start, end=self.end, step=self.step, body=self.body)


class SwitchNode(StmtNode):
    __slots__ = ['value', 'cases', 'default_block', 'line', 'col']
    
    def __init__(self, value, cases, default_block=None, line=0, col=0):
        self.value = value
        self.cases = cases  # List of (case_value_expr, body_block) tuples
        self.default_block = default_block
        self.line = line
        self.col = col
    
    def __repr__(self):
        return _node_repr(self, value=self.value, cases=self.cases, default_block=self.default_block)


class TryCatchNode(StmtNode):
    __slots__ = ['try_body', 'catch_param', 'catch_body', 'finally_body', 'line', 'col']
    
    def __init__(self, try_body, catch_param=None, catch_body=None, finally_body=None, line=0, col=0):
        self.try_body = try_body
        self.catch_param = catch_param  # Exception parameter name (e.g., "error")
        self.catch_body = catch_body    # BlockNode for catch handler
        self.finally_body = finally_body  # BlockNode for finally handler
        self.line = line
        self.col = col
    
    def __repr__(self):
        return _node_repr(self, try_body=self.try_body, catch_param=self.catch_param, 
                         catch_body=self.catch_body, finally_body=self.finally_body)


class DefNode(StmtNode):
    __slots__ = ['name', 'params', 'body', 'line', 'col']
    
    def __init__(self, name, params, body, line=0, col=0):
        self.name = name
        self.params = params
        self.body = body
        self.line = line
        self.col = col
    
    def __repr__(self):
        return _node_repr(self, name=self.name, params=self.params, body=self.body)


class CommentNode(StmtNode):
    """Comment statement (ignored during execution)."""
    __slots__ = ['text', 'line', 'col']
    
    def __init__(self, text, line=0, col=0):
        self.text = text
        self.line = line
        self.col = col
    
    def __repr__(self):
        return _node_repr(self, text=self.text)


class PassNode(StmtNode):
    """Pass statement (no-op)."""
    __slots__ = ['line', 'col']
    
    def __init__(self, line=0, col=0):
        self.line = line
        self.col = col
    
    def __repr__(self):
        return _node_repr(self)


class HelpNode(StmtNode):
    __slots__ = ['topic', 'line', 'col']
    
    def __init__(self, topic=None, line=0, col=0):
        self.topic = topic
        self.line = line
        self.col = col
    
    def __repr__(self):
        return _node_repr(self, topic=self.topic)


class ImportNode(StmtNode):
    """Import statement: import module"""
    __slots__ = ['module', 'line', 'col']
    
    def __init__(self, module, line=0, col=0):
        self.module = module
        self.line = line
        self.col = col
    
    def __repr__(self):
        return _node_repr(self, module=self.module)


class FromImportNode(StmtNode):
    """From import: from module import name1, name2
       Optional module alias: from module as alias import name1, name2
       Optional function aliases: from module import name1 as alias1, name2 as alias2"""
    __slots__ = ['module', 'names', 'alias', 'name_aliases', 'line', 'col']
    
    def __init__(self, module, names, line=0, col=0, alias=None, name_aliases=None):
        self.module = module
        self.names = names
        self.alias = alias
        self.name_aliases = name_aliases or {}
        self.line = line
        self.col = col
    
    def __repr__(self):
        return _node_repr(self, module=self.module, names=self.names, alias=self.alias, name_aliases=self.name_aliases)


class CustomOperatorDef(StmtNode):
    """Custom operator definition: def infixl prec symbol param1, param2: body"""
    __slots__ = ['symbol', 'op_type', 'precedence', 'params', 'body', 'line', 'col']
    
    def __init__(self, symbol, op_type, precedence, params, body, line=0, col=0):
        """
        :param symbol: The operator symbol (e.g., '^', '--')
        :param op_type: Operator associativity - "infixl", "infixr", or "infix"
        :param precedence: Operator precedence (number)
        :param params: List of parameter names (e.g., ["a", "b"] for infix)
        :param body: AST node representing the operator body
        """
        self.symbol = symbol
        self.op_type = op_type
        self.precedence = precedence
        self.params = params
        self.body = body
        self.line = line
        self.col = col
    
    def __repr__(self):
        return _node_repr(self, symbol=self.symbol, op_type=self.op_type, precedence=self.precedence, params=self.params, body=self.body)


class CustomOperatorCall(ExprNode):
    """Custom operator call: 5^2 or ~>'hello'"""
    __slots__ = ['symbol', 'op_type', 'args', 'line', 'col']
    
    def __init__(self, symbol, op_type, args, line=0, col=0):
        """
        :param symbol: The operator symbol (e.g., '^', '~>')
        :param op_type: Operator type - "infix", "prefix", or "suffix"
        :param args: List of argument AST nodes (e.g., [NumberNode(5), NumberNode(2)] for 5^2)
        """
        self.symbol = symbol
        self.op_type = op_type
        self.args = args
        self.line = line
        self.col = col
    
    def __repr__(self):
        return _node_repr(self, symbol=self.symbol, op_type=self.op_type, args=self.args)


class DelNode(StmtNode):
    """Delete statement: del identifier"""
    __slots__ = ['target', 'line', 'col']
    
    def __init__(self, target, line=0, col=0):
        self.target = target
        self.line = line
        self.col = col
    
    def __repr__(self):
        return _node_repr(self, target=self.target)


class DeferNode(StmtNode):
    """Defer statement: defer statement or defer: block"""
    __slots__ = ['statement', 'line', 'col']
    
    def __init__(self, statement, line=0, col=0):
        self.statement = statement  # Can be a single statement or BlockNode
        self.line = line
        self.col = col
    
    def __repr__(self):
        return _node_repr(self, statement=self.statement)
