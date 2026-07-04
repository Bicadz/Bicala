# ============================================================
# eval.py — Execute AST nodes
# Expression evaluator and statement executor
# Imports: ast, env, tok, err (NO parser - avoid circular)
# ============================================================

import math
from tok import ASSIGNMENT_OPERATORS
from main.ast import (
    NumberNode, BooleanNode, StringNode, VarNode, ArrayNode, UnaryOpNode, BinaryOpNode,
    CompareNode, CallNode, IndexNode, SliceNode, TernaryNode, InlineIfNode, AttrNode, LambdaNode, TypeNode,
    NoneNode, NaNNode,
    ExprStmtNode, AssignNode, CompoundAssignNode, IncDecNode,
    SayNode, InputNode, DebugNode, ErrorNode, ReturnNode, BreakNode, ContinueNode,
    BlockNode, IfNode, WhileNode,
    ForNode, DefNode, CommentNode, HelpNode, FromImportNode,
    CustomOperatorDef, CustomOperatorCall, SwitchNode, DelNode, DeferNode, PassNode, TryCatchNode
)
from env import (
    Environment, BUILTIN_FUNCTIONS, 
    register_module_alias, resolve_module_alias, 
    check_circular_import, clear_module_registry,
    register_module,
    register_custom_operator, get_custom_operator
)
from err import (
    BicalaNameError, BicalaImportError,
    BicalaTypeError, BicalaValueError, BicalaRuntimeError,
    BicalaAttributeError
)
from sem import (
    require_boolean, require_loop_int, validate_callable,
    validate_function_arity, resolve_name, validate_name_not_defined,
    validate_name_exists, validate_interpolation_name,
    validate_custom_operator, validate_operator, validate_comparison_op
)


# ============================================================
# CONTROL FLOW SIGNALS
# ============================================================

class BreakSignal(Exception):
    """Raised by break statement."""
    def __init__(self, line=None, col=None):
        self.line = line
        self.col = col
        super().__init__("break")


class ContinueSignal(Exception):
    """Raised by continue statement."""
    def __init__(self, line=None, col=None):
        self.line = line
        self.col = col
        super().__init__("continue")


class ReturnSignal(Exception):
    """Raised by return statement."""
    def __init__(self, value=None):
        self.value = value
        super().__init__(f"Return with value: {value}")


# ============================================================
# BUILT-IN FUNCTIONS
# ============================================================

# Track current source directory for .bica imports
_current_source_dir = None

# Callback for GUI input (set by IDE)
_gui_input_callback = None
_cli_input_callback = input

def set_gui_input_callback(callback):
    """Set a callback function for GUI-based input."""
    global _gui_input_callback
    _gui_input_callback = callback

def set_source_dir(path):
    """Set the directory of the currently running .bica file."""
    global _current_source_dir
    import os
    if path:
        _current_source_dir = os.path.dirname(os.path.abspath(path))

def _import(name):
    """Import built-in module (math, str) or .bica file."""
    import sys
    import os
    
    # 1. Try built-in modules from env.py (fast direct Python callables)
    from env import get_builtin_module
    try:
        return get_builtin_module(name)
    except ImportError:
        pass  # Not a built-in, try .bica file
    
    # 2. Try .bica file
    search_dirs = [_current_source_dir or '.']
    for search_dir in search_dirs:
        bica_path = os.path.join(search_dir, name + '.bica')
        if os.path.isfile(bica_path):
            return _import_bica(bica_path, name)
    
    raise BicalaImportError(
        code="M001",
        line=0,
        col=0,
        name=name
    )

def _import_bica(filepath, module_name):
    """Import a .bica file as a module proxy."""
    from pars.stmt import parse_program
    from env import Environment
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Parse and execute in isolated environment
    program = parse_program(lines, line_num_offset=0)
    mod_funcs = {}
    mod_env = execute_program(program, mod_funcs)
    
    # Collect all exported names (variables + functions)
    attrs = {}
    for var_name in mod_env.vars:
        attrs[var_name] = mod_env.vars[var_name]
    for func_name, (params, body) in mod_funcs.items():
        attrs[func_name] = (params, body)
    
    return _ModuleProxy(module_name, attrs, mod_env, mod_funcs)


class _ModuleProxy:
    """Proxy to access module attributes (both built-in and .bica)."""
    
    __slots__ = ['_name', '_attrs', '_env', '_functions']
    
    def __init__(self, name, attrs, env=None, functions=None):
        self._name = name
        self._attrs = attrs
        self._env = env
        self._functions = functions or {}
    
    def __getattr__(self, name):
        if name in self._attrs:
            if name in self._functions:
                return _BicaFunction(name, self._functions[name], self._env, self._functions)
            return self._attrs[name]
        raise BicalaImportError(
            code="M004",
            line=0,
            col=0,
            name=name,
            module=self._name
        )
    
    def __repr__(self):
        return f"<module '{self._name}'>"
    
    def __dir__(self):
        return list(self._attrs.keys())


