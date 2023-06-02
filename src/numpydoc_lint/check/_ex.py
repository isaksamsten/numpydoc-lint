from typing import Generator

from ..numpydoc import Node, DocString
from ._base import Check, Error


class EX01(Check):
    def _validate(
        self,
        node: Node,
        docstring: DocString,
    ) -> Generator[Error, None, None]:
        if not docstring.sections.get("Examples"):
            yield Error(
                start=docstring.start,
                end=docstring.end,
                code="EX01",
                message="No examples section found.",
                suggestion="Add a Examples section",
            )
