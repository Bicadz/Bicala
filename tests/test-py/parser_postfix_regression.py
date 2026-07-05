import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main.ast_nodes import AttrNode, BinaryOpNode, CallNode, IndexNode, NumberNode, VarNode
from main.parser import parse_expression


def assert_var(node, name):
    assert isinstance(node, VarNode), f"expected VarNode({name}), got {type(node).__name__}"
    assert node.name == name, f"expected var name {name}, got {node.name}"


def test_a_b_call_index_d():
    # a.b(c)[i].d
    ast = parse_expression("a.b(c)[i].d")
    assert isinstance(ast, AttrNode)
    assert ast.attr == "d"
    assert isinstance(ast.obj, IndexNode)
    assert_var(ast.obj.index, "i")
    assert isinstance(ast.obj.base, CallNode)
    assert isinstance(ast.obj.base.callee, AttrNode)
    assert ast.obj.base.callee.attr == "b"
    assert_var(ast.obj.base.callee.obj, "a")
    assert len(ast.obj.base.args) == 1
    assert_var(ast.obj.base.args[0], "c")


def test_a_b_call_index0_c():
    # a.b()[0].c
    ast = parse_expression("a.b()[0].c")
    assert isinstance(ast, AttrNode)
    assert ast.attr == "c"
    assert isinstance(ast.obj, IndexNode)
    assert isinstance(ast.obj.index, NumberNode)
    assert ast.obj.index.value == 0
    assert isinstance(ast.obj.base, CallNode)
    assert isinstance(ast.obj.base.callee, AttrNode)
    assert ast.obj.base.callee.attr == "b"
    assert_var(ast.obj.base.callee.obj, "a")
    assert ast.obj.base.args == []


def test_a_plus_b_chain():
    # a + b.c(d)[0]
    ast = parse_expression("a + b.c(d)[0]")
    assert isinstance(ast, BinaryOpNode)
    assert ast.op == "+"
    assert_var(ast.left, "a")
    assert isinstance(ast.right, IndexNode)
    assert isinstance(ast.right.index, NumberNode)
    assert ast.right.index.value == 0
    assert isinstance(ast.right.base, CallNode)
    assert isinstance(ast.right.base.callee, AttrNode)
    assert ast.right.base.callee.attr == "c"
    assert_var(ast.right.base.callee.obj, "b")
    assert len(ast.right.base.args) == 1
    assert_var(ast.right.base.args[0], "d")


def test_a_b_plus_c_d_call():
    # a.b + c.d(e)
    ast = parse_expression("a.b + c.d(e)")
    assert isinstance(ast, BinaryOpNode)
    assert ast.op == "+"
    assert isinstance(ast.left, AttrNode)
    assert ast.left.attr == "b"
    assert_var(ast.left.obj, "a")
    assert isinstance(ast.right, CallNode)
    assert isinstance(ast.right.callee, AttrNode)
    assert ast.right.callee.attr == "d"
    assert_var(ast.right.callee.obj, "c")
    assert len(ast.right.args) == 1
    assert_var(ast.right.args[0], "e")


def run():
    test_a_b_call_index_d()
    test_a_b_call_index0_c()
    test_a_plus_b_chain()
    test_a_b_plus_c_d_call()
    print("parser postfix regression passed")


if __name__ == "__main__":
    run()
