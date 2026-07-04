# ============================================================
# env.py — Runtime environment (scope management) for BImuila
# Supports nested scopes (functions, blocks)
# Imports: err (for BicalaEnvironmentError)
# ============================================================

from err import BicalaImportError, BicalaNameError

import math as _math
import builtins as _builtins
import time as _time


class Module:
    """
    Runtime Library Module - contains built-in functions as Python callables.
    Provides fast direct Python function execution without intermediate layers.
    """
    
    __slots__ = ['_name', '_attrs']
    
    def __init__(self, name, attrs):
        """
        Create a module with given name and attributes.
        
        :param name: Module name (e.g., 'math', 'str', 'arr')
        :param attrs: Dictionary of attribute names to Python callables/values
        """
        self._name = name
        self._attrs = attrs
    
    def __getattr__(self, name):
        """Get module attribute (function or constant)."""
        if name in self._attrs:
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


class Environment:
    """
    Environment for variable storage with parent scope support.
    Enables proper scoping for function calls and nested blocks.
    """
    
    __slots__ = ['vars', 'functions', 'parent', 'defer_stack', 'const_vars', 'typed_vars']
    
    def __init__(self, parent=None):
        """
        Create new environment.
        :param parent: Parent environment for lookup chain
        """
        self.vars = {}
        self.functions = {}  # Track function names separately for collision detection
        self.parent = parent
        self.defer_stack = []  # Stack for defer statements (LIFO order)
        self.const_vars = set()  # Track constant variable names
        self.typed_vars = {}  # Track type-constrained variables: {name: type}
    
    def define(self, name, value):
        """Define (or overwrite) a variable in the current local scope."""
        self.vars[name] = value

    def define_function(self, name, func_def):
        """
        Define a function in the current local scope.
        Raises ValueError if name collides with existing variable or function.
        """
        if name in self.vars:
            raise BicalaNameError(
                code="N007",
                line=0,
                col=0,
                name=name
            )
        if name in self.functions:
            raise BicalaNameError(
                code="N007",
                line=0,
                col=0,
                name=name
            )
        self.functions[name] = func_def

    def undefine_local(self, name):
        """Remove a variable from current local scope if present."""
        self.vars.pop(name, None)
        # Also remove from functions if present
        self.functions.pop(name, None)

    def undefine_function_local(self, name):
        """Remove a function from current local scope if present."""
        self.functions.pop(name, None)

    def _iter_chain(self):
        """Yield current env then parents (nearest scope first)."""
        env = self
        while env is not None:
            yield env
            env = env.parent

    def _find_env_containing(self, name):
        """Return nearest environment containing `name`, or None if missing."""
        for env in self._iter_chain():
            if name in env.vars:
                return env
        return None
    
    def get(self, name):
        """
        Get variable value, looking up parent chain if needed.
        Raises NameError if not found.
        """
        owner = self._find_env_containing(name)
        if owner is not None:
            return owner.vars[name]
        raise NameError(f"Variable '{name}' is not defined")  # Caught by evaluator, re-raised as BicalaNameError
    
    def set(self, name, value):
        """
        Set variable value, looking up parent chain for existing vars.
        Raises NameError if variable doesn't exist anywhere.
        """
        owner = self._find_env_containing(name)
        if owner is not None:
            owner.vars[name] = value
            return
        raise NameError(f"Variable '{name}' is not defined")  # Caught by evaluator, re-raised as BicalaNameError
    
    def has(self, name):
        """Check if variable exists in this or parent scope."""
        return self._find_env_containing(name) is not None
    
    def has_local(self, name):
        """Check if variable exists only in current scope."""
        return name in self.vars
    
    def assign(self, name, value):
        """
        Syntax-level assignment behavior:
        - update nearest existing binding if found in scope chain
        - otherwise create in current local scope
        - raises ValueError if name collides with function in current scope
        """
        owner = self._find_env_containing(name)
        if owner is None:
            # Check for function name collision in current scope
            if name in self.functions:
                raise BicalaNameError(
                    code="N007",
                    line=0,
                    col=0,
                    name=name
                )
            self.vars[name] = value
            return
        owner.vars[name] = value
    
    def is_const(self, name):
        """Check if a variable is marked as constant in any scope."""
        for env in self._iter_chain():
            if name in env.const_vars:
                return True
        return False
    
    def get_declared_type(self, name):
        """Get the declared type of a variable if it has one."""
        for env in self._iter_chain():
            if name in env.typed_vars:
                return env.typed_vars[name]
        return None
    
    def mark_const(self, name):
        """Mark a variable as constant in the current scope."""
        self.const_vars.add(name)
    
    def mark_typed(self, name, var_type):
        """Mark a variable with a declared type in the current scope."""
        self.typed_vars[name] = var_type
    
    def all_vars(self):
        """Get merged variables for debug/introspection (parents first, locals override)."""
        chain = list(self._iter_chain())
        result = {}
        for env in reversed(chain):
            result.update(env.vars)
        return result
    
    def __repr__(self):
        depth = sum(1 for _ in self._iter_chain()) - 1
        return f"Environment(depth={depth}, local_vars={list(self.vars.keys())}, has_parent={self.parent is not None})"


