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
    def _validate(self, node: Node) -> Generator[Error, None, None]:
        if node.type in ("function", "method"):
            yield from self._validate_returns(
                node.docstring,
                node.returns,
            )

    @abstractmethod
    def _validate_returns(
        self,
        docstring: DocString,
        n_returns: int,
    ) -> Generator[Error, None, None]:
        pass


class RT01(ReturnCheck):
    def _validate_returns(
        self,
        docstring: DocString,
        n_returns: int,
    ) -> Generator[Error, None, None]:
        returns = docstring.get_section("Returns")
        if n_returns > 0 and not returns:
            yield Error(
                docstring=docstring,
                start=docstring.end,
                end=docstring.end,
                code="RT01",
                message="No return section found.",
                suggestion="Declare return section.",
            )


class RT02(ReturnCheck):
    def _validate_returns(
        self,
        docstring: DocString,
        n_returns: int,
    ) -> Generator[Error, None, None]:
        returns = docstring.get_section("Returns")
        if (
            returns
            and len(returns.contents) == 1
            and returns.contents[0].name is not None
        ):
            ret = returns.contents[0]
            yield Error(
                docstring=docstring,
                start=ret.name.start,
                end=ret.name.end,
                code="RT02",
                message="Single return should only contain the type.",
                suggestion="Remove the name `{}`.".format(ret.name.value),
            )


class ReturnDescriptionCheck(ReturnCheck, metaclass=ABCMeta):
    def _validate_returns(
        self,
        docstring: DocString,
        n_returns: int,
    ) -> Generator[Error, None, None]:
        returns = docstring.get_section("Returns")
        if returns:
            for ret in returns.contents:
                yield from self._validate_parameter_description(docstring, ret)

    @abstractmethod
    def _validate_parameter_description(
        self, docstring: DocString, parameter: DocStringParameter
    ) -> Generator[Error, None, None]:
        pass


class RT03(ReturnDescriptionCheck):
    def _validate_parameter_description(
        self, docstring: DocString, parameter: DocStringParameter
    ) -> Generator[Error, None, None]:
        name = (
            parameter.name.value if parameter.name is not None else parameter.type.value
        )
        yield from _validate_parameter_has_description(
            docstring=docstring,
            parameter=parameter,
            code="RT03",
            message="Return `{}` has no description.".format(name),
            suggestion="Add description.",
        )


class RT04(ReturnDescriptionCheck):
    def _validate_parameter_description(
        self, docstring: DocString, parameter: DocStringParameter
    ) -> Generator[Error, None, None]:
        name = (
            parameter.name.value if parameter.name is not None else parameter.type.value
        )
        yield from _validate_parameter_description_start_uppercase(
            docstring=docstring,
            parameter=parameter,
            code="RT04",
            message=(
                "Return `{}` description should start with uppercase letter."
            ).format(name),
            suggestion="Change first letter to uppercase.",
        )


class RT05(ReturnDescriptionCheck):
    def _validate_parameter_description(
        self, docstring: DocString, parameter: DocStringParameter
    ) -> Generator[Error, None, None]:
        name = (
            parameter.name.value if parameter.name is not None else parameter.type.value
        )
        yield from _validate_parameter_description_ends_period(
            docstring=docstring,
            parameter=parameter,
            code="RT05",
            message=("Return `{}` description should end with period.").format(name),
            suggestion="Add period to end of description.",
        )
