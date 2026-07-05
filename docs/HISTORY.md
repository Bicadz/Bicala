# Bicala Language Evolution Chronicle

This document chronicles the historical evolution of the Bicala programming language from its origins as MiniLang through the Bimila and Bimuila eras to its current state as Bicala.

---

## The MiniLang Origin

**April 26, 2026** - Initial Prototype

The language began as a minimal experimental prototype with only a few lines of Python code. This era represented the foundational experimentation phase before the language had a true interpreter or formal structure.

- **Architecture**: Direct code execution without a dedicated interpreter runtime
- **Execution Model**: Code written directly without `run()` function abstraction
- **Primitive Commands**: Basic operations limited to `set`, `add`, and `print`
- **Design Philosophy**: Proof-of-concept for language parsing concepts

---

## The 40 Era - Bimila

**April 26-27, 2026** - The Interpreter Emergence

The "40 Era" marked the transition from experimental prototype to structured interpreter. The name "Bimila" derived from "BIca MIni LAnguage." During this period, the language evolved through rapid iteration from v0.1 to v0.4.

### Bimila v0.1
- **Interpreter Architecture**: Separation of interpreter logic from direct execution
- **Function Abstraction**: Introduction of `run()` function for program execution
- **Input Method**: Programs passed via Python list data structures

### Bimila v0.2
#### Bimila v0.2.0
- **File System Integration**: Introduction of `.bml` file extension for source code storage
- **Program Persistence**: Programs could be saved and loaded from dedicated files
- **Control Flow Primitives**: Addition of `if` conditional and `loop` iteration constructs
- **Language Independence**: Bimila emerged as a standalone programming language

#### Bimila v0.2.1
- **Command Line Interface**: Implementation of CLI for terminal-based execution
- **Entry Point Architecture**: Integration with `sys.argv` for command-line argument handling
- **Debugging Infrastructure**: Addition of `debug` command for memory state inspection
- **Direct Execution**: Support for running `.bml` files directly from terminal

### Bimila v0.3
#### Bimila v0.3.0
- **Function-Style Syntax**: Transition to function-based syntax paradigm
- **Expression Evaluation**: `print x` evolved to `print(x)` syntax
- **Regex-Based Parsing**: Implementation of regular expression-based command analysis
- **Modern Syntax Foundation**: Establishment of groundwork for contemporary language syntax

#### Bimila v0.3.1
- **Single-Line Comments**: Implementation of `#` prefix for line comments

#### Bimila v0.3.2
- **Multi-Line Comments**: Introduction of block comment syntax `/* ... */`
- **JavaScript Inspiration**: Direct adoption of JavaScript-style comment delimiters

#### Bimila v0.3.3
- **Comment Syntax Refinement**: Replacement of `/* ... */` with `### ... ###`
- **Language Identity**: Elimination of borrowed syntax to establish unique language style

#### Bimila v0.3.4
- **Compound Assignment Operators**: Addition of `+=` operator for augmented assignment
- **Syntax Simplification**: Replacement of `add x y` with `x += y` notation

#### Bimila v0.3.5
- **Error Handling Infrastructure**: Implementation of basic error reporting system
- **Error Classification**: Introduction of Syntax Error and Unknown Command error types

#### Bimila v0.3.6
- **Error Reporting Enhancement**: Addition of line numbers to all error messages

#### Bimila v0.3.7
- **Operator Expansion**: Addition of `-=` compound assignment operator
- **Milestone Achievement**: Reached 100 lines of source code

#### Bimila v0.3.8
- **Assignment Syntax Modernization**: Introduction of `=` operator for variable assignment
- **Syntax Evolution**: Replacement of `set x 10` with `x = 10` notation

##### Bimila v0.3.8.1
- **Assignment Stabilization**: Hotfix for `=` operator implementation

#### Bimila v0.3.9
- **Expression System**: Addition of parenthesized expression support `()`
- **Runtime Evaluation**: Introduction of `eval_expr()` for dynamic computation

#### Bimila v0.3.10
- **Syntax Simplification**: Return to v0.3 philosophy for simplicity
- **Output Function Rename**: Replacement of `print(x)` with `log(x)`

##### Bimila v0.3.10.1
- **Function Hotfix**: Resolution of `log()` parsing issues

### Bimila v0.4
#### Bimila v0.4.0
- **Control Flow Foundation**: Implementation of `if`/`else` conditional statements
- **Multi-Line Parsing**: Parser transition from single-line to multi-line processing
- **Flow Interpreter**: Evolution from line-by-line interpreter to flow-based execution

