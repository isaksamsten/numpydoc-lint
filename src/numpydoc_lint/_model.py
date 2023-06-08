from dataclasses import dataclass

from typing import List, Mapping


@dataclass
class Pos:
    """Represent a Line:Column position."""

    line: int
    column: int

    def move_line(self, *, line=None, column=None):
        return Pos(
            self.line + line if line is not None else self.line,
            column if column is not None else self.column,
        )

    def move_column(self, *, line=None, column=None):
        return Pos(
            line if line is not None else self.line,
            self.column + column if column is not None else self.column,
        )

    def move(self, *, line=None, column=None, absolute_line=None, absolute_column=None):
        if line is not None:
            line = self.line + line
        elif absolute_line is not None:
            line = absolute_line
        else:
            line = self.line

        if column is not None:
            column = self.column + column
        elif absolute_column is not None:
            column = absolute_column
        else:
            column = self.column
        return Pos(line, column)

    def normalize(self, relative: "Pos"):
        return Pos(
            line=self.line - relative.line,
            column=self.column,
        )


@dataclass(frozen=True, kw_only=True)
class DocStringParagraph:
    start: Pos
    end: Pos
    data: list[str]


@dataclass(frozen=True, kw_only=True)
class DocStringSummary:
    content: DocStringParagraph
    extended_content: DocStringParagraph


@dataclass(frozen=True, kw_only=True)
class DocStringName:
    start: Pos
    end: Pos
    value: str

    def __len__(self):
        return len(self.value)


@dataclass(frozen=True, kw_only=True)
class DocStringParameter:
    start: Pos
    end: Pos
    header: str
    name: DocStringName
    types: DocStringName
    optional: int
    description: DocStringParagraph


@dataclass(frozen=True, kw_only=True)
class DocStringParameters:
    header: str
    parameters: List[DocStringParameter]


@dataclass(frozen=True, kw_only=True)
class DocStringSection:
    name: DocStringName
    valid_heading: bool
    contents: List[str | DocStringParameter]
    start_contents: Pos
    end_contents: Pos


@dataclass(frozen=True, kw_only=True)
class Parameter:
    start: Pos
    end: Pos
    name: str
    default: str = None  # For future --fix
    annotation: str = None
    star_count: int

    @property
    def iskwargs(self):
        return self.star_count == 2

    @property
    def isargs(self):
        return self.star_count == 1


@dataclass(frozen=True, kw_only=True)
class Name:
    value: str
    start: Pos
    end: Pos


@dataclass(frozen=True, kw_only=True)
class DocString:
    start: Pos
    end: Pos
    indent: int
    summary: DocStringSummary
    sections: Mapping[str, DocStringSection]
    raw: str
    lines: List[str]


class Error:
    def __init__(
        self,
        *,
        start: Pos = None,
        end: Pos = None,
        code: str = None,
        message: str = None,
        suggestion: str = None,
    ) -> None:
        if start is None:
            raise ValueError()
        self.start = start
        self.end = end if end is not None else start
        self._code = code
        self._message = message
        self._suggestion = suggestion

    @property
    def code(self):
        return self._code if self._code is not None else self.__class__.__name__.upper()

    @property
    def message(self):
        return self._message

    @property
    def suggestion(self):
        return self._suggestion

    def __repr__(self):
        return str(self.__dict__)
