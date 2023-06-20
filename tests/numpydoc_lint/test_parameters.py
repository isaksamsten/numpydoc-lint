from dataclasses import dataclass

import pytest
from numpydoc_lint.numpydoc import Parser, Pos
from numpydoc_lint.check import (
    I0001,
    I0102,
    W0101,
    W0102,
    W0103,
    W0104,
    E0101,
    E0102,
    W0105,
    I0101,
    I0102,
    W0106,
    I0103,
    I0104,
    I0105,
)
from common import check_docstring


def test_W0101_with_parameters_section():
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
    func, docstring, errors, warnings = check_docstring(code, W0101())
    assert len(errors) == 0
    assert warnings[0].code == "W0101"
    assert warnings[0].start == Pos(line=2, column=16)


def test_W0101_without_parameters_section():
    code = '''
def test(p, x, y):
    """Summary."""
    pass
'''
    func, docstring, errors, warnings = check_docstring(code, W0101())
    assert len(errors) == 0
    assert len(warnings) == 3
    assert warnings[0].code == "W0101"
    assert warnings[0].start == Pos(line=2, column=10)


def test_W0101_with_other_parameters():
    code = '''
def test(p, x, y):
    """
    Summary.

    Other Parameters
    ----------------
    p : int
    x : str
    """
    pass
'''
    func, docstring, errors, warnings = check_docstring(code, W0101())
    assert len(warnings) == 1
    assert warnings[0].start == Pos(2, 16)


def test_W0101_with_other_parameters_and_parameters():
    code = '''
def test(p, x, y):
    """
    Summary.

    Parameters
    ----------
    y : int

    Other Parameters
    ----------------
    p : int
    x : str
    """
    pass
'''
    func, docstring, errors, warnings = check_docstring(code, W0101())
    assert len(warnings) == 0


def test_W0102_parameter_does_not_exist():
    code = '''
def test(a):
    """
    Parameters
    ----------
    a : int
        Test
    b : int
        Test

    Other Parameters
    ----------------
    c : int
    """
    pass
'''
    func, docstring, errors, warnings = check_docstring(code, W0102())
    assert len(warnings) == 2
    assert warnings[0].code == "W0102"
    assert "`b`" in warnings[0].message
    assert warnings[0].start == Pos(8, 5)
    assert "`c`" in warnings[1].message


def test_W0103_parameter_wrong_order():
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
    func, docstring, errors, warnings = check_docstring(code, W0103())
    assert len(warnings) == 2
    assert warnings[0].code == "W0103"
    assert "`aaa`" in warnings[0].message
    assert warnings[0].start == Pos(6, 5)
    assert warnings[0].end == Pos(6, 8)

    assert warnings[1].code == "W0103"
    assert "`b`" in warnings[1].message
    assert warnings[1].start == Pos(8, 5)
    assert warnings[1].end == Pos(8, 6)


def test_W0103_parameter_wrong_order_other_parameters_wrong_order():
    code = '''
def test(b, aaa, x, z, y):
    """
    Parameters
    ----------
    aaa : int
        Test
    b : int
        Test

    Other Parameters
    ----------------
    x : int
    y : int
    z : int
    """
    pass
'''
    func, docstring, errors, warnings = check_docstring(code, W0103())
    assert len(warnings) == 4
    assert "`aaa`" in warnings[0].message
    assert "`b`" in warnings[1].message
    assert "`y`" in warnings[2].message
    assert "`z`" in warnings[3].message


def test_W0104_type_declaration_missing():
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
    func, docstring, errors, warnings = check_docstring(code, W0104())
    assert len(warnings) == 1
    assert warnings[0].code == "W0104"
    assert "`int`" in warnings[0].suggestion
    assert "`aaa`" in warnings[0].message
    assert warnings[0].start == Pos(6, 5)
    assert warnings[0].end == Pos(6, 8)


