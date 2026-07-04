# ============================================================
# sem.py — Semantic Analysis Layer
# Name Resolution (Nxxx), Type/Arity validation (Txxx)
# Imports: err (no eval, no parser - avoid circular)
# ============================================================

import math
from err import (
    BicalaNameError, BicalaTypeError, BicalaValueError
)


# ============================================================
# TYPE VALIDATION
# ============================================================

def require_boolean(value, node=None, context="condition"):
    """Require a real boolean value; do not inherit Python truthiness."""
    if type(value) is bool:
        return value
    line = getattr(node, 'line', None)
    col = getattr(node, 'col', None)
    raise BicalaTypeError(
        code="T002",
        line=line,
        col=col,
        context=context,
        value=value
    )


def require_loop_int(value, node=None, context="loop bound"):
    """Require an integer for loop bounds (not boolean)."""
    if type(value) is bool:
        line = getattr(node, 'line', None)
        col = getattr(node, 'col', None)
        raise BicalaTypeError(
            code="T003",
            line=line,
            col=col,
            context=context,
            value=value
        )
    return int(value)


def validate_callable(target, target_label, line=0, col=0):
    """Validate that a value is callable."""
    # Check if it's a Bica function tuple
    if isinstance(target, tuple) and len(target) == 2:
        params, body = target
        # params should be a list, body should be a BlockNode
        if isinstance(params, list):
            return True
    
    # Check if it's a Python callable
    if callable(target) and not isinstance(target, type):
        return True
    
    raise BicalaTypeError(
        code="T004",
        line=line,
        col=col,
        name=target_label
    )


def validate_function_arity(expected_params, actual_args, line=0, col=0):
    """Validate function call arity (number of arguments)."""
    if len(actual_args) < len(expected_params):
        raise BicalaTypeError(
            code="T005",
            line=line,
            col=col,
            expected=len(expected_params),
            got=len(actual_args)
        )
    if len(actual_args) > len(expected_params):
        raise BicalaTypeError(
            code="T006",
            line=line,
            col=col,
            expected=len(expected_params),
            got=len(actual_args)
        )


# ============================================================
# NAME RESOLUTION
# ============================================================

def resolve_name(name, env, functions, line=0, col=0):
    """
    Resolve a variable name using priority:
    1) environment variable
    2) user-defined function table
    3) builtin function table
    """
    if env.has(name):
        return env.get(name)
    if name in functions:
        return functions[name]
    # Builtins are checked at call time, not here
    raise BicalaNameError(
        code="N001",
        line=line,
        col=col,
        name=name
    )


def validate_name_not_defined(name, env, functions, line=0, col=0):
    """Validate that a name is NOT already defined (for new definitions)."""
    if env.has(name):
        raise BicalaNameError(
            code="N002",
            line=line,
            col=col,
            name=name
        )
    if name in functions:
        raise BicalaNameError(
            code="N002",
            line=line,
            col=col,
            name=name
        )


def validate_name_exists(name, env, functions, line=0, col=0):
    """Validate that a name IS defined (for usage)."""
    if env.has(name):
        return
    if name in functions:
        return
    raise BicalaNameError(
        code="N001",
        line=line,
        col=col,
        name=name
    )


def validate_interpolation_name(name, env, line=0, col=0):
    """Validate that a name used in string interpolation exists."""
    if not env.has(name):
        raise BicalaNameError(
            code="N004",
            line=line,
            col=col,
            name=name
        )


def validate_custom_operator(symbol, line=0, col=0):
    """Validate that a custom operator is registered."""
    from env import get_custom_operator
    op_def = get_custom_operator(symbol)
    if op_def is None:
        raise BicalaNameError(
            code="N004",
            line=line,
            col=col,
            name=symbol
        )
    return op_def


# ============================================================
# VALUE VALIDATION
# ============================================================

def validate_operator(op, line=0, col=0):
    """Validate that an operator is recognized."""
    from tok import OPERATORS
    if op not in OPERATORS:
        raise BicalaValueError(
            code="V001",
            line=line,
            col=col,
            op=op
        )


def validate_comparison_op(op, line=0, col=0):
    """Validate that a comparison operator is recognized."""
    valid_ops = ['==', '===', '.=', '!=', '!==', '!===', '>', '<', '>=', '<=', 'in']
    if op not in valid_ops:
        raise BicalaValueError(
            code="V003",
            line=line,
            col=col,
            op=op
        )


# ============================================================
# CONST VALIDATION
# ============================================================

def validate_const_assignment(node, env):
    """
    Validate that a constant variable is not being reassigned.
    Raises N002 if attempting to reassign a constant.
    """
    if hasattr(node, 'target') and hasattr(node.target, 'name'):
        var_name = node.target.name
        if env.is_const(var_name):
            line = getattr(node, 'line', 0)
            col = getattr(node, 'col', 0)
            raise BicalaNameError(
                code="N002",
                line=line,
                col=col,
                name=var_name
            )


# ============================================================
# TYPE VALIDATION
# ============================================================

def get_type_string(value):
    """
    Get the type string for a value.
    Returns: 'int', 'float', 'string', 'bool', 'array', or 'unknown'
    """
    if isinstance(value, int) and not isinstance(value, bool):
        return 'int'
    elif isinstance(value, float):
        return 'float'
    elif isinstance(value, str):
        return 'string'
    elif isinstance(value, bool):
        return 'bool'
    elif isinstance(value, list):
        return 'array'
    else:
        return 'unknown'


def validate_type_assignment(node, expr_value, env):
    """
    Validate that the expression type matches the declared type.
    Raises T002 if types don't match.
    """
    if not hasattr(node, 'declared_type') or node.declared_type is None:
        return  # No type constraint
    
    declared_type = node.declared_type
    actual_type = get_type_string(expr_value)
    
    # Map type aliases if needed
    type_mapping = {
        'int': 'int',
        'float': 'float', 
        'string': 'string',
        'bool': 'bool',
        'array': 'array'
    }
    
    expected_type = type_mapping.get(declared_type, declared_type)
    
    if actual_type != expected_type:
        line = getattr(node, 'line', 0)
        col = getattr(node, 'col', 0)
        raise BicalaTypeError(
            code="T002",
            line=line,
            col=col,
            expected_type=expected_type,
            actual_type=actual_type
        )
