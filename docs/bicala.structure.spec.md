# Bicala Compiler Architecture Specification (Beta 5.1.24.3)

This document provides a deep-dive analysis of the internal structure, responsibilities, and key functions/classes of each component in the Bicala compiler.

---

## 1. Compiler Infrastructure Core (`main/`)

### 1.1 `lex.py` - Lexical Analysis (Tokenizer)

**Purpose**: Converts source code strings into a stream of tokens for the parser.

**Key Functions**:

- `tokenize(expr, line_num=1, base_col=0)` - Main tokenization function
  - Parameters:
    - `expr`: Source string to tokenize
    - `line_num`: Starting line number for error reporting (1-based)
    - `base_col`: Column offset for the first character (0-based)
  - Returns: List of `Token` objects
  - Tracks line/column positions for error reporting

**Tokenization Strategy**:

The lexer processes characters sequentially with the following priority order:

1. **Whitespace & Newlines** - Skipped but tracked for line/column counting
2. **Block Comments** (`###...###`) - Multi-line comments with L006 error if unterminated
3. **Single-line Comments** (`#`) - Consumed until end of line
4. **Multi-character Operators** (longest-first matching) - Ensures compound operators like `.=`, `**`, `==`, `!==` are matched completely
5. **Punctuation** - Single-character structural tokens:
   - `(` `)` - Grouping
   - `[` `]` - Arrays/slices
   - `,` - Expression separator
   - `;` - Function call terminator
   - `|` - Statement separator
   - `:` - Block header
   - `.` - Property accessor
6. **String Literals** - Supports:
   - Escape sequences: `\n`, `\t`, `\r`, `\\`, `\"`, `\'`, `\{`, `\}`
   - String interpolation: `{variable}` syntax
   - Stored as either simple string or `('INTERPOLATED', parts_list)` tuple
7. **Numbers** - Integers and floats with L005 error for invalid literals
8. **Identifiers & Keywords** - Distinguished via `is_keyword()` and `is_builtin()` checks
9. **Single-character Operators** - Fallback for remaining operators
10. **Unknown Characters** - Raises L002 error

**Error Codes Raised**:
- L001: Unterminated string
- L002: Invalid character
- L003: Invalid escape sequence
- L004: Unterminated string literal (newline in string)
- L005: Invalid number literal
- L006: Unterminated block comment
- L007: Unterminated interpolation in string
- L008: Empty interpolation in string

---

### 1.2 `tok.py` - Token Definitions & Dynamic Syntax Configuration

**Purpose**: Single source of truth for all token definitions, syntax configuration, operators, and keyword mappings. No internal project imports allowed (base module).

**Key Data Structures**:

**Dynamic Syntax Overrides**:
- Group-based keyword dictionaries for maintainability:
  - `_LOGICAL`: `and`, `or`, `not`, `in`
  - `_CONTROL_FLOW`: `if`, `elif`, `else`, `while`, `for`, `repeat`, `forever`, `try`, `catch`, `finally`, `switch`, `default`, `defer`
  - `_FUNCTIONS`: `def`, `return`, `define`, `infix`, `infixl`, `infixr`, `prefix`, `postfix`, `fn`
  - `_DECLARATIONS`: `const`
  - `_LOOP_CONTROL`: `break`, `continue`, `del`, `pass`
  - `_LITERALS`: `true`, `false`, `none`, `nan`
  - `_IO`: `input`, `say` (maps 'say' to internal PRINT token)
  - `_BUILTINS`: `debug`, `help`, `error`, `type`
  - `_MODULE`: `import`, `from`, `as`

- `SYNTAX` - Merged dictionary of all keyword groups (uppercase keys → lowercase values)
- `KEYWORDS` - Active keyword set derived from `SYNTAX` (via `_build_keyword_set()`)
- `BUILTINS` - Active built-in function set derived from `SYNTAX` (via `_build_builtin_set()`)

**Key Functions**:

- `refresh_syntax()` - Re-derives KEYWORDS, BUILTINS, and OPERATORS after SYNTAX mutations
- `get_syntax(key)` - Returns active keyword string for internal token name
- `resolve_syntax(text)` - Returns internal token name for user-facing keyword, or None
- `is_keyword(text)` - Checks if text is an active keyword
- `is_builtin(text)` - Checks if text is an active built-in

**Operator System**:

- `OPERATOR_PRECEDENCE` - Scale 0-1000 for flexible custom operator insertion
  - COMMA: 50
  - ASSIGN: 100
  - COMPOUND_ASSIGN: 150
  - TERNARY: 200
  - OR: 300
  - AND: 400
  - NOT: 500
  - CMP: 600
  - ADD: 700
  - MUL: 800
  - POW: 900
  - UNARY: 950
  - PAREN: 1000

