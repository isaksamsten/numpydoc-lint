import sys
from argparse import ArgumentParser, FileType

from .numpydoc import Parser
from .validate import Validator, ErrorFormatter, DetailedErrorFormatter

_ERROR_FORMATTERS = {
    "default": ErrorFormatter,
    "detailed": DetailedErrorFormatter,
}


def run() -> None:
    """[TODO:description]."""
    parser = ArgumentParser(prog="numpydoc_lint", description="Lint numpydoc comments")
    parser.add_argument("input", nargs="*", type=FileType("r"), default=[sys.stdin])
    parser.add_argument("--format", choices=["default", "detailed"], default="default")
    parser.add_argument("--ignore", nargs="*", action="append")
    parser.add_argument("--print-errors", action="store_true")

    args = parser.parse_args()

    print(args)
    docstring = Parser(print_errors=args.print_errors)
    error_formatter = _ERROR_FORMATTERS[args.format]()
    for input in args.input:
        code = input.read()

        for node in docstring.iter_docstring(code):
            # print(node.name or "__module__")
            # print("-----")
            # print(node.raw_docstring)
            # print("-----")
            validator = Validator(node)

            for error in validator.validate():
                error_formatter.add_error(input.name, error)
                # print(f"{error.code}: {error.message} (Line: {error.start.line})")
                # if error.details:
                #     print(error.details)

    error_formatter.write(sys.stdout)
