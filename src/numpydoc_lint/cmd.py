"""Command line interface for numpydoc-lint."""
import sys
from pathlib import Path
from argparse import ArgumentParser
from .numpydoc import Parser
from .validate import DetailedErrorFormatter, ErrorFormatter, Validator
from ._config import Config, load_config_from_pyproject

_ERROR_FORMATTERS = {
    "simple": ErrorFormatter,
    "full": DetailedErrorFormatter,
}


def _validate(file, *, parser, config, error_formatter, path=None):
    for node in parser.iter_docstring(file):
        validator = Validator(config)

        for error in validator.validate(node):
            error_formatter.add_error(
                path.name if path is not None else file.name, node, error
            )


def run() -> None:
    parser = ArgumentParser(prog="numpydoc_lint", description="Lint numpydoc comments")
    parser.add_argument("input", nargs="?", default="-")
    parser.add_argument("--format", choices=["simple", "full"], default="simple")
    parser.add_argument("--ignore", nargs="*")
    parser.add_argument("--select", nargs="*")
    parser.add_argument("--exclude", nargs="*")
    parser.add_argument("--include-private", action="store_true", default=None)
    parser.add_argument("--exclude-magic", action="store_true", default=None)
    parser.add_argument("--stdin-filename")
    args = parser.parse_args()

    config = Config(
        ignore=args.ignore,
        select=args.select,
        exclude=args.exclude,
        include_private=args.include_private,
        exclude_magic=args.exclude_magic,
    )
    parser = Parser()
    error_formatter = _ERROR_FORMATTERS[args.format]()
    if args.input == "-":
        if args.stdin_filename is not None:
            path = Path(args.stdin_filename)
        else:
            path = None

        if not config.is_defined and path and path.exists():
            config = load_config_from_pyproject(path)

        if path is None or (path is not None and not config.is_path_excluded(path)):
            _validate(
                sys.stdin,
                parser=parser,
                config=config,
                error_formatter=error_formatter,
                path=path,
            )
    else:
        root = Path(args.input)
        if not root.exists():
            print("Path does not exist.", file=sys.stderr)
            sys.exit(2)

        if not config.is_defined:
            config = load_config_from_pyproject(root)

        if root.is_file() and not config.is_path_excluded(root):
            with root.open("r", encoding="utf-8") as file:
                _validate(
                    file,
                    parser=parser,
                    config=config,
                    error_formatter=error_formatter,
                )
        else:
            for path in root.rglob("*.py"):
                if config.exclude and config.is_path_excluded(path):
                    continue

                with path.open("r", encoding="utf-8") as file:
                    _validate(
                        file,
                        parser=parser,
                        config=config,
                        error_formatter=error_formatter,
                    )
    error_formatter.write(sys.stdout)
    if error_formatter.has_errors:
        print("Found {} errors.".format(error_formatter.errors))
        sys.exit(1)
    else:
        sys.exit(0)
