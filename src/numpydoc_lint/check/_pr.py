import re
from abc import ABCMeta, abstractmethod
from typing import Generator, List

from ..numpydoc import DocString, DocStringParameter, DocStringSection, Node, Parameter
from ._base import (
    Check,
    Error,
    _validate_parameter_description_ends_period,
    _validate_parameter_description_start_uppercase,
    _validate_parameter_has_description,
    empty_prefix_lines,
    empty_suffix_lines,
)


class ParameterCheck(Check):
    def _validate(
        self, node: Node, docstring: DocString
    ) -> Generator[Error, None, None]:
        if node.type in ("function", "method", "class"):
            yield from self._validate_parameters(
                docstring,
                node.parameters,
            )


class PR01(ParameterCheck):
    """Check that all parameters are documented."""

    def _validate_parameters(
        self,
        docstring: DocString,
        expected_parameters: List[Parameter],
    ) -> Generator[Error, None, None]:
        parameters = docstring.sections.get("Parameters")

        if parameters:
            start = parameters.start_contents
            end = parameters.end_contents
            actual_parameters = [p.name.value for p in parameters.contents]
        else:
            start = docstring.start
            end = docstring.end
            actual_parameters = []

        for expected in expected_parameters:
            if expected.name not in actual_parameters:
                yield Error(
                    start=expected.start,
                    end=expected.end,
                    code="PR01",
                    message=f"Parameter `{expected.name}` should be documented.",
                    suggestion=f"Add documentation for `{expected.name}`.",
                )


class PR02(ParameterCheck):
    """Check that all documented parameters exists."""

    def _validate_parameters(
        self,
        docstring: DocString,
        expected_parameters: List[Parameter],
    ) -> Generator[Error, None, None]:
        parameters: DocStringSection = docstring.sections.get("Parameters")
        if parameters:
            expected_parameters = [p.name for p in expected_parameters]
            for actual_parameter in parameters.contents:
                if actual_parameter.name.value not in expected_parameters:
                    yield Error(
                        start=actual_parameter.name.start,
                        end=actual_parameter.name.end,
                        code="PR02",
                        message=(
                            f"Parameter `{actual_parameter.name.value}` does "
                            "not exist in the declaration."
                        ),
                        suggestion=(
                            f"Remove or declare `{actual_parameter.name.value}`."
                        ),
                    )


class PR03(ParameterCheck):
    """Validate that the parameters are in the same order as function declaration."""

    def _validate_parameters(
        self,
        docstring: DocString,
        declared_parameters: List[Parameter],
    ) -> Generator[Error, None, None]:
        parameters = docstring.sections.get("Parameters")
        if parameters:
            if len(parameters.contents) == len(declared_parameters):
                for doc_parameter, dec_parameter in zip(
                    parameters.contents, declared_parameters
                ):
                    if doc_parameter.name.value != dec_parameter.name:
                        yield Error(
                            start=doc_parameter.name.start,
                            end=doc_parameter.name.end,
                            code="PR03",
                            message="The parameter `{0}` is in wrong order.".format(
                                doc_parameter.name.value
                            ),
                            suggestion="The parameter should be `{0}`.".format(
                                dec_parameter.name
                            ),
                        )


class PR04(ParameterCheck):
    """Validate that each parameter has a declared type."""

    def _validate_parameters(
        self,
        docstring: DocString,
        declared_parameters: List[Parameter],
    ) -> Generator[Error, None, None]:
        parameters = docstring.sections.get("Parameters")
        if parameters:
            for parameter in parameters.contents:
                if parameter.types is None:
                    declared_parameter = next(
                        filter(
                            lambda x: x.name == parameter.name.value,
                            declared_parameters,
                        ),
                        None,
                    )
                    if declared_parameter and declared_parameter.annotation:
                        suggestion = "Add the type declaration `{0}`.".format(
                            declared_parameter.annotation
                        )
                    else:
                        suggestion = "Add a type declaration."

                    yield Error(
                        start=parameter.name.start,
                        end=parameter.name.end,
                        code="PR04",
                        message="Parameter `{0}` should have a type.".format(
                            parameter.name.value
                        ),
                        suggestion=suggestion,
                    )


class PR05(ParameterCheck):
    """Validate that the type specification does not end with period."""

    def _validate_parameters(
        self,
        docstring: DocString,
        declared_parameters: List[Parameter],
    ) -> Generator[Error, None, None]:
        parameters: DocStringSection = docstring.sections.get("Parameters")
        if not parameters:
            return

        for parameter in parameters.contents:
            if parameter.types:
                type = parameter.types[-1]
                if type.value.strip()[-1] == ".":
                    message = "Parameter `{}` type should not finish with `.`.".format(
                        parameter.name.value
                    )
                    yield Error(
                        start=type.end,
                        end=type.end,
                        code="PR05",
                        message=message,
                        suggestion="Remove `.`.",
                    )