##### Bimila v0.4.0.1
- **Control Flow Hotfix**: Resolution of if/else execution issues

> **Historical Transition Phase: The Missing Link (April 27, 2026)**
>
> Following the 40 Era, the language underwent a significant transformation period marking the evolution from Bimila to Bimuila. This transitional phase introduced the `.bica` file extension paradigm and comprehensive syntax overhauls:
>
> - **Language Rebranding**: Official rename from Bimila to Bimuila
> - **System Integration**: Creation of `.reg` file for PATH registration
> - **IDE Development**: Commencement of integrated development environment
> - **File Extension Change**: Decision to change from `.bml` to `.bica` (BImuila Code Archive)
> - **Assignment Syntax Overhaul**: Replacement of `=` with `:` for assignment operations
> - **Compound Operators**: Addition of comprehensive compound assignment operators (`+:`, `-:`, `*:`, `/:`, `//:`, `%:`, `**:`)
> - **Increment/Decrement**: Implementation of `++` and `--` operators
> - **Output Syntax**: Transition of `say` to new syntax `say <expr>`
> - **Input Operations**: Addition of `input` with return value syntax
> - **Loop Enhancement**: Addition of `for` loop with range iteration
> - **Comparison System**: Implementation of three-tier comparison system (`=`, `==`, `===`)
> - **Logical Operators**: Addition of `and`, `or`, `not`, `in` logical operations

---

## The Beta Era

### Beta 2
**Late April - Early May 2026** - Function Definition Era

- **Function Definitions**: Introduction of `def` keyword for function declaration
- **Function Invocation**: Implementation of `name()` syntax for function calls
- **IDE Enhancements**: Syntax highlighting, indentation guides, auto-indentation, status bar

### The Missing Link: Transition from Beta 2 to Beta 3 (Historical Recovery)
**Transition Phase** - Architectural Decision Point

This period represents the critical architectural turning point where Bicala transitioned from an eval-based execution model to a full AST compilation pipeline.

- **Historical Decision**: Selection of full AST architecture over eval-based evaluation
- **Compiler Architecture**: Implementation of tokenizer → parser → AST → AST execution pipeline
- **AST Node Separation**: Expression nodes and Statement nodes separation
- **Expression Parser**: Implementation of precedence climbing algorithm
- **File Evolution**: `Bimuila-0305,21.py` (2947 lines) - Complete AST implementation
- **IDE Separation**: Extraction of IDE into separate file `Bimuide-0305,22.py`

### Beta 3
**May 8, 2026** - Comprehensive Enhancement

- **Error System Overhaul**: Implementation of comprehensive error reporting system
- **Math Module**: Implementation of mathematical functions (`abs`, `min`, `max`, `round`, `floor`, `ceil`)
- **String Module**: Implementation of string manipulation functions (`len`, `upper`, `lower`, `slice`, `find`)
- **Array Module**: Addition of array data structure and operations
- **Type Conversion**: Implementation of type conversion functions (`str()`, `int()`, `float()`, `bool()`, `type()`)
- **Package Architecture**: Refactoring into package structure `bimuila_main/`

### Beta 4
**Early June 2026** - Syntax Evolution

#### Beta 4.0
- **Semicolon Introduction**: Addition of `;` as function terminator and statement separator
- **Implementation Rules**: Optional at top-level, mandatory for nested functions, statement separator

#### Beta 4.1
- **Separator Specialization**: Separation of `;` (function terminator) from `|` (statement separator)

#### Beta 4.2
- **Import System Enhancement**: Implementation of multiple import syntax variants

### Beta 5
**Early June 2026** - Error System Revolution

#### Beta 5.0
Comprehensive error code system establishment with Lexer (Lxxx), Parser (Sxxx), Name (Nxxx), Type (Txxx), Runtime (Rxxx), Import (Mxxx), and Value (Vxxx) error categories.

#### Beta 5.1
##### Beta 5.1.0
- **AST Node System Enhancement**: Addition of `dump_tree()` method for recursive AST display
- **Type Checking Standardization**: Type validation on all primitive nodes

##### Beta 5.1.1
- **EBNF Grammar Corrections**: Removal of duplicate definitions, TernaryExpr hierarchy fix, PostfixExpr left recursion fix

##### Beta 5.1.2
###### Beta 5.1.2.0
- **Syntax Configuration System**: Creation of syntax_config.py for centralized syntax management

###### Beta 5.1.2.1
- **Punctuation Refactoring**: Function-based naming (GROUP_START, CALL_END, etc.)

