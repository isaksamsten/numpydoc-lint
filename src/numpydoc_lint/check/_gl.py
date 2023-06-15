import re
from typing import Generator, Optional

from ..numpydoc import DocStringParagraph, Node, DocString
from ._base import Check, Error, empty_suffix_lines

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
    r"^\s*(\.\. (:?{})(?!::))".format("|".join(DIRECTIVES)), re.I
)

DEPRECATED_START_PATTERN = re.compile(r"\s*(\.\. deprecated::)\s+")


def _find_deprectated(paragraph: DocStringParagraph):
    if paragraph:
        for line in paragraph.data:
            match = re.search(DEPRECATED_START_PATTERN, line.value)
            if match:
                yield (
                    line.pos.move(absolute_column=match.start(1) + 1),
                    line.pos.move(absolute_column=match.end(1) + 1),
                )


class GL01(Check):
    """Check that multiline docstrings has 1 blank line before summary."""

    def _validate(
        self, node: Node, docstring: DocString
    ) -> Generator[Error, None, None]:
        if (
            node.has_docstring
            and docstring.summary is not None
            and docstring.summary.content.data
            and docstring.summary.content.start.line != docstring.start.line + 1
            and docstring.start.line < docstring.end.line
        ):
            yield Error(
                start=docstring.summary.content.data[0].pos,
                end=docstring.summary.content.data[0].pos,
                code="GL01",
                message="Docstring should start on a new line.",
            )


class GL02(Check):
    """Validates that there are no blank lines before the end quote."""

    def _validate(
        self, node: Node, docstring: DocString
    ) -> Generator[Error, None, None]:
        if len(docstring.lines) > 1 and empty_suffix_lines(docstring.lines) != 1:
            yield Error(
                start=docstring.lines[-1].pos,
                end=docstring.lines[-1].pos,
                code="GL02",
                message="Docstring should end one line before the closing quotes.",
                suggestion="Remove empty line.",
            )


class GL03(Check):
    """Validate that the docstring don't contain multiple consecutive blank lines."""

    # TODO: improve start/end position
    def _validate(
        self, node: Node, docstring: DocString
    ) -> Generator[Error, None, None]:
        if len(docstring.lines) > 2:
            prev_line = docstring.lines[0]
            for i, current_line in enumerate(docstring.lines[1:]):
                if (
                    not prev_line.value.strip()
                    and not current_line.value.strip()
                    and i < len(docstring.lines) - 2
                ):
                    yield Error(
                        code="GL03",
                        start=prev_line.pos,
                        end=current_line.pos,
                        message="Docstring should not contain double line breaks.",
                    )
                prev_line = current_line


class GL05(Check):
    """Validate that the docstring only contain leading spaces."""

    def _validate(self, node: Node, docstring: DocString) -> Optional[Error]:
        for line in docstring.lines:
            for match in re.finditer("^(\t+)", line.value):
                yield Error(
                    start=line.pos.move(absolute_column=match.start(1) + 1),
                    end=line.pos.move(absolute_column=match.end(1) + 1),
                    code="GL05",
                    message="Docstring line should not start with tabs.",
                )


class GL06(Check):
    def _validate(
        self, node: Node, docstring: DocString
    ) -> Generator[Error, None, None]:
        for name, section in docstring.sections.items():
            if name not in _ALLOWED_SECTIONS:
                yield Error(
                    start=section.name.start,
                    end=section.name.end,
                    code="GL06",
                    message="Docstring contains unexpected section.",
                    suggestion="Remove section or fix spelling.",
                )


class GL07(Check):
    def _validate(
        self, node: Node, docstring: DocString
    ) -> Generator[Error, None, None]:
        expected_sections = [
            section
            for section in _ALLOWED_SECTIONS
            if section in docstring.sections.keys()
        ]
        actual_sections = [
            section
            for section in docstring.sections.values()
            if section.name.value in _ALLOWED_SECTIONS
        ]
        for expected_section, actual_section in zip(expected_sections, actual_sections):
            if expected_section != actual_section.name.value:
                yield Error(
                    start=actual_section.name.start,
                    end=actual_section.name.end,
                    code="GL07",
                    message="Section `{}` should be swapped with `{}`.".format(
                        actual_section.name.value, expected_section
                    ),
                    suggestion=f"Section should be `{expected_section}`",
                )


class GL09(Check):
    def _validate(
        self, node: Node, docstring: DocString
    ) -> Generator[Error, None, None]:
        if docstring.summary and docstring.summary.extended_content:
            deprecated_markers = list(
                _find_deprectated(docstring.summary.extended_content),
            )

            if deprecated_markers:
                paragraph = docstring.summary.extended_content
                deprecated_start, deprecated_end = deprecated_markers[0]
                if deprecated_start.line != paragraph.start.line:
                    yield Error(
                        start=deprecated_start,
                        end=deprecated_end,
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
        if docstring.summary and docstring.summary.extended_content:
            marks = list(
                _find_deprectated(docstring.summary.extended_content),
            )
            if len(marks) > 1:
                paragraph = docstring.summary.extended_content
                offenders = [
                    (start, end)
                    for start, end in marks
                    if start.line != paragraph.start.line
                ]
                # TODO: improve suggestion if there is no correct deprecation warning.
                if len(offenders) == 1:
                    where = f"line {offenders[0][0].line}"
                else:
                    offending_lines = ", ".join(
                        str(offender[0].line) for offender in offenders[:-1]
                    )
                    where = f"lines {offending_lines} and {offenders[-1][0].line}"

                for start, end in offenders:
                    yield Error(
                        start=start,
                        end=end,
                        code="GLE01",
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
        for line in docstring.lines:
            match = re.match(DIRECTIVE_PATTERN, line.value)
            if match:
                yield Error(
                    start=line.pos.move(absolute_column=match.start(1) + 1),
                    end=line.pos.move(absolute_column=match.end(1) + 1),
                    code="GL10",
                    message="reST directives must be followed by two colon.",
                    suggestion="Fix the directive by inserting `::`",
                )
