from typing import Generator

from ..numpydoc import (
    Node,
)
from ._base import Check, Error


class ES01(Check):
    def _validate(self, node: Node) -> Generator[Error, None, None]:
        doc = node._docstring
        if not doc.summary.extended_content:
            yield Error(
                docstring=doc,
                start=doc.start,
                end=doc.start.move(column=3),
                code="ES01",
                message="No extended summary found.",
            )