from err import BicalaEnvironmentError

# Keep backward compat alias
EnvironmentError = BicalaEnvironmentError


# ============================================================
# BUILT-IN MODULES - Runtime Library
# ============================================================

# Math Module
MathModule = Module('math', {
    # Constants
    'pi': _math.pi,
    'e': _math.e,
    'tau': _math.tau,
    'inf': _math.inf,
    'nan': _math.nan,
    # Root / Pow / Abs
    'sqrt': _math.sqrt,
    'cbrt': _math.cbrt,
    'root': lambda x, n: x ** (1/n),
    'pow': _math.pow,
    'abs': abs,
    'fabs': _math.fabs,
    # Number Theory
    'fact': lambda x: _math.factorial(int(x)),
    'gcd': _math.gcd,
    'lcm': lambda a, b: abs(a * b) // _math.gcd(a, b),
    # Rounding
    'floor': _math.floor,
    'ceil': _math.ceil,
    'trunc': _math.trunc,
    'round': round,
    'sum': sum,
    'fsum': _math.fsum,
    # Log / exp
    'log': lambda x, base=None: _math.log(x, base) if base else _math.log(x, 10),
    'ln': lambda x: _math.log(x, _math.e),
    'log10': _math.log10,
    'log2': _math.log2,
    'log1p': _math.log1p,
    'exp': _math.exp,
    'expm1': _math.expm1,
    # Trigonometry
    'sin': _math.sin,
    'cos': _math.cos,
    'tan': _math.tan,
    'asin': _math.asin,
    'acos': _math.acos,
    'atan': _math.atan,
    'atan2': _math.atan2,
    'sinh': _math.sinh,
    'cosh': _math.cosh,
    'tanh': _math.tanh,
    'asinh': _math.asinh,
    'acosh': _math.acosh,
    'atanh': _math.atanh,
    # Geometry
    'hypot': _math.hypot,
    'dist': lambda x1, y1, x2, y2: _math.hypot(x2 - x1, y2 - y1),
    # Angle System
    'degrees': _math.degrees,
    'radians': _math.radians,
    'grad': lambda x: x * (200 / _math.pi),
    # Time Angle
    'sec_to_deg': lambda s: s / 3600,
    'min_to_deg': lambda m: m / 60,
    'hour_to_deg': lambda h: h * 15,
    'deg_to_sec': lambda d: d * 3600,
    'deg_to_min': lambda d: d * 60,
    'deg_to_hour': lambda d: d / 15,
    # Floating-point control
    'copysign': _math.copysign,
    'frexp': _math.frexp,
    'ldexp': _math.ldexp,
    # Checks
    'isfinite': _math.isfinite,
    'isnan': _math.isnan,
    'isinf': _math.isinf,
    # Combinatorics
    'perm': _math.perm,
    'comb': _math.comb,
    # Extras
    'clamp': lambda x, a, b: max(a, min(b, x)),
    'sign': lambda x: (x > 0) - (x < 0),
    'neg': lambda x: -x,
    'lerp': lambda a, b, t: a + (b - a) * t,
})