class _BicaFunction:
    """Callable wrapper for functions imported from .bica modules."""

    __slots__ = ['_name', '_func_def', '_env', '_functions']

    def __init__(self, name, func_def, env, functions):
        self._name = name
        self._func_def = func_def
        self._env = env
        self._functions = functions

    def __call__(self, *args):
        try:
            return call_bica_function(self._func_def, list(args), self._env, self._functions)
        except TypeError as exc:
            if str(exc).startswith("Function expected "):
                raise BicalaTypeError(
                    code="T004",
                    line=0,
                    col=0,
                    name=self._name
                )
            raise

    def __repr__(self):
        return f"<function '{self._name}'>"


class _LambdaFunction:
    """Callable wrapper for lambda expressions (fn arg: expr)."""

    __slots__ = ['_param', '_body', '_env']

    def __init__(self, param, body, env):
        self._param = param
        self._body = body
        self._env = env

    def __call__(self, *args):
        if len(args) != 1:
            raise BicalaTypeError(
                code="T005",
                line=0,
                col=0,
                expected=1,
                got=len(args)
            )
        # Create a new environment with the parameter bound
        new_env = Environment(parent=self._env)
        new_env.assign(self._param, args[0])
        # Evaluate the body in the new environment
        return evaluate_expression(self._body, new_env)

    def __repr__(self):
        return f"<lambda fn {self._param}: ...>"


def _builtin_input(prompt=""):
    """Built-in input function that uses GUI callback if available."""
    try:
        if _gui_input_callback:
            return str(_gui_input_callback(prompt))
        return str(_cli_input_callback(prompt))
    except Exception:
        return str(_cli_input_callback(prompt))
BUILTINS = {
    'len': len,
    'abs': abs,
    'round': round,
    'max': max,
    'min': min,
    'int': int,
    'float': float,
    'str': str,
    'bool': bool,
    'range': range,
    'enumerate': enumerate,
    'zip': zip,
    'list': list,
    'tuple': tuple,
    'sum': sum,
    'sorted': sorted,
    'reversed': lambda x: list(reversed(x)),
    'any': any,
    'all': all,
    'import': _import,
    'input': _builtin_input,
}


# ============================================================
# EXPRESSION EVALUATOR
# ============================================================

def is_truthy(value):
    """Bicala truthiness check: false, None, NaN, 0, "" are falsy; everything else is truthy."""
    if value is None:
        return False
    if isinstance(value, float) and math.isnan(value):
        return False
    if value is False:
        return False
    if value == 0:
        return False
    if value == "":
        return False
    return True


def _loose_equals(left, right):
    """Loose equality (.=): dynamic type coercion.

    Rules:
    - None .= None → True; None .= anything else → False
    - bool  ↔ str  : compare via lowered string form
    - str   ↔ num  : coerce string to float, compare numerically
    - num   ↔ num  : compare values (int 2 .= float 2.0 → True)
    - str   ↔ str  : case-insensitive comparison
    - fallback     : Python ==
    """
    if left is None or right is None:
        return left is right
    
    # Boolean to string coercion
    if isinstance(left, bool) and isinstance(right, str):
        return str(left).lower() == right.lower()
    if isinstance(left, str) and isinstance(right, bool):
        return left.lower() == str(right).lower()
    
    # String to number coercion
    if isinstance(left, str) and isinstance(right, (int, float)):
        try:
            return float(left) == right
        except ValueError:
            return False
    if isinstance(left, (int, float)) and isinstance(right, str):
        try:
            return left == float(right)
        except ValueError:
            return False
    
    # Number coercion (int vs float)
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left == right
    
    # String comparison (case-insensitive)
    if isinstance(left, str) and isinstance(right, str):
        return left.lower() == right.lower()
    
    # Fallback to strict equality
    return left == right


def _strict_equals(left, right):
    """Strict equality (==): both value AND data type must be identical."""
    if type(left) != type(right):
        return False
    return left == right


def resolve_callable(callee_node, env, functions):
    """
    Resolve call target using one deterministic priority:
    1) environment variable
    2) user-defined function table
    3) builtin function table
    """
    if isinstance(callee_node, VarNode):
        name = callee_node.name
        try:
            return resolve_name(name, env, functions, callee_node.line, callee_node.col), name
        except BicalaNameError:
            # Check builtins as fallback
            if name in BUILTINS:
                return BUILTINS[name], name
            raise

    target = evaluate_expression(callee_node, env, functions)
    return target, repr(callee_node)


def invoke_callable(target, target_label, args, env, functions):
    validate_callable(target, target_label)
    if is_bica_function(target):
        return call_bica_function(target, args, env, functions)
    if callable(target):
        return target(*args)
    raise BicalaTypeError(
        code="T004",
        line=0,
        col=0,
        name=target_label
    )