###### Beta 5.1.2.2
- **Configuration Bug Fix**: Resolution of config.assignment_operators list/dictionary conflict

##### Beta 5.1.3
###### Beta 5.1.3.0
- **Custom Operators Implementation**: User-defined infix and prefix operators with custom symbols

###### Beta 5.1.3.1
- **Declaration and Assignment System**: Unified 'def' for all definitions, '=' assignment syntax

###### Beta 5.1.3.1a
- **Assignment Syntax Standardization**: Removal of legacy ':' assignment syntax

###### Beta 5.1.3.1b
- **File Renaming**: ast_nodes.py → ast.py, syntax_config → cfg.py, etc.

###### Beta 5.1.3.1c
- **Dynamic Syntax and File Optimization**: Complete cfg.py removal, SYNTAX dictionary in tok.py

##### Beta 5.1.4
###### Beta 5.1.4.0
- **Dynamic Lexing and Multi-Statement Support**: Multi-statement syntax with ';' separator

###### Beta 5.1.4.1
- **Parser Refactoring**: Monolithic pars.py split into modular package (base.py, expr.py, stmt.py)

###### Beta 5.1.4.2
- **Dynamic Operator System**: OPERATOR dictionary transition from static to dynamic

###### Beta 5.1.4.2a
- **Official Language Rename to Bicala**: Bicala = BICA LAnguage (June 14, 2026)

###### Beta 5.1.4.2b
- **Custom Operator Definition Support**: INFIX, INFIX_L, INFIX_R integration

###### Beta 5.1.4.2c
- **tok.py Refactoring**: Dynamic group-based dictionaries

###### Beta 5.1.4.2d
- **EBNF Grammar Update**: Custom operator alignment

###### Beta 5.1.4.2e
- **Parser Logic Sync**: Strict constraint enforcement

##### Beta 5.1.4.3
- **Switch Statement Implementation**: Indentation-based switch with default support

##### Beta 5.1.4.4
- **Precedence System Refactoring**: OPERATOR_PRECEDENCE expansion to 0-1000 scale

##### Beta 5.1.5
###### Beta 5.1.5.0
- **Array Iteration Support**: For loop array iteration capability

###### Beta 5.1.5.1
- **BicaIDE UI Bug Fixes**: Output console copy, workspace paste duplication fixes

###### Beta 5.1.5.2
- **Switch Default Indentation Rule Fix**: Default at same level as switch

###### Beta 5.1.5.2a
- **Switch Error Code Reassignment**: Sequential S039-S042 compliance

###### Beta 5.1.5.3
- **Built-in Error Function Resurrection**: error() function implementation

##### Beta 5.1.6
###### Beta 5.1.6.0
- **Lambda Expression Implementation**: fn arg: expr syntax

###### Beta 5.1.6.1
- **Built-in Type Function Legalization**: type() as official built-in

###### Beta 5.1.6.1a
- **Bug Fixes**: LambdaNode import, evaluate function reference fixes

##### Beta 5.1.7
###### Beta 5.1.7.0
- **R001 Removal and None/NaN Literal Implementation**: Division by zero returns NaN, none/nan literals

##### Beta 5.1.8
###### Beta 5.1.8.0
- **Inline If Expression Implementation**: if cond: true_expr else: false_expr

###### Beta 5.1.8.1
- **N-ary Inline If Expression**: elif support for multiple branches

##### Beta 5.1.9
###### Beta 5.1.9.0
- **Scope Security and Identifier Management**: Name collision checks, del statement

##### Beta 5.1.10
###### Beta 5.1.10.0
- **Custom Prefix and Postfix Operators**: def prefix/postfix syntax

###### Beta 5.1.10a
- **Bug Fixes**: Extended assignment operators, for loop scope

###### Beta 5.1.10b
- **Legacy Assignment Syntax Elimination**: Complete removal of +:, -:,: operators

###### Beta 5.1.10c
- **Imports Directory Rename**: imports → stdlib

##### Beta 5.1.11
###### Beta 5.1.11.0
- **Time Module Addition**: Complete time operation functions

##### Beta 5.1.12
###### Beta 5.1.12.0
- **BicaIDE Status Bar Improvement**: Automatic version detection, real-time updates

##### Beta 5.1.13
###### Beta 5.1.13.0
- **Flexible Colon Requirements**: Inline mandatory, multi-line optional

###### Beta 5.1.13.1
- **Infinite Loop Fix**: Single-line parsing correction

