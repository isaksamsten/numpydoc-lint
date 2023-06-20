import re
from abc import ABCMeta, abstractmethod
from typing import Generator, List, Tuple
import itertools

from ..numpydoc import DocString, DocStringParameter, Node, Parameter
from ._base import (
    Check,
    Error,
    _validate_parameter_description_ends_period,
    _validate_parameter_description_start_uppercase,
    _validate_parameter_has_description,
    empty_prefix_lines,
    empty_suffix_lines,
)


class ParameterCheck(Check, metaclass=ABCMeta):
    def _validate(
        self, node: Node, docstring: DocString
    ) -> Generator[Error, None, None]:
        if node.type in ("function", "method", "class"):
            yield from self._validate_parameters(
                docstring,
                node.parameters,
            )
            yield from self._validate_other_parameters(docstring, node.parameters)

    @abstractmethod
    def _validate_parameters(
        self, docstring: DocString, expected_parameters: List[Parameter]
    ) -> Generator[Error, None, None]:
        pass

    def _validate_other_parameters(
        self, docstring: DocString, expected_parameters: List[Parameter]
    ) -> Generator[Error, None, None]:
        return
        yield


def _get_all_parameters(
    docstring: DocString,
) -> List[Parameter]:
    """
    Get the `parameters` and `other parameters`.

    Parameters
    ----------
    docstring : DocString
        The docstring.

    Returns
    -------
    List[Parameter]
        All parameters defined in `parameters` and `other parameters`.
    """
    parameters = docstring.sections.get("parameters")
    other_parameters = docstring.sections.get("other parameters")

    parameters = parameters.contents if parameters else []
    other_parameters = other_parameters.contents if other_parameters else []
    return list(itertools.chain(parameters, other_parameters))


def _partition_parameters(
    parameters: List[Parameter], pivot: str
) -> Tuple[List[Parameter], List[Parameter]]:
    """
    Partition parameters into `parameters` and `other parameters`.

    Parameters
    ----------
    parameters : List[Parameter]
        The list of prameters.
    pivot : str
        The first documented `other parameters`.

    Returns
    -------
    Tuple[List[Parameter], List[Parameter]]
        The parameters and other parameters.
    """
    if pivot is None:
        return parameters, []

    p = []
    o = []
    found = False
    for parameter in parameters:
        if not found:
            found = parameter.name == pivot

        if found:
            o.append(parameter)
        else:
            p.append(parameter)
    return p, o


class W0101(ParameterCheck):
    """Check that all parameters are documented."""

    def _validate_parameters(
        self,
        docstring: DocString,
        expected_parameters: List[Parameter],
    ) -> Generator[Error, None, None]:
        parameters = docstring.sections.get("parameters")
        other_parameters = docstring.sections.get("other parameters")

        if parameters:
            start = parameters.name.start
            end = parameters.name.end
            actual_parameters = [p.name.value for p in parameters.contents]
        else:
            start = docstring.start  # TODO: this should be node.name.start
            end = docstring.end
            actual_parameters = []

        # NOTE: parameters can also be documented under Other Parameter.
        if other_parameters:
            for p in other_parameters.contents:
                actual_parameters.append(p.name.value)

        for expected in expected_parameters:
            if expected.name not in actual_parameters:
                yield self.new_error(
                    message_args={"parameter": expected.name},
                    start=expected.start,
                    end=expected.end,
                    suggestion=f"Add documentation for `{expected.name}`.",
                )


class W0102(ParameterCheck):
    """Check that all documented parameters exists."""

    def _validate_parameters(
        self,
        docstring: DocString,
        expected_parameters: List[Parameter],
    ) -> Generator[Error, None, None]:
        parameters = _get_all_parameters(docstring)

        if parameters:
            expected_parameters = [p.name for p in expected_parameters]
            for actual_parameter in parameters:
                if actual_parameter.name.value not in expected_parameters:
                    yield self.new_error(
                        message_args={"parameter": actual_parameter.name.value},
                        start=actual_parameter.name.start,
                        end=actual_parameter.name.end,
                        suggestion=(
                            f"Remove or declare `{actual_parameter.name.value}`."
                        ),
                    )


