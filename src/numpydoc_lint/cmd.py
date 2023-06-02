"""Command line interface for numpydoc-lint."""
import tomli
import sys
from pathlib import Path
from argparse import ArgumentParser
from typing import Optional, List, Mapping
from .numpydoc import Parser
from .validate import _CHECKS, DetailedErrorFormatter, ErrorFormatter, Validator, Check

_ERROR_FORMATTERS = {
    "simple": ErrorFormatter,
    "full": DetailedErrorFormatter,
}


def _get_checks(select, ignore):
    if select is None or "all" in select:
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


def _config_from_pyproject(file: Path):
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

    pyproject = _find_pyproject(file)

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


def _validate(file, *, parser, config, error_formatter, filename=None):
    for node in parser.iter_docstring(file):
        validator = Validator(
            include_private=config.include_private,
            exclude_magic=config.exclude_magic,
            checks=config.get_checks(),
        )

        for error in validator.validate(node):
            error_formatter.add_error(
                filename if filename is not None else file.name, node, error
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
            filename = Path(args.stdin_filename)
        else:
            filename = None

        if not config.is_defined and filename and filename.exists():
            config = _config_from_pyproject(filename)

        _validate(
            sys.stdin,
            parser=parser,
            config=config,
            error_formatter=error_formatter,
        )
    else:
        root = Path(args.input)
        if not root.exists():
            print("Path does not exist.", file=sys.stderr)
            sys.exit(2)

        if not config.is_defined:
            config = _config_from_pyproject(root)

        print(config)
        if root.is_file():
            with root.open("r", encoding="utf-8") as file:
                _validate(
                    file,
                    parser=parser,
                    config=config,
                    error_formatter=error_formatter,
                )
        else:
            for path in root.rglob("*.py"):
                if config.exclude and filename in config.exclude:
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
