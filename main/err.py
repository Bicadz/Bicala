# ============================================================
# ERRORS - Custom error classes for Bicala
# Rich error system with codes, context, and formatted output
# ============================================================

# --- Error Code Ranges ---
# L001-L099  Lexer Errors
# S001-S099  Syntax/Parser Errors (including indentation)
# R001-R099  Runtime Errors
# T001-T099  Type Errors
# V001-V099  Value Errors
# N001-N099  Name Errors (including attribute errors)
# M001-M099  Import Errors

# --- Severity Levels ---
SEVERITY_FATAL = "FATAL"       # Cannot continue (internal error, stack overflow)
SEVERITY_ERROR = "ERROR"       # Compilation / parse error (cannot run)
SEVERITY_RUNTIME = "RUNTIME"   # Generic runtime error
SEVERITY_WARNING = "WARNING"   # Non-fatal issue (deprecated syntax, etc.)

# --- Specific Runtime Sub-Categories ---
SEVERITY_NAME = "NAME"         # Name/scope resolution error
SEVERITY_TYPE = "TYPE"         # Type system error
SEVERITY_VALUE = "VALUE"       # Value/operation error
SEVERITY_ATTRIBUTE = "ATTRIBUTE"  # Object model error
SEVERITY_IMPORT = "IMPORT"     # Module system error

# Map code prefix to default severity
_CODE_SEVERITY = {
    "L": SEVERITY_ERROR,
    "S": SEVERITY_ERROR,
    "R": SEVERITY_RUNTIME,
    "T": SEVERITY_TYPE,
    "V": SEVERITY_VALUE,
    "N": SEVERITY_NAME,
    "M": SEVERITY_RUNTIME,  # Import errors are runtime errors
}


# ============================================================
# ERROR DATABASE - Templates for dynamic formatting
# ============================================================