##### Beta 5.1.14
###### Beta 5.1.14.0
- **Deprecated Ternary Syntax Removal**: Complete ? : syntax removal
- **Inline Syntax Consistency**: All control flow statements support inline

##### Beta 5.1.15
###### Beta 5.1.15.0
- **String Interpolation**: {} syntax with escape character support

##### Beta 5.1.16
###### Beta 5.1.16.0
- **Defer Mechanism**: Go-style deferred execution

##### Beta 5.1.17
###### Beta 5.1.17.0
- **Centralized Error Architecture**: BicalaError architecture refactoring

###### Beta 5.1.17.1
- **Bug Fixes**: BicalaRuntimeError, AssignNode target fixes

###### Beta 5.1.17.2
- **Bug Fixes & Keyword Support**: pass keyword, N004 scope leak fix

###### Beta 5.1.17.3
- **Optional Parentheses for Zero-Argument Function Calls**: Allowing functions with no arguments to be invoked without empty parentheses, similar to Ruby/Kotlin style

###### Beta 5.1.17.4
- **For-Loop Range Colon Conflict Fix**: Token-based lookahead, loop variable binding

##### Beta 5.1.18
###### Beta 5.1.18.0
- **Comprehensive Test Suite Generation**: 100% syntax specification coverage
- **Compiler Excavation & Refactor**: Repeat/forever loop restoration

##### Beta 5.1.19
###### Beta 5.1.19.0
- **Core Exception Handling**: try/catch/finally implementation

###### Beta 5.1.19.1
- **Error Code Sequencing**: S043/S044 correction

##### Beta 5.1.20
###### Beta 5.1.20.0
- **Syntax Specification Overhaul**: Primitive types, operator precedence, greedy parsing documentation

###### Beta 5.1.20.1
- **ImportError Regression Fix**: __init__.py restoration

###### Beta 5.1.20.2
- **Package Cleanup**: Direct script architecture, zero package overhead

###### Beta 5.1.20.3
- **Zero __init__.py Architecture**: Clean namespace layout

##### Beta 5.1.21
###### Beta 5.1.21.0
- **For Loop Range Separator Change**: Colon to comma for range syntax

##### Beta 5.1.22
###### Beta 5.1.22.0
- **Syntax Specification Improvements**: Identity description, logical operators, reserved keywords

###### Beta 5.1.22.1
- **BicaIDE Regression Fix**: Zero __init__.py compatibility

##### Beta 5.1.23
###### Beta 5.1.23.0
- **Semantic Layer Extraction**: main/sem.py creation for semantic analysis isolation
- **Omni-Error Architecture**: Strict continuous indexing, no gaps in error codes
- **IDE Launch Enhancement**: pathlib-based path resolution

###### Beta 5.1.23.1
- **Keyword Protection & Parser Stability**: S041 keyword guard, del crash prevention

##### Beta 5.1.24
###### Beta 5.1.24.0 - Immutable Constants (`const`) & Type-Constrained Variables
- **Architecture Documentation**:
  - Comprehensive `docs/spec.md` with semantic rules for const and type-constrained variables
  - Error codes N002 and T002 documentation with examples
  - AST node extensions documentation
  - Implementation guidelines and validation flow diagram
  - Type system with supported types and matching rules
- **Error Code Updates**:
  - Repurposed N002 from "Name already defined" to "Cannot reassign a constant variable"
  - Repurposed T002 from "Unsupported operand type" to "Type mismatch"
- **Syntax Extensions**:
  - Addition of CONST keyword to _DECLARATIONS group
  - Const declaration parsing: `const <identifier> = <expression>`
  - Type-constrained variable parsing: `<type> <identifier> = <expression>`
  - Combined const + type parsing: `const <type> <identifier> = <expression>`
  - Supported types: int, string, bool, float, array
- **AST & Environment Layers**:
  - **AST Extensions**:
    - AssignNode update with `is_const` flag for immutable constants
    - AssignNode update with `declared_type` for type-constrained variables
    - Parameter additions to __init__ method with default values
    - __repr__ and __slots__ updates for new attributes
  - **Environment Extensions**:
    - const_vars set addition for constant variable tracking across scopes
    - typed_vars dictionary addition for declared type tracking
    - is_const(), get_declared_type(), mark_const(), mark_typed() methods
- **Semantic Analysis & Evaluation**:
  - **Semantic Analysis Layer**:
    - validate_const_assignment() function for N002 error
    - validate_type_assignment() function for T002 error
    - get_type_string() function for type determination
    - Type mapping for consistent type name handling
  - **Evaluator Integration**:
    - Const validation in AssignNode handling
    - Type validation in AssignNode handling
    - Const validation in CompoundAssignNode handling
    - Const validation in IncDecNode handling
    - Const and typed variable marking in environment

