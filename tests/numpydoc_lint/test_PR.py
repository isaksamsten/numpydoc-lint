from dataclasses import dataclass

import pytest
from numpydoc_lint.numpydoc import Parser, Pos
from numpydoc_lint.validate import Error, GL01, PR09, PR01, PR02, PR03, PR04, PR05
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


def test_PR02_parameter_does_not_exist():
    code = '''
def test(a):
    """
    Parameters
    ----------
    a : int
        Test
    b : int
        Test
    """
    pass
'''
    func, docstring, errors, warnings = check_docstring(code, PR02())
    assert len(warnings) == 1
    assert warnings[0].code == "PR02"
    assert "`b`" in warnings[0].message
    assert warnings[0].start == Pos(8, 5)


def test_PR03_parameter_wrong_order():
    code = '''
def test(b, aaa):
    """
    Parameters
    ----------
    aaa : int
        Test
    b : int
        Test
    """
    pass
'''
    func, docstring, errors, warnings = check_docstring(code, PR03())
    assert len(warnings) == 2
    assert warnings[0].code == "PR03"
    assert "`aaa`" in warnings[0].message
    assert warnings[0].start == Pos(6, 5)
    assert warnings[0].end == Pos(6, 8)

    assert warnings[1].code == "PR03"
    assert "`b`" in warnings[1].message
    assert warnings[1].start == Pos(8, 5)
    assert warnings[1].end == Pos(8, 6)


def test_PR04_type_declaration_missing():
    code = '''
def test(b, aaa: int):
    """
    Parameters
    ----------
    aaa
        Test
    b : int
        Test
    """
    pass
'''
    func, docstring, errors, warnings = check_docstring(code, PR04())
    assert len(warnings) == 1
    assert warnings[0].code == "PR04"
    assert "`int`" in warnings[0].suggestion
    assert "`aaa`" in warnings[0].message
    assert warnings[0].start == Pos(6, 5)
    assert warnings[0].end == Pos(6, 8)


def test_PR05_period_ends_type():
    code = '''
def test(b, aaa: int):
    """
    Parameters
    ----------
    aaa : int.
        Test
    b : int or string.
        Test
    """
    pass
'''
    func, docstring, errors, warnings = check_docstring(code, PR05())
    assert len(warnings) == 2
    assert warnings[0].code == "PR05"
    assert warnings[0].start == Pos(6, 15)
    assert warnings[0].end == Pos(6, 15)

    assert warnings[1].code == "PR05"
    assert warnings[1].start == Pos(8, 23)
    assert warnings[1].end == Pos(8, 23)


def test_PR05_period_ends_type_optional():
    """
    Summary.

    Parameters
    ----------
    a : int
        Test.

    """
    code = '''
def test(b, aaa: int):
    """
    Parameters
    ----------
    b : int or string, optional .
        Test
    """
    pass
'''
    func, docstring, errors, warnings = check_docstring(code, PR05())
    assert len(warnings) == 1
    assert warnings[0].code == "PR05"
    assert warnings[0].start == Pos(6, 34)