ERRORS = {
    # Lexer Errors (L001-L099)
    "L001": {
        "message": "Unterminated string",
        "hint": "Add closing quote to end the string"
    },
    "L002": {
        "message": "Invalid character '{char}'",
        "hint": "Character '{char}' is not allowed in Bicala syntax"
    },
    "L003": {
        "message": "Invalid escape sequence '\\{char}'",
        "hint": "Use valid escape sequences: \\n, \\t, \\\\, \\\", \\{, \\}"
    },
    "L004": {
        "message": "Unterminated string literal (newline in string)",
        "hint": "Use \\n for newline or close the string before the line break"
    },
    "L005": {
        "message": "Invalid number literal",
        "hint": "Add whitespace/operator between number and identifier"
    },
    "L006": {
        "message": "Unterminated block comment",
        "hint": "Add ### to close the block comment"
    },
    "L007": {
        "message": "Unterminated interpolation in string",
        "hint": "Add closing }} to end the interpolation"
    },
    "L008": {
        "message": "Empty interpolation in string",
        "hint": "Add variable name inside {{}}"
    },

    # Syntax/Parser Errors (S001-S099)
    "S001": {
        "message": "Expected expression",
        "hint": "Provide a valid expression"
    },
    "S002": {
        "message": "Expected name/identifier",
        "hint": "Provide a valid identifier"
    },
    "S003": {
        "message": "Expected expression after '{op}'",
        "hint": "Provide a valid expression after the operator"
    },
    "S004": {
        "message": "Expected name after '.'",
        "hint": "Provide a valid attribute name"
    },
    "S005": {
        "message": "Expected ':'",
        "hint": "Add ':' at the end of the control statement"
    },
    "S006": {
        "message": "Expected end of input",
        "hint": "Check for missing operator or extra characters"
    },
    "S007": {
        "message": "Expected '{expected}' but got '{got}'",
        "hint": "Check syntax and fix the error"
    },
    "S008": {
        "message": "Unknown statement '{statement}'",
        "hint": "Flat statements must be: name: value, function_call(), or control keyword"
    },
    "S009": {
        "message": "Expected '{expected}' in {context}",
        "hint": "Add the missing element"
    },
    "S010": {
        "message": "Invalid {context} syntax",
        "hint": "Check the syntax for {context}"
    },
    "S011": {
        "message": "Expected indented block after control statement",
        "hint": "Indent this line with 4 spaces (or one tab) relative to the header"
    },
    "S012": {
        "message": "Unexpected token '{token}' in {context}",
        "hint": "Remove or replace the token"
    },
    "S013": {
        "message": "Expected '{expected}' in function definition",
        "hint": "Provide the missing element"
    },
    "S014": {
        "message": "Indentation must be multiple of 4 spaces, got {spaces} space(s)",
        "hint": "Use 4 spaces per indent level (or a tab)"
    },
    "S015": {
        "message": "Missing closing bracket {expected}",
        "hint": "Add a closing bracket to match the opening one"
    },
    "S016": {
        "message": "Expected block after function definition",
        "hint": "Add an indented block for the function body"
    },
    "S017": {
        "message": "Extra opening bracket",
        "hint": "Remove the extra opening bracket"
    },
    "S018": {
        "message": "Extra closing bracket {expected}",
        "hint": "Remove the extra closing bracket"
    },
    "S019": {
        "message": "Expected '{kw}' after module name",
        "hint": "Add the missing keyword"
    },
    "S020": {
        "message": "Expected name(s) to import after '{kw}'",
        "hint": "Provide one or more names to import"
    },
    "S021": {
        "message": "Expected alias name after '{kw}'",
        "hint": "Provide a valid alias name"
    },
    "S022": {
        "message": "Expected '{kw}' or '{kw2}' after module name",
        "hint": "Add the missing keyword"
    },
    "S023": {
        "message": "Invalid switch case syntax",
        "hint": "Use: case value: or default:"
    },
    "S024": {
        "message": "Expected '{expected}' in switch statement",
        "hint": "Add the missing element"
    },
    "S025": {
        "message": "Invalid repeat syntax",
        "hint": "Use: repeat count: or repeat count"
    },
    "S026": {
        "message": "Expected number after '{kw}'",
        "hint": "Provide a valid number"
    },
    "S027": {
        "message": "Invalid for loop syntax",
        "hint": "Use: for var in range or for var in array"
    },
    "S028": {
        "message": "Expected '{kw}' in for loop",
        "hint": "Add the missing keyword"
    },
    "S029": {
        "message": "Invalid range syntax: {range_expr}",
        "hint": "Use: start:end or start:end:step"
    },
    "S030": {
        "message": "Expected array after '{kw}'",
        "hint": "Provide an array literal"
    },
    "S031": {
        "message": "Invalid array literal",
        "hint": "Use: [item1, item2, ...]"
    },
    "S032": {
        "message": "Expected '{expected}' in array literal",
        "hint": "Add the missing element"
    },
    "S033": {
        "message": "Expected module name after '{kw}'",
        "hint": "Example: {kw} math import sqrt"
    },
    "S034": {
        "message": "Expected '{kw}' or '{kw2}' after module name",
        "hint": "Example: {kw} math import sqrt or {kw} math as m"
    },
    "S035": {
        "message": "Expected name(s) to import after '{kw}'",
        "hint": "Example: {kw} math import sqrt, sin"
    },
    "S036": {
        "message": "Expected alias name after '{kw}'",
        "hint": "Example: {kw} math import sqrt as square_root"
    },
    "S037": {
        "message": "Invalid attribute access: {attr}",
        "hint": "Use: object.attribute"
    },
    "S038": {
        "message": "Expected '{expected}' in expression",
        "hint": "Add the missing element"
    },
    "S039": {
        "message": "Invalid expression: {expr}",
        "hint": "Check expression syntax"
    },
    "S040": {
        "message": "Expected '{expected}' after '{kw}'",
        "hint": "Add the missing element"
    },
    "S041": {
        "message": "Cannot use reserved keyword as an identifier",
        "hint": "Reserved keywords cannot be used as variable or function names"
    },
    "S042": {
        "message": "Expected '{expected}' in function call",
        "hint": "Add the missing element"
    },
    "S043": {
        "message": "Invalid assignment syntax",
        "hint": "Use: var = value or var op= value"
    },
    "S044": {
        "message": "Expected '{expected}' in assignment",
        "hint": "Add the missing element"
    },
    "S045": {
        "message": "Invalid compound assignment operator: {op}",
        "hint": "Use: +=, -=, *=, /=, //=, %=, or **="
    },
    "S046": {
        "message": "Expected identifier in assignment",
        "hint": "Provide a valid variable name"
    },
    "S047": {
        "message": "Invalid increment/decrement syntax",
        "hint": "Use: var++ or var--"
    },
    "S048": {
        "message": "Expected identifier before {op}",
        "hint": "Provide a valid variable name"
    },
    "S049": {
        "message": "Invalid delete syntax",
        "hint": "Use: del identifier"
    },
    "S050": {
        "message": "Expected identifier after '{kw}'",
        "hint": "Provide a valid variable name"
    },
    "S051": {
        "message": "Invalid help syntax",
        "hint": "Use: help or help topic"
    },
    "S052": {
        "message": "Expected topic after '{kw}'",
        "hint": "Provide a help topic"
    },
    "S053": {
        "message": "Invalid debug syntax",
        "hint": "Use: debug or debug all or debug var"
    },
    "S054": {
        "message": "Expected identifier after '{kw}'",
        "hint": "Provide a valid variable name or 'all'"
    },
    "S055": {
        "message": "Invalid input syntax",
        "hint": "Use: input or input \"prompt\""
    },
    "S056": {
        "message": "Expected expression after '{kw}'",
        "hint": "Provide a valid expression for the prompt"
    },
    "S057": {
        "message": "Invalid return syntax",
        "hint": "Use: return or return value"
    },
    "S058": {
        "message": "Expected expression after '{kw}'",
        "hint": "Provide a valid expression to return"
    },
    "S059": {
        "message": "Invalid break/continue syntax",
        "hint": "Use: break or continue (without arguments)"
    },
    "S060": {
        "message": "Expected '{expected}' in block",
        "hint": "Add the missing element"
    },
    "S061": {
        "message": "Invalid block syntax",
        "hint": "Ensure proper indentation and structure"
    },
    "S062": {
        "message": "Expected '{expected}' after '{kw}'",
        "hint": "Add the missing element"
    },
    "S063": {
        "message": "Invalid if/elif/else syntax",
        "hint": "Use: if condition: or elif condition: or else:"
    },
    "S064": {
        "message": "Expected condition after '{kw}'",
        "hint": "Provide a valid condition expression"
    },
    "S065": {
        "message": "Invalid while loop syntax",
        "hint": "Use: while condition:"
    },
    "S066": {
        "message": "Expected condition after '{kw}'",
        "hint": "Provide a valid condition expression"
    },
    "S067": {
        "message": "Invalid forever loop syntax",
        "hint": "Use: forever:"
    },
    "S068": {
        "message": "Invalid defer syntax",
        "hint": "Use: defer statement or defer: block"
    },

    # Indentation Errors (I001-I099)
    "I001": {
        "message": "Inconsistent indentation: expected {expected} spaces, got {got}",
        "hint": "Use consistent indentation (4 spaces or 1 tab)"
    },
    "I002": {
        "message": "Expected an indented block after block header",
        "hint": "Indent this line with 4 spaces (or one tab) relative to the header"
    },
    "I003": {
        "message": "Unexpected indentation",
        "hint": "Remove extra indentation"
    },

    # Runtime Errors (R001-R099)
    "R001": {
        "message": "Internal runtime error: {context} - {error}",
        "hint": "Check the operation and values"
    },
    "R002": {
        "message": "break used outside of a loop",
        "hint": "break can only be used inside while/for blocks"
    },
    "R003": {
        "message": "continue used outside of a loop",
        "hint": "continue can only be used inside while/for blocks"
    },
    "R004": {
        "message": "Division by zero",
        "hint": "Check the divisor"
    },
    "R005": {
        "message": "Modulo by zero",
        "hint": "Check the divisor"
    },
    "R006": {
        "message": "Invalid operation: {op}",
        "hint": "Check the operation and operand types"
    },
    "R007": {
        "message": "Stack overflow",
        "hint": "Check for infinite recursion"
    },

    # Type Errors (T001-T099)
    "T001": {
        "message": "Type mismatch: expected {expected}, got {got}",
        "hint": "Ensure the value has the correct type"
    },
    "T002": {
        "message": "Type mismatch: expected {expected_type}, got {actual_type}",
        "hint": "Ensure the expression type matches the declared type"
    },
    "T003": {
        "message": "Cannot convert {from_type} to {to_type}",
        "hint": "Check the conversion operation"
    },
    "T004": {
        "message": "Value '{name}' is not callable",
        "hint": "Ensure the value is a function or callable object"
    },
    "T005": {
        "message": "Missing function arguments: expected {expected}, got {got}",
        "hint": "Provide the required number of arguments"
    },
    "T006": {
        "message": "Extra function arguments: expected {expected}, got {got}",
        "hint": "Remove the extra arguments"
    },

    # Value Errors (V001-V099)
    "V001": {
        "message": "Invalid value: {value}",
        "hint": "Provide a valid value"
    },
    "V002": {
        "message": "Value out of range: {value}",
        "hint": "Provide a value within the valid range"
    },
    "V003": {
        "message": "Invalid index: {index}",
        "hint": "Provide a valid index"
    },
    "V007": {
        "message": "Operator precedence must be between 0 and 1000, got {precedence}",
        "hint": "Provide a precedence value between 0 and 1000"
    },

    # Name Errors (N001-N099)
    "N001": {
        "message": "Name '{name}' is not defined",
        "hint": "Define the variable before using it"
    },
    "N002": {
        "message": "Cannot reassign constant variable '{name}'",
        "hint": "Constants are immutable and cannot be reassigned"
    },
    "N003": {
        "message": "Cannot delete '{name}'",
        "hint": "Check if the name exists"
    },
    "N004": {
        "message": "Variable '{name}' is not defined in string interpolation",
        "hint": "Define the variable before using it in interpolation"
    },
    "N007": {
        "message": "Name collision: '{name}' already exists in this scope",
        "hint": "Use a different name"
    },
    "N005": {
        "message": "Function '{name}' is not defined",
        "hint": "Define the function before calling it"
    },
    "N006": {
        "message": "Attribute '{attr}' not found on object",
        "hint": "Check the object's attributes"
    },

    # Import Errors (M001-M099)
    "M001": {
        "message": "Module '{module}' not found",
        "hint": "Check the module name and path"
    },
    "M002": {
        "message": "Circular import detected: module '{name}' is already being loaded",
        "hint": "Refactor to avoid circular dependencies"
    },
    "M003": {
        "message": "Duplicate alias '{name}' in scope",
        "hint": "Use a different name for the import alias"
    },
    "S043": {
        "message": "Invalid catch parameter syntax",
        "hint": "Use: catch (error) with a valid identifier"
    },
    "S044": {
        "message": "Try block must be followed by catch or finally",
        "hint": "Add a catch or finally block after the try block"
    },
}


