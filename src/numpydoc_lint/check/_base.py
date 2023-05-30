import re
from abc import ABCMeta, abstractmethod
from typing import Generator, List

from ..numpydoc import (
    DocString,
    DocStringParameter,
    Node,
    Pos,
)

DIRECTIVES = ["versionadded", "versionchanged", "deprecated"]
DIRECTIVE_PATTERN = re.compile(
    r"^\s*\.\. ({})(?!::)".format("|".join(DIRECTIVES)), re.I
)


class Error:
    def __init__(
        self,
        *,
        docstring: DocString,
        start: Pos = None,
        end: Pos = None,
        code: str = None,
        message: str = None,
        suggestion: str = None,
        terminate: str = False,
    ) -> None:
        self.docstring = docstring
        self.start = start if start is not None else docstring.start
        self.end = end if end is not None else docstring.end
        self._code = code
        self._message = message
        self._suggestion = suggestion
        self._terminate = terminate

    @property
    def code(self):
        return self._code if self._code is not None else self.__class__.__name__.upper()

    @property
    def message(self):
        return self._message

    @property
    def suggestion(self):
        return self._suggestion

    @property
    def terminate(self) -> bool:
        """
        If the error terminates the remaining checks.

        Returns
        -------
        bool
            `True` if the remaining checks should be skipped; `False`
            otherwise.
        """
        return self._terminate


class Check(metaclass=ABCMeta):
    """Abstract docstring check."""

    @abstractmethod
    def _validate(self, doc: Node) -> Generator[Error, None, None]:
        return
        yield

    def validate(self, doc: Node) -> Generator[Error, None, None]:
        """
        Ensure that the docstring is valid.

        Parameters
        ----------
        doc : Docstring
            The docstring to validate.

        Yields
        ------
        Error
            The error.
        """
        if doc.has_docstring:
            yield from self._validate(doc)


def _before_directive(lines: List[str]) -> List[str]:
    new_lines = []
    for line in lines:
        if any(f".. {directive}" in line for directive in DIRECTIVES):
            return new_lines

        if line.strip():
            new_lines.append(line)

    return new_lines


# TODO: Improve placement of error message
def _validate_parameter_has_description(
    *,
    docstring: DocString,
    parameter: DocStringParameter,
    code: str,
    message: str,
    suggestion: str,
) -> Generator[Error, None, None]:
    if not parameter.description.data or all(
        line.strip() == "" for line in _before_directive(parameter.description.data)
    ):
        name = parameter.name if parameter.name is not None else parameter.types[0]
        yield Error(
            docstring=docstring,
            start=name.start,
            end=name.end,
            code=code,
            message=message,
            suggestion=suggestion,
        )


# TODO: Improve placement of error message
def _validate_parameter_description_start_uppercase(
    *,
    docstring: DocString,
    parameter: DocStringParameter,
    code: str,
    message: str,
    suggestion: str,
) -> Generator[Error, None, None]:
    data = _before_directive(parameter.description.data)
    if data:
        first = data[0].lstrip()
        if first and first[0].isalpha() and not first[0].isupper():
            name = parameter.name if parameter.name is not None else parameter.types[0]
            yield Error(
                docstring=docstring,
                start=name.start,
                end=name.end,
                code=code,
                message=message,
                suggestion=suggestion,
            )


# TODO: Improve placement of error message
def _validate_parameter_description_ends_period(
    *,
    docstring: DocString,
    parameter: DocStringParameter,
    code: str,
    message: str,
    suggestion: str,
) -> Generator[Error, None, None]:
    data = _before_directive(parameter.description.data)
    if data:
        last = data[-1]
        if last:
            match = re.match("^(\s*)", last)
            indent = 0
            if match:
                start, end = match.span(1)
                indent = end - start

            if (
                last[-1] != "."
                and not last.startswith(("*", "- "))
                and indent <= docstring.indent  # code-blocks
            ):
                name = (
                    parameter.name if parameter.name is not None else parameter.types[0]
                )
                yield Error(
                    docstring=docstring,
                    start=name.start,
                    end=name.end,
                    code=code,
                    message=message,
                    suggestion=suggestion,
                )


def empty_prefix_lines(lines: List[str]):
    i = None
    for i, row in enumerate(lines):
        if row.strip():
            break
    return i


def empty_suffix_lines(lines: List[str]):
    i = None
    for i, row in enumerate(reversed(lines)):
        if row.strip():
            break
    return i
