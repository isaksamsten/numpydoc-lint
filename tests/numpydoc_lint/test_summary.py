from common import check_docstring
from numpydoc_lint._model import Pos
from numpydoc_lint.check import (
    I0009,
)


def test_I0009_single_line():
    code = '''
def f():
    """test"""
    pass
'''
    node, docstring, errors, warnings = check_docstring(code, I0009())
    assert len(warnings) == 1
    assert "`t`" in warnings[0].suggestion
    assert warnings[0].start == Pos(3, 5)


def test_I0009_multiline_line_without_blank_line():
    code = '''
def f():
    """
    test
    
    Extended summary.
    """
    pass
'''
    node, docstring, errors, warnings = check_docstring(code, I0009())
    assert len(warnings) == 1
    assert warnings[0].code == "I0009"
    assert warnings[0].start == Pos(line=4, column=5)