# NOTE: We defer testing if the parameter belongs to the correct
# section. W0110 performs that check.
class W0103(ParameterCheck):
    """Validate that the parameters are in the same order as function declaration."""

    def _validate_parameters(
        self,
        docstring: DocString,
        declared_parameters: List[Parameter],
    ) -> Generator[Error, None, None]:
        parameters = docstring.sections.get("parameters")
        other_parameters = docstring.sections.get("other parameters")
        if parameters and (
            not other_parameters or (other_parameters and not other_parameters.contents)
        ):
            yield from self._validate_parameter_order(
                parameters.contents, declared_parameters
            )
        elif not parameters and other_parameters:
            yield from self._validate_parameter_order(
                other_parameters.contents, declared_parameters
            )
        elif parameters and other_parameters:
            declared_parameters, declared_other_parameters = _partition_parameters(
                declared_parameters, other_parameters.contents[0].name.value
            )
            yield from self._validate_parameter_order(
                parameters.contents, declared_parameters
            )
            yield from self._validate_parameter_order(
                other_parameters.contents, declared_other_parameters
            )

    def _validate_parameter_order(
        self, parameters: List[DocStringParameter], declared_parameters: List[Parameter]
    ) -> Generator[Error, None, None]:
        if len(parameters) == len(declared_parameters):
            for doc_parameter, dec_parameter in zip(parameters, declared_parameters):
                if doc_parameter.name.value != dec_parameter.name:
                    yield self.new_error(
                        message_args={
                            "documented_parameter": doc_parameter.name.value,
                            "declared_parameter": dec_parameter.name,
                        },
                        start=doc_parameter.name.start,
                        end=doc_parameter.name.end,
                        suggestion="The parameter should be `{0}`.".format(
                            dec_parameter.name
                        ),
                    )


class W0104(ParameterCheck):
    """Validate that each parameter has a declared type."""

    def _validate_parameters(
        self,
        docstring: DocString,
        declared_parameters: List[Parameter],
    ) -> Generator[Error, None, None]:
        parameters = _get_all_parameters(docstring)

        if parameters:
            for parameter in parameters:
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

                    yield self.new_error(
                        message_args={"parameter": parameter.name.value},
                        start=parameter.name.start,
                        end=parameter.name.end,
                        suggestion=suggestion,
                    )


class E0101(ParameterCheck):
    """Validate that the type specification does not end with period."""

    def _validate_parameters(
        self,
        docstring: DocString,
        declared_parameters: List[Parameter],
    ) -> Generator[Error, None, None]:
        for parameter in _get_all_parameters(docstring):
            if parameter.types:
                type = parameter.types[-1]
                if type.value.strip()[-1] == ".":
                    yield self.new_error(
                        message_args={"parameter": parameter.name.value},
                        start=type.end,
                        end=type.end,
                        suggestion="Remove `.`.",
                    )


class E0102(ParameterCheck):
    _common_type_errors = {"integer": "int", "boolean": "bool", "string": "str"}

    def _validate_parameters(
        self,
        docstring: DocString,
        declared_parameters: List[Parameter],
    ) -> Generator[Error, None, None]:
        parameters = docstring.sections.get("parameters")
        if not parameters:
            return
        for parameter in parameters.contents:
            if parameter.types:
                for type in parameter.types:
                    if type.value in E0102._common_type_errors:
                        yield self.new_error(
                            message_args={
                                "parameter": parameter.name.value,
                                "wrong_type": type.value,
                                "correct_type": E0102._common_type_errors[type.value],
                            },
                            start=type.start,
                            end=type.end,
                            suggestion="Use `{}` instead of `{}`.".format(
                                E0102._common_type_errors[type.value], type.value
                            ),
                        )
                    elif re.match("{\s*}", type.value):
                        yield self.new_error(
                            message_args={"parameter": parameter.name.value},
                            code="E0103",
                            start=type.start,
                            end=type.end,
                            suggestion="Insert choices.",
                        )