def evaluate_expression(node, env, functions=None):
    """
    Evaluate expression AST node with given environment.
    Returns computed value.
    """
    if functions is None:
        functions = {}

    if isinstance(node, NumberNode):
        return node.value

    if isinstance(node, BooleanNode):
        return node.value
    
    if isinstance(node, NoneNode):
        return None
    
    if isinstance(node, NaNNode):
        return float('nan')
    
    if isinstance(node, StringNode):
        # Check if this is an interpolated string
        if isinstance(node.value, tuple) and node.value[0] == 'INTERPOLATED':
            parts = node.value[1]  # List of (is_literal, value) tuples
            result = []
            for is_literal, value in parts:
                if is_literal:
                    result.append(str(value))
                else:
                    # Variable interpolation - look up the variable
                    validate_interpolation_name(value, env, node.line, node.col)
                    var_value = env.get(value)
                    result.append(str(var_value))
            return ''.join(result)
        # Simple string (no interpolation)
        return node.value
    
    if isinstance(node, VarNode):
        try:
            val = env.get(node.name)
        except NameError:
            # Check if it's a user-defined function
            if node.name in functions:
                val = functions[node.name]
            # Check if it's a builtin
            elif node.name in BUILTINS:
                val = BUILTINS[node.name]
            else:
                raise BicalaNameError(
                    code="N001",
                    line=node.line,
                    col=node.col,
                    name=node.name
                )
        return _auto_invoke(val, env, functions)
    
    if isinstance(node, ArrayNode):
        return [evaluate_expression(item, env, functions) for item in node.items]
    
    if isinstance(node, CustomOperatorCall):
        # Check if the operator is registered
        op_def = validate_custom_operator(node.symbol, node.line, node.col)
        
        # Evaluate arguments
        arg_values = [evaluate_expression(arg, env, functions) for arg in node.args]
        
        # Create a new environment for the operator body
        op_env = Environment(parent=env)
        
        # Bind parameters to argument values
        validate_function_arity(op_def['params'], arg_values, node.line, node.col)
        
        for param_name, arg_value in zip(op_def['params'], arg_values):
            op_env.define(param_name, arg_value)
        
        # Execute the operator body
        try:
            result = evaluate_expression(op_def['body'], op_env, functions)
        except Exception as e:
            raise BicalaRuntimeError(
                code="R001",
                line=node.line,
                col=node.col,
                symbol=node.symbol,
                error=str(e)
            )
        
        return result
    
    if isinstance(node, UnaryOpNode):
        # Check if this is a custom prefix operator
        op_def = get_custom_operator(node.op)
        if op_def is not None and op_def['type'] == 'prefix':
            # Execute as custom prefix operator
            operand = evaluate_expression(node.operand, env, functions)
            
            # Create a new environment for the operator body
            op_env = Environment(parent=env)
            
            # Bind parameter to argument value
            validate_function_arity(op_def['params'], [operand], node.line, node.col)
            
            op_env.define(op_def['params'][0], operand)
            
            # Execute the operator body
            try:
                result = evaluate_expression(op_def['body'], op_env, functions)
            except Exception as e:
                raise BicalaRuntimeError(
                    code="R001",
                    line=node.line,
                    col=node.col,
                    symbol=node.op,
                    error=str(e)
                )
            
            return result
        
        # Regular unary operator handling
        operand = evaluate_expression(node.operand, env, functions)
        if node.op == '-':
            return -operand
        if node.op == '+':
            return +operand
        if node.op == 'not':
            # Custom truthiness: None and NaN are falsy
            if operand is None:
                return True  # !None = true
            if isinstance(operand, float) and math.isnan(operand):
                return True  # !NaN = true
            # For other values, use Python truthiness
            return not operand
        raise BicalaValueError(
            code="V001",
            line=node.line,
            col=node.col,
            op=node.op
        )
    
    if isinstance(node, BinaryOpNode):
        # Check if this is a custom operator
        op_def = get_custom_operator(node.op)
        if op_def is not None and op_def['type'] == 'infix':
            # Execute as custom infix operator
            left = evaluate_expression(node.left, env, functions)
            right = evaluate_expression(node.right, env, functions)
            
            # Create a new environment for the operator body
            op_env = Environment(parent=env)
            
            # Bind parameters to argument values
            validate_function_arity(op_def['params'], [left, right], node.line, node.col)
            
            op_env.define(op_def['params'][0], left)
            op_env.define(op_def['params'][1], right)
            
            # Execute the operator body
            try:
                # Execute as expression (body is now parsed as expression, not block)
                result = evaluate_expression(op_def['body'], op_env, functions)
            except Exception as e:
                raise BicalaRuntimeError(
                    code="R001",
                    line=node.line,
                    col=node.col,
                    symbol=node.op,
                    error=str(e)
                )
            
            return result
        
        # Regular binary operator handling
        left = evaluate_expression(node.left, env, functions)
        right = evaluate_expression(node.right, env, functions)
        
        # Arithmetic
        if node.op == '+':
            if isinstance(left, str) or isinstance(right, str):
                return str(left) + str(right)
            return left + right
        if node.op == '-':
            return left - right
        if node.op == '*':
            if isinstance(left, str) and isinstance(right, int):
                return left * right
            if isinstance(right, str) and isinstance(left, int):
                return right * left
            return left * right
        if node.op == '/':
            if right == 0:
                return float('nan')
            return left / right
        if node.op == '//':
            if right == 0:
                return float('nan')
            return left // right
        if node.op == '%':
            if right == 0:
                return float('nan')
            return left % right
        if node.op == '**':
            return left ** right
        
        # Logical
        if node.op == 'and':
            return require_boolean(left, node.left, "'and' left operand") and require_boolean(right, node.right, "'and' right operand")
        if node.op == 'or':
            return require_boolean(left, node.left, "'or' left operand") or require_boolean(right, node.right, "'or' right operand")
        
        # String concatenation (comma)
        if node.op == ',':
            return str(left) + str(right)
        
        raise BicalaValueError(
            code="V002",
            line=node.line,
            col=node.col,
            op=node.op
        )
    
    if isinstance(node, CompareNode):
        left = evaluate_expression(node.left, env, functions)
        right = evaluate_expression(node.right, env, functions)

        # == : Strict equality — value AND data type must be identical
        if node.op == '==':
            return _strict_equals(left, right)
        # === : Identity check (same object)
        if node.op == '===':
            return left is right
        # .= : Loose equality — dynamic type coercion
        if node.op == '.=':
            return _loose_equals(left, right)
        # != : Strict inequality — negation of strict equality
        if node.op == '!=':
            return not _strict_equals(left, right)
        # !== : Negation of strict equality (alias)
        if node.op == '!==':
            return not _strict_equals(left, right)
        # !=== : Identity inequality
        if node.op == "!===":
            return left is not right
        if node.op == '>':
            return left > right
        if node.op == '<':
            return left < right
        if node.op == '>=':
            return left >= right
        if node.op == '<=':
            return left <= right
        if node.op == 'in':
            return left in right
        
        raise BicalaValueError(
            code="V003",
            line=node.line,
            col=node.col,
            op=node.op
        )
    
    if isinstance(node, CallNode):
        args = [evaluate_expression(arg, env, functions) for arg in node.args]
        target, label = resolve_callable(node.callee, env, functions)
        return invoke_callable(target, label, args, env, functions)
    
    if isinstance(node, IndexNode):
        base = evaluate_expression(node.base, env, functions)
        index = evaluate_expression(node.index, env, functions)
        return base[index]
    
    if isinstance(node, SliceNode):
        base = evaluate_expression(node.base, env, functions)
        start = evaluate_expression(node.start, env, functions) if node.start else None
        end = evaluate_expression(node.end, env, functions) if node.end else None
        return base[start:end]
    
    if isinstance(node, TernaryNode):
        condition = evaluate_expression(node.condition, env, functions)
        if require_boolean(condition, node.condition, "ternary condition"):
            return evaluate_expression(node.true_expr, env, functions)
        else:
            return evaluate_expression(node.false_expr, env, functions)
    
    if isinstance(node, InlineIfNode):
        condition = evaluate_expression(node.condition, env, functions)
        if is_truthy(condition):
            return evaluate_expression(node.true_expr, env, functions)
        # Check elif branches sequentially
        for elif_cond, elif_expr in node.elif_branches:
            elif_condition = evaluate_expression(elif_cond, env, functions)
            if is_truthy(elif_condition):
                return evaluate_expression(elif_expr, env, functions)
        # If all conditions are falsy, return else expression
        return evaluate_expression(node.false_expr, env, functions)
    
    if isinstance(node, AttrNode):
        try:
            obj = evaluate_expression(node.obj, env, functions)
        except BicalaNameError:
            if isinstance(node.obj, VarNode):
                raise BicalaImportError(
                    code="M001",
                    line=node.obj.line,
                    col=node.obj.col,
                    name=node.obj.name
                )
            raise
        val = getattr(obj, node.attr)
        return _auto_invoke(val, env, functions)
    
    if isinstance(node, LambdaNode):
        return _LambdaFunction(node.param, node.body, env)
    
    if isinstance(node, TypeNode):
        try:
            value = evaluate_expression(node.value, env, functions)
            # Convert Python types to Bicala-standard type names
            python_type = type(value)
            if python_type == str:
                return "str"
            elif python_type == bool:
                return "bool"
            elif python_type == int:
                return "int"
            elif python_type == float:
                return "float"
            elif python_type == list:
                return "arr"
            elif isinstance(value, _BicaFunction) or isinstance(value, _LambdaFunction):
                return "function"
            else:
                # Fallback to Python type name for unknown types
                return python_type.__name__
        except Exception as exc:
            raise BicalaTypeError(
                code="T002",
                line=node.line,
                col=node.col,
                context="type expression",
                error=str(exc)
            )
    
    raise ValueError(f"Unknown expression node: {type(node)}")