class PR06(ParameterCheck):
    _common_type_errors = {"integer": "int", "boolean": "bool", "string": "str"}

    def _validate_parameters(
        self,
        docstring: DocString,
        declared_parameters: List[Parameter],
    ) -> Generator[Error, None, None]:
        parameters = docstring.sections.get("Parameters")
        if not parameters:
            return
        for parameter in parameters.contents:
            if parameter.types:
                for type in parameter.types:
                    if type.value in PR06._common_type_errors:
                        message = "Parameter `{}` uses wrong type `{}` instead of `{}`."
                        yield Error(
                            start=type.start,
                            end=type.end,
                            code="PR06",
                            message=message.format(
                                parameter.name.value,
                                type.value,
                                PR06._common_type_errors[type.value],
                            ),
                            suggestion="Use `{}` instead of `{}`.".format(
                                PR06._common_type_errors[type.value], type.value
                            ),
                        )
                    elif re.match("{\s*}", type.value):
                        yield Error(
                            start=type.start,
                            end=type.end,
                            code="PR06",
                            message="Parameter `{}` uses empty choice.".format(
                                parameter.name.value
                            ),
                            suggestion="Insert choices.",
                        )


class ParameterDescriptionCheck(ParameterCheck, metaclass=ABCMeta):
    def _validate_parameters(
        self,
        docstring: DocString,
        declared_parameters: List[Parameter],
    ) -> Generator[Error, None, None]:
        parameters = docstring.sections.get("Parameters")
        if parameters:
            for parameter in parameters.contents:
                yield from self._validate_parameter_description(docstring, parameter)

    @abstractmethod
    def _validate_parameter_description(
        self, docstring: DocString, parameter: DocStringParameter
    ) -> Generator[Error, None, None]:
        pass


class PR07(ParameterDescriptionCheck):
    def _validate_parameter_description(
        self, docstring: DocString, parameter: DocStringParameter
    ) -> Generator[Error, None, None]:
        yield from _validate_parameter_has_description(
            docstring=docstring,
            parameter=parameter,
            code="PR07",
            message="Parameter `{}` has no description.".format(parameter.name.value),
            suggestion="Add description.",
        )


class PR08(ParameterDescriptionCheck):
    def _validate_parameter_description(
        self, docstring: DocString, parameter: DocStringParameter
    ) -> Generator[Error, None, None]:
        yield from _validate_parameter_description_start_uppercase(
            docstring=docstring,
            parameter=parameter,
            code="PR08",
            message=(
                "Parameter `{}` description should start with uppercase letter."
            ).format(parameter.name.value),
            suggestion="Change first letter to uppercase.",
        )


class PR09(ParameterDescriptionCheck):
    """Check that all parameter descriptions end with period."""

    def _validate_parameter_description(
        self, docstring: DocString, parameter: DocStringParameter
    ) -> Generator[Error, None, None]:
        yield from _validate_parameter_description_ends_period(
            docstring=docstring,
            parameter=parameter,
            code="PR09",
            message=("Parameter `{}` description should end with period.").format(
                parameter.name.value
            ),
            suggestion="Add period to end of description.",
        )


class PRE01(ParameterDescriptionCheck):
    def _validate_parameter_description(
        self, docstring: DocString, parameter: DocStringParameter
    ) -> Generator[Error, None, None]:
        if parameter.description.data:
            if empty_prefix_lines(parameter.description.data) > 0:
                yield Error(
                    start=parameter.name.start,
                    end=parameter.name.end,
                    code="PRE01",
                    message="Parameter `{}` description has empty prefix lines.".format(
                        parameter.name.value
                    ),
                    suggestion="Remove empty lines.",
                )


class PRE02(ParameterDescriptionCheck):
    def _validate_parameter_description(
        self, docstring: DocString, parameter: DocStringParameter
    ) -> Generator[Error, None, None]:
        if parameter.description.data:
            if empty_suffix_lines(parameter.description.data) > 0:
                yield Error(
                    start=parameter.name.start,
                    end=parameter.name.end,
                    code="PRE02",
                    message="Parameter `{}` description has empty suffix lines.".format(
                        parameter.name.value
                    ),
                    suggestion="Remove empty lines.",
                )


class PRE03(ParameterCheck):
    def _validate_parameters(
        self,
        docstring: DocString,
        declared_parameters: List[Parameter],
    ) -> Generator[Error, None, None]:
        parameters = docstring.sections.get("Parameters")
        if parameters and parameters.contents:
            for parameter in parameters.contents:
                if parameter.optional > 1:
                    yield Error(
                        start=parameter.name.start,
                        end=parameter.name.end,
                        code="PRE03",
                        message="Paramter `{}` specify optional multiple times.".format(
                            parameter.name.value
                        ),
                        suggestion="Remove duplicate `optional`.",
                    )


# TODO: PRE04 - optional but no default value, default value but no optional
# TODO: PRE05 - type(s) does not agree with type annotation


class PR10(ParameterCheck):
    def _validate_parameters(
        self,
        docstring: DocString,
        declared_parameters: List[Parameter],
    ) -> Generator[Error, None, None]:
        parameters = docstring.sections.get("Parameters")
        if parameters and parameters.contents:
            for parameter in parameters.contents:
                for match in re.finditer(r"(\S:|:\S|:\s*$|^\s*:)", parameter.header):
                    print(match)
                    yield Error(
                        start=parameter.name.start.move(column=match.start(1)),
                        end=parameter.name.start.move(column=match.end(1)),
                        code="PR10",
                        message=(
                            "Parameter `{}` requires a space between name and type."
                        ).format(parameter.name.value),
                        suggestion="Insert a space before and/or after `:`.",
                    )
