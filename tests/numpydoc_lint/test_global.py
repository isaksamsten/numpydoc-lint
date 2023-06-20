from common import check_docstring
from numpydoc_lint._model import Pos
from numpydoc_lint.check import (
    I0001,
    I0002,
    I0003,
    I0004,
    W0001,
    I0005,
    I0006,
    I0007,
    I0008,
    I0010,
)


def test_I0001_single_line():
    code = '''
def f():
    """Test"""
    pass
'''
    node, docstring, errors, warnings = check_docstring(code, I0001())
    assert len(warnings) == 0


def test_I0001_multiline_line_without_blank_line():
    code = '''
def f():
    """Test
    
    Extended summary.
    """
    pass
'''
    node, docstring, errors, warnings = check_docstring(code, I0001())
    assert len(warnings) == 1
    assert warnings[0].code == "I0001"
    assert warnings[0].start == Pos(line=3, column=5)
    assert warnings[0].end == Pos(line=3, column=5)


def test_I0001_multiline_correct():
    code = '''
def f():
    """
    Test.
    
    Extended summary.
    """
    pass
'''
    node, docstring, errors, warnings = check_docstring(code, I0001())
    assert len(warnings) == 0


def test_I0002_single_line_no_blank_after():
    code = '''
def f():
    """Summary"""
    pass
'''
    node, docstring, errors, warnings = check_docstring(code, I0002())
    assert len(warnings) == 0


def test_I0002_multiline_no_blank():
    code = '''
def f():
    """Summary

    """
    pass
'''
    node, docstring, errors, warnings = check_docstring(code, I0002())
    assert len(warnings) == 1
    assert warnings[0].code == "I0002"
    assert warnings[0].start == Pos(5, 5)

    node, docstring, errors, warnings = check_docstring(code, I0001())
    assert len(warnings) == 1


def test_I0002_multiline_blank():
    code = '''
def f():
    """
    Summary

    """
    pass
'''
    node, docstring, errors, warnings = check_docstring(code, I0002())
    assert len(warnings) == 1


def test_I0003_multiple_blank_lines():
    code = '''
def f():
    """
    Summary


    Extended summary

    """
    pass
'''
    node, docstring, errors, warnings = check_docstring(code, I0003())
    print(warnings[0])
    assert len(warnings) == 1
    assert warnings[0].code == "I0003"
    assert warnings[0].start == Pos(5, 5)
    assert warnings[0].end == Pos(6, 5)


def test_I0003_single_blank_lines():
    code = '''
def f():
    """
    Summary

    Extended summary

    """
    pass
'''
    node, docstring, errors, warnings = check_docstring(code, I0003())
    assert len(warnings) == 0


def test_I0004_tabs():
    code = '''
def f():
    """
    Summary
		
    """
    pass
'''
    node, docstring, errors, warnings = check_docstring(code, I0004())
    assert len(warnings) == 1
    assert warnings[0].code == "I0004"
    assert warnings[0].start == Pos(5, 1)


def test_I0004_no_tabs():
    code = '''
def f():
    """
    Summary
    """
    pass
'''
    node, docstring, errors, warnings = check_docstring(code, I0004())
    assert len(warnings) == 0


def test_W0001_invalid_section():
    code = '''
def f():
    """
    Invalid
    -------
    The section

    Examples
    --------
    >>> impor test
    """
    pass
'''
    node, docstring, errors, warnings = check_docstring(code, W0001())
    assert len(warnings) == 1
    assert warnings[0].code == "W0001"
    assert warnings[0].start == Pos(4, 5)
    assert warnings[0].end == Pos(4, 5 + len("Invalid"))


def test_I0005_wrong_order():
    code = '''
def f():
    """
    Examples
    --------
    >>> impor test

    Parameters
    ----------
    p
        Test.

    Attributes
    ----------
    o 
        Test.
    """
    pass
'''
    node, docstring, errors, warnings = check_docstring(code, I0005())
    assert len(warnings) == 3
    assert warnings[0].code == "I0005"
    assert warnings[0].start == Pos(4, 5)
    assert warnings[0].end == Pos(4, 5 + len("Examples"))
    assert warnings[1].code == "I0005"
    assert warnings[1].start == Pos(8, 5)
    assert warnings[1].end == Pos(8, 5 + len("Parameters"))
    assert warnings[2].code == "I0005"
    assert warnings[2].start == Pos(13, 5)
    assert warnings[2].end == Pos(13, 5 + len("Attributes"))


def test_I0005_correct_order():
    code = '''
def f():
    """
    Parameters
    ----------
    p
        Test.
    Attributes
    ----------
    o 
        Test.
    """
    pass
'''
    node, docstring, errors, warnings = check_docstring(code, I0005())
    assert len(warnings) == 0
    assert len(errors) == 1  # No blank line
    assert errors[0].code == "E0001"


def test_I0006_deprecation_after_extended_summary():
    code = '''
def f():
    """
    Summary.

    This is an extend summary.

    .. deprecated:: 

    Returns
    -------
    o
        Test.
    """
    pass
'''
    node, docstring, errors, warnings = check_docstring(code, I0006())
    assert len(warnings) == 1
    assert warnings[0].code == "I0006"
    assert warnings[0].start == Pos(8, 5)
    assert warnings[0].end == Pos(8, 5 + len(".. deprecated::"))


def test_I0006_deprecation_before_extended_summary():
    code = '''
def f():
    """
    Summary.

    .. deprecated:: 
    This is an extend summary.

    Returns
    -------
    o
        Test.
    """
    pass
'''
    node, docstring, errors, warnings = check_docstring(code, I0006())
    assert len(warnings) == 0


def test_I0007_multiple_deprecated():
    code = '''
def f():
    """
    Summary.

    .. deprecated:: 
    This is an extend summary.

    .. deprecated:: 

    Returns
    -------
    o
        Test.
    """
    pass
'''
    node, docstring, errors, warnings = check_docstring(code, I0007())
    assert len(warnings) == 1
    assert warnings[0].code == "I0007"
    assert warnings[0].start == Pos(9, 5)
    assert warnings[0].end == Pos(9, 5 + len(".. deprecated::"))


def test_I0007_single_deprecated():
    code = '''
def f():
    """
    Summary.

    This is an extend summary.

    .. deprecated:: 

    Returns
    -------
    o
        Test.
    """
    pass
'''
    node, docstring, errors, warnings = check_docstring(code, I0007())
    assert len(warnings) == 0


def test_I0008_incorrect_reST_directives():
    code = '''
def f():
    """
    Summary.

    This is an extend summary.

    .. deprecated     

    Returns
    -------
    o
        Test.
        .. versionadded
    
    Examples
    --------

    .. versionchanged::

    test
    """
    pass
'''
    node, docstring, errors, warnings = check_docstring(code, I0008())
    assert len(warnings) == 2
    assert warnings[0].code == "I0008"
    assert warnings[0].start == Pos(8, 5)
    assert warnings[0].end == Pos(8, 5 + len(".. deprecated"))
    assert warnings[1].code == "I0008"
    assert warnings[1].start == Pos(14, 9)
    assert warnings[1].end == Pos(14, 9 + len(".. versionadded"))


def test_I0010_no_period_single_line():
    code = '''
def f():
    """Summary"""
    pass
'''
    node, docstring, errors, warnings = check_docstring(code, I0010())
    assert len(warnings) == 1
    assert warnings[0].start == Pos(3, 5)
    assert warnings[0].end == Pos(3, 5 + len("Summary"))
