from common import check_docstring
from numpydoc_lint._model import Pos
from numpydoc_lint.check import GL01, GL02, GL03, GL05, GL06, GL07, GL09, GLE01, GL10


def test_GL01_single_line():
    code = '''
def f():
    """Test"""
    pass
'''
    node, docstring, errors, warnings = check_docstring(code, GL01())
    assert len(warnings) == 0


def test_GL01_multiline_line_without_blank_line():
    code = '''
def f():
    """Test
    
    Extended summary.
    """
    pass
'''
    node, docstring, errors, warnings = check_docstring(code, GL01())
    assert len(warnings) == 1
    assert warnings[0].code == "GL01"
    assert warnings[0].start == Pos(line=2, column=5)
    assert warnings[0].end == Pos(line=2, column=6)


def test_GL02_single_line_no_blank_after():
    code = '''
def f():
    """Summary"""
    pass
'''
    node, docstring, errors, warnings = check_docstring(code, GL02())
    assert len(warnings) == 0


def test_GL02_multiline_no_blank():
    code = '''
def f():
    """Summary
    """
    pass
'''
    node, docstring, errors, warnings = check_docstring(code, GL02())
    assert len(warnings) == 1
    assert warnings[0].code == "GL02"
    assert warnings[0].start == Pos(2, 5)

    node, docstring, errors, warnings = check_docstring(code, GL01())
    assert len(warnings) == 1


def test_GL02_multiline_blank():
    code = '''
def f():
    """
    Summary

    """
    pass
'''
    node, docstring, errors, warnings = check_docstring(code, GL02())
    assert len(warnings) == 0


def test_GL03_multiple_blank_lines():
    code = '''
def f():
    """
    Summary


    Extended summary

    """
    pass
'''
    node, docstring, errors, warnings = check_docstring(code, GL03())
    assert len(warnings) == 1
    assert warnings[0].code == "GL03"
    assert warnings[0].start == Pos(2, 5)


def test_GL03_single_blank_lines():
    code = '''
def f():
    """
    Summary

    Extended summary

    """
    pass
'''
    node, docstring, errors, warnings = check_docstring(code, GL03())
    assert len(warnings) == 0


def test_GL05_tabs():
    code = '''
def f():
    """
    Summary
		
    """
    pass
'''
    node, docstring, errors, warnings = check_docstring(code, GL05())
    assert len(warnings) == 1
    assert warnings[0].code == "GL05"
    assert warnings[0].start == Pos(5, 1)


def test_GL05_no_tabs():
    code = '''
def f():
    """
    Summary
    """
    pass
'''
    node, docstring, errors, warnings = check_docstring(code, GL05())
    assert len(warnings) == 0


def test_GL06_invalid_section():
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
    node, docstring, errors, warnings = check_docstring(code, GL06())
    assert len(warnings) == 1
    assert warnings[0].code == "GL06"
    assert warnings[0].start == Pos(4, 5)
    assert warnings[0].end == Pos(4, 5 + len("Invalid"))


def test_GL07_wrong_order():
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
    node, docstring, errors, warnings = check_docstring(code, GL07())
    assert len(warnings) == 3
    assert warnings[0].code == "GL07"
    assert warnings[0].start == Pos(4, 5)
    assert warnings[0].end == Pos(4, 5 + len("Examples"))
    assert warnings[1].code == "GL07"
    assert warnings[1].start == Pos(8, 5)
    assert warnings[1].end == Pos(8, 5 + len("Parameters"))
    assert warnings[2].code == "GL07"
    assert warnings[2].start == Pos(13, 5)
    assert warnings[2].end == Pos(13, 5 + len("Attributes"))


def test_GL07_correct_order():
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
    node, docstring, errors, warnings = check_docstring(code, GL07())
    assert len(warnings) == 0
    assert len(errors) == 1  # No blank line
    assert errors[0].code == "ER01"


def test_GL09_deprecation_after_extended_summary():
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
    node, docstring, errors, warnings = check_docstring(code, GL09())
    assert len(warnings) == 1
    assert warnings[0].code == "GL09"
    assert warnings[0].start == Pos(8, 5)
    assert warnings[0].end == Pos(8, 5 + len(".. deprecated::"))


def test_GL09_deprecation_before_extended_summary():
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
    node, docstring, errors, warnings = check_docstring(code, GL09())
    assert len(warnings) == 0


def test_GLE01_multiple_deprecated():
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
    node, docstring, errors, warnings = check_docstring(code, GLE01())
    assert len(warnings) == 1
    assert warnings[0].code == "GLE01"
    assert warnings[0].start == Pos(9, 5)
    assert warnings[0].end == Pos(9, 5 + len(".. deprecated::"))


def test_GLE01_single_deprecated():
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
    node, docstring, errors, warnings = check_docstring(code, GLE01())
    assert len(warnings) == 0


def test_GL10_incorrect_reST_directives():
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
    node, docstring, errors, warnings = check_docstring(code, GL10())
    assert len(warnings) == 2
    assert warnings[0].code == "GL10"
    assert warnings[0].start == Pos(8, 5)
    assert warnings[0].end == Pos(8, 5 + len(".. deprecated"))
    assert warnings[1].code == "GL10"
    assert warnings[1].start == Pos(14, 9)
    assert warnings[1].end == Pos(14, 9 + len(".. versionadded"))
