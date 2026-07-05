# The Bicala Programming Language (Beta 5.1.24.4)

*An indentation-based dynamic programming language with custom dynamic syntax definitions, implemented in Python.*

> **Repository Status**: This repository is now officially frozen and archived as a permanent educational monument and learning milestone in language design and compiler architecture.

---

## Project Chronicle

Bicala was a two-month intensive journey into compiler design, spanning from initial conception to a stable Beta 5.1.24.3 release. The project has reached its end of development, not as a failure, but as a completed learning milestone.

This repository represents the final state of a language that evolved through multiple iterations—from MiniLang to Bimila, and finally to Bicala—culminating in a functional compiler with advanced features including dynamic syntax, custom operators, type constraints, and comprehensive error handling.

---

## Lessons Learned

### What Happened

The core architecture grew beyond its original scope. The dynamic syntax definitions, while innovative, introduced unexpected complexity that made the codebase increasingly difficult to maintain. The feature set expanded to include three tiers of equality, Go-style defer statements, exception handling, and a complete semantic analysis layer—all of which contributed to a sophisticated but increasingly complex system.

### The Insight

The architecture served its purpose as a proof-of-concept, demonstrating that a dynamic, user-extensible language could be built with a relatively small codebase. However, it has reached its limit for long-term scalability. The trade-offs made for flexibility—particularly the dynamic syntax system and the greedy parsing model—created architectural debt that would require significant refactoring for continued evolution.

### Educational Value

This repository is preserved for others to study the practical implementation of compiler components:

- **Parser Design**: The recursive descent parser in `main/pars/` demonstrates how to handle complex grammars with precedence and associativity
- **AST Construction**: The node definitions in `main/ast.py` show how to represent language constructs as structured data
- **Semantic Analysis**: The isolated validation layer in `main/sem.py` illustrates the separation between parsing and type checking
- **Error Architecture**: The centralized error system in `main/err.py` provides a model for comprehensive diagnostic management
- **Dynamic Language Features**: The custom operator and syntax systems offer insights into user-extensible language design

These components serve as a foundation for understanding how modern compilers work, from tokenization through evaluation.

---

## Execution

Bicala programs use the `.bica` file extension. Execute a Bicala program using the Python entry point:

```bash
python run.py filename.bica

```

The integrated development environment provides syntax highlighting, real-time execution, and debugging capabilities:

```bash
python bicaide.py

```

---

## Compiler Architecture

### Execution Pipeline

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

### Diagnostic Architecture

Bicala implements a centralized error management system with strict continuous indexing:

* **Lxxx (Lexer)**: L001-L008 - Tokenization errors
* **Sxxx (Parser)**: S001-S068 - Syntax errors
* **Nxxx (Name)**: N001-N007 - Name resolution errors
* **Txxx (Type)**: T001-T006 - Type errors
* **Rxxx (Runtime)**: R001-R007 - Runtime exceptions
* **Mxxx (Import)**: M001-M004 - Module import errors
* **Vxxx (Value)**: V001-V007 - Value validation errors

All errors are dynamically generated through a centralized error engine in `main/err.py`.

---

## Documentation

* [📄 Syntax Specification](docs/bicala.syntax.spec.md) - Complete syntax guide with examples
* [📄 Semantic & Architecture Specification](docs/bicala.sematic.spec.md) - Type system and validation rules
* [📄 Structural Specification](docs/bicala.structure.spec.md) - Deep-dive internal architecture and file responsibilities
* [Error Code Reference](docs/error.doc) - Complete diagnostic lookup table
* [Formal Grammar](docs/Bicala.ebnf) - EBNF grammar specification
* [Historical Chronicle](docs/HISTORY.md) - Language evolution from MiniLang to Bicala
* [Change Log](docs/change.log) - Detailed development history (Vietnamese)
* [Documentation README](README.md) - Additional documentation resources

---

## Repository Structure

```
Bicala/
├── main/                    # Core compiler modules
│   ├── ast.py              # AST node definitions
│   ├── eval.py             # Runtime evaluator
│   ├── env.py              # Environment management
│   ├── err.py              # Centralized error architecture
│   ├── lex.py              # Lexer/tokenizer
│   ├── tok.py              # Token definitions & dynamic syntax
│   ├── sem.py              # Semantic analysis layer
│   ├── pars/               # Parser package
│   │   ├── base.py         # Parser core helpers
│   │   ├── expr.py         # Expression parser
│   │   └── stmt.py         # Statement parser
├── stdlib/                  # Standard library
│   ├── math.py             # Mathematical functions
│   ├── str.py              # String manipulation
│   ├── array.py            # Array operations
│   └── time.py             # Time functions
├── tests/                   # Test suite
│   ├── run_test_suite.py   # Automated test runner
│   └── *.bica              # Test files
├── docs/                    # Documentation
│   ├── HISTORY.md          # Evolution chronicle
│   ├── change.log          # Development log
│   ├── error.doc           # Error reference
│   ├── bicala.ebnf         # Grammar specification
│   ├── bicala.syntax.spec.md    # Syntax guide
│   ├── bicala.sematic.spec.md   # Semantic rules
│   └── bicala.structure.spec.md # Architectural & component structure
├── bicaide.py              # Built-in IDE
├── run.py                  # Main entry point
└── README.md               # This file

```

---

## Language Features (Beta 5.1.24.3)

* **Dynamic Syntax**: User-configurable keywords and operators
* **Custom Operators**: Define infix, prefix, postfix operators with custom precedence
* **Type Constraints**: Immutable constants and type-constrained variables
* **Advanced Control Flow**: Indentation-based switch, defer, try/catch/finally
* **Functional Programming**: Lambda expressions, higher-order functions
* **String Interpolation**: Python f-string style with `{variable}` syntax
* **Three-Tier Equality**: Loose (.=), strict (==), identity (===)
* **Greedy Parsing**: Space-separated function calls with semicolon closure
* **Comprehensive Error System**: 44+ error codes with centralized management
* **Semantic Analysis**: Isolated validation layer for type and name checking
* **Standard Library**: Math, string, array, and time modules
* **IDE Integration**: Built-in development environment

---

## Future Extensions (Project Archived - No Further Development)

### Potential Type System Enhancements *(Cancelled due to project archive)*

* Type inference for variables without explicit declarations
* Union types (e.g., `int|string`)
* Generic types
* Type aliases
* Interface/struct types

### Potential Const Enhancements *(Defunct - Frozen at Beta 5.1.24.3)*

* Const expressions (compile-time evaluation)
* Const propagation (optimization)
* Const correctness analysis

---

*This repository stands as a completed milestone in dynamic language design, demonstrating advanced compiler architecture, semantic analysis, and user-extensible syntax systems.*