class BicalaError(Exception):
    """Base error for all Bicala-specific errors."""

    def __init__(self, code="E000", line=None, col=None, **context):
        super().__init__()
        self.code = code
        self.line = line
        self.col = col
        self.context = context

        # Extract commonly used fields from context for backward compatibility
        self.message = self._format_message()
        self.expected = context.get('expected')
        self.got = context.get('got')
        self.hint = self._format_hint()
        self.length = context.get('length', 1)
        if self.length is None:
            self.length = 1
        else:
            self.length = max(1, int(self.length))

        # Auto-detect severity from code prefix if not given
        severity = context.get('severity')
        if severity is None and code:
            prefix = code[0].upper()
            self.severity = _CODE_SEVERITY.get(prefix, SEVERITY_ERROR)
        else:
            self.severity = severity or SEVERITY_ERROR

    def _format_message(self):
        """Format error message using template from ERRORS database."""
        error_info = ERRORS.get(self.code, {"message": "Unknown error", "hint": ""})
        template = error_info.get("message", "Unknown error")
        try:
            return template.format(**self.context)
        except (KeyError, ValueError):
            # If formatting fails, return template with placeholders
            return template

    def _format_hint(self):
        """Format hint using template from ERRORS database."""
        error_info = ERRORS.get(self.code, {"message": "Unknown error", "hint": ""})
        template = error_info.get("hint", "")
        try:
            return template.format(**self.context)
        except (KeyError, ValueError):
            # If formatting fails, return template with placeholders
            return template

    def __str__(self):
        parts = [f"[{self.severity}] [{self.code}] {self.message}"]
        if self.line is not None:
            col_info = f", Col {self.col}" if self.col is not None else ""
            parts.append(f"Line {self.line}{col_info}")
        if self.expected is not None:
            parts.append(f"Expected: {self.expected}")
        if self.got is not None:
            parts.append(f"Got: {self.got}")
        if self.hint:
            parts.append(f"Hint: {self.hint}")
        return "\n".join(parts)


