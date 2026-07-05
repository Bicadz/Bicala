#!/usr/bin/env python
# Test script to verify error code refactoring

from main.parser import parse_expression, parse_statement
from main.errors import BicalaSyntaxError

# Test S001: Expected expression
print("Testing S001 (Expected expression)...")
try:
    parse_expression("+")
except BicalaSyntaxError as e:
    print(f"  Code: {e.code}, Message: {e.message}")

# Test S002: Expected name/identifier (after dot)
print("\nTesting S002 (Expected name/identifier)...")
try:
    parse_expression("x .")
except BicalaSyntaxError as e:
    print(f"  Code: {e.code}, Message: {e.message}")

# Test S005: Expected ':' after block header
print("\nTesting S005 (Expected ':' after block header)...")
try:
    # Use the parser.py which handles control statements
    from main.parser import parse_program
    parse_program(["if true"], 0)
except BicalaSyntaxError as e:
    print(f"  Code: {e.code}, Message: {e.message}")

# Test S033: Expected module name after 'from'
print("\nTesting S033 (Expected module name after 'from')...")
try:
    parse_statement("from import join", 1)
except BicalaSyntaxError as e:
    print(f"  Code: {e.code}, Message: {e.message}")

# Test S034: Expected 'import' or 'as' after module name
print("\nTesting S034 (Expected 'import' or 'as' after module name)...")
try:
    parse_statement("from math", 1)
except BicalaSyntaxError as e:
    print(f"  Code: {e.code}, Message: {e.message}")

# Test S035: Expected name(s) to import after 'import'
print("\nTesting S035 (Expected name(s) to import after 'import')...")
try:
    parse_statement("from math import", 1)
except BicalaSyntaxError as e:
    print(f"  Code: {e.code}, Message: {e.message}")

# Test S036: Expected alias name after 'as'
print("\nTesting S036 (Expected alias name after 'as')...")
try:
    parse_statement("from math import sqrt as", 1)
except BicalaSyntaxError as e:
    print(f"  Code: {e.code}, Message: {e.message}")

print("\nAll error code tests completed!")
