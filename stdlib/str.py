# ============================================================
# STR - String module for Bicala
# ============================================================

import builtins as _builtins

# Constants
whitespace = ' \t\n\r\f\v'

def upper(s):
    """Convert to uppercase."""
    return str(s).upper()

def lower(s):
    """Convert to lowercase."""
    return str(s).lower()

def title(s):
    """Convert to title case."""
    return str(s).title()

def capitalize(s):
    """Capitalize first letter."""
    return str(s).capitalize()

def strip(s, chars=None):
    """Strip whitespace or chars from both ends."""
    return str(s).strip(chars)

def lstrip(s, chars=None):
    """Strip from left."""
    return str(s).lstrip(chars)

def rstrip(s, chars=None):
    """Strip from right."""
    return str(s).rstrip(chars)

def split(s, sep=None, maxsplit=-1):
    """Split string."""
    return str(s).split(sep, maxsplit)

def join(sep, items):
    """Join items with separator."""
    return str(sep).join(str(i) for i in items)

def replace(s, old, new, count=-1):
    """Replace substring."""
    return str(s).replace(old, new, count)

def find(s, sub, start=0, end=None):
    """Find substring position."""
    return str(s).find(sub, start, end)

def rfind(s, sub, start=0, end=None):
    """Find substring from right."""
    return str(s).rfind(sub, start, end)

def count(s, sub, start=0, end=None):
    """Count substring occurrences."""
    return str(s).count(sub, start, end)

def startswith(s, prefix, start=0, end=None):
    """Check if starts with prefix."""
    return str(s).startswith(prefix, start, end)

def endswith(s, suffix, start=0, end=None):
    """Check if ends with suffix."""
    return str(s).endswith(suffix, start, end)

def length(s):
    """Get string length."""
    return _builtins.len(str(s))

# Alias for len
len = length


def format(s, *args, **kwargs):
    """Format string."""
    return str(s).format(*args, **kwargs)

def isdigit(s):
    """Check if all digits."""
    return str(s).isdigit()

def isalpha(s):
    """Check if all letters."""
    return str(s).isalpha()

def isalnum(s):
    """Check if alphanumeric."""
    return str(s).isalnum()

def isspace(s):
    """Check if all whitespace."""
    return str(s).isspace()

def isupper(s):
    """Check if uppercase."""
    return str(s).isupper()

def islower(s):
    """Check if lowercase."""
    return str(s).islower()
