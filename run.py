# ============================================================
# MAIN - Entry point and Runtime for Bicala interpreter
# Single source of truth for execution
# ============================================================

import os
import sys

# Force the terminal to use UTF-8 to avoid Unicode character printing errors (like ✓) on Windows.
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Add main directory to sys.path for imports without __init__.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'main'))

from warnings import filterwarnings
filterwarnings("ignore", category=RuntimeWarning, module="runpy")

from pars.stmt import parse_program
from pars.expr import parse_expression
from eval import execute_program, evaluate_expression, execute_statement, set_source_dir
from env import Environment
from err import BicalaError, BicalaRuntimeError, format_error


def run_file_ast(filename):
    """
    Run Bicala source file using AST interpreter.

    :param filename: Path to .bica file
        """
    set_source_dir(os.path.abspath(filename))

    try:
        with open(filename, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as exc:
        print(f"Error: Could not read file '{filename}' -> {str(exc)}")
        return

    try:
        program = parse_program(lines, line_num_offset=0)
        execute_program(program)
    except BicalaError as err:
        print(format_error(err, lines, context=1))
    except Exception as exc:
        err = BicalaRuntimeError(
            code="R000",
            error=str(exc),
            context="program execution",
            hint="Internal runtime error while executing program"
        )
        print(format_error(err, lines, context=1))


def run_code_text_ast(code_text, source_path=None):
    """
    Run Bicala code string using AST interpreter.

    :param code_text: Source code as string
    :param source_path: Optional path for resolving .bica imports
    """
    if source_path:
        set_source_dir(source_path)

    lines = code_text.splitlines(True)
    try:
        program = parse_program(lines, line_num_offset=0)
        execute_program(program)
    except BicalaError as err:
        print(format_error(err, lines, context=1))
    except Exception as exc:
        err = BicalaRuntimeError(
            code="R000",
            error=str(exc),
            context="code text execution",
            hint="Internal runtime error while executing code text"
        )
        print(format_error(err, lines, context=1))


def eval_expression(expr_text):
    """
    Evaluate single expression (for REPL/testing).

    :param expr_text: Expression string
    :return: Computed value
    """
    ast = parse_expression(expr_text)
    env = Environment()
    return evaluate_expression(ast, env)


def _main():
    if len(sys.argv) < 2:
        print("Usage: python run.py <file.bica>")
        print("       python run.py -c \"code\"")
        return
    
    if sys.argv[1] == "-c":
        if len(sys.argv) < 3:
            print("Error: -c requires code string")
            return
        run_code_text_ast(sys.argv[2])
    else:
        run_file_ast(sys.argv[1])


if __name__ == "__main__":
    _main()