###### Beta 5.1.24.1
- **Greedy Parsing & Loop Edge-Cases**: Hardened the indentation-based parsing layer and resolved syntax boundary issues within greedy space-separated function calls (`callee arg1, arg2`).
- **Parser Stability**: Refined dynamic token registration logic to prevent potential parser deadlocks during token streaming.

###### Beta 5.1.24.2
- **Centralized Diagnostic Alignment**: Conducted a final alignment of the 44+ error codes database inside `main/err.py`.
- **Position Tracking Accuracy**: Enhanced the lexer and parser diagnostic engines to ensure precise line and column error pointers (`^`) for complex inline components, multi-line block comments, and string interpolation.

###### Beta 5.1.24.3
- **System Integrity & Protected Core Names (Final Frozen State)**: Implemented a robust scope protection architecture to prevent system corruption.
- **Del Statement Enforcement**: Introduced the `N003: Cannot delete protected name` error rule to explicitly block the `del` statement from deleting core language keywords, boolean/null constants (`true`, `false`, `none`, `nan`), or registered built-in functions.
- **Project Conclusion**: Permanently frozen as a completed educational monument.

###### Beta 5.1.24.4
- **Runtime R000 Error Fix**: Resolved critical runtime error caused by module naming conflict with Python's built-in `ast` module.
- **Module Renaming**: Renamed `main/ast.py` to `main/bicala_ast.py` to avoid import conflicts with Python's standard library.
- **Import Updates**: Updated all imports across the codebase (`main/pars/base.py`, `main/pars/stmt.py`, `main/eval.py`) to use the new module name.
- **Comprehensive Test Suite**: Created automated test suite for core protection validation:
  - `tests/test_success.bica`: Positive path validation for const and type constraints
  - `tests/test_err_n002.bica`: N002 error validation for const reassignment
  - `tests/test_err_t002.bica`: T002 error validation for type mismatch
  - `tests/test_err_n003_keyword.bica`: N003 error validation for protected constant deletion
  - `tests/test_err_n003_builtin.bica`: N003 error validation for protected builtin deletion
  - `tests/run_tests.py`: Automated Python test runner with subprocess execution and colored output
- **Test Results**: 5/5 tests PASSED (100%) - all core protections verified as active and functional

###### Beta 5.1.24.5
- **Regression Fix: Code Duplication & Import Restoration**: Resolved regressions introduced after Beta 5.1.24.4.
- **Code Duplication Removal**: Fixed massive code duplication (~730 lines) in `main/pars/stmt.py` that caused syntax errors and continue/break statements outside loop errors.
- **Import Restoration**: Restored all Beta 5.1.24.4 fixes that were reverted:
  - `main/eval.py`: Restored `from bicala_ast import` and `KEYWORDS, BUILTINS` imports
  - `main/pars/base.py`: Changed from relative imports (`from ..tok`, `from ..ast`) to direct imports (`from tok`, `from bicala_ast`)
  - `main/pars/stmt.py`: Restored `from bicala_ast import DeferNode, TryCatchNode`
  - `main/eval.py`: Re-inserted N003 protection check in DelNode handler to prevent deletion of keywords and built-ins
- **Zero __init__.py Architecture**: Maintained direct import architecture without package initialization files
- **Test Verification**: 5/5 core protection tests PASSED (100%) - all protections verified active

---

## Version Summary

The Bicala language has evolved through distinct eras:

1. **MiniLang Origin** (April 26, 2026) - Experimental prototype
2. **40 Era - Bimila** (April 26-27, 2026) - Interpreter emergence (v0.1-v0.4) with historical transition to Bimuila
3. **Beta Era** (Late April 2026 - June 19, 2026) - Comprehensive enhancement
   - Beta 2: Function definition
   - Transition to Beta 3: AST architecture decision point
   - Beta 3: Module system
   - Beta 4: Syntax evolution
   - Beta 5: Comprehensive error system and language features (Beta 5.0 - Beta 5.1.24.3)

**Official Rename**: Bimuila → Bicala at Beta 5.1.4.2a (June 14, 2026)

**Current Version**: Beta 5.1.24.5 (July 5, 2026) - Regression Fix

---

*This chronicle documents the complete evolution from MiniLang prototype to the modern Bicala programming language with its comprehensive error system, semantic analysis layer, and advanced language features.*
