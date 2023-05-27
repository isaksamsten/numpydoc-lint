import pytest
from numpydoc_lint.numpydoc import Parser


def test_parse_function_parameters():
    code = ''' 
def test(a, *args, b=10, c: int = 2, **kwargs):
    """"""
    pass
    '''
    docstrings = list(Parser().iter_docstring(code))
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
    docstrings = list(Parser().iter_docstring(code))
    klass = docstrings[1]
    parameters = klass.parameters
    assert klass.type == "class"
    assert parameters[0].name == "test"
    assert parameters[0].default == '"10"'
    assert parameters[0].annotation == "str"
