import re
from abc import ABCMeta, abstractmethod
from typing import Generator, List, Optional

from ..numpydoc import (
    DocString,
    DocStringParameter,
    Node,
)
from .._model import Error

DIRECTIVES = ["versionadded", "versionchanged", "deprecated"]
DIRECTIVE_PATTERN = re.compile(
    r"^\s*\.\. ({})(?!::)".format("|".join(DIRECTIVES)), re.I
)


class Check(metaclass=ABCMeta):
    """Abstract docstring check."""

    @abstractmethod
    def _validate(
        self, doc: Node, docstring: DocString
    ) -> Generator[Error, None, None]:
        return
        yield

    def validate(self, doc: Node, docstring: DocString) -> Generator[Error, None, None]:
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
            yield from self._validate(doc, docstring)


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


def first_non_blank(lines: List[str]) -> Optional[str]:
    for line in lines:
        if not line.strip():
            return line
    return None