- `OPERATORS` - Dynamic operator table: `{symbol: (precedence, associativity)}`
- `register_custom_operator(op_symbol, precedence, associativity)` - Runtime operator registration
- `unregister_custom_operator(op_symbol)` - Remove custom operator
- `get_precedence(op)` - Get operator precedence
- `get_associativity(op)` - Get operator associativity
- `is_right_associative(op)` - Check if operator is right-associative

**Token Class**:

```python
class Token:
    __slots__ = ("type", "value", "line", "col", "length")
    def __init__(self, type_, value=None, line=0, col=0, length=None)
```

**Token Types**:
- `TOKEN_NUMBER`, `TOKEN_STRING`, `TOKEN_IDENT`, `TOKEN_KEYWORD`
- `TOKEN_OP`, `TOKEN_DOT`, `TOKEN_LPAREN`, `TOKEN_RPAREN`
- `TOKEN_LBRACKET`, `TOKEN_RBRACKET`, `TOKEN_COMMA`, `TOKEN_COLON`
- `TOKEN_SEMICOLON`, `TOKEN_PIPE`, `TOKEN_EOF`

**SyntaxConfig Singleton**:
- Property-based accessor for syntax tables
- Provides convenient access to: assignment_operators, comparison_operators, arithmetic_operators, logical_operators, punctuation, keywords, comment_markers, operator_precedence

---

### 1.3 `ast.py` - Abstract Syntax Tree Node Definitions

**Purpose**: Pure data structures representing parsed program. NO logic/eval methods here. No imports allowed (base module).

**Node Hierarchy**:

```
ASTNode (base)
├── ExprNode (expression base)
│   ├── NumberNode
│   ├── BooleanNode
│   ├── NoneNode
│   ├── NaNNode
│   ├── StringNode (supports interpolation)
│   ├── VarNode
│   ├── ArrayNode
│   ├── UnaryOpNode
│   ├── BinaryOpNode
│   ├── CompareNode
│   ├── CallNode
│   ├── LambdaNode
│   ├── IndexNode
│   ├── SliceNode
│   ├── InlineIfNode
│   ├── TernaryNode
│   ├── AttrNode (attribute access: obj.attr)
│   └── TypeNode
└── StmtNode (statement base)
    ├── ExprStmtNode (expression as statement)
    ├── AssignNode (with is_const, declared_type)
    ├── CompoundAssignNode
    ├── IncDecNode
    ├── SayNode
    ├── InputNode
    ├── DebugNode
    ├── ErrorNode
    ├── ReturnNode
    ├── BreakNode
    ├── ContinueNode
    ├── BlockNode
    ├── IfNode (with elif_blocks, else_block)
    ├── WhileNode
    ├── ForNode (supports range and array iteration)
    ├── SwitchNode (with cases, default_block)
    ├── TryCatchNode (with try_body, catch_param, catch_body, finally_body)
    ├── DefNode
    ├── CommentNode
    ├── PassNode
    ├── HelpNode
    ├── ImportNode
    ├── FromImportNode (with alias, name_aliases)
    ├── CustomOperatorDef (symbol, op_type, precedence, params, body)
    ├── CustomOperatorCall (symbol, op_type, args)
    ├── DelNode
    └── DeferNode
```

**Key Features**:

- All nodes use `__slots__` for memory efficiency
- Each node stores `line` and `col` for error reporting
- `dump_tree(indent)` method for recursive AST debugging
- `__repr__` methods for readable node representation
- Validation in constructors (e.g., AssignNode validates target is valid l-value)

**Special Nodes**:

- `StringNode.value` can be either plain string or `('INTERPOLATED', parts_list)` tuple
- `CallNode.callee` can be string (converted to VarNode) or AST node
- `ForNode` supports both range iteration (`for i: 1:10`) and array iteration (`for item in arr`)
- `CustomOperatorDef` and `CustomOperatorCall` enable user-defined operators

---

### 1.4 `env.py` - Runtime Environment & Scope Management

**Purpose**: Manages variable storage, scope hierarchy (parent/child), constant enforcement, and function bindings.

**Key Classes**:

**Module Class**:
```python
class Module:
    __slots__ = ['_name', '_attrs']
    def __init__(self, name, attrs)  # attrs: dict of name → Python callable
    def __getattr__(self, name)      # Raises M004 if not found
```

**Environment Class**:
```python
class Environment:
    __slots__ = ['vars', 'functions', 'parent', 'defer_stack', 'const_vars', 'typed_vars']
```

