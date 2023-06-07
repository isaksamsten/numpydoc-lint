import pytest
from io import StringIO
from numpydoc_lint.numpydoc import Parser
from numpydoc_lint._model import Pos


def parse_code(code):
    return list(Parser().iter_docstring(StringIO(code)))


def parse_docstring(code, nth=1):
    return parse_code(code)[nth].parse_docstring()


def test_parse_function_parameters():
    code = ''' 
def test(a, *args, b=10, c: int = 2, **kwargs):
    """"""
    pass
    '''
    docstrings = parse_code(code)
    function = docstrings[1]
    assert function.type == "function"

    names = ["a", "args", "b", "c", "kwargs"]
    default = [None, None, "10", "2", None]
    annotation = [None, None, None, "int", None]
    assert names == [parameter.name for parameter in function.parameters]
    assert default == [parameter.default for parameter in function.parameters]
    assert annotation == [parameter.annotation for parameter in function.parameters]
    assert 1 == function.parameters[1].star_count
    assert 2 == function.parameters[-1].star_count


def test_parse_class():
    code = """
class Test:
    def test():
        pass
    a: int
    b: str

    def __init__(self, test: str = "10"):
        pass
"""
    docstrings = parse_code(code)
    klass = docstrings[1]
    parameters = klass.parameters
    assert klass.type == "class"
    assert parameters[0].name == "test"
    assert parameters[0].default == '"10"'
    assert parameters[0].annotation == "str"


def test_parse_function_parameters():
    code = '''
def t(x):
    """Parameters
    ----------
    x : object
        Test.
    y : int, optional
        J.
    z
        F.
    """
'''

    func, errors = parse_docstring(code)
    assert len(errors) == 0
    parameters = func.sections.get("Parameters")
    assert parameters is not None

    assert parameters.name.start.line == 3
    assert parameters.name.end.column == 4 + len("Parameters") + 1
    assert parameters.name.value == "Parameters"
    assert parameters.contents[0].name.value == "x"
    assert parameters.contents[0].types[0].value == "object"
    assert parameters.contents[1].name.value == "y"
    assert parameters.contents[1].types[0].value == "int"
    assert parameters.contents[1].optional == 1
    assert parameters.contents[2].name.value == "z"
    assert parameters.contents[2].types == None


def test_error_unless_blank_line_before_section():
    code = '''
def f():
    """
    Summary.

    Extended summary.
    Parameters
    ----------
    x
        Test.
    Returns
    -------
    bool
        Test.
    """
    pass
'''
    func, errors = parse_docstring(code, nth=1)  # F
    assert len(errors) == 2
    assert errors[0].code == "ER01"
    assert errors[0].start.line == 7
    assert errors[1].code == "ER01"
    assert errors[1].start.line == 11


def test_parse_empty_summary_extended_summary():
    code = '''
def f():
    """

    Parameters
    ----------
    a : obj
        Test
    """
'''
    doc, errors = parse_docstring(code, nth=1)
    assert len(errors) == 0
    assert doc.summary == None