def test_E0101_period_ends_type():
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
    func, docstring, errors, warnings = check_docstring(code, E0101())
    assert len(warnings) == 2
    assert warnings[0].code == "E0101"
    assert warnings[0].start == Pos(6, 15)
    assert warnings[0].end == Pos(6, 15)

    assert warnings[1].code == "E0101"
    assert warnings[1].start == Pos(8, 23)
    assert warnings[1].end == Pos(8, 23)


def test_E0101_period_ends_type_optional():
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
    func, docstring, errors, warnings = check_docstring(code, E0101())
    assert len(warnings) == 1
    assert warnings[0].code == "E0101"
    assert warnings[0].start == Pos(6, 34)


def test_E0102_wrong_type():
    code = '''
def test(b, aaa: int):
    """
    Parameters
    ----------
    b : int or string, optional .
        Test
    a : integer
        Test
    c : int or boolean
        Test
    d : { } or int
        Test.

    """
    pass
'''
    func, docstring, errors, warnings = check_docstring(code, E0102())
    assert len(warnings) == 4
    assert warnings[0].code == "E0102"
    assert "`b`" in warnings[0].message
    assert warnings[0].start == Pos(6, 16)
    assert warnings[0].end == Pos(6, 22)

    assert warnings[1].code == "E0102"
    assert "`a`" in warnings[1].message
    assert warnings[1].start == Pos(8, 9)
    assert warnings[1].end == Pos(8, 16)

    assert warnings[2].code == "E0102"
    assert "`c`" in warnings[2].message
    assert warnings[2].start == Pos(10, 16)
    assert warnings[2].end == Pos(10, 23)

    assert warnings[3].code == "E0103"
    assert "`d`" in warnings[3].message
    assert warnings[3].start == Pos(12, 9)
    assert warnings[3].end == Pos(12, 12)


def test_W0105_no_description():
    code = '''
def test(b, aaa: int):
    """
    Parameters
    ----------
    b : int or string, optional .
    a : integer
        Test

    """
    pass
'''
    func, docstring, errors, warnings = check_docstring(code, W0105())
    assert len(warnings) == 1
    assert warnings[0].code == "W0105"
    assert warnings[0].start == Pos(6, 5)
    assert warnings[0].end == Pos(6, 6)


def test_I0101_not_uppercase():
    code = '''
def test(b, aaa: int):
    """
    Parameters
    ----------
    b : int or string, optional .
        test.
    a : integer



        Test

    """
    pass
'''
    func, docstring, errors, warnings = check_docstring(code, I0101())
    assert len(warnings) == 1
    assert warnings[0].code == "I0101"
    assert warnings[0].start == Pos(6, 5)
    assert warnings[0].end == Pos(6, 6)


def test_I0102_no_period():
    code = '''
def test(b, aaa: int):
    """
    Parameters
    ----------
    b : int or string, optional .
        test
    a : integer

        Test

    """
    pass
'''
    func, docstring, errors, warnings = check_docstring(code, I0102())
    assert len(warnings) == 2
    assert warnings[0].code == "I0102"
    assert warnings[0].start == Pos(6, 5)
    assert warnings[0].end == Pos(6, 6)


def test_W0106_no_space():
    code = '''
def test(b, aaa: int):
    """
    Parameters
    ----------
    b: int or string, optional .
        test
    a :integer
        Test
    c:int
        Test.
    d : int
    """
    pass
'''
    func, docstring, errors, warnings = check_docstring(code, W0106())
    print(warnings)
    assert len(warnings) == 3
    assert warnings[0].code == "W0106"
    assert warnings[0].start == Pos(6, 5)
    assert warnings[0].end == Pos(6, 7)

    assert warnings[1].code == "W0106"
    assert warnings[1].start == Pos(8, 7)
    assert warnings[1].end == Pos(8, 9)

    assert warnings[2].code == "W0106"
    assert warnings[2].start == Pos(10, 5)
    assert warnings[2].end == Pos(10, 7)


