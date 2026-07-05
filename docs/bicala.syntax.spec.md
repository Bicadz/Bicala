# 📑 Bicala Language Syntax Specification (Beta 5.1.19)

Welcome to the official human-readable syntax guide for **Bicala**, a lightweight, highly expressive, indentation-based programming language.

---

### 1. Source Code Structure & Comments

Bicala source files use the `.bica` extension. The language utilizes an indentation-based layout (using 4 spaces or tabs) to define block scopes.

* **Line Comments:** Begin with a `#` symbol and extend to the end of the line.

```python
# This is a single-line comment in Bicala
```

* **Block Comments:** Enclosed within triple hashtags `###`.

```python
###
This is a multi-line block comment
spanning across multiple lines
###
```

---

### 2. Variables & Assignment Matrix

Variables in Bicala are dynamically typed and do not require formal type declarations. Assignment is explicitly driven by the single equals sign `=`, separating it from comparison semantics.

* **Standard Assignment:** 

```python
x = 10
name = "Bicala"
```

* **Compound Assignments:** Bicala natively supports compound mathematical mutations:

```python
x += 5    # Addition assignment (x = x + 5)
x -= 3    # Subtraction assignment
x *= 2    # Multiplication assignment
x /= 2    # Division assignment
x //= 2   # Floor Division assignment
x %= 3    # Modulo assignment
x **= 2   # Exponentiation assignment
```

* **Inline Mutators:** Fast variable increments and decrements.

```python
i++       # Increment i by 1 (i = i + 1)
i--       # Decrement i by 1
```

---

### 3. The Three Tiers of Equality

Bicala handles data comparisons using a unique three-tier evaluation system to guarantee precise logic control:

| Operator | Type | Semantic Behavior | Examples |
| --- | --- | --- | --- |
| **`.=`** | **Loose Equality** | Performs automatic type coercion and executes case-insensitive string matching. | `"a" .= "A"` → `True`<br>`5 .= 5.0` → `True`<br>`"5" .= 5` → `True` |
| **`==`** | **Strict Equality** | Requires exact value and data type matching. String evaluations are case-sensitive. | `"a" == "A"` → `False`<br>`"5" == 5` → `False`<br>`5 == 5.0` → `False` |
| **`===`** | **Identity Equality** | Uses Python's `is` operator to verify if both references resolve to the exact same object instance in memory. | `x === y` → `True` only if `x is y` in Python |

> ℹ️ **Inequality Operators:** Negative logical checks strictly follow the same tier structures: loose `!=`, strict `!==`, and identity `!===`. Standard relational operators include `<`, `>`, `<=`, and `>=`.

---

### 4. Advanced Control Flow & Loops

Bicala supports powerful loop constructs that drop mandatory condition parentheses for a clean, human-centric layout.

* **While Loops:** 

```python
while x > 0:
    x -= 1
```

* **The For-Loop Range Family:** Supports basic bounds, inclusive bounds, and step-skipping configurations.

```python
for i in 5:          # Iterates 5 times from 0 to 4
for i in 2:8:        # Iterates from 2 to 8 inclusive (2, 3, 4, 5, 6, 7, 8)
for i in 0:10:2:     # Iterates from 0 to 10 with a step increment of 2
```

* **Inline Block Fix (v5.1.17.4):** Single-line loops now resolve seamlessly without colon ambiguity:
```python
for i in 1:10: pass  # Token lookahead accurately resolves the range vs block
```

* **Utility Loops:** 

```python
repeat 3:
    say "Hello"

forever:
    say "Infinite"
```

---

### 5. Functions & The Semicolon `;` Terminator Rule

Functions are defined using the unified `def` keyword.

```python
def greet name:
    say "Hello, " + name + "!"
    return str.upper name
```

⚠️ Structural Rules for Semicolons (`;`)

1. **Top-Level Declarations:** The function terminator `;` is entirely optional.

2. **Nested Inline Declarations:** The semicolon `;` is **strictly mandatory** to wrap and bind inline inner function evaluations accurately.

```python
s.join s.join "bruh", 150.2; a   # Resolves structural nesting cleanly
```

3. **Whitespace Enforcement:** A trailing blank space or newline sequence **MUST** physically follow a semicolon.

```python
150.2; a    # VALID 
150.2;a     # INVALID (Triggers Syntax Error)
```

---

### 6. Exception Handling with Try/Catch/Finally

Bicala supports structured exception handling to gracefully manage runtime errors:

```python
try:
    result = 10 / 0
catch error:
    say "Error occurred: " + error
finally:
    say "Cleanup code runs here"
```

* **try:** Marks a block of code that might raise an exception
* **catch:** Defines exception handling logic with an error parameter
* **finally:** Optional cleanup block that always executes, regardless of exceptions

> ✅ **Implementation Status (Beta 5.1.19):** Full try/catch/finally functionality has been implemented and tested with strict validation rules.

---

### 7. Space-Separated Built-in Core Engine

Bicala standard library methods parse arguments greedily from left to right using **whitespace separation**, completely dropping traditional commas for built-in calls:

* **Mathematical Utilities:** `math.abs x`, `math.min a b`, `math.max a b`, `math.round x`.

* **String Utilities:** `str.len text`, `str.upper text`, `str.slice text start end`.

* **Array Manipulation:** `arr.len list`, `arr.push list element`, `arr.insert list index element`.

* **Type Casting Expressions:** `int "42"`, `str 123`, `float "3.14"`, `bool true`.
