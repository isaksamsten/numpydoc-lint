from typing import Generator

from ..numpydoc import Node
from ._base import Check, Error


class YD01(Check):
    def _validate(self, node: Node) -> Generator[Error, None, None]:
        if node.type in ("function", "method"):
            docstring = node.docstring
            if not docstring.get_section("Yields") and node.yields > 0:
                yield Error(
                    docstring=node.docstring,
                    start=node.docstring.start,
                    end=node.docstring.end,
                    code="YD01",
                    message="No yields section found.",
                    suggestion="Add a Yields section",
                )
