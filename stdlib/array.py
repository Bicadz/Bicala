# ============================================================
# ARRAY - Array/list module for Bicala
# ============================================================

def len(items):
    """Get array length."""
    return __builtins__['len'](items)


def first(items):
    """Get first item."""
    return items[0]


def last(items):
    """Get last item."""
    return items[-1]


def push(items, value):
    """Append value and return the same array."""
    items.append(value)
    return items


def pop(items, index=-1):
    """Remove and return item at index, defaulting to the last item."""
    return items.pop(index)


def insert(items, index, value):
    """Insert value at index and return the same array."""
    items.insert(index, value)
    return items


def remove(items, value):
    """Remove first matching value and return the same array."""
    items.remove(value)
    return items


def concat(left, right):
    """Return a new array containing both arrays."""
    return list(left) + list(right)


def reverse(items):
    """Return a reversed copy."""
    return list(reversed(items))


def sort(items):
    """Return a sorted copy."""
    return sorted(items)

