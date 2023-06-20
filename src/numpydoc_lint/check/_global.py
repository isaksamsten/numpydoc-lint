import re
from typing import Generator, Optional

from ..numpydoc import (
    DocStringParagraph,
    Node,
    DocString,
    ALLOWED_SECTIONS,
    DIRECTIVE_PATTERN,
    DEPRECATED_START_PATTERN,
)
from ._base import Check, Error, empty_suffix_lines, first_non_blank


def _find_deprectated(paragraph: DocStringParagraph):
    if paragraph:
        for line in paragraph.data:
            match = re.search(DEPRECATED_START_PATTERN, line.value)
            if match:
                yield (
                    line.pos.move(absolute_column=match.start(1) + 1),
                    line.pos.move(absolute_column=match.end(1) + 1),
                )


class H0004(Check):
    def _validate(
        self, node: Node, docstring: DocString
    ) -> Generator[Error, None, None]:
        if node.type in ("function", "method"):
            if not docstring.sections.get("yields") and node.yields > 0:
                yield self.new_error(
                    start=node.name.start,
                    end=node.name.end,
                    suggestion="Add a Yields section",
                )


class H0002(Check):
    def _validate(
        self,
        node: Node,
        docstring: DocString,
    ) -> Generator[Error, None, None]:
        if not docstring.sections.get("examples"):
            yield self.new_error(
                start=node.name.start,
                end=node.name.end,
                suggestion="Add an Examples section.",
            )


class H0001(Check):
    def _validate(
        self, node: Node, docstring: DocString
    ) -> Generator[Error, None, None]:
        if not docstring.summary.extended_content:
            yield self.new_error(
                start=docstring.start,
                end=docstring.start.move(column=3),
                code="H0001",
            )


class H0003(Check):
    def _validate(
        self, node: Node, docstring: DocString
    ) -> Generator[Error, None, None]:
        if not docstring.summary:
            yield self.new_error(
                start=docstring.start,
                code="H0003",
                suggestion="Add a short summary in a single line",
            )


class I0009(Check):
    def _validate(
        self, node: Node, docstring: DocString
    ) -> Generator[Error, None, None]:
        if docstring.summary:
            data = docstring.summary.content.data
            first_line = first_non_blank(data)
            if not first_line:
                return

            first_letter = first_line.value.strip()[0]
            if first_letter.isalpha() and not first_letter.isupper():
                column = len(first_line.value) - len(first_line.value.lstrip())
                yield self.new_error(
                    start=first_line.pos,
                    code="I0009",
                    suggestion=(
                        f"Replace `{first_letter}` with `{first_letter.upper()}`"
                    ),
                )


class I0010(Check):
    """Validate that the summary ends with a period."""

    def _validate(
        self, node: Node, docstring: DocString
    ) -> Generator[Error, None, None]:
        if docstring.summary:
            data = docstring.summary.content.data
            if data and data[0].value[-1] != ".":
                yield self.new_error(
                    start=data[0].pos,
                    end=data[0].pos.move(absolute_column=len(data[0].value) + 1),
                    suggestion="Insert a period.",
                )


class I0011(Check):
    def _validate(
        self, node: Node, docstring: DocString
    ) -> Generator[Error, None, None]:
        if docstring.summary:
            data = docstring.summary.content.data
            indent = docstring.indent
            first_line_indent = len(data[0].value) - len(data[0].value.lstrip())
            if first_line_indent != indent:
                yield self.new_error(
                    start=data[0].pos.move(
                        absolute_column=indent,
                    ),
                    end=data[0].pos.move(absolute_column=first_line_indent),
                    code="I0011",
                    suggestion="Remove leading whitespace.",
                )


