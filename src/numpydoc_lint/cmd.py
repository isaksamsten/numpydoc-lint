import sys
from argparse import ArgumentParser, FileType

from .numpydoc import DocstringParser
from .validate import Validator, ErrorFormatter


def run() -> None:
    """[TODO:description]."""
    parser = ArgumentParser(prog="numpydoc_lint", description="Lint numpydoc comments")
    parser.add_argument("input", nargs="*", type=FileType("r"), default=[sys.stdin])
    parser.add_argument("--ignore", nargs="*", action="append")
    parser.add_argument("--print-errors", action="store_true")

    args = parser.parse_args()

    docstring = DocstringParser(print_errors=args.print_errors)
    error_formatter = ErrorFormatter()
    for input in args.input:
        code = input.read()

        for node in docstring.iter_docstring(code):
            # print(node.name or "__module__")
            # print("-----")
            # print(node.raw_docstring)
            # print("-----")
            validator = Validator(node)

            for error in validator.validate():
                error_formatter.add_error(input.name, docstring, error)
                # print(f"{error.code}: {error.message} (Line: {error.start.line})")
                # if error.details:
                #     print(error.details)

    error_formatter.write(sys.stdout)