def is_bica_function(value):
    return (
        isinstance(value, tuple)
        and len(value) == 2
        and isinstance(value[0], list)
        and isinstance(value[1], BlockNode)
    )


def _auto_invoke(val, env, functions=None):
    if functions is None:
        functions = {}

    # Check if Bica function tuple
    if is_bica_function(val):
        params, _ = val
        if len(params) == 0:
            return call_bica_function(val, [], env, functions)
        return val

    # Check if Python callable
    if callable(val) and not isinstance(val, type):
        if isinstance(val, _LambdaFunction):
            return val

        # If it is a wrapper _BicaFunction
        if isinstance(val, _BicaFunction):
            params, _ = val._func_def
            if len(params) == 0:
                return val()
            return val

        # Otherwise, inspect signature for Python callable
        import inspect
        try:
            sig = inspect.signature(val)
            has_zero_required = True
            for param in sig.parameters.values():
                if (param.default is inspect.Parameter.empty and 
                    param.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)):
                    has_zero_required = False
                    break
            if has_zero_required:
                return val()
        except ValueError:
            pass

    return val


def call_bica_function(func_def, args, parent_env, functions):
    params, body = func_def
    validate_function_arity(params, args)

    local_env = Environment(parent_env)
    for param, arg in zip(params, args):
        local_env.define(param, arg)

    try:
        execute_statement(body, local_env, functions)
    except ReturnSignal as signal:
        # Execute deferred statements in LIFO order before returning
        for deferred_stmt in reversed(local_env.defer_stack):
            execute_statement(deferred_stmt, local_env, functions)
        return signal.value
    except Exception:
        # Execute deferred statements in LIFO order even on exception
        for deferred_stmt in reversed(local_env.defer_stack):
            try:
                execute_statement(deferred_stmt, local_env, functions)
            except:
                pass  # Ignore errors in deferred statements during exception handling
        raise
    else:
        # Execute deferred statements in LIFO order on normal exit
        for deferred_stmt in reversed(local_env.defer_stack):
            execute_statement(deferred_stmt, local_env, functions)
    return None