class I0012(Check):
    def _validate(
        self, node: Node, docstring: DocString
    ) -> Generator[Error, None, None]:
        if docstring.summary is None:
            return

        data = docstring.summary.content.data
        if node.type in ["function", "method"] and data:
            match = re.match(r"^\s*(.*?)\s+", data[0].value)
            if match:
                word = match.group(1).strip()
                if word != "" and word[-1] == "s":
                    yield self.new_error(
                        start=data[0].pos.move(absolute_column=match.start(1)),
                        end=data[0].pos.move(absolute_column=match.end(1)),
                        suggestion="Remove third person `s`",
                    )


class I0013(Check):
    def _validate(
        self, node: Node, docstring: DocString
    ) -> Generator[Error, None, None]:
        if docstring.summary is None:
            return

        data = docstring.summary.content.data
        if len(data) > 1:
            yield self.new_error(
                start=data[0].pos,
                end=data[-1].pos,
            )


class I0001(Check):
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
            yield self.new_error(
                start=docstring.summary.content.data[0].pos,
                end=docstring.summary.content.data[0].pos,
            )


class I0002(Check):
    """Validates that there are no blank lines before the end quote."""

    def _validate(
        self, node: Node, docstring: DocString
    ) -> Generator[Error, None, None]:
        if len(docstring.lines) > 1 and empty_suffix_lines(docstring.lines) != 1:
            yield self.new_error(
                start=docstring.lines[-1].pos,
                end=docstring.lines[-1].pos,
                suggestion="Remove empty line.",
            )


class I0003(Check):
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
                    yield self.new_error(
                        start=prev_line.pos,
                        end=current_line.pos,
                    )
                prev_line = current_line


class I0004(Check):
    """Validate that the docstring only contain leading spaces."""

    def _validate(self, node: Node, docstring: DocString) -> Optional[Error]:
        for line in docstring.lines:
            for match in re.finditer("^(\t+)", line.value):
                yield Error(
                    start=line.pos.move(absolute_column=match.start(1) + 1),
                    end=line.pos.move(absolute_column=match.end(1) + 1),
                    code="I0004",
                    message="Docstring line should not start with tabs.",
                )


class W0001(Check):
    def _validate(
        self, node: Node, docstring: DocString
    ) -> Generator[Error, None, None]:
        for name, section in docstring.sections.items():
            if section.name.value not in ALLOWED_SECTIONS:
                yield self.new_error(
                    start=section.name.start,
                    end=section.name.end,
                    suggestion="Remove section or fix spelling.",
                )


class I0005(Check):
    def _validate(
        self, node: Node, docstring: DocString
    ) -> Generator[Error, None, None]:
        expected_sections = [
            section
            for section in ALLOWED_SECTIONS
            if section.lower() in docstring.sections.keys()
        ]
        actual_sections = [
            section
            for section in docstring.sections.values()
            if section.name.value in ALLOWED_SECTIONS
        ]
        for expected_section, actual_section in zip(expected_sections, actual_sections):
            if expected_section != actual_section.name.value:
                yield self.new_error(
                    message_args={
                        "actual": actual_section.name.value,
                        "expected": expected_section,
                    },
                    start=actual_section.name.start,
                    end=actual_section.name.end,
                    suggestion=f"Section should be `{expected_section}`",
                )


class I0006(Check):
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
                    yield self.new_error(
                        start=deprecated_start,
                        end=deprecated_end,
                        suggestion=(
                            f"Move deprecation warning to line {paragraph.start.line}"
                        ),
                    )


class I0007(Check):
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
                    yield self.new_error(
                        start=start,
                        end=end,
                        suggestion=(
                            f"Remove duplicate deprecation warnings on {where}"
                        ),
                    )


class I0008(Check):
    def _validate(
        self, node: Node, docstring: DocString
    ) -> Generator[Error, None, None]:
        for line in docstring.lines:
            match = re.match(DIRECTIVE_PATTERN, line.value)
            if match:
                yield self.new_error(
                    start=line.pos.move(absolute_column=match.start(1) + 1),
                    end=line.pos.move(absolute_column=match.end(1) + 1),
                    suggestion="Fix the directive by inserting `::`.",
                )