class BicalaParseError(BicalaError):
    """Base class for parsing-related errors."""
    pass


class BicalaExecutionError(BicalaError):
    """Base class for runtime/execution-related errors."""
    pass


class BicalaScopeError(BicalaExecutionError):
    """Base class for scope and name-resolution issues."""
    pass


class BicalaLexerError(BicalaParseError):
    """Lexer/tokenization error. Code range: L001-L099."""
    pass


class BicalaSyntaxError(BicalaParseError):
    """Syntax/parser error. Code range: S001-S099."""
    pass


class BicalaNameError(BicalaScopeError):
    """Name/variable not found error. Code range: N001-N099."""
    pass


class BicalaImportError(BicalaExecutionError):
    """Module import error. Code range: M001-M099."""
    pass


class BicalaTypeError(BicalaExecutionError):
    """Type mismatch error. Code range: T001-T099."""
    pass


class BicalaValueError(BicalaExecutionError):
    """Invalid value error. Code range: V001-V099."""
    pass


class BicalaRuntimeError(BicalaExecutionError):
    """Runtime execution error. Code range: R001-R099."""
    pass


class BicalaEnvironmentError(BicalaScopeError):
    """Environment/scope operation error."""
    pass


class BicalaIndentationError(BicalaParseError):
    """Indentation error. Code range: I001-I099."""
    pass