def test_I0103_has_empty_prefix_lines():
    code = '''
def test(b, aaa: int):
    """
    Parameters
    ----------
    b: int or string, optional .

        test
    a :integer
        Test
    c:int
        Test.
    d : int

    """
    pass
'''
    func, docstring, errors, warnings = check_docstring(code, I0103())
    assert len(warnings) == 2
    assert warnings[0].start == Pos(6, 5)
    assert warnings[1].start == Pos(13, 5)


def test_I0103_has_empty_prefix_lines():
    code = '''
def test(b, aaa: int):
    """
    Parameters
    ----------
    b: int or string, optional .
        test

    a :integer
        Test
    c:int
        Test.
    d : int

    """
    pass
'''
    func, docstring, errors, warnings = check_docstring(code, I0104())
    assert len(warnings) == 2
    assert warnings[0].start == Pos(6, 5)
    assert warnings[1].start == Pos(13, 5)

    assert len(warnings) == 1
    assert warnings[0].code == "I0101"
    assert warnings[0].start == Pos(6, 5)
    assert warnings[0].end == Pos(6, 6)


def test_I0102_no_period():
    code = '''
def test(b, aaa: int):
    """
    Parameters
    ----------
    b : int or string, optional .
        test
    a : integer

        Test

    """
    pass
'''
    func, docstring, errors, warnings = check_docstring(code, I0102())
    assert len(warnings) == 2
    assert warnings[0].code == "I0102"
    assert warnings[0].start == Pos(6, 5)
    assert warnings[0].end == Pos(6, 6)


def test_I0102_raw_string_space():
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
    node, docstring, errors, warnings = check_docstring(code, I0102())
    assert docstring.sections["parameters"].contents[0].types[0].value == "object\\"
    assert (
        docstring.sections["parameters"].contents[0].description.data[0].value
        == "        test"
    )
    assert len(errors) == 0


def test_W0106_no_space():
    code = '''
def test(b, aaa: int):
    """
    Parameters
    ----------
    b: int or string, optional .
        test
    a :integer
        Test
    c:int
        Test.
    d : int
    """
    pass
'''
    func, docstring, errors, warnings = check_docstring(code, W0106())
    print(warnings)
    assert len(warnings) == 3
    assert warnings[0].code == "W0106"
    assert warnings[0].start == Pos(6, 5)
    assert warnings[0].end == Pos(6, 7)

    assert warnings[1].code == "W0106"
    assert warnings[1].start == Pos(8, 7)
    assert warnings[1].end == Pos(8, 9)

    assert warnings[2].code == "W0106"
    assert warnings[2].start == Pos(10, 5)
    assert warnings[2].end == Pos(10, 7)


def test_I0103_has_empty_prefix_lines():
    code = '''
def test(b, aaa: int):
    """
    Parameters
    ----------
    b: int or string, optional .

        test
    a :integer
        Test
    c:int
        Test.
    d : int

    """
    pass
'''
    func, docstring, errors, warnings = check_docstring(code, I0103())
    assert len(warnings) == 1
    assert warnings[0].start == Pos(6, 5)


def test_I0103_I0104_correct():
    code = '''
def test(b, aaa: int):
    """
    Parameters
    ----------
    b: int or string, optional .
        test
    a :integer
        Test
    c:int
        Test.
    d : int
    """
    pass
'''
    func, docstring, errors, warnings = check_docstring(code, I0103())
    assert len(warnings) == 0
    func, docstring, errors, warnings = check_docstring(code, I0104())
    assert len(warnings) == 0


def test_I0105_multiple_optional():
    code = '''
def test(b, aaa: int):
    """
    Parameters
    ----------
    b: int or string, optional
        test
    a :integer, optional, optional
        Test
    c:int, optional
        Test.
    d : int
    """
    pass
'''
    func, docstring, errors, warnings = check_docstring(code, I0105())
    assert len(warnings) == 1
    assert warnings[0].start == Pos(8, 5)
