# Bicala Language Specification & Architecture

## Overview

This document defines the semantic rules, type system, and error codes for the Bicala programming language. It serves as the authoritative reference for language behavior and implementation guidelines.

## Version: Beta 5.1.24

---

## Semantic Rules

### Variable Declaration & Assignment

#### Standard Variable Assignment
Variables can be assigned using the `=` operator:
```bica
x = 5
name = "Bicala"
```

#### Immutable Constants (`const`)
- **Syntax:** `const <identifier> = <expression>`
- **Behavior:** Constants are immutable and cannot be reassigned after declaration
- **Scope:** Constants follow the same scope rules as regular variables
- **Examples:**
  ```bica
  const PI = 3.14159
  const MAX_SIZE = 100
  const APP_NAME = "Bicala"
  ```
- **Error:** Attempting to reassign a constant raises **N002: Cannot reassign a constant variable**

#### Type-Constrained Variables
- **Syntax:** `<type> <identifier> = <expression>`
- **Behavior:** Variables with explicit type declarations enforce type matching at assignment time
- **Supported Types:** `int`, `string`, `bool`, `float`, `array`
- **Examples:**
  ```bica
  int count = 5
  string name = "Bicala"
  bool flag = true
  float price = 19.99
  array items = [1, 2, 3]
  ```
- **Error:** Type mismatch between declared type and expression type raises **T002: Type mismatch**

#### Combined: Type-Constrained Constants
- **Syntax:** `const <type> <identifier> = <expression>`
- **Behavior:** Combines immutability with type constraints
- **Examples:**
  ```bica
  const int MAX_USERS = 1000
  const string VERSION = "1.0.0"
  const bool DEBUG_MODE = false
  ```
- **Errors:** Both N002 (reassignment) and T002 (type mismatch) apply

---

## Type System

### Supported Types

| Type | Description | Example Values | Type Matching Rules |
|------|-------------|----------------|---------------------|
| `int` | Integer numbers | `42`, `-10`, `0` | Exact match required |
| `float` | Floating-point numbers | `3.14`, `-0.5`, `2.0` | Exact match required |
| `string` | Text values | `"hello"`, `'world'` | Exact match required |
| `bool` | Boolean values | `true`, `false` | Exact match required |
| `array` | Arrays/lists | `[1, 2, 3]`, `["a", "b"]` | Exact match required |

### Type Matching Rules

1. **Exact Type Matching:** The expression type must exactly match the declared type
2. **No Implicit Conversion:** Bicala does not perform automatic type coercion
3. **Static Validation:** Type checking occurs at parse/semantic analysis time, not runtime
4. **Expression Evaluation:** The right-hand side expression is evaluated to determine its type

### Type Determination

- **Literals:** Type is determined by the literal syntax (e.g., `42` is `int`, `"text"` is `string`)
- **Variables:** Type is inherited from the variable's current value
- **Expressions:** Type is determined by the result of the expression evaluation
- **Function Calls:** Type is determined by the function's return value

---

## Error Codes

### Name Errors (N001-N099)

#### N001: Function is not defined
- **Category:** Name Error
- **Severity:** ERROR
- **Message:** "Function '{function_name}' is not defined"
- **Hint:** "Define the function before calling it"
- **Example:** `undefined_function()` → N001

#### N002: Cannot reassign a constant variable
- **Category:** Name Error  
- **Severity:** ERROR
- **Message:** "Cannot reassign constant variable '{variable_name}'"
- **Hint:** "Constants are immutable and cannot be reassigned"
- **Example:** 
  ```bica
  const PI = 3.14
  PI = 3.14159  # N002: Cannot reassign constant variable 'PI'
  ```

#### N004: Variable not defined
- **Category:** Name Error
- **Severity:** ERROR
- **Message:** "Variable '{variable_name}' is not defined"
- **Hint:** "Define the variable before using it"
- **Example:** `print(undefined_var)` → N004

#### N007: Name collision in scope
- **Category:** Name Error
- **Severity:** ERROR
- **Message:** "Name '{name}' already exists in current scope"
- **Hint:** "Use a different name to avoid collision"
- **Example:** Declaring the same variable twice in the same scope

### Type Errors (T001-T099)

#### T002: Type mismatch
- **Category:** Type Error
- **Severity:** ERROR
- **Message:** "Type mismatch: expected {expected_type}, got {actual_type}"
- **Hint:** "Ensure the expression type matches the declared type"
- **Example:**
  ```bica
  int count = "hello"  # T002: Type mismatch: expected int, got string
  string name = 123    # T002: Type mismatch: expected string, got int
  ```

#### T003: Expected number
- **Category:** Type Error
- **Severity:** ERROR
- **Message:** "Expected number"
- **Hint:** "Provide a numeric value"
- **Example:** Using a string where a number is required

#### T004: Value is not callable
- **Category:** Type Error
- **Severity:** ERROR
- **Message:** "Value is not callable"
- **Hint:** "Ensure the value is a function"
- **Example:** `5()` → T004

#### T005: Missing function arguments
- **Category:** Type Error
- **Severity:** ERROR
- **Message:** "Missing function arguments"
- **Hint:** "Provide all required function arguments"
- **Example:** Calling a function without required arguments

#### T006: Extra function arguments
- **Category:** Type Error
- **Severity:** ERROR
- **Message:** "Extra function arguments"
- **Hint:** "Remove extra function arguments"
- **Example:** Calling a function with too many arguments

---

## AST Node Extensions

### AssignNode Extensions

#### Additional Attributes
- `is_const: bool` - Flag indicating if the variable is a constant (immutable)
- `declared_type: str | None` - Explicit type declaration (e.g., "int", "string")

#### Usage
```python
# Standard assignment
AssignNode(VarNode("x", line, col), expr, line, col)

# Constant assignment
AssignNode(VarNode("PI", line, col), expr, line, col, is_const=True)

# Type-constrained assignment
AssignNode(VarNode("count", line, col), expr, line, col, declared_type="int")

# Combined: constant with type constraint
AssignNode(VarNode("MAX", line, col), expr, line, col, is_const=True, declared_type="int")
```

---

## Implementation Guidelines

### Parser Responsibilities (`main/pars/`)
1. **Syntax Recognition:** Identify `const` and type-constrained variable syntax
2. **AST Node Construction:** Create AssignNode with appropriate flags (`is_const`, `declared_type`)
3. **Error Reporting:** Report syntax errors (not semantic errors)

### Semantic Layer Responsibilities (`main/sem.py`)
1. **Const Validation:** Check for constant reassignment attempts (N002)
2. **Type Validation:** Perform static type checking for type-constrained variables (T002)
3. **Error Reporting:** Raise semantic errors with appropriate error codes

### Evaluator Responsibilities (`main/eval.py`)
1. **Runtime Execution:** Execute the program based on validated AST
2. **No Semantic Checks:** Do not perform const or type validation (delegated to sem.py)
3. **Runtime Errors Only:** Handle only runtime errors, not semantic violations

---

## Validation Flow

```
Source Code
    ↓
Parser (main/pars/)
    ↓
AST with semantic annotations
    ↓
Semantic Analysis (main/sem.py)
    ↓
Const Validation (N002)
    ↓
Type Validation (T002)
    ↓
Validated AST
    ↓
Evaluator (main/eval.py)
    ↓
Runtime Execution
```

---

## Future Extensions

### Potential Type System Enhancements
- Type inference for variables without explicit declarations
- Union types (e.g., `int|string`)
- Generic types
- Type aliases
- Interface/struct types

### Potential Const Enhancements
- Const expressions (compile-time evaluation)
- Const propagation (optimization)
- Const correctness analysis