class ParameterDescriptionCheck(ParameterCheck, metaclass=ABCMeta):
    def _validate_parameters(
        self,
        docstring: DocString,
        declared_parameters: List[Parameter],
    ) -> Generator[Error, None, None]:
        parameters = docstring.sections.get("parameters")
        if parameters:
            for i, parameter in enumerate(parameters.contents):
                yield from self._validate_parameter_description(
                    docstring, parameter, i, len(parameters.contents)
                )

    @abstractmethod
    def _validate_parameter_description(
        self, docstring: DocString, parameter: DocStringParameter, i: int, n: int
    ) -> Generator[Error, None, None]:
        pass


class W0105(ParameterDescriptionCheck):
    def _validate_parameter_description(
        self, docstring: DocString, parameter: DocStringParameter, i: int, n: int
    ) -> Generator[Error, None, None]:
        yield from _validate_parameter_has_description(
            docstring=docstring,
            parameter=parameter,
            code="W0105",
            message_args={"parameter": parameter.name.value},
            suggestion="Add description.",
        )


class I0101(ParameterDescriptionCheck):
    def _validate_parameter_description(
        self, docstring: DocString, parameter: DocStringParameter, i: int, n: int
    ) -> Generator[Error, None, None]:
        yield from _validate_parameter_description_start_uppercase(
            docstring=docstring,
            parameter=parameter,
            code="I0101",
            message_args={"parameter": parameter.name.value},
            suggestion="Change first letter to uppercase.",
        )


class I0102(ParameterDescriptionCheck):
    """Check that all parameter descriptions end with period."""

    def _validate_parameter_description(
        self, docstring: DocString, parameter: DocStringParameter, i: int, n: int
    ) -> Generator[Error, None, None]:
        yield from _validate_parameter_description_ends_period(
            docstring=docstring,
            parameter=parameter,
            code="I0102",
            message_args={"parameter": parameter.name.value},
            suggestion="Add period to end of description.",
        )


class I0103(ParameterDescriptionCheck):
    def _validate_parameter_description(
        self, docstring: DocString, parameter: DocStringParameter, i: int, n: int
    ) -> Generator[Error, None, None]:
        if parameter.description.data:
            if empty_prefix_lines(parameter.description.data) > 0 and i < n - 1:
                yield self.new_error(
                    message_args={"parameter": parameter.name.value},
                    start=parameter.name.start,
                    end=parameter.name.end,
                    suggestion="Remove empty lines.",
                )


class I0104(ParameterDescriptionCheck):
    def _validate_parameter_description(
        self, docstring: DocString, parameter: DocStringParameter, i: int, n: int
    ) -> Generator[Error, None, None]:
        if parameter.description.data:
            if empty_suffix_lines(parameter.description.data) > 0 and i < n - 1:
                yield self.new_error(
                    message_args={"parameter": parameter.name.value},
                    start=parameter.name.start,
                    end=parameter.name.end,
                    suggestion="Remove empty lines.",
                )


class I0105(ParameterDescriptionCheck):
    def _validate_parameter_description(
        self, docstring: DocString, parameter: DocStringParameter, i: int, n: int
    ) -> Generator[Error, None, None]:
        # parameters = docstring.sections.get("parameters")
        # if parameters and parameters.contents:
        #     for parameter in parameters.contents:
        #         print(parameter.optional, parameter.types)
        if parameter.optional > 1:
            yield self.new_error(
                message_args={"parameter": parameter.name.value},
                start=parameter.name.start,
                end=parameter.name.end,
                code="I0105",
                suggestion="Remove duplicate `optional`.",
            )


# TODO: PRE04 - optional but no default value, default value but no optional
# TODO: PRE05 - type(s) does not agree with type annotation


class W0106(ParameterCheck):
    def _validate_parameters(
        self,
        docstring: DocString,
        declared_parameters: List[Parameter],
    ) -> Generator[Error, None, None]:
        parameters = docstring.sections.get("parameters")
        if parameters and parameters.contents:
            for parameter in parameters.contents:
                for match in re.finditer(r"(\S:|:\S|:\s*$|^\s*:)", parameter.header):
                    yield self.new_error(
                        message_args={"parameter": parameter.name.value},
                        start=parameter.name.start.move(column=match.start(1)),
                        end=parameter.name.start.move(column=match.end(1)),
                        code="W0106",
                        suggestion="Insert a space before and/or after `:`.",
                    )
