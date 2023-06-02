import pytest
from io import StringIO
from numpydoc_lint.numpydoc import Parser


def parse_code(code):
    return list(Parser().iter_docstring(StringIO(code)))


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


def test_parse_parameter_list():
    code = '''
def t(x):
    """
    Header.
    
    Extended.

    Parameters
    ----------
    x : object
        Test.
    y : object
        J.
    """
'''
    docstrings = parse_code(code)
    func = docstrings[1].docstring_node
    print(func.sections)
    # assert func.summary.content.data == ["    Header."]
    # assert func.summary.extended_content.data == ["    Extended."]
    # assert func.sections.get("Parameters") is not None
