"""Command line interface for numpydoc-lint."""
import tomli
from pathlib import Path
from typing import Optional, List, Mapping
from .check._base import Check
from .check import __dict__ as CHECKS, __all__ as ALL_CHECKS

# from .check import (
#     ES01,
#     GL01,
#     GL02,
#     GL03,
#     GL05,
#     GL06,
#     GL07,
#     GL09,
#     GL10,
#     GLE01,
#     PR01,
#     PR02,
#     PR03,
#     PR04,
#     PR05,
#     PR06,
#     PR07,
#     PR08,
#     PR09,
#     PR10,
#     PRE01,
#     PRE02,
#     PRE03,
#     RT01,
#     RT02,
#     RT03,
#     RT04,
#     RT05,
#     SS01,
#     SS02,
#     SS03,
#     SS04,
#     SS05,
#     SS06,
#     YD01,
# )
#
# CHECKS = OrderedDict(
#     GL01=GL01(),
#     GL02=GL02(),
#     GL03=GL03(),
#     GL05=GL05(),
#     GL06=GL06(),
#     GL07=GL07(),
#     GL09=GL09(),
#     GL10=GL10(),
#     GLE01=GLE01(),
#     SS01=SS01(),
#     SS02=SS02(),
#     SS03=SS03(),
#     SS04=SS04(),
#     SS05=SS05(),
#     SS06=SS06(),
#     ES01=ES01(),
#     PR01=PR01(),
#     PR02=PR02(),
#     PR03=PR03(),
#     PR04=PR04(),
#     PR05=PR05(),
#     PR06=PR06(),
#     PR07=PR07(),
#     PR08=PR08(),
#     PR09=PR09(),
#     PR10=PR10(),
#     PRE01=PRE01(),
#     PRE02=PRE02(),
#     PRE03=PRE03(),
#     RT01=RT01(),
#     RT02=RT02(),
#     RT03=RT03(),
#     RT04=RT04(),
#     RT05=RT05(),
#     YD01=YD01(),
# )

ERROR_CODES = [
    # Errors
    "ER01",
    "ER02",
    "ER03",
    "ER04",
    "ER05",
    "ER06",
    # Checks
    "GL01",
    "GL02",
    "GL03",
    "GL05",
    "GL06",
    "GL07",
    "GL09",
    "GL10",
    "GLE0",
    "SS01",
    "SS02",
    "SS03",
    "SS04",
    "SS05",
    "SS06",
    "ES01",
    "PR01",
    "PR02",
    "PR03",
    "PR04",
    "PR05",
    "PR06",
    "PR07",
    "PR08",
    "PR09",
    "PR10",
    "PRE0",
    "PRE0",
    "PRE0",
    "RT01",
    "RT02",
    "RT03",
    "RT04",
    "RT05",
    "YD01",
]


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
        if self.select is None:
            return [CHECKS[s]() for s in ALL_CHECKS]
        else:
            return [
                CHECKS[name]()
                for name in ALL_CHECKS
                if not self.is_error_ignored(name) and self.is_selected(name)
            ]

    def is_error_ignored(self, code):
        return (
            self.ignore is not None and code in self.ignore
        ) or not self.is_selected(code)

    def is_path_excluded(self, path: Path):
        """
        Determine if a path is excluded.

        Parameters
        ----------
        path : Path
            The path.

        """
        return self.exclude is not None and any(
            path.match(exclude) for exclude in self.exclude
        )

    def is_node_excluded(self, node):
        if not self.include_private and node.is_private:
            return True

        if self.exclude_magic and node.is_magic:
            return True

        return False

    def is_selected(self, code):
        return self.select is None or any(
            code.startswith(selected) for selected in self.select
        )

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


def load_config_from_pyproject(file: Path):
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
