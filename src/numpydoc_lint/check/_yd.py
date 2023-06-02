from typing import Generator

from ..numpydoc import Node, DocString
from ._base import Check, Error


class YD01(Check):
    def _validate(
        self, node: Node, docstring: DocString
    ) -> Generator[Error, None, None]:
        if node.type in ("function", "method"):
            if not docstring.sections.get("Yields") and node.yields > 0:
                yield Error(
                    start=docstring.start,
                    end=docstring.end,
                    code="YD01",
                    message="No yields section found.",
                    suggestion="Add a Yields section",
                )