**Key Methods**:

- `define(name, value)` - Define/overwrite variable in current local scope
- `define_function(name, func_def)` - Define function, raises N007 on collision
- `undefine_local(name)` - Remove variable from current scope
- `undefine_function_local(name)` - Remove function from current scope
- `get(name)` - Get variable, looking up parent chain (raises NameError if not found)
- `set(name, value)` - Set variable in nearest scope (raises NameError if not found)
- `has(name)` - Check if variable exists in this or parent scope
- `has_local(name)` - Check if variable exists only in current scope
- `assign(name, value)` - Syntax-level assignment: updates nearest existing or creates in local scope
- `is_const(name)` - Check if variable is marked constant in any scope
- `get_declared_type(name)` - Get declared type of variable if it has one
- `mark_const(name)` - Mark variable as constant in current scope
- `mark_typed(name, var_type)` - Mark variable with declared type
- `all_vars()` - Get merged variables for debug (parents first, locals override)

**Scope Chain**:
- `_iter_chain()` - Yields current env then parents (nearest scope first)
- `_find_env_containing(name)` - Returns nearest environment containing name

**Built-in Modules**:

- `MathModule` - Constants (pi, e, tau, inf, nan), root/pow/abs, number theory, rounding, log/exp, trigonometry, geometry, angle system, floating-point control, combinatorics
- `StrModule` - String manipulation: upper/lower, strip, split, join, replace, find, count, startswith/endswith, length, format, isdigit/isalpha/isalnum/isspace/isupper/islower
- `ArrayModule` (alias 'arr') - len, first, last, push, pop, insert, remove, concat, reverse, sort
- `TimeModule` - sleep, ctime, perf_counter, strftime/strptime, local/GMT time unit getters, time

**Module Registry Functions**:

- `get_builtin_module(name)` - Get built-in module (raises M001 if not found)
- `list_builtin_modules()` - List available built-in module names
- `register_module_alias(original_name, alias)` - Register alias (raises M003 on collision)
- `resolve_module_alias(name)` - Resolve alias to original name
- `is_module_loaded(name)` - Check if module in registry (prevents circular loading)
- `register_module(name, module)` - Register loaded module
- `check_circular_import(name)` - Check for circular import (raises M002)
- `clear_module_registry()` - Clear registry (for testing)
- `get_registered_module(name)` - Get registered module

**Custom Operator Registry**:

- `CUSTOM_OPERATORS` - Dict: `{symbol: {"type": "infix"/"prefix"/"suffix", "params": [param_names], "body": ast_node}}`
- `register_custom_operator(symbol, op_type, params, body_ast)` - Register custom operator
- `get_custom_operator(symbol)` - Get custom operator definition
- `is_custom_operator(symbol)` - Check if symbol is registered
- `clear_custom_operators()` - Clear all custom operators
- `list_custom_operators()` - List all registered symbols

---

### 1.5 `err.py` - Centralized Error Architecture

**Purpose**: Rich error system with codes, context, and formatted output. Single source of truth for all error messages and hints.

**Error Code Ranges**:
- L001-L099: Lexer Errors
- S001-S099: Syntax/Parser Errors (including indentation)
- R001-R099: Runtime Errors
- T001-T099: Type Errors
- V001-V099: Value Errors
- N001-N099: Name Errors (including attribute errors)
- M001-M099: Import Errors

**Severity Levels**:
- `SEVERITY_FATAL`: Cannot continue (internal error, stack overflow)
- `SEVERITY_ERROR`: Compilation/parse error (cannot run)
- `SEVERITY_RUNTIME`: Generic runtime error
- `SEVERITY_WARNING`: Non-fatal issue (deprecated syntax, etc.)
- `SEVERITY_NAME`: Name/scope resolution error
- `SEVERITY_TYPE`: Type system error
- `SEVERITY_VALUE`: Value/operation error
- `SEVERITY_ATTRIBUTE`: Object model error
- `SEVERITY_IMPORT`: Module system error

**ERRORS Database**:
- Dictionary mapping error codes to templates:
  ```python
  "L001": {
      "message": "Unterminated string",
      "hint": "Add closing quote to end the string"
  }
  ```
- Templates support placeholder formatting: `{name}`, `{char}`, `{expected}`, `{got}`, etc.

**Error Class Hierarchy**:

```
BicalaError (base)
├── BicalaParseError
│   ├── BicalaLexerError (L001-L099)
│   ├── BicalaSyntaxError (S001-S099)
│   └── BicalaIndentationError (I001-I099)
├── BicalaExecutionError
│   ├── BicalaScopeError
│   │   ├── BicalaNameError (N001-N099)
│   │   ├── BicalaEnvironmentError
│   │   └── BicalaAttributeError (A001-A099)
│   ├── BicalaTypeError (T001-T099)
│   ├── BicalaValueError (V001-V099)
│   ├── BicalaRuntimeError (R001-R099)
│   └── BicalaImportError (M001-M099)
```

**BicalaError Class**:
```python
class BicalaError(Exception):
    __init__(self, code="E000", line=None, col=None, **context)
```
- Auto-detects severity from code prefix
- Formats message and hint using ERRORS database templates
- Stores: code, line, col, message, expected, got, hint, length, severity

**format_error Function**:
```python
def format_error(err, source_lines=None, context=1)
```
- Formats error with source context and pointer
- Shows surrounding lines with line numbers
- Points to error location with `^` characters
- Displays expected/got values and hint

---

### 1.6 `sem.py` - Semantic Analysis Layer

**Purpose**: Isolated validation layer for name resolution, type checking, and value validation before evaluation. No circular imports (no eval, no parser).

**Type Validation Functions**:

- `require_boolean(value, node=None, context="condition")` - Requires real boolean (no Python truthiness), raises T002
- `require_loop_int(value, node=None, context="loop bound")` - Requires integer for loop bounds (not boolean), raises T003
- `validate_callable(target, target_label, line=0, col=0)` - Validates value is callable, raises T004
- `validate_function_arity(expected_params, actual_args, line=0, col=0)` - Validates argument count, raises T005/T006

**Name Resolution Functions**:

- `resolve_name(name, env, functions, line=0, col=0)` - Resolves name with priority: env variable → user function → builtin, raises N001
- `validate_name_not_defined(name, env, functions, line=0, col=0)` - Validates name is NOT defined (for new definitions), raises N002
- `validate_name_exists(name, env, functions, line=0, col=0)` - Validates name IS defined (for usage), raises N001
- `validate_interpolation_name(name, env, line=0, col=0)` - Validates name in string interpolation exists, raises N004
- `validate_custom_operator(symbol, line=0, col=0)` - Validates custom operator is registered, raises N004

**Value Validation Functions**:

- `validate_operator(op, line=0, col=0)` - Validates operator is recognized, raises V001
- `validate_comparison_op(op, line=0, col=0)` - Validates comparison operator, raises V003

**Const Validation**:

- `validate_const_assignment(node, env)` - Validates constant not being reassigned, raises N002

**Type Validation**:

- `get_type_string(value)` - Returns type string: 'int', 'float', 'string', 'bool', 'array', or 'unknown'
- `validate_type_assignment(node, expr_value, env)` - Validates expression type matches declared type, raises T002

---

### 1.7 `eval.py` - Runtime Tree-Walking Evaluator

**Purpose**: Executes AST nodes by walking the tree and evaluating expressions/statements. Stateful interactions with `env.py`.

**Control Flow Signals**:

```python
class BreakSignal(Exception)    # Raised by break statement
class ContinueSignal(Exception) # Raised by continue statement
class ReturnSignal(Exception)    # Raised by return statement
```

**Built-in Functions**:

- `_current_source_dir` - Tracks current source directory for .bica imports
- `_gui_input_callback` - Callback for GUI-based input (set by IDE)
- `_cli_input_callback` - Fallback to Python's input()
- `set_gui_input_callback(callback)` - Set GUI input callback
- `set_source_dir(path)` - Set current source directory

**Import System**:

- `_import(name)` - Import built-in module or .bica file
  - First tries built-in modules from env.py
  - Then tries .bica file in current source directory
  - Raises M001 if not found
- `_import_bica(filepath, module_name)` - Import .bica file as module proxy
  - Parses and executes in isolated environment
  - Collects exported names (variables + functions)
  - Returns `_ModuleProxy`

**Module Proxy Classes**:

- `_ModuleProxy` - Proxy to access module attributes (both built-in and .bica)
  - `__getattr__(name)` - Returns attribute or raises M004
- `_BicaFunction` - Callable wrapper for functions from .bica modules
  - `__call__(*args)` - Calls function with arity validation
- `_LambdaFunction` - Callable wrapper for lambda expressions
  - `__call__(*args)` - Creates new environment with parameter bound

**Built-in Functions Dictionary**:

```python
BUILTINS = {
    'len': len, 'abs': abs, 'round': round, 'max': max, 'min': min,
    'int': int, 'float': float, 'str': str, 'bool': bool,
    'range': range, 'enumerate': enumerate, 'zip': zip,
    'list': list, 'tuple': tuple, 'sum': sum, 'sorted': sorted,
    'reversed': lambda x: list(reversed(x)),
    'any': any, 'all': all,
    'import': _import, 'input': _builtin_input,
}
```

