from typing import Generator

from ..numpydoc import Node, DocString
from ._base import Check, Error


class ES01(Check):
    def _validate(
        self, node: Node, docstring: DocString
    ) -> Generator[Error, None, None]:
        if not docstring.summary.extended_content:
            yield Error(
                start=docstring.start,
                end=docstring.start.move(column=3),
                code="ES01",
                message="No extended summary found.",
            )
