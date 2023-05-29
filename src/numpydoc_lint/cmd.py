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
    parser.add_argument("--select", nargs="*")
    parser.add_argument("--exclude", nargs="*")
    parser.add_argument("--include-private", action="store_true")
    parser.add_argument("--exclude-magic", action="store_true")
    args = parser.parse_args()

    if args.select is None or args.select == "all":
        checks = _CHECKS
    else:
        checks = {
            key: value
            for key, value in _CHECKS.items()
            if any(key.startswith(select) for select in args.select)
        }

    checks = [
        checks[check]
        for check in checks.keys()
        if args.ignore is None
        or not any(check.startswith(ignore) for ignore in args.ignore)
    ]
    docstring = Parser()
    error_formatter = _ERROR_FORMATTERS[args.format]()
    for input in args.input:
        if args.exclude and input.name in args.exclude:
            continue
        code = input.read()

        for node in docstring.iter_docstring(code):
            validator = Validator(
                node,
                include_private=args.include_private,
                exclude_magic=args.exclude_magic,
                checks=checks,
            )

            for error in validator.validate():
                error_formatter.add_error(input.name, error)

    error_formatter.write(sys.stdout)
    if error_formatter.has_errors:
        sys.exit(1)
    else:
        sys.exit(0)
