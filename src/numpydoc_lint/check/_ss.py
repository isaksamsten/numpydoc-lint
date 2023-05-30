import re
from typing import Generator

from ..numpydoc import (
    Node,
)
from ._base import Check, Error


class SS01(Check):
    def _validate(self, node: Node) -> Generator[Error, None, None]:
        doc = node.docstring
        if not doc.summary.content:
            yield Error(
                docstring=doc,
                code="SS01",
                message="No summary found.",
                suggestion="Add a short summary in a single line",
            )


class SS02(Check):
    def _validate(self, node: Node) -> Generator[Error, None, None]:
        doc = node.docstring
        if doc.summary.content:
            data = doc.summary.content.data
            first_line = data[0].strip()
            if first_line[0].isalpha() and not first_line[0].isupper():
                yield Error(
                    docstring=doc,
                    start=doc.summary.content.start,
                    code="SS02",
                    message="Summary does not start with a capital letter",
                    suggestion=(
                        f"Replace `{first_line[0]}` with `{first_line[0].upper()}`"
                    ),
                )


class SS03(Check):
    def _validate(self, node: Node) -> Generator[Error, None, None]:
        doc = node.docstring
        if doc.summary.content:
            data = doc.summary.content.data
            if data[0][-1] != ".":
                yield Error(
                    docstring=doc,
                    start=doc.summary.content.start,
                    end=doc.summary.content.start.move(
                        absolute_column=len(data[0]) + 1
                    ),
                    code="SS03",
                    message="Summary does not end with a period.",
                    suggestion="Insert a period.",
                )


class SS04(Check):
    def _validate(self, node: Node) -> Generator[Error, None, None]:
        doc = node.docstring
        if doc.summary.content:
            data = doc.summary.content.data
            indent = doc.indent
            first_line_indent = len(data[0]) - len(data[0].lstrip())
            if first_line_indent != indent:
                yield Error(
                    docstring=doc,
                    start=doc.summary.content.start.move(
                        absolute_column=indent,
                    ),
                    end=doc.summary.content.start.move(
                        absolute_column=first_line_indent
                    ),
                    code="SS04",
                    message="Summary contains heading whitespaces.",
                    suggestion="Remove leading whitespace.",
                )


class SS05(Check):
    def _validate(self, node: Node) -> Generator[Error, None, None]:
        doc = node.docstring
        if doc.summary.content is None:
            return

        data = doc.summary.content.data
        if node.type in ["function", "method"] and data:
            match = re.match(r"^\s*(.*?)\s+", data[0])
            if match:
                word = match.group(1).strip()
                if word != "" and word[-1] == "s":
                    yield Error(
                        docstring=doc,
                        start=doc.start.move(absolute_column=match.start(1)),
                        end=doc.start.move(absolute_column=match.end(1)),
                        message=(
                            "Summary must start with infinitive verb, not third person."
                        ),
                        suggestion="Remove third person `s`",
                        code="SS05",
                    )


class SS06(Check):
    def _validate(self, node: Node) -> Generator[Error, None, None]:
        if node.docstring.summary.content is None:
            return

        data = node.docstring.summary.content.data
        if len(data) > 1:
            yield Error(
                docstring=node.docstring,
                start=node.docstring.summary.content.start,
                end=node.docstring.summary.content.end,
                code="SS06",
                message="Summary should fit in a single line",
            )
