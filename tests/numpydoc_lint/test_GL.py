from common import check_docstring
from numpydoc_lint._model import Pos
from numpydoc_lint.check import GL01, GL02, GL03


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
