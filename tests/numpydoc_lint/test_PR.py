from dataclasses import dataclass

import pytest
from numpydoc_lint.numpydoc import Parser, Pos
from numpydoc_lint.validate import Error, GL01, PR09, PR01
from common import check_docstring


def test_PR09_raw_string():
    code = r'''
def test(p):
    r"""Parameters
    ----------
    p : object\
            test
        Test test test '\n'.
    """
    pass
    '''
    node, docstring, errors, warnings = check_docstring(code, PR09())
    assert docstring.sections["Parameters"].contents[0].types[0].value == "object\\"
    assert len(errors) == 0


def test_PR01_with_parameters_section():
    code = '''
def test(p, x, y):
    """Parameters
    ----------
    p : object
        Test.
    x : object
        J
    """
    pass
'''
    func, docstring, errors, warnings = check_docstring(code, PR01())
    assert len(errors) == 0
    assert warnings[0].code == "PR01"
    assert warnings[0].start == Pos(line=2, column=16)


def test_PR01_without_parameters_section():
    code = '''
def test(p, x, y):
    """Summary."""
    pass
'''
    func, docstring, errors, warnings = check_docstring(code, PR01())
    assert len(errors) == 0
    assert len(warnings) == 3
    assert warnings[0].code == "PR01"
    assert warnings[0].start == Pos(line=2, column=10)
