import sys
from argparse import ArgumentParser, FileType

from .numpydoc import Parser
from .validate import _CHECKS, DetailedErrorFormatter, ErrorFormatter, Validator

_ERROR_FORMATTERS = {
    "simple": ErrorFormatter,
    "full": DetailedErrorFormatter,
}


def run() -> None:
    parser = ArgumentParser(prog="numpydoc_lint", description="Lint numpydoc comments")
    parser.add_argument("input", nargs="*", type=FileType("r"), default=[sys.stdin])
    parser.add_argument("--format", choices=["simple", "full"], default="simple")
    parser.add_argument("--ignore", nargs="*")
    parser.add_argument("--print-errors", action="store_true")

    args = parser.parse_args()
    checks = [
        _CHECKS[check]
        for check in _CHECKS.keys()
        if args.ignore is None or check not in args.ignore
    ]
    docstring = Parser(print_errors=args.print_errors)
    error_formatter = _ERROR_FORMATTERS[args.format](args.ignore)
    for input in args.input:
        code = input.read()

        for node in docstring.iter_docstring(code):
            validator = Validator(node, checks=checks)

            for error in validator.validate():
                error_formatter.add_error(input.name, error)

    error_formatter.write(sys.stdout)
