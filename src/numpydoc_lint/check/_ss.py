import re
from typing import Generator

from ..numpydoc import Node, DocString
from ._base import Check, Error, first_non_blank


class SS01(Check):
    def _validate(
        self, node: Node, docstring: DocString
    ) -> Generator[Error, None, None]:
        if not docstring.summary:
            yield Error(
                code="SS01",
                message="No summary found.",
                suggestion="Add a short summary in a single line",
            )


class SS02(Check):
    def _validate(
        self, node: Node, docstring: DocString
    ) -> Generator[Error, None, None]:
        if docstring.summary:
            data = docstring.summary.content.data
            first_line = first_non_blank(data)
            if not first_line:
                return

            if first_line[0].isalpha() and not first_line[0].isupper():
                yield Error(
                    start=docstring.summary.content.start,
                    code="SS02",
                    message="Summary does not start with a capital letter",
                    suggestion=(
                        f"Replace `{first_line[0]}` with `{first_line[0].upper()}`"
                    ),
                )


class SS03(Check):
    def _validate(
        self, node: Node, docstring: DocString
    ) -> Generator[Error, None, None]:
        if docstring.summary:
            data = docstring.summary.content.data
            if data and data[0].value[-1] != ".":
                yield Error(
                    start=docstring.summary.content.start,
                    end=docstring.summary.content.start.move(
                        absolute_column=len(data[0]) + 1
                    ),
                    code="SS03",
                    message="Summary does not end with a period.",
                    suggestion="Insert a period.",
                )


class SS04(Check):
    def _validate(
        self, node: Node, docstring: DocString
    ) -> Generator[Error, None, None]:
        if docstring.summary:
            data = docstring.summary.content.data
            indent = docstring.indent
            first_line_indent = len(data[0].value) - len(data[0].value.lstrip())
            if first_line_indent != indent:
                yield Error(
                    start=docstring.summary.content.start.move(
                        absolute_column=indent,
                    ),
                    end=docstring.summary.content.start.move(
                        absolute_column=first_line_indent
                    ),
                    code="SS04",
                    message="Summary contains heading whitespaces.",
                    suggestion="Remove leading whitespace.",
                )


class SS05(Check):
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
                    yield Error(
                        start=docstring.start.move(absolute_column=match.start(1)),
                        end=docstring.start.move(absolute_column=match.end(1)),
                        message=(
                            "Summary must start with infinitive verb, not third person."
                        ),
                        suggestion="Remove third person `s`",
                        code="SS05",
                    )


class SS06(Check):
    def _validate(
        self, node: Node, docstring: DocString
    ) -> Generator[Error, None, None]:
        if docstring.summary is None:
            return

        data = docstring.summary.content.data
        if len(data) > 1:
            yield Error(
                start=docstring.summary.content.start,
                end=docstring.summary.content.end,
                code="SS06",
                message="Summary should fit in a single line",
            )