# String Module
StrModule = Module('str', {
    'whitespace': ' \t\n\r\f\v',
    'upper': lambda s: str(s).upper(),
    'lower': lambda s: str(s).lower(),
    'title': lambda s: str(s).title(),
    'capitalize': lambda s: str(s).capitalize(),
    'strip': lambda s, chars=None: str(s).strip(chars),
    'lstrip': lambda s, chars=None: str(s).lstrip(chars),
    'rstrip': lambda s, chars=None: str(s).rstrip(chars),
    'split': lambda s, sep=None, maxsplit=-1: str(s).split(sep, maxsplit),
    'join': lambda sep, items: str(sep).join(str(i) for i in items),
    'replace': lambda s, old, new, count=-1: str(s).replace(old, new, count),
    'find': lambda s, sub, start=0, end=None: str(s).find(sub, start, end),
    'rfind': lambda s, sub, start=0, end=None: str(s).rfind(sub, start, end),
    'count': lambda s, sub, start=0, end=None: str(s).count(sub, start, end),
    'startswith': lambda s, prefix, start=0, end=None: str(s).startswith(prefix, start, end),
    'endswith': lambda s, suffix, start=0, end=None: str(s).endswith(suffix, start, end),
    'length': lambda s: _builtins.len(str(s)),
    'len': lambda s: _builtins.len(str(s)),
    'format': lambda s, *args, **kwargs: str(s).format(*args, **kwargs),
    'isdigit': lambda s: str(s).isdigit(),
    'isalpha': lambda s: str(s).isalpha(),
    'isalnum': lambda s: str(s).isalnum(),
    'isspace': lambda s: str(s).isspace(),
    'isupper': lambda s: str(s).isupper(),
    'islower': lambda s: str(s).islower(),
})

# Array Module (also known as 'arr')
ArrayModule = Module('arr', {
    'len': lambda items: _builtins.len(items),
    'first': lambda items: items[0],
    'last': lambda items: items[-1],
    'push': lambda items, value: (items.append(value), items)[1],
    'pop': lambda items, index=-1: items.pop(index),
    'insert': lambda items, index, value: (items.insert(index, value), items)[1],
    'remove': lambda items, value: (items.remove(value), items)[1],
    'concat': lambda left, right: list(left) + list(right),
    'reverse': lambda items: list(reversed(items)),
    'sort': lambda items: sorted(items),
})

# Time Module
TimeModule = Module('time', {
    # Core time functions
    'sleep': lambda seconds: _time.sleep(seconds),
    'ctime': lambda seconds=None: _time.ctime(seconds) if seconds is not None else _time.ctime(),
    'perf_counter': _time.perf_counter,
    'strftime': lambda format, seconds=None: _time.strftime(format, _time.localtime(seconds)) if seconds is not None else _time.strftime(format),
    'strptime': lambda string, format: _time.strptime(string, format),
    # Local time unit getters
    'local_year': lambda: _time.localtime().tm_year,
    'local_month': lambda: _time.localtime().tm_mon,
    'local_day': lambda: _time.localtime().tm_mday,
    'local_weekday': lambda: _time.localtime().tm_wday,
    'local_hour': lambda: _time.localtime().tm_hour,
    'local_minute': lambda: _time.localtime().tm_min,
    'local_second': lambda: _time.localtime().tm_sec,
    # GMT time unit getters
    'gmt_year': lambda: _time.gmtime().tm_year,
    'gmt_month': lambda: _time.gmtime().tm_mon,
    'gmt_day': lambda: _time.gmtime().tm_mday,
    'gmt_weekday': lambda: _time.gmtime().tm_wday,
    'gmt_hour': lambda: _time.gmtime().tm_hour,
    'gmt_minute': lambda: _time.gmtime().tm_min,
    'gmt_second': lambda: _time.gmtime().tm_sec,
    # Additional useful time functions
    'time': _time.time,
})