**Expression Evaluator**:

- `is_truthy(value)` - Bicala truthiness: false, None, NaN, 0, "" are falsy
- `_loose_equals(left, right)` - Loose equality (.=) with dynamic type coercion
  - None .= None → True
  - bool ↔ str: compare via lowered string form
  - str ↔ num: coerce string to float
  - num ↔ num: compare values (int 2 .= float 2.0 → True)
  - str ↔ str: case-insensitive
  - fallback: Python ==
- `_strict_equals(left, right)` - Strict equality (==): type and value must match
- `_identity_equals(left, right)` - Identity equality (===): Python `is`

**Expression Evaluation**:

- `evaluate_expression(node, env, functions=None)` - Main expression evaluator
  - Handles all expression node types
  - Resolves names via `resolve_name()`
  - Validates callables and arity
  - Evaluates custom operators
  - Handles string interpolation

**Statement Execution**:

- `execute_statement(node, env, functions)` - Main statement executor
  - Handles all statement node types
  - Manages control flow signals (break, continue, return)
  - Handles defer statements (LIFO stack)
  - Manages scope for blocks and functions

**Program Execution**:

- `execute_program(program, functions=None)` - Execute program AST
  - Creates global environment
  - Registers built-in functions
  - Executes statements sequentially
  - Returns environment and functions

**Custom Operator Execution**:

- `evaluate_custom_operator_call(node, env, functions)` - Evaluates custom operator calls
  - Retrieves operator definition from registry
  - Creates new environment with parameters bound
  - Evaluates operator body

---

## 2. The Parser Package (`main/pars/`)

### 2.1 `base.py` - Parser Core Helpers

**Purpose**: Core parsing helpers, constants, and utility functions for parsing. No circular dependencies.

**Precomputed Operator Sets**:

- `_COMPARISON_OPS` - Set of comparison operators including `.=`
- `_ADD_OPS` - `{'+', '-'}`
- `_MUL_OPS` - `{'*', '/', '//', '%'}`
- `_POW_OPS` - `{'**', '^'}`
- `_KW_AND`, `_KW_OR`, `_KW_NOT` - Logical operator keywords

**Key Functions**:

- `_line_indent(raw_line)` - Count leading spaces (4-space tabs)
- `_line_indent_level(raw_line, line_num=0)` - Get indentation level (0-based), raises S014 if not multiple of 4
- `_is_block_header(line)` - Check if line starts a block structure (if, while, for, def, switch, defer, try, etc.)
- `_split_statements(line)` - Split line by `|` and `;` at top level only (respects parentheses, brackets, strings)
- `_find_block_range(lines, start_idx, base_indent)` - Find range of indented block after header
  - Returns: `(block_start_idx, next_idx_after_block)` or `(-1, -1)` if no block
  - Raises S011 if expected indented block not found

---

### 2.2 `expr.py` - Expression Parser

**Purpose**: Recursive descent parser with precedence climbing for expressions. Avoids left-recursion using iterative loops.

**Main Function**:

- `parse_expression_to_ast(tokens)` - Parse expression tokens into AST
  - Uses recursive descent with precedence climbing
  - Tracks position with mutable list for closure access
  - Tracks semicolon state for function termination

**Precedence Levels (lowest to highest)**:

1. `parse_comma()` - Comma/concatenation (lowest)
2. `parse_inline_if()` - Inline if: `if cond: true_expr { elif cond: expr } else: false_expr`
3. `parse_or()` - Logical OR
4. `parse_and()` - Logical AND
5. `parse_not()` - Logical NOT (unary)
6. `parse_comparison()` - Comparison operators
7. `parse_add()` - Addition/subtraction
8. `parse_mul()` - Multiplication/division
9. `parse_power()` - Exponentiation (right-associative)
10. `parse_unary()` - Unary operators and custom prefix operators
11. `parse_primary()` - Primary expressions (literals, identifiers, parentheses, arrays)

**Key Parsing Functions**:

- `consume(expected_type, expected_value=None)` - Consume token or raise syntax error
  - Uses specific error codes: S002 for identifier, S005 for colon, S015 for brackets
- `is_expr_start(tok)` - Check if token can start an expression
- `is_arg_start(tok)` - Check if token can start function call argument (more restrictive)
- `dotted_name_to_ast(name, line, col)` - Convert dotted name to AttrNode chain

**Postfix Chain Parsing**:

- `parse_postfix_chain(base_node, nested_depth=0)` - Parse postfix operators with uniform precedence
  - Handles: DOT (attribute access), CALL (function call), INDEX/Slice, POSTFIX operators
  - Space-call syntax: `callee arg1, arg2` (with optional `;` terminator)
  - Custom postfix operators

**Special Cases**:

- Lambda: `fn arg: expr` - Parses parameter and body expression
- Input keyword: `input "prompt"` - Parses as function call
- Type keyword: `type value` - Parses as function call
- Custom prefix operators - Handled in `parse_unary()`
- Custom postfix/operators - Handled in `parse_postfix_on_node()` and `parse_postfix_chain()`

**Error Handling**:

- Raises S001 for expected expression
- Raises S002 for expected identifier
- Raises S003 for expected expression after operator
- Raises S004 for expected name after '.'
- Raises S005 for missing ':'
- Raises S015 for missing closing bracket
- Raises S018 for extra closing bracket
- Raises S006 for unexpected token at end

---

### 2.3 `stmt.py` - Statement Parser

**Purpose**: Parse statements, control structures, and blocks with indentation-based syntax.

**Main Function**:

- `parse_statement(line, line_num=1)` - Parse single line into statement AST node
  - Returns None for empty/comment lines
  - Handles all statement types
  - Raises S008 for unknown/unimplemented keywords as standalone statements

**Statement Types Parsed**:

1. **Comments** - Single-line (`#`) and block (`###...###`)
2. **Control Flow** - `break`, `continue`, `pass`
3. **Delete Statement** - `del identifier` (validates identifier format)
4. **Help Statement** - `help` or `help topic` (or `expr /help`)
5. **From Import** - `from module import name1, name2`
   - With module alias: `from module as alias import name1, name2`
   - With function aliases: `from module import name1 as alias1`
   - Validates aliases are not reserved keywords (S041)
6. **Import Statement** - `import module` or `import module as alias`
7. **Assignment** - `var = value` or `var op= value`
   - Supports compound assignment: `+=`, `-=`, `*=`, `/=`, `//=`, `%=`, `**=`
   - Supports type constraints: `var: type = value`
   - Supports const: `const var = value`
8. **Increment/Decrement** - `var++` or `var--`
9. **Function Definition** - `def name(param1, param2):`
10. **Custom Operator Definition** - `def infixl prec symbol param1, param2: body`
11. **Switch Statement** - `switch value:` with `case value:` and `default:` blocks
12. **Try/Catch/Finally** - `try:`, `catch (error):`, `finally:` blocks
13. **Defer Statement** - `defer statement` or `defer: block`
14. **Control Structures** - `if/elif/else:`, `while:`, `for:`, `repeat:`, `forever:`
15. **Output Statements** - `say expr`, `input "prompt"`, `debug var`, `error "message"`
16. **Return Statement** - `return` or `return value`
17. **Expression Statements** - Function calls, expressions

**Block Parsing**:

- `parse_program(lines, line_num_offset=0)` - Parse entire program into list of statements
  - Handles indentation-based block structure
  - Uses `_find_block_range()` to determine block boundaries
  - Creates BlockNode for indented statements
  - Recursively parses nested blocks

**Key Features**:

- Validates identifiers are not reserved keywords (S041)
- Validates assignment targets are valid l-values
- Handles type constraints and const declarations
- Supports custom operator definitions with precedence
- Handles complex import syntax with aliases

---

## 3. Standard Library (`stdlib/`)

### 3.1 Module Overview

The standard library provides Python-callable functions wrapped in Bicala's `Module` class for fast direct execution.

**Available Modules**:

| Module | Purpose | Key Functions |
|--------|---------|---------------|
| `math.py` | Mathematical operations | sqrt, pow, sin, cos, tan, log, exp, floor, ceil, round, gcd, lcm, factorial, etc. |
| `str.py` | String manipulation | upper, lower, strip, split, join, replace, find, count, startswith, endswith, length, etc. |
| `array.py` (alias `arr`) | Array operations | len, first, last, push, pop, insert, remove, concat, reverse, sort |
| `time.py` | Time functions | sleep, ctime, perf_counter, strftime, strptime, local/GMT time getters |

**Module Interface**:

All modules are instances of the `Module` class from `env.py`:
```python
MathModule = Module('math', {
    'pi': _math.pi,
    'sqrt': _math.sqrt,
    # ... more functions
})
```

**Usage in Bicala**:
```bica
import math
math.sqrt 16  # Returns 4.0

import str
str.upper "hello"  # Returns "HELLO"
```

---

## 4. Entry Points & Tooling

### 4.1 `run.py` - CLI Entry Point

**Purpose**: Main entry point for executing Bicala programs from command line.

