import itertools
import re
from typing import Generator, Optional

from ..numpydoc import (
    DocStringParagraph,
    Node,
)
from ._base import Check, Error, empty_prefix_lines, empty_suffix_lines

_ALLOWED_SECTIONS = [
    "Parameters",
    "Attributes",
    "Methods",
    "Returns",
    "Yields",
    "Other Parameters",
    "Raises",
    "Warns",
    "Warnings",
    "See Also",
    "Notes",
    "References",
    "Examples",
]

DIRECTIVES = ["versionadded", "versionchanged", "deprecated"]
DIRECTIVE_PATTERN = re.compile(
    r"^\s*\.\. ({})(?!::)".format("|".join(DIRECTIVES)), re.I
)


def _find_deprectated(paragraph: DocStringParagraph):
    if paragraph:
        for i, line in enumerate(paragraph.data):
            if ".. deprecated:: " in line:
                yield paragraph.start.move(line=i)


class GL01(Check):
    """Check for too many/few empty prefix lines."""

    def _validate(self, node: Node) -> Generator[Error, None, None]:
        doc = node.docstring
        if (
            node.has_docstring
            and empty_prefix_lines(doc.lines) != 1
            and "\n" in doc.raw
        ):
            yield Error(
                docstring=doc,
                start=doc.start,
                code="GL01",
                message="Docstring should start on a new line.",
            )


# TODO: Incorrectly flagged if docstring start on the same line as """.
class GL02(Check):
    def _validate(self, node: Node) -> Generator[Error, None, None]:
        doc = node.docstring
        if empty_suffix_lines(doc.lines) != 1 and "\n" in doc.raw:
            yield Error(
                start=doc.end.move_line(line=-1),
                docstring=doc,
                code="GL02",
                message="Docstring should end one line before the closing quotes.",
                suggestion="Remove empty line.",
            )


class GL03(Check):
    def _validate(self, node: Node) -> Generator[Error, None, None]:
        doc = node.docstring
        prev = True
        for i, row in enumerate(doc.lines):
            if not prev and not row.strip() and i < len(doc.lines) - 1:
                yield Error(
                    start=doc.start.move_line(line=i),
                    docstring=doc,
                    code="GL03",
                    message="Docstring should not contain double line breaks.",
                )
            prev = row.strip()
        return None


class GL04(Check):
    def _validate(self, node: Node) -> Optional[Error]:
        doc = node.docstring
        for i, line in enumerate(doc.lines):
            first = next(re.finditer("^\s*(\t)", line), None)
            if first:
                yield Error(
                    start=doc.start.move_line(line=i, column=first.start(0)),
                    end=doc.start.move_line(line=i, column=first.end(0)),
                    docstring=doc,
                    code="GL04",
                    message="Docstring line should not start with tabs.",
                )


class GL06(Check):
    def _validate(self, node: Node) -> Generator[Error, None, None]:
        doc = node.docstring
        for section in doc.sections:
            if section.name not in _ALLOWED_SECTIONS:
                yield Error(
                    docstring=doc,
                    start=section.start_header,
                    end=section.end_header,
                    code="GL06",
                    message="Docstring contains unexpected section.",
                    suggestion="Remove section or fix spelling.",
                )


class GL07(Check):
    def _validate(self, node: Node) -> Generator[Error, None, None]:
        doc = node.docstring
        expected_sections = [
            section for section in _ALLOWED_SECTIONS if section in doc.sections
        ]
        actual_sections = [
            section for section in doc.sections if section.name in _ALLOWED_SECTIONS
        ]
        for expected_section, actual_section in zip(expected_sections, actual_sections):
            if expected_section != actual_section.name:
                yield Error(
                    docstring=doc,
                    start=actual_section.start_header,
                    end=actual_section.end_header,
                    code="GL07",
                    message="Sections are in the wrong order.",
                    suggestion=f"Section should be `{expected_section}`",
                )


class GL08(Check):
    """Check that the class/function/module has a docstring."""

    def _validate(self, node: Node) -> Generator[Error, None, None]:
        return
        yield

    def validate(self, node: Node) -> Generator[Error, None, None]:
        if not node.has_docstring:
            yield Error(
                start=node.start,
                end=node.end,
                docstring=None,
                code="GL08",
                message=f"The {node.type} does not have a docstring",
                terminate=True,
            )


class GL09(Check):
    def _validate(self, node: Node) -> Generator[Error, None, None]:
        doc = node.docstring
        if doc.summary:
            deprecated_markers = list(
                itertools.chain(
                    _find_deprectated(doc.summary.content),
                    _find_deprectated(doc.summary.extended_content),
                )
            )

            if deprecated_markers:
                paragraph = (
                    doc.summary.extended_content
                    if doc.summary.extended_content is not None
                    else doc.summary
                )
                if deprecated_markers[0].line != paragraph.start.line:
                    yield Error(
                        docstring=doc,
                        start=deprecated_markers[0],
                        end=deprecated_markers[0].move(column=15),
                        code="GL09",
                        message="Deprecation warning should precede extended summary.",
                        suggestion=(
                            f"Move deprecation warning to line {paragraph.start.line}"
                        ),
                    )


# TODO: Extended
class GLE01(Check):
    def _validate(self, node: Node) -> Generator[Error, None, None]:
        doc = node.docstring
        if doc.summary:
            marks = list(
                itertools.chain(
                    _find_deprectated(doc.summary.content),
                    _find_deprectated(doc.summary.extended_content),
                )
            )
            if len(marks) > 1:
                paragraph = (
                    doc.summary.extended_content
                    if doc.summary.extended_content is not None
                    else doc.summary
                )
                offenders = [
                    mark for mark in marks if mark.line != paragraph.start.line
                ]
                # TODO: improve suggestion if there is no correct deprecation warning.
                if len(offenders) == 1:
                    where = f"line {offenders[0].line}"
                else:
                    offending_lines = ", ".join(
                        str(offender.line) for offender in offenders[:-1]
                    )
                    where = f"lines {offending_lines} and {offenders[-1].line}"

                for mark in offenders:
                    yield Error(
                        docstring=doc,
                        start=mark,
                        end=mark.move(column=15),
                        code="GL11",
                        message=(
                            "Summary should only contain a single deprecation "
                            "warning."
                        ),
                        suggestion=(
                            f"Remove duplicate deprecation warnings on {where}"
                        ),
                    )


class GL10(Check):
    def _validate(self, node: Node) -> Generator[Error, None, None]:
        doc = node.docstring
        for i, line in enumerate(doc.lines):
            match = re.match(DIRECTIVE_PATTERN, line)
            if match:
                yield Error(
                    docstring=doc,
                    start=doc.start.move(line=i, absolute_column=match.start(1)),
                    end=doc.start.move(line=i, absolute_column=match.end(1) + 1),
                    code="GL10",
                    message="reST directives must be followed by two colon.",
                    suggestion="Fix the directive by inserting `::`",
                )
