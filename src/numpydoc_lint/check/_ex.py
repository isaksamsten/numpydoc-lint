from typing import Generator

from ..numpydoc import Node
from ._base import Check, Error


class EX01(Check):
    def _validate(self, node: Node) -> Generator[Error, None, None]:
        docstring = node.docstring
        if not docstring.get_section("Examples"):
            yield Error(
                docstring=node.docstring,
                start=node.docstring.start,
                end=node.docstring.end,
                code="EX01",
                message="No examples section found.",
                suggestion="Add a Examples section",
            )