**Key Functions**:

- `run_file_ast(filename)` - Run Bicala source file using AST interpreter
  - Sets source directory for .bica imports
  - Reads file lines
  - Parses program via `parse_program()`
  - Executes via `execute_program()`
  - Formats errors with source context

- `run_code_text_ast(code_text, source_path=None)` - Run Bicala code string
  - Similar to `run_file_ast()` but accepts string input
  - Useful for REPL or code evaluation

- `eval_expression(expr_text)` - Evaluate single expression (for REPL/testing)
  - Parses expression via `parse_expression()`
  - Evaluates in fresh environment
  - Returns computed value

- `_main()` - CLI entry point
  - Usage: `python run.py <file.bica>`
  - Usage: `python run.py -c "code"`

**Error Handling**:

- Catches `BicalaError` and formats with source context
- Catches generic exceptions and wraps as R000 (internal runtime error)
- Forces UTF-8 output for Windows compatibility

**Path Configuration**:

- Adds `main/` directory to `sys.path` for imports without `__init__.py`
- Zero-architecture: No `__init__.py` files in the codebase

---

### 4.2 `bicaide.py` - Integrated Development Environment

**Purpose**: Tkinter-based IDE with syntax highlighting, real-time execution, and debugging capabilities.

**Architecture**:

- Imports Bicala core via `importlib.util` to avoid circular dependencies
- Thread-safe input handling using queues (`input_request_queue`, `input_response_queue`)
- Status state management with queue-based updates
- Syntax highlighting using Bicala keywords from `tok.py`

**Key Components**:

- `get_latest_version()` - Parses `docs/change.log` to find latest version string
- `launch_ide(initial_file=None, auto_run=False)` - Main IDE initialization
  - Creates Tkinter window (1000x680)
  - Manages current file and project root paths
  - Sets up thread-safe input handling
  - Initializes status state management

**GUI Features**:

- Syntax highlighting for Bicala keywords
- Real-time code execution via `run_code_text_ast()`
- GUI input callback integration via `set_gui_input_callback()`
- Error formatting with source context
- File operations (open, save, new)
- Version display from change.log

**Fallback Mode**:

If Bicala core fails to load, IDE falls back to pure Python execution:
```python
def run_code_text(code):
    glb = {"__name__": "__main__"}
    exec(compile(code, "<editor>", "exec"), glb, glb)
```

**Thread Safety**:

- Input requests queued from execution thread
- GUI thread processes input dialogs
- Responses returned via response queue
- Status updates queued for thread-safe UI updates

---

## 5. Execution Pipeline Summary

```
Source Code (.bica)
    ↓
[run.py] or [bicaide.py]
    ↓
Tokenizer (lex.py::tokenize)
    ↓
Token Stream
    ↓
Parser Package (pars/)
    ├── base.py (helpers: indent, block detection)
    ├── expr.py (expression parsing with precedence climbing)
    └── stmt.py (statement parsing with block structure)
    ↓
Abstract Syntax Tree (ast.py nodes)
    ↓
Semantic Layer (sem.py)
    ├── Name resolution (resolve_name)
    ├── Type validation (require_boolean, validate_type_assignment)
    ├── Callable validation (validate_callable, validate_function_arity)
    └── Const validation (validate_const_assignment)
    ↓
Evaluator (eval.py)
    ├── Expression evaluation (evaluate_expression)
    ├── Statement execution (execute_statement)
    ├── Control flow signals (BreakSignal, ContinueSignal, ReturnSignal)
    └── Environment interaction (env.py)
    ↓
Environment (env.py)
    ├── Scope management (parent/child chain)
    ├── Variable storage (vars, functions)
    ├── Const enforcement (const_vars)
    ├── Type constraints (typed_vars)
    ├── Defer stack (defer_stack)
    └── Module registry (BUILTIN_MODULES, MODULE_REGISTRY)
    ↓
Runtime Output
```

---

## 6. Key Design Patterns

### 6.1 Zero Architecture

- No `__init__.py` files in any directory
- `sys.path` manipulation in entry points to enable imports
- Flat module structure: `from main.ast import ...`

### 6.2 Dynamic Syntax System

- Keywords and operators configurable via `SYNTAX` dictionary in `tok.py`
- `refresh_syntax()` rebuilds derived sets after mutations
- Custom operators registerable at runtime with custom precedence

### 6.3 Centralized Error Architecture

- Single ERRORS database in `err.py`
- Error codes auto-map to severity levels
- Rich formatting with source context and pointers
- Hierarchical error class hierarchy for type-specific handling

### 6.4 Isolated Semantic Layer

