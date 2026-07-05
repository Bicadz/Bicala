# Test file for def and assignment syntax

# Inline function definition
def add a, b: a + b

# Block function definition
def greet name:
    say "Hello, " + name

# Inline operator definition
def infixl 10 -- a, b: a - b - 1

# Block operator definition
def infix 5 == a, b:
    if a == b:
        return True
    else:
        return False

# Assignment with =
result = 10 - 2

# Test the function
say "add 3, 4:"
say add 3, 4

# Test the assignment
say "result:"
say result

# Test the block function
greet "World"