def call_user_function(name, args, parent_env, functions):
    try:
        return call_bica_function(functions[name], args, parent_env, functions)
    except TypeError as exc:
        if str(exc).startswith("Function expected "):
            raise BicalaTypeError(
                code="T004",
                line=0,
                col=0,
                name=name
            )
        raise


# ============================================================
# STATEMENT EXECUTOR
# ============================================================

def execute_statement(node, env, functions=None):
    """
    Execute a single statement node.
    Returns None, or raises control flow signals.
    """
    if functions is None:
        functions = {}
    
    if isinstance(node, CommentNode):
        return
        
    if isinstance(node, PassNode):
        return
    
    if isinstance(node, BreakNode):
        raise BreakSignal(node.line, node.col)
    
    if isinstance(node, ContinueNode):
        raise ContinueSignal(node.line, node.col)
    
    if isinstance(node, ReturnNode):
        value = evaluate_expression(node.value, env, functions) if node.value else None
        raise ReturnSignal(value)
    
    if isinstance(node, SayNode):
        value = evaluate_expression(node.expr, env, functions)
        print(value)
        return
    
    if isinstance(node, InputNode):
        if node.prompt:
            prompt_val = evaluate_expression(node.prompt, env, functions)
            prompt_str = str(prompt_val)
        else:
            prompt_str = ""
        
        # Use GUI callback if available (for IDE), otherwise use console input
        try:
            if _gui_input_callback:
                result = _gui_input_callback(prompt_str)
            else:
                result = _cli_input_callback(prompt_str)
        except Exception:
            result = input(prompt_str)
        
        return result

    if isinstance(node, DebugNode):
        if node.var_name:
            if env.has(node.var_name):
                value = env.get(node.var_name)
                print(f"{node.var_name} = {repr(value)} (type: {type(value).__name__})")
            else:
                print(f"Error (line {node.line}): variable '{node.var_name}' not defined")
        else:
            print(env.all_vars())
        return
    
    if isinstance(node, ErrorNode):
        message = evaluate_expression(node.message, env)
        print(f"ERROR: {message}")
        raise SystemExit(1)
    
    if isinstance(node, HelpNode):
        if node.topic:
            _print_help_topic(node.topic)
        else:
            _print_help()
        return
    
    if isinstance(node, AssignNode):
        if (
            isinstance(node.value, CallNode)
            and node.value.name == 'import'
            and env.has_local(node.target)
        ):
            raise BicalaImportError(
                code="M003",
                line=node.line,
                col=node.col,
                name=node.target
            )
        value = evaluate_expression(node.value, env, functions)
        # Extract name from VarNode if needed
        target_name = node.target.name if isinstance(node.target, VarNode) else node.target
        
        # Check for function name collision in current scope
        if target_name in env.functions:
            raise BicalaNameError(
                code="N007",
                line=node.line,
                col=node.col,
                name=target_name
            )
        
        # Semantic validation: const reassignment check
        from sem import validate_const_assignment, validate_type_assignment
        validate_const_assignment(node, env)
        
        # Semantic validation: type constraint check
        if node.declared_type is not None:
            validate_type_assignment(node, value, env)
        
        env.assign(target_name, value)
        
        # Mark variable as const if it's a constant declaration
        if node.is_const and not env.is_const(target_name):
            env.mark_const(target_name)
        
        # Mark variable with declared type if it has one
        if node.declared_type is not None:
            env.mark_typed(target_name, node.declared_type)
        
        return
    
    if isinstance(node, CompoundAssignNode):
        target_name = node.target.name if isinstance(node.target, VarNode) else node.target
        if not isinstance(target_name, str):
            raise BicalaRuntimeError(
                code="R001",
                line=node.line,
                col=node.col,
                context="compound assignment",
                target=type(target_name).__name__
            )
        
        # Semantic validation: const reassignment check
        from sem import validate_const_assignment
        validate_const_assignment(node, env)
        
        if not env.has(target_name):
            raise BicalaNameError(
                code="N001",
                line=node.line,
                col=node.col,
                name=target_name
            )
        
        old_val = env.get(target_name)
        new_val = evaluate_expression(node.value, env, functions)
        
        if node.op == ASSIGNMENT_OPERATORS['ADD']:
            env.set(target_name, old_val + new_val)
        elif node.op == ASSIGNMENT_OPERATORS['SUB']:
            env.set(target_name, old_val - new_val)
        elif node.op == ASSIGNMENT_OPERATORS['MUL']:
            env.set(target_name, old_val * new_val)
        elif node.op == ASSIGNMENT_OPERATORS['DIV']:
            if new_val == 0:
                raise ZeroDivisionError("Division by zero")
            env.set(target_name, old_val / new_val)
        elif node.op == ASSIGNMENT_OPERATORS['FLOOR_DIV']:
            if new_val == 0:
                raise ZeroDivisionError("Division by zero")
            env.set(target_name, old_val // new_val)
        elif node.op == ASSIGNMENT_OPERATORS['MOD']:
            if new_val == 0:
                raise ZeroDivisionError("Division by zero")
            env.set(target_name, old_val % new_val)
        elif node.op == ASSIGNMENT_OPERATORS['POW']:
            env.set(target_name, old_val ** new_val)
        else:
            raise BicalaRuntimeError(
                f"Unknown compound assignment operator '{node.op}'",
                code="R001",
                line=node.line,
                col=node.col,
                expected=f"one of: {', '.join(ASSIGNMENT_OPERATORS.values())}",
                got=f"'{node.op}'"
            )
        return
    
    if isinstance(node, IncDecNode):
        target_name = node.target.name if isinstance(node.target, VarNode) else node.target
        if not isinstance(target_name, str):
            raise BicalaRuntimeError(
                code="R001",
                line=node.line,
                col=node.col,
                context="increment/decrement",
                target=type(target_name).__name__
            )
        
        # Semantic validation: const reassignment check
        from sem import validate_const_assignment
        validate_const_assignment(node, env)
        
        if not env.has(target_name):
            raise BicalaNameError(
                code="N001",
                line=node.line,
                col=node.col,
                name=target_name
            )
        
        old_val = env.get(target_name)
        if node.op == '++':
            env.set(target_name, old_val + 1)
        elif node.op == '--':
            env.set(target_name, old_val - 1)
        return
    
    if isinstance(node, ExprStmtNode):
        evaluate_expression(node.expr, env, functions)
        return
    
    if isinstance(node, CustomOperatorDef):
        # Register the custom operator in the global registry
        register_custom_operator(node.symbol, node.op_type, node.params, node.body)
        return
    
    if isinstance(node, BlockNode):
        for stmt in node.statements:
            execute_statement(stmt, env, functions)
        return
    
    if isinstance(node, IfNode):
        cond_val = evaluate_expression(node.condition, env, functions)
        if require_boolean(cond_val, node.condition, "'if' condition"):
            execute_statement(node.then_block, env, functions)
            return
        for elif_condition, elif_block in node.elif_blocks:
            elif_val = evaluate_expression(elif_condition, env, functions)
            if require_boolean(elif_val, elif_condition, "'elif' condition"):
                execute_statement(elif_block, env, functions)
                return
        if node.else_block:
            execute_statement(node.else_block, env, functions)
        return
    
    if isinstance(node, WhileNode):
        while True:
            cond_val = evaluate_expression(node.condition, env, functions)
            if not require_boolean(cond_val, node.condition, "'while' condition"):
                break
            try:
                execute_statement(node.body, env, functions)
            except ContinueSignal:
                continue
            except BreakSignal:
                break
        return
    
    if isinstance(node, ForNode):
        # Check if this is array iteration or numeric range
        if node.iterable is not None:
            # Array iteration: for item in arr or for item in [1, 2, 3]
            iterable_val = evaluate_expression(node.iterable, env, functions)
            
            # Ensure the iterable is a list
            if not isinstance(iterable_val, list):
                raise BicalaValueError(
                    f"for loop iterable must be a list, got {type(iterable_val).__name__}",
                    code="V006",
                    expected="list", got=type(iterable_val).__name__
                )
            
            loop_var = node.var
            loop_env = Environment(parent=env)
            for item in iterable_val:
                if loop_var is not None:
                    loop_env.define(loop_var, item)
                try:
                    execute_statement(node.body, loop_env, functions)
                except ContinueSignal:
                    # Execute deferred statements before continuing
                    for deferred_stmt in reversed(loop_env.defer_stack):
                        execute_statement(deferred_stmt, loop_env, functions)
                    loop_env.defer_stack.clear()
                    continue
                except BreakSignal:
                    # Execute deferred statements before breaking
                    for deferred_stmt in reversed(loop_env.defer_stack):
                        execute_statement(deferred_stmt, loop_env, functions)
                    loop_env.defer_stack.clear()
                    break
                # Execute deferred statements after each iteration
                for deferred_stmt in reversed(loop_env.defer_stack):
                    execute_statement(deferred_stmt, loop_env, functions)
                loop_env.defer_stack.clear()
        else:
            # Numeric range: for i in 0:10 or for i in 10
            start_val = evaluate_expression(node.start, env, functions)
            end_val = evaluate_expression(node.end, env, functions)
            step_val = evaluate_expression(node.step, env, functions)
            
            start_int = require_loop_int(start_val, node.start, "for start")
            end_int = require_loop_int(end_val, node.end, "for end")
            step_int = require_loop_int(step_val, node.step, "for step")
            if step_int == 0:
                raise BicalaValueError(
                    "for step must not be 0",
                    code="V005",
                    expected="non-zero step", got="0"
                )
            
            loop_var = node.var
            loop_env = Environment(parent=env)
            i = start_int
            # Use inclusive end behavior to match range(start, end + 1) semantics
            while (step_int > 0 and i <= end_int) or (step_int < 0 and i >= end_int):
                if loop_var is not None:
                    # Use assign instead of define to properly update the variable in the environment
                    loop_env.assign(loop_var, i)
                try:
                    execute_statement(node.body, loop_env, functions)
                except ContinueSignal:
                    # Execute deferred statements before continuing
                    for deferred_stmt in reversed(loop_env.defer_stack):
                        execute_statement(deferred_stmt, loop_env, functions)
                    loop_env.defer_stack.clear()
                    i += step_int
                    continue
                except BreakSignal:
                    # Execute deferred statements before breaking
                    for deferred_stmt in reversed(loop_env.defer_stack):
                        execute_statement(deferred_stmt, loop_env, functions)
                    loop_env.defer_stack.clear()
                    break
                # Execute deferred statements after each iteration
                for deferred_stmt in reversed(loop_env.defer_stack):
                    execute_statement(deferred_stmt, loop_env, functions)
                loop_env.defer_stack.clear()
                i += step_int
        return
    
    if isinstance(node, SwitchNode):
        switch_value = evaluate_expression(node.value, env, functions)
        
        # Try each case in order, execute first matching
        for case_value_expr, case_block in node.cases:
            case_value = evaluate_expression(case_value_expr, env, functions)
            # Use strict equality (==) for comparison
            if _strict_equals(switch_value, case_value):
                execute_statement(case_block, env, functions)
                return
        
        # If no case matched, execute default block if present
        if node.default_block:
            execute_statement(node.default_block, env, functions)
        return
    
    if isinstance(node, FromImportNode):
        mod = _import(node.module)
        
        # Only check for circular imports for non-built-in modules
        # Built-in modules (math, str, arr) can be imported multiple times
        if node.module not in ['math', 'str', 'arr']:
            # Check for circular import
            try:
                check_circular_import(node.module)
            except ImportError as e:
                raise BicalaImportError(
                    str(e),
                    code="M002",
                    line=node.line, col=node.col,
                    expected="non-circular import", got="circular dependency",
                    hint="Check your import structure to avoid circular references"
                )
            
            # Register the module in registry
            register_module(node.module, mod)
        
        # Handle module alias (from X as Y import Z)
        if node.alias:
            # Register the alias
            try:
                register_module_alias(node.module, node.alias)
                # Define the alias as the module in the environment
                env.define(node.alias, mod)
            except ValueError as e:
                raise BicalaImportError(
                    str(e),
                    code="M003",
                    line=node.line, col=node.col, length=len(node.alias),
                    expected="unique alias name",
                    got=f"'{node.alias}' (already in use)"
                )
        
        # Import the specified names with optional aliases
        for name in node.names:
            try:
                val = getattr(mod, name)
            except AttributeError:
                raise BicalaImportError(
                    f"Name '{name}' not found in module '{node.module}'",
                    code="M004",
                    expected=f"attribute of '{node.module}'", got=f"'{name}'"
                )
            
            # Use alias if provided, otherwise use original name
            final_name = node.name_aliases.get(name, name)
            
            # Check for name collision (shadowing)
            if env.has(final_name):
                raise BicalaNameError(
                    f"Name collision: '{final_name}' already exists in current scope",
                    code="N007",
                    line=node.line, col=node.col, length=len(final_name),
                    expected="unique name",
                    got=f"'{final_name}' (already defined)"
                )
            
            env.define(final_name, val)
        return
    
    if isinstance(node, DefNode):
        # Store function definition with collision detection
        try:
            env.define_function(node.name, (node.params, node.body))
        except ValueError as e:
            raise BicalaNameError(
                str(e),
                code="N007",
                line=node.line, col=node.col, length=len(node.name),
                expected="unique function name",
                got=f"'{node.name}' (already defined)"
            )
        # Also store in functions dict for backward compatibility
        functions[node.name] = (node.params, node.body)
        return
    
    if isinstance(node, DelNode):
        # Delete statement: del identifier
        target_name = node.target.name if isinstance(node.target, VarNode) else node.target
        
        # Check if identifier exists in current scope
        if not env.has_local(target_name) and target_name not in env.functions:
            raise BicalaNameError(
                f"Variable '{target_name}' is not defined",
                code="N004",
                line=node.line, col=node.col, length=len(target_name),
                expected="defined variable or function", got=f"'{target_name}'",
                hint=f"Did you define '{target_name}' before trying to delete it?"
            )
        
        # Remove from both vars and functions in current scope
        env.undefine_local(target_name)
        env.undefine_function_local(target_name)
        return
    
    if isinstance(node, DeferNode):
        # Defer statement: push onto defer_stack for later execution
        env.defer_stack.append(node.statement)
        return
    
    if isinstance(node, TryCatchNode):
        # Try/Catch/Finally statement
        caught_exception = None
        finally_executed = False
        
        # Execute try block
        try:
            execute_statement(node.try_body, env, functions)
        except Exception as e:
            caught_exception = e
        
        # Execute catch block if exception occurred and catch body exists
        if caught_exception is not None and node.catch_body is not None:
            # Define the exception parameter in the catch scope
            catch_env = Environment(parent=env)
            if node.catch_param:
                catch_env.define(node.catch_param, str(caught_exception))
            
            # Execute catch block in catch environment
            execute_statement(node.catch_body, catch_env, functions)
        
        # Execute finally block if it exists (always executes regardless of exception)
        if node.finally_body is not None:
            finally_executed = True
            execute_statement(node.finally_body, env, functions)
        
        # Re-raise exception if it wasn't caught and there's no finally block to handle it
        if caught_exception is not None and node.catch_body is None and not finally_executed:
            raise caught_exception
        
        return
    
    raise ValueError(f"Unknown statement node: {type(node)}")


def _print_help():
    """Print general help."""
    print("""Bicala Language Help:
    =        - Assignment (var = value)
    += -= *= /= //= %= **= - Compound assignments
    ++ --    - Increment/decrement
    say      - Print value
    input    - Read input
    if/elif/else - Conditional
    while    - Loop while true
    for      - Range loop
    repeat   - Repeat n times
    forever  - Infinite loop
    def      - Define function
    int      - Convert value to integer
    str      - Convert value to string
    float    - Convert value to float
    return   - Return from function
    break    - Exit loop
    continue - Skip iteration
    debug    - Debug variables
    help     - Show this help
    """)


def _print_help_topic(topic):
    """Print help for specific topic."""
    HELP_TEXT = {
        "help": "help -> Show all available Bicala commands.",
        ":": "<var> : <expr> -> Assign expression result to a variable.",
        "int": "int <expr> -> Convert value to integer. Example: say int \"42\"",
        "str": "str <expr> -> Convert value to string. Example: say str 123",
        "float": "float <expr> -> Convert value to float. Example: say float \"3.14\"",
    }
    if topic in HELP_TEXT:
        print(HELP_TEXT[topic])
    else:
        print(f"No help available for: {topic}")


# ============================================================
# PROGRAM EXECUTION
# ============================================================

def execute_program(program_node, functions=None):
    """
    Execute entire program AST.
    Returns final environment.
    """
    # Clear module registry for fresh execution
    clear_module_registry()
    
    if functions is None:
        functions = {}
    
    env = Environment()
    
    # Load built-in functions into global scope
    for name, func in BUILTIN_FUNCTIONS.items():
        env.define(name, func)
    
    try:
        execute_statement(program_node, env, functions)
    except BreakSignal as signal:
        raise BicalaRuntimeError(
            "break used outside of a loop",
            code="R002",
            line=signal.line,
            col=signal.col,
            expected="break inside while/for block",
            got="break in top-level/function body",
        )
    except ContinueSignal as signal:
        raise BicalaRuntimeError(
            "continue used outside of a loop",
            code="R003",
            line=signal.line,
            col=signal.col,
            expected="continue inside while/for block",
            got="continue in top-level/function body",
        )
    
    return env
