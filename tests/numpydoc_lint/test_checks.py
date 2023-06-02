from dataclasses import dataclass

import pytest
from io import StringIO
from numpydoc_lint.numpydoc import Parser, Pos
from numpydoc_lint.validate import Error, GL01, PR09, PR01


@dataclass
class Expected:
    type: str
    errors: list[Error]
    skip: bool = False


def first_class_or_func(code):
    return list(Parser().iter_docstring(StringIO(code)))[0]


@pytest.fixture
def tester():
    def f(checker, code, expected):
        actual = Parser().iter_docstring(code)
        for actual_docstring, expected_docstring in zip(actual, expected):
            if not expected_docstring.skip:
                actual_errors = list(checker.validate(actual_docstring))
                assert len(expected_docstring.errors) == len(actual_errors)
                for actual_error, expected_error in zip(
                    actual_errors, expected_docstring.errors
                ):
                    assert actual_error.code == expected_error.code
                    assert actual_error.message == expected_error.message
                    assert actual_error.suggestion == expected_error.suggestion
                    assert actual_error.start == expected_error.start
                    assert actual_error.end == expected_error.end

    return f


@pytest.mark.parametrize(
    "code, expected",
    [
        (
            '''
class Test:
    """
    
    This is a summary.
    """
    pass
''',
            [
                Expected(type="module", errors=None, skip=True),
                Expected(
                    type="class",
                    errors=[
                        Error(
                            code="GL01",
                            message="Docstring should start on a new line.",
                            start=Pos(line=3, column=4),
                            end=Pos(line=6, column=7),
                        )
                    ],
                ),
            ],
        )
    ],
)
def test_GL01(code, expected, tester):
    tester(GL01(), code, expected)


def test_PR09_raw_string():
    check = PR09()
    code = r'''
def test(p):
    r"""
    Parameters
    ----------
    p : object\
            test
        Test test test '\n'.
    """
    pass
    '''
    node = first_class_or_func(code)
    docstring, errors = node.parse_docstring()
    error = list(check.validate(node, docstring))
    assert len(error) == 0


def test_PR01():
    code = '''
def test(p):
    """
    Summary.

    Extended.
    Parameters
    ----------
    p : object
        Test.
    x : object
        J.
    """
    pass
'''
    func = first_class_or_func(code)
    error = list(PR01().validate(func))
    print(error)
    assert len(error) == 0
