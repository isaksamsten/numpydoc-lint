from abc import ABCMeta, abstractmethod
from typing import Generator

from ..numpydoc import DocString, DocStringParameter, Node
from ._base import (
    Check,
    Error,
    _validate_parameter_description_ends_period,
    _validate_parameter_description_start_uppercase,
    _validate_parameter_has_description,
)


class ReturnCheck(Check, metaclass=ABCMeta):
    def _validate(
        self, node: Node, docstring: DocString
    ) -> Generator[Error, None, None]:
        if node.type in ("function", "method"):
            yield from self._validate_returns(
                docstring,
                node.returns,
            )

    @abstractmethod
    def _validate_returns(
        self,
        docstring: DocString,
        n_returns: int,
    ) -> Generator[Error, None, None]:
        pass


class H0005(Check):
    def _validate(
        self, node: Node, docstring: DocString
    ) -> Generator[Error, None, None]:
        returns = docstring.sections.get("returns")
        if node.type in ("function", "method") and node.returns > 0 and not returns:
            yield self.new_error(
                start=node.name.end,
                end=node.name.end,
                suggestion="Declare return section.",
            )


class W0401(ReturnCheck):
    def _validate_returns(
        self,
        docstring: DocString,
        n_returns: int,
    ) -> Generator[Error, None, None]:
        returns = docstring.sections.get("returns")
        if (
            returns
            and len(returns.contents) == 1
            and returns.contents[0].name is not None
        ):
            ret = returns.contents[0]
            yield self.new_error(
                start=ret.name.start,
                end=ret.name.end,
                suggestion="Remove the name `{}`.".format(ret.name.value),
            )


class ReturnDescriptionCheck(ReturnCheck, metaclass=ABCMeta):
    def _validate_returns(
        self,
        docstring: DocString,
        n_returns: int,
    ) -> Generator[Error, None, None]:
        returns = docstring.sections.get("returns")
        if returns:
            for ret in returns.contents:
                yield from self._validate_parameter_description(docstring, ret)

    @abstractmethod
    def _validate_parameter_description(
        self, docstring: DocString, parameter: DocStringParameter
    ) -> Generator[Error, None, None]:
        pass


class W0402(ReturnDescriptionCheck):
    def _validate_parameter_description(
        self, docstring: DocString, parameter: DocStringParameter
    ) -> Generator[Error, None, None]:
        name = (
            parameter.name.value
            if parameter.name is not None
            else ",".join(t.value for t in parameter.types)
        )
        yield from _validate_parameter_has_description(
            docstring=docstring,
            parameter=parameter,
            message_args={"return": name},
            code="W0402",
            suggestion="Add description.",
        )


class I0401(ReturnDescriptionCheck):
    def _validate_parameter_description(
        self, docstring: DocString, parameter: DocStringParameter
    ) -> Generator[Error, None, None]:
        name = (
            parameter.name.value
            if parameter.name is not None
            else ",".join(t.value for t in parameter.types)
        )
        yield from _validate_parameter_description_start_uppercase(
            docstring=docstring,
            parameter=parameter,
            message_args={"return": name},
            code="I0401",
            suggestion="Change first letter to uppercase.",
        )


class I0402(ReturnDescriptionCheck):
    def _validate_parameter_description(
        self, docstring: DocString, parameter: DocStringParameter
    ) -> Generator[Error, None, None]:
        name = (
            parameter.name.value
            if parameter.name is not None
            else ",".join(t.value for t in parameter.types)
        )
        yield from _validate_parameter_description_ends_period(
            docstring=docstring,
            parameter=parameter,
            message_args={"return": name},
            code="I0402",
            suggestion="Add period to end of description.",
        )
