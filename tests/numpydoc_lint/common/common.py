from numpydoc_lint.numpydoc import Parser
from io import StringIO


def check_docstring(code, check, nth=1):
    node = list(Parser().iter_docstring(StringIO(code)))[nth]
    docstring, errors = node.parse_docstring()
    return node, docstring, errors, list(check.validate(node, docstring))