# Module registry for import system
BUILTIN_MODULES = {
    'math': MathModule,
    'str': StrModule,
    'arr': ArrayModule,
    'time': TimeModule,
}

# Built-in functions (global scope)
BUILTIN_FUNCTIONS = {
    'say': lambda x: print(x),
    'time': _time.time,
}

# Module Alias Table - tracks module aliases (from X as Y)
MODULE_ALIAS_TABLE = {}

# Module Registry - prevents circular loading
MODULE_REGISTRY = {}


def get_builtin_module(name):
    """Get built-in module by name."""
    if name not in BUILTIN_MODULES:
        raise BicalaImportError(
            code="M001",
            line=0,
            col=0,
            name=name
        )
    return BUILTIN_MODULES[name]


def list_builtin_modules():
    """List available built-in module names."""
    return list(BUILTIN_MODULES.keys())


def register_module_alias(original_name, alias):
    """
    Register a module alias (from X as Y).
    Raises ValueError if alias already exists for a different module (name collision).
    Allows re-registering the same alias for the same module (idempotent).
    """
    global MODULE_ALIAS_TABLE
    if alias in MODULE_ALIAS_TABLE:
        if MODULE_ALIAS_TABLE[alias] != original_name:
            raise BicalaImportError(
                code="M003",
                line=0,
                col=0,
                name=alias
            )
        # Same alias for same module - idempotent, no error
        return
    MODULE_ALIAS_TABLE[alias] = original_name


def resolve_module_alias(name):
    """
    Resolve a module name through alias table.
    Returns the original module name if it's an alias, otherwise returns the name as-is.
    """
    return MODULE_ALIAS_TABLE.get(name, name)


def is_module_loaded(name):
    """Check if a module is already in the registry (prevents circular loading)."""
    return name in MODULE_REGISTRY


def register_module(name, module):
    """Register a loaded module in the registry."""
    MODULE_REGISTRY[name] = module


def check_circular_import(name):
    """
    Check if importing this module would cause a circular import.
    Raises ImportError if circular dependency detected.
    """
    global MODULE_REGISTRY
    if name in MODULE_REGISTRY:
        raise BicalaImportError(
            code="M002",
            line=0,
            col=0,
            name=name
        )


def clear_module_registry():
    """Clear the module registry (useful for testing or fresh execution)."""
    global MODULE_REGISTRY
    MODULE_REGISTRY.clear()


def get_registered_module(name):
    """Get a registered module from the registry."""
    return MODULE_REGISTRY.get(name)


# ============================================================
# CUSTOM OPERATOR REGISTRY
# Stores user-defined custom operators (infix, prefix, suffix)
# ============================================================

CUSTOM_OPERATORS = {}  # Format: {symbol: {"type": "infix"/"prefix"/"suffix", "params": [param_names], "body": ast_node}}


def register_custom_operator(symbol, op_type, params, body_ast):
    """
    Register a custom operator definition.
    
    :param symbol: The operator symbol (e.g., '^', '~>')
    :param op_type: Operator type - "infix", "prefix", or "suffix"
    :param params: List of parameter names (e.g., ["a", "b"] for infix, ["a"] for prefix)
    :param body_ast: AST node representing the operator body
    """
    CUSTOM_OPERATORS[symbol] = {
        "type": op_type,
        "params": params,
        "body": body_ast
    }


def get_custom_operator(symbol):
    """Get custom operator definition by symbol, or None if not found."""
    return CUSTOM_OPERATORS.get(symbol)


def is_custom_operator(symbol):
    """Check if a symbol is a registered custom operator."""
    return symbol in CUSTOM_OPERATORS


def clear_custom_operators():
    """Clear all custom operators (useful for testing or fresh execution)."""
    global CUSTOM_OPERATORS
    CUSTOM_OPERATORS.clear()


def list_custom_operators():
    """Return list of all registered custom operator symbols."""
    return list(CUSTOM_OPERATORS.keys())
