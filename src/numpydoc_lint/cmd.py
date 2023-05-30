"""Command line interface for numpydoc-lint."""
import tomli
import sys
from pathlib import Path
from argparse import ArgumentParser, FileType
from typing import Optional, List, Mapping
from .numpydoc import Parser
from .validate import _CHECKS, DetailedErrorFormatter, ErrorFormatter, Validator, Check

_ERROR_FORMATTERS = {
    "simple": ErrorFormatter,
    "full": DetailedErrorFormatter,
}


def _get_checks(select, ignore):
    if select is None or select == "all":
        checks = _CHECKS
    else:
        checks = {
            key: value
            for key, value in _CHECKS.items()
            if any(key.startswith(select) for select in select)
        }

    checks = [
        checks[check]
        for check in checks.keys()
        if ignore is None or not any(check.startswith(ignore) for ignore in ignore)
    ]

    return checks


class Config:
    def __init__(
        self,
        ignore: Optional[List[str]] = None,
        select: Optional[List[str]] = None,
        exclude: Optional[List[str]] = None,
        include_private: bool = None,
        exclude_magic: bool = None,
    ) -> None:
        self.ignore = ignore
        self.select = select
        self.exclude = exclude
        self.include_private = include_private
        self.exclude_magic = exclude_magic
        self._checks = None

    def get_checks(self) -> Mapping[str, Check]:
        if self._checks is None:
            self._checks = _get_checks(self.select, self.ignore)
        return self._checks

    @property
    def is_defined(self):
        return (
            self.ignore is not None
            or self.select is not None
            or self.exclude is not None
            or self.include_private is not None
            or self.exclude_magic is not None
        )

    def __repr__(self):
        return str(self.__dict__)


def _config_from_pyproject(file):
    def _find_pyproject(path):
        if path.is_file():
            path = path.parent

        for file in path.iterdir():
            if file.is_file() and file.name == "pyproject.toml":
                return file
        if path == path.parent:
            return None
        else:
            return _find_pyproject(path.parent)

    pyproject = _find_pyproject(Path(file))

    if pyproject is None:
        pyproject = _find_pyproject(Path("."))

    if pyproject:
        cfg = tomli.load(pyproject.open(mode="rb"))
        if "tool" in cfg and "numpydoc-lint" in cfg["tool"]:
            cfg = cfg["tool"]["numpydoc-lint"]
            return Config(
                ignore=cfg.get("ignore", None),
                select=cfg.get("select", None),
                exclude=cfg.get("exclude", None),
                include_private=cfg.get("include-private", None),
                exclude_magic=cfg.get("exclude-magic", None),
            )

    class C(Config):
        @property
        def is_defined(self):
            return True

    return C()


def run() -> None:
    parser = ArgumentParser(prog="numpydoc_lint", description="Lint numpydoc comments")
    parser.add_argument("input", nargs="*", type=FileType("r"), default=[sys.stdin])
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
    docstring = Parser()
    error_formatter = _ERROR_FORMATTERS[args.format]()
    for input in args.input:
        filename = input.name
        if input.name == "<stdin>" and args.stdin_filename is not None:
            filename = args.stdin_filename

        if not config.is_defined:
            config = _config_from_pyproject(filename)

        if config.exclude and filename in config.exclude:
            continue

        for node in docstring.iter_docstring(input.read()):
            validator = Validator(
                node,
                include_private=config.include_private,
                exclude_magic=config.exclude_magic,
                checks=config.get_checks(),
            )

            for error in validator.validate():
                error_formatter.add_error(filename, error)

    error_formatter.write(sys.stdout)
    if error_formatter.has_errors:
        print("Found {} errors.".format(error_formatter.errors))
        sys.exit(1)
    else:
        sys.exit(0)