- `sem.py` performs validation before evaluation
- No circular dependencies (no eval, no parser imports)
- Separates name resolution, type checking, and value validation

### 6.5 Precedence Climbing Parser

- `expr.py` uses iterative loops to avoid left-recursion
- Each precedence level has dedicated parse function
- Custom operators integrate into precedence system

### 6.6 Scope Chain Environment

- Parent-child environment hierarchy in `env.py`
- Name resolution walks scope chain from local to global
- Constants and type constraints tracked per scope
- Defer statements use LIFO stack for cleanup

---

## 7. Error Code Reference

| Category | Range | Code | Description |
|----------|-------|------|-------------|
| Lexer | L001-L099 | L001 | Unterminated string |
| Lexer | L001-L099 | L002 | Invalid character |
| Lexer | L001-L099 | L003 | Invalid escape sequence |
| Lexer | L001-L099 | L004 | Unterminated string literal (newline) |
| Lexer | L001-L099 | L005 | Invalid number literal |
| Lexer | L001-L099 | L006 | Unterminated block comment |
| Lexer | L001-L099 | L007 | Unterminated interpolation |
| Lexer | L001-L099 | L008 | Empty interpolation |
| Syntax | S001-S099 | S001 | Expected expression |
| Syntax | S001-S099 | S002 | Expected name/identifier |
| Syntax | S001-S099 | S003 | Expected expression after operator |
| Syntax | S001-S099 | S004 | Expected name after '.' |
| Syntax | S001-S099 | S005 | Expected ':' |
| Syntax | S001-S099 | S006 | Expected end of input |
| Syntax | S001-S099 | S007 | Expected '{expected}' but got '{got}' |
| Syntax | S001-S099 | S008 | Unknown statement |
| Syntax | S001-S099 | S011 | Expected indented block |
| Syntax | S001-S099 | S014 | Indentation must be multiple of 4 |
| Syntax | S001-S099 | S015 | Missing closing bracket |
| Syntax | S001-S099 | S018 | Extra closing bracket |
| Syntax | S001-S099 | S041 | Cannot use reserved keyword as identifier |
| Indentation | I001-I099 | I001 | Inconsistent indentation |
| Indentation | I001-I099 | I002 | Expected indented block |
| Runtime | R001-R099 | R001 | Internal runtime error |
| Runtime | R001-R099 | R002 | break used outside loop |
| Runtime | R001-R099 | R003 | continue used outside loop |
| Runtime | R001-R099 | R004 | Division by zero |
| Runtime | R001-R099 | R005 | Modulo by zero |
| Runtime | R001-R099 | R006 | Invalid operation |
| Runtime | R001-R099 | R007 | Unknown runtime error (R000) |
| Type | T001-T099 | T001 | Type mismatch |
| Type | T001-T099 | T002 | Type mismatch (expected/actual) |
| Type | T001-T099 | T003 | Cannot convert types |
| Type | T001-T099 | T004 | Value not callable |
| Type | T001-T099 | T005 | Missing function arguments |
| Type | T001-T099 | T006 | Extra function arguments |
| Value | V001-V099 | V001 | Invalid value |
| Value | V001-V099 | V002 | Value out of range |
| Value | V001-V099 | V003 | Invalid index |
| Value | V001-V099 | V007 | Operator precedence out of range (0-1000) |
| Name | N001-N099 | N001 | Name not defined |
| Name | N001-N099 | N002 | Cannot reassign constant |
| Name | N001-N099 | N003 | Cannot delete protected name |
| Name | N001-N099 | N004 | Name not defined in interpolation |
| Name | N001-N099 | N005 | Function not defined |
| Name | N001-N099 | N006 | Attribute not found |
| Name | N001-N099 | N007 | Name collision in scope |
| Import | M001-M099 | M001 | Module not found |
| Import | M001-M099 | M002 | Circular import detected |
| Import | M001-M099 | M003 | Duplicate alias in scope |
| Import | M001-M099 | M004 | Attribute not found in module |

---

## 8. Version Information

**Current Version**: Beta 5.1.24.3

**Key Features in Beta 5.1.24.3**:
- Del statement protection (N003 error for protected builtins/keywords)
- Dynamic syntax system with keyword remapping
- Custom operator registration with precedence control
- Three-tier equality (.=, ==, ===)
- String interpolation with `{variable}` syntax
- Indentation-based block structure
- Comprehensive error system with 44+ error codes
- Semantic analysis layer for type and name checking
- Standard library modules (math, str, array, time)
- IDE integration with syntax highlighting

---

*This specification documents the internal architecture of Bicala Beta 5.1.24.3 as of the final frozen state of the project.*