class BicalaAttributeError(BicalaExecutionError):
    """Attribute not found error. Code range: A001-A099."""
    pass


# ============================================================
# ERROR FORMATTER - Pretty output with source context
# ============================================================

def format_error(err, source_lines=None, context=1):
    """
    Format a BicalaError into a rich, readable error message.

    :param err: BicalaError instance
    :param source_lines: List of source code lines (raw, with newlines)
    :param context: Number of surrounding lines to show (0 = none)
    :return: Formatted error string
    """
    result = []

    # Header: [SEVERITY] [Code] Message
    result.append(f"[{err.severity}] [{err.code}] {err.message}")

    # Location
    if err.line is not None:
        col_info = f", Col {err.col}" if err.col is not None else ""
        result.append(f"Line {err.line}{col_info}")

    # Source context with pointer
    if source_lines and err.line is not None and 1 <= err.line <= len(source_lines):
        result.append("")  # blank line

        start = max(1, err.line - context)
        end = min(len(source_lines), err.line + context)

        # Calculate line number width for alignment
        max_width = len(str(end))

        for ln in range(start, end + 1):
            raw = source_lines[ln - 1].rstrip('\n').rstrip('\r')
            marker = ">" if ln == err.line else " "
            line_num = str(ln).rjust(max_width)
            result.append(f"{marker} {line_num} | {raw}")

            # Pointer line under the error line
            if ln == err.line and err.col is not None:
                prefix = f"  {line_num} | "
                pointer_spaces = " " * (len(prefix) + err.col - 1)
                pointer_carets = "^" * err.length
                result.append(f"{pointer_spaces}{pointer_carets}")

    # Expected / Got
    if err.expected is not None or err.got is not None:
        result.append("")
        if err.expected is not None:
            result.append(f"Expected: {err.expected}")
        if err.got is not None:
            result.append(f"Got: {err.got}")

    # Hint
    if err.hint:
        result.append(f"\nHint: {err.hint}")

    return "\n".join(result)
