import io
import re
from collections import OrderedDict, defaultdict
from typing import Generator, Iterable, List, Mapping

from .check import (
    ES01,
    GL01,
    GL02,
    GL03,
    GL04,
    GL06,
    GL07,
    GL08,
    GL09,
    GL10,
    GLE01,
    PR01,
    PR02,
    PR03,
    PR04,
    PR05,
    PR06,
    PR07,
    PR08,
    PR09,
    PR10,
    PRE01,
    PRE02,
    PRE03,
    RT01,
    RT02,
    RT03,
    RT04,
    RT05,
    SS01,
    SS02,
    SS03,
    SS04,
    SS05,
    SS06,
    YD01,
)
from .check._base import Check, Error
from .numpydoc import (
    Node,
)

_CHECKS = OrderedDict(
    GL08=GL08(),  # Terminates if fails
    GL01=GL01(),
    GL02=GL02(),
    GL03=GL03(),
    GL04=GL04(),
    GL06=GL06(),
    GL07=GL07(),
    GL09=GL09(),
    GL10=GL10(),
    GLE01=GLE01(),
    SS01=SS01(),
    SS02=SS02(),
    SS03=SS03(),
    SS04=SS04(),
    SS05=SS05(),
    SS06=SS06(),
    ES01=ES01(),
    PR01=PR01(),
    PR02=PR02(),
    PR03=PR03(),
    PR04=PR04(),
    PR05=PR05(),
    PR06=PR06(),
    PR07=PR07(),
    PR08=PR08(),
    PR09=PR09(),
    PR10=PR10(),
    PRE01=PRE01(),
    PRE02=PRE02(),
    PRE03=PRE03(),
    RT01=RT01(),
    RT02=RT02(),
    RT03=RT03(),
    RT04=RT04(),
    RT05=RT05(),
    YD01=YD01(),
)


class Validator:
    def __init__(
        self,
        node: Node,
        *,
        include_private=False,
        exclude_magic=False,
        checks: List[Check] = None
    ) -> None:
        self.node = node
        self.include_private = include_private
        self.exclude_magic = exclude_magic
        self.checks = checks

    def validate(self) -> Generator[Error, None, None]:
        self._is_validated = True

        if not self.include_private and self.node.private:
            return

        if self.exclude_magic and self.node.magic:
            return

        for check in self.checks:
            if check.__class__.__name__ not in self.node.noqa:
                for error in check.validate(self.node):
                    yield error
                    if error.terminate:
                        return


class ErrorFormatter:
    def __init__(self):
        self._errors: Mapping[str, Iterable[Error]] = defaultdict(list)

    def add_error(self, file: str, error: Error) -> None:
        self._errors[file].append(error)

    def _format_error(self, file: str, error: Error):
        return "{}:{}:{}:{}:{}: {} {}\n".format(
            file,
            error.start.line,
            error.start.column,
            error.end.line,
            error.end.column,
            error.code,
            error.message,
        )

    def write(self, output: io.TextIOBase) -> None:
        for file, errors in self._errors.items():
            for error in errors:
                output.write(self._format_error(file, error))

    @property
    def has_errors(self):
        return len(self._errors) > 0

    @property
    def errors(self):
        return sum(len(errors) for errors in self._errors.values())


class DetailedErrorFormatter(ErrorFormatter):
    def _format_error(self, file: str, error: Error) -> str:
        line = str(error.start.line)
        docstring = error.docstring
        if docstring:
            error_start = error.start.normalize(docstring.start)
            offending_lines = []

            for i in range(max(0, error_start.line - 2), error_start.line + 1):
                if i == 0 and re.match("^\s*$", docstring.lines[i]):
                    continue

                offending_lines.append(
                    "{} | {}\n".format(
                        docstring.start.line + i,
                        docstring.lines[i],
                        # if i > 0
                        # else (" " * docstring.start.column) + '"""',  # FIXME!
                    )
                )
            offending_line = "".join(offending_lines)

            line_pad = (" " * len(line)) + " | " + (" " * (error.start.column - 1))
            underline_len = error.end.column - error.start.column
            if underline_len == 0:
                underline_len = 1
            underline = line_pad + ("^" * underline_len)
            if error.suggestion:
                line_mark = line_pad + (" " * (underline_len - 1)) + "|\n"
                suggestion = (
                    "\n"
                    + line_mark
                    + line_pad
                    + (" " * (underline_len - 1))
                    + error.suggestion
                )
            else:
                suggestion = ""

            return "error[{}]: {}\n{}:{}:{}\n{}{}{}\n".format(
                error.code,
                error.message,
                (" " * len(line)) + "--> " + file,
                error.start.line,
                error.start.column,
                offending_line,
                underline,
                suggestion,
            )
        else:
            return super()._format_error(file, error)
