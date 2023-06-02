import itertools
import re
from typing import Generator, Optional

from ..numpydoc import DocStringParagraph, Node, DocString
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

    def _validate(
        self, node: Node, docstring: DocString
    ) -> Generator[Error, None, None]:
        if (
            node.has_docstring
            and empty_prefix_lines(docstring.lines) != 1
            and "\n" in docstring.raw
        ):
            yield Error(
                start=docstring.start,
                code="GL01",
                message="Docstring should start on a new line.",
            )


# TODO: Incorrectly flagged if docstring start on the same line as """.
class GL02(Check):
    def _validate(
        self, node: Node, docstring: DocString
    ) -> Generator[Error, None, None]:
        if empty_suffix_lines(docstring.lines) != 1 and "\n" in docstring.raw:
            yield Error(
                start=docstring.end.move_line(line=-1),
                code="GL02",
                message="Docstring should end one line before the closing quotes.",
                suggestion="Remove empty line.",
            )


class GL03(Check):
    def _validate(
        self, node: Node, docstring: DocString
    ) -> Generator[Error, None, None]:
        prev = True
        for i, row in enumerate(docstring.lines):
            if not prev and not row.strip() and i < len(docstring.lines) - 1:
                yield Error(
                    code="GL03",
                    message="Docstring should not contain double line breaks.",
                )
            prev = row.strip()
        return None


class GL04(Check):
    def _validate(self, node: Node, docstring: DocString) -> Optional[Error]:
        for i, line in enumerate(docstring.lines):
            first = next(re.finditer("^\s*(\t)", line), None)
            if first:
                yield Error(
                    end=docstring.start.move_line(line=i, column=first.end(0)),
                    code="GL04",
                    message="Docstring line should not start with tabs.",
                )


class GL06(Check):
    def _validate(
        self, node: Node, docstring: DocString
    ) -> Generator[Error, None, None]:
        for section in docstring.sections.values():
            if section.name not in _ALLOWED_SECTIONS:
                yield Error(
                    start=section.start_header,
                    end=section.end_header,
                    code="GL06",
                    message="Docstring contains unexpected section.",
                    suggestion="Remove section or fix spelling.",
                )


class GL07(Check):
    def _validate(
        self, node: Node, docstring: DocString
    ) -> Generator[Error, None, None]:
        expected_sections = [
            section for section in _ALLOWED_SECTIONS if section in docstring.sections
        ]
        actual_sections = [
            section
            for section in docstring.sections.values()
            if section.name in _ALLOWED_SECTIONS
        ]
        for expected_section, actual_section in zip(expected_sections, actual_sections):
            if expected_section != actual_section.name:
                yield Error(
                    start=actual_section.start_header,
                    end=actual_section.end_header,
                    code="GL07",
                    message="Sections are in the wrong order.",
                    suggestion=f"Section should be `{expected_section}`",
                )


class GL08(Check):
    """Check that the class/function/module has a docstring."""

    def _validate(
        self, node: Node, docstring: DocString
    ) -> Generator[Error, None, None]:
        return
        yield

    def validate(self, node: Node) -> Generator[Error, None, None]:
        if not node.has_docstring:
            yield Error(
                start=node.start,
                code="GL08",
                message=f"{node.type.capitalize()} does not have a docstring",
            )


class GL09(Check):
    def _validate(
        self, node: Node, docstring: DocString
    ) -> Generator[Error, None, None]:
        if docstring.summary:
            deprecated_markers = list(
                itertools.chain(
                    _find_deprectated(docstring.summary.content),
                    _find_deprectated(docstring.summary.extended_content),
                )
            )

            if deprecated_markers:
                paragraph = (
                    docstring.summary.extended_content
                    if docstring.summary.extended_content is not None
                    else docstring.summary
                )
                if deprecated_markers[0].line != paragraph.start.line:
                    yield Error(
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
    def _validate(
        self, node: Node, docstring: DocString
    ) -> Generator[Error, None, None]:
        if docstring.summary:
            marks = list(
                itertools.chain(
                    _find_deprectated(docstring.summary.content),
                    _find_deprectated(docstring.summary.extended_content),
                )
            )
            if len(marks) > 1:
                paragraph = (
                    docstring.summary.extended_content
                    if docstring.summary.extended_content is not None
                    else docstring.summary
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
    def _validate(
        self, node: Node, docstring: DocString
    ) -> Generator[Error, None, None]:
        for i, line in enumerate(docstring.lines):
            match = re.match(DIRECTIVE_PATTERN, line)
            if match:
                yield Error(
                    start=docstring.start.move(line=i, absolute_column=match.start(1)),
                    end=docstring.start.move(line=i, absolute_column=match.end(1) + 1),
                    code="GL10",
                    message="reST directives must be followed by two colon.",
                    suggestion="Fix the directive by inserting `::`",
                )
