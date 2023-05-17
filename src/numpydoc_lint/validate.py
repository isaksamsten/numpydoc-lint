import re
import io
import itertools
from .numpydoc import (
    Node,
    Pos,
    DocStringParagraph,
    DocStringSection,
    Parameter,
    DocString,
)
from typing import Optional, Generator, Iterable, Mapping, List
from abc import ABCMeta, abstractmethod
from collections import OrderedDict, defaultdict

_ALLOWED_SECTIONS = [
    "Parameters",
    "Attributes",
    "Methods",
    "Returns",
    "Yields",
    "Other Parameters",
    "Raises",
    "Warns",
    "Warnings",
    "See Also",
    "Notes",
    "References",
    "Examples",
]


class Error:
    def __init__(
        self,
        *,
        docstring: DocString,
        start: Pos = None,
        end: Pos = None,
        code: str = None,
        message: str = None,
        suggestion: str = None,
        terminate: str = False,
    ) -> None:
        self.docstring = docstring
        self.start = start if start is not None else docstring.start
        self.end = end if end is not None else docstring.end
        self._code = code
        self._message = message
        self._suggestion = suggestion
        self._terminate = terminate

    @property
    def code(self):
        return self._code if self._code is not None else self.__class__.__name__.upper()

    @property
    def message(self):
        return self._message

    @property
    def suggestion(self):
        return self._suggestion

    @property
    def terminate(self) -> bool:
        """
        If the error terminates the remaining checks.

        Returns
        -------
        bool
            ``True`` if the remaining checks should be skipped; ``False``
            otherwise.
        """
        return self._terminate


def empty_prefix_lines(doc: Node):
    i = None
    for i, row in enumerate(doc.lines):
        if row.strip():
            break
    return i


def empty_suffix_lines(doc: Node):
    i = None
    for i, row in enumerate(reversed(doc.lines)):
        if row.strip():
            break
    return i


class Check(metaclass=ABCMeta):
    """Abstract docstring check."""

    @abstractmethod
    def validate(self, doc: Node) -> Generator[Error, None, None]:
        """
        Ensure that the docstring is valid.

        Parameters
        ----------
        doc : Docstring
            The docstring to validate.

        Yields
        ------
        Error
            The error.
        """
        yield


class GL08Check(Check):
    """Check that the class/function/module has a docstring."""

    def validate(self, node: Node) -> Optional[Error]:
        if not node.has_docstring:
            yield Error(
                start=node.start,
                end=node.end,
                docstring=None,
                code="GL08",
                message=f"The {node.type} does not have a docstring",
                terminate=True,
            )


class GL01Check(Check):
    """Check for too many/few empty prefix lines."""

    def validate(self, node: Node) -> Optional[Error]:
        doc = node.docstring
        if node.has_docstring and empty_prefix_lines(doc) != 1 and "\n" in doc.raw:
            yield Error(
                docstring=doc,
                start=doc.start,
                code="GL01",
                message="Docstring should start on a new line.",
            )


# TODO: Incorrectly flagged if docstring start on the same line as """.
class GL02Check(Check):
    def validate(self, node: Node) -> Optional[Error]:
        doc = node.docstring
        if empty_suffix_lines(doc) != 1 and "\n" in doc.raw:
            yield Error(
                start=doc.end.move_line(line=-1),
                docstring=doc,
                code="GL02",
                message="Docstring should end one line before the closing quotes.",
                suggestion="Remove empty line.",
            )


class GL03Check(Check):
    def validate(self, node: Node) -> Optional[Error]:
        doc = node.docstring
        prev = True
        for i, row in enumerate(doc.lines):
            if not prev and not row.strip() and i < len(doc.lines) - 1:
                yield Error(
                    start=doc.start.move_line(line=i),
                    docstring=doc,
                    code="GL03",
                    message="Docstring should not contain double line breaks.",
                )
            prev = row.strip()
        return None


class GL04Check(Check):
    def validate(self, node: Node) -> Optional[Error]:
        doc = node.docstring
        for i, line in enumerate(doc.lines):
            first = next(re.finditer("^\s*(\t)", line), None)
            if first:
                yield Error(
                    start=doc.start.move_line(line=i, column=first.start(0)),
                    end=doc.start.move_line(line=i, column=first.end(0)),
                    docstring=doc,
                    code="GL04",
                    message="Docstring line should not start with tabs.",
                )


class GL06Check(Check):
    def validate(self, node: Node) -> Optional[Error]:
        doc = node.docstring
        for section in doc.sections:
            if section.name not in _ALLOWED_SECTIONS:
                yield Error(
                    docstring=doc,
                    start=section.start_header,
                    end=section.end_header,
                    code="GL06",
                    message="Docstring contains unexpected section.",
                    suggestion="Remove section or fix spelling.",
                )


class GL07Check(Check):
    def validate(self, node: Node) -> Generator[Error, None, None]:
        doc = node.docstring
        expected_sections = [
            section for section in _ALLOWED_SECTIONS if section in doc.sections
        ]
        actual_sections = [
            section for section in doc.sections if section.name in _ALLOWED_SECTIONS
        ]
        for expected_section, actual_section in zip(expected_sections, actual_sections):
            if expected_section != actual_section.name:
                yield Error(
                    docstring=doc,
                    start=actual_section.start_header,
                    end=actual_section.end_header,
                    code="GL07",
                    message="Sections are in the wrong order.",
                    suggestion=f"Section should be `{expected_section}`",
                )


def find_deprectated(paragraph: DocStringParagraph):
    if paragraph:
        for i, line in enumerate(paragraph.data):
            if ".. deprecated:: " in line:
                yield paragraph.start.move(line=i)


class GL10(Error):
    @property
    def message(self):
        return "reST directives must be followed by two colon."

    @property
    def suggestion(self):
        return "Fix the directive by inserting `::`"


class GL09Check(Check):
    def validate(self, node: Node) -> Generator[Error, None, None]:
        doc = node.docstring
        if doc.summary:
            deprecated_markers = list(
                itertools.chain(
                    find_deprectated(doc.summary.content),
                    find_deprectated(doc.summary.extended_content),
                )
            )

            if deprecated_markers:
                paragraph = (
                    doc.summary.extended_content
                    if doc.summary.extended_content is not None
                    else doc.summary
                )
                if deprecated_markers[0].line != paragraph.start.line:
                    yield Error(
                        docstring=doc,
                        start=deprecated_markers[0],
                        end=deprecated_markers[0].move(column=15),
                        code="GL09",
                        message="Deprecation warning should precede extended summary.",
                        suggestion=(
                            f"Move deprecation warning to line {paragraph.start.line}"
                        ),
                    )


class GL11Check(Check):
    def validate(self, node: Node) -> Generator[Error, None, None]:
        doc = node.docstring
        if doc.summary:
            marks = list(
                itertools.chain(
                    find_deprectated(doc.summary.content),
                    find_deprectated(doc.summary.extended_content),
                )
            )
            if len(marks) > 1:
                paragraph = (
                    doc.summary.extended_content
                    if doc.summary.extended_content is not None
                    else doc.summary
                )
                offenders = [
                    mark for mark in marks if mark.line != paragraph.start.line
                ]
                # TODO: improve suggestion if there is no correct deprecation warning.
                if len(offenders) == 1:
                    where = f"line {offenders[0].line}"
                else:
                    offending_lines = ", ".join(
                        str(offender.line) for offender in offenders[:-1]
                    )
                    where = f"lines {offending_lines} and {offenders[-1].line}"

                for mark in offenders:
                    yield Error(
                        docstring=doc,
                        start=mark,
                        end=mark.move(column=15),
                        code="GL11",
                        message=(
                            "Summary should only contain a single deprecation "
                            "warning."
                        ),
                        suggestion=(
                            f"Remove duplicate deprecation warnings on {where}"
                        ),
                    )


DIRECTIVES = ["versionadded", "versionchanged", "deprecated"]
DIRECTIVE_PATTERN = re.compile(
    r"^\s*\.\. ({})(?!::)".format("|".join(DIRECTIVES)), re.I | re.M
)


class GL10Check(Check):
    def validate(self, node: Node) -> Generator[Error, None, None]:
        doc = node.docstring
        for i, line in enumerate(doc.lines):
            match = re.match(DIRECTIVE_PATTERN, line)
            if match:
                yield GL10(
                    docstring=doc,
                    start=doc.start.move(line=i, absolute_column=match.start(1)),
                    end=doc.start.move(line=i, absolute_column=match.end(1) + 1),
                )


class SS01Check(Check):
    def validate(self, node: Node) -> Generator[Error, None, None]:
        doc = node.docstring
        if not doc.summary.content.data:
            yield Error(
                docstring=doc,
                code="SS01",
                message="No summary found.",
                suggestion="Add a short summary in a single line",
            )


class SS02Check(Check):
    def validate(self, node: Node) -> Generator[Error, None, None]:
        doc = node.docstring
        data = doc.summary.content.data
        if data:
            first_line = data[0].strip()
            if first_line[0].isalpha() and not first_line[0].isupper():
                yield Error(
                    docstring=doc,
                    start=doc.summary.content.start,
                    code="SS02",
                    message="Summary does not start with a capital letter",
                    suggestion=(
                        f"Replace `{first_line[0]}` with `{first_line[0].upper()}`"
                    ),
                )


class SS03Check(Check):
    def validate(self, node: Node) -> Generator[Error, None, None]:
        doc = node.docstring
        data = doc.summary.content.data
        if data:
            if data[0][-1] != ".":
                yield Error(
                    docstring=doc,
                    start=doc.summary.content.start,
                    end=doc.summary.content.start.move(
                        absolute_column=len(data[0]) + 1
                    ),
                    code="SS03",
                    message="Summary does not end with a period.",
                    suggestion="Insert a period.",
                )


class SS04Check(Check):
    def validate(self, node: Node) -> Generator[Error, None, None]:
        doc = node.docstring
        data = doc.summary.content.data
        if data:
            indent = doc.indent
            first_line_indent = len(data[0]) - len(data[0].lstrip())
            if first_line_indent != indent:
                yield Error(
                    docstring=doc,
                    start=doc.summary.content.start.move(
                        absolute_column=indent,
                    ),
                    end=doc.summary.content.start.move(
                        absolute_column=first_line_indent
                    ),
                    code="SS04",
                    message="Summary contains heading whitespaces.",
                    suggestion="Remove leading whitespace.",
                )


class SS05Check(Check):
    def validate(self, node: Node) -> Generator[Error, None, None]:
        doc = node.docstring
        data = doc.summary.content.data
        if node.type in ["function", "method"] and data:
            match = re.match(r"^\s*(.*?)\s+", data[0])
            if match:
                word = match.group(1).strip()
                if word != "" and word[-1] == "s":
                    yield Error(
                        docstring=doc,
                        start=doc.start.move(absolute_column=match.start(1)),
                        end=doc.start.move(absolute_column=match.end(1)),
                        message=(
                            "Summary must start with infinitive verb, not third person."
                        ),
                        suggestion="Remove third person `s`",
                        code="SS05",
                    )


class SS06Check(Check):
    def validate(self, node: Node) -> Generator[Error, None, None]:
        data = node.docstring.summary.content.data
        if len(data) > 1:
            yield Error(
                docstring=node.docstring,
                start=node.docstring.summary.content.start,
                end=node.docstring.summary.content.end,
                code="SS06",
                message="Summary should fit in a single line",
            )


class ES01Check(Check):
    def validate(self, node: Node) -> Generator[Error, None, None]:
        doc = node._docstring
        if not doc.summary.extended_content.data:
            yield Error(
                docstring=doc,
                code="ES01",
                message="No extended summary found.",
            )


class ParameterCheck(Check):
    def validate(self, node: Node) -> Generator[Error, None, None]:
        if node.has_docstring and node.type in ("function", "method", "class"):
            yield from self._validate_parameters(
                node.docstring,
                node.parameters,
            )


class PR01Check(ParameterCheck):
    def _validate_parameters(
        self,
        docstring: DocString,
        expected_parameters: List[Parameter],
    ) -> Generator[Error, None, None]:
        parameters: DocStringSection = docstring.get_section("Parameters")

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
                    docstring=docstring,
                    start=start,
                    end=end,
                    code="PR01",
                    message=f"Parameter `{expected.name}` should be documented.",
                    suggestion=f"Add documentation for `{expected.name}`.",
                )


class PR02Check(ParameterCheck):
    def _validate_parameters(
        self,
        docstring: DocString,
        expected_parameters: List[Parameter],
    ) -> Generator[Error, None, None]:
        parameters: DocStringSection = docstring.get_section("Parameters")
        if parameters:
            expected_parameters = [p.name for p in expected_parameters]
            for actual_parameter in parameters.contents:
                if actual_parameter.name.value not in expected_parameters:
                    yield Error(
                        docstring=docstring,
                        start=actual_parameter.name.start,
                        end=actual_parameter.name.end,
                        code="PR02",
                        message=(
                            f"Parameter `{actual_parameter.name.value}` does "
                            "not exist in the declaration."
                        ),
                        suggestion=f"Remove or declare `{actual_parameter.name.value}`.",
                    )


class PR03Check(ParameterCheck):
    def _validate_parameters(
        self,
        docstring: DocString,
        declared_parameters: List[Parameter],
    ) -> Generator[Error, None, None]:
        parameters = docstring.get_section("Parameters")
        if parameters:
            if len(parameters.contents) == len(declared_parameters):
                for doc_parameter, dec_parameter in zip(
                    parameters.contents, declared_parameters
                ):
                    if doc_parameter.name.value != dec_parameter.name:
                        yield Error(
                            docstring=docstring,
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


class PR04Check(ParameterCheck):
    def _validate_parameters(
        self,
        docstring: DocString,
        declared_parameters: List[Parameter],
    ) -> Generator[Error, None, None]:
        parameters = docstring.get_section("Parameters")
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
                        docstring=docstring,
                        start=parameter.name.start,
                        end=parameter.name.end,
                        code="PR04",
                        message="Parameter `{0}` should have a type".format(
                            parameter.name.value
                        ),
                        suggestion=suggestion,
                    )


class PR05Check(ParameterCheck):
    def _validate_parameters(
        self,
        docstring: DocString,
        declared_parameters: List[Parameter],
    ) -> Generator[Error, None, None]:
        parameters: DocStringSection = docstring.get_section("Parameters")
        for parameter in parameters.contents:
            if parameter.types:
                type = parameter.types[-1]
                if type.value.strip()[-1] == ".":
                    message = "Parameter `{}` type should not finish with `.`.".format(
                        parameter.name.value
                    )
                    yield Error(
                        docstring=docstring,
                        start=type.end,
                        end=type.end,
                        code="PR05",
                        message=message,
                        suggestion="Remove `.`.",
                    )


_COMMON_TYPE_ERRORS = {"integer": "int", "boolean": "bool", "string": "str"}


class PR06Check(ParameterCheck):
    def _validate_parameters(
        self,
        docstring: DocString,
        declared_parameters: List[Parameter],
    ) -> Generator[Error, None, None]:
        parameters = docstring.get_section("Parameters")
        for parameter in parameters.contents:
            if parameter.types:
                for type in parameter.types:
                    if type.value in _COMMON_TYPE_ERRORS:
                        yield Error(
                            docstring=docstring,
                            start=type.start,
                            end=type.end,
                            code="PR06",
                            message="Parameter `{}` uses wrong type.".format(
                                parameter.name.value
                            ),
                            suggestion="Use `{}` instead of `{}`.".format(
                                _COMMON_TYPE_ERRORS[type.value], type.value
                            ),
                        )
                    elif type.value == "{}":
                        yield Error(
                            docstring=docstring,
                            start=type.start,
                            end=type.end,
                            code="PR06",
                            message="Parameter `{}` uses empty choice.".format(
                                parameter.name.value
                            ),
                            suggestion="Insert correct choices.",
                        )


_CHECKS = OrderedDict(
    GL08=GL08Check(),  # Terminates if fails
    GL01=GL01Check(),
    GL02=GL02Check(),
    GL03=GL03Check(),
    GL04=GL04Check(),
    GL06=GL06Check(),
    GL07=GL07Check(),
    GL09=GL09Check(),
    GL10=GL10Check(),
    GL11=GL11Check(),
    SS01=SS01Check(),
    SS02=SS02Check(),
    SS03=SS03Check(),
    SS04=SS04Check(),
    SS05=SS05Check(),
    SS06=SS06Check(),
    ES01=ES01Check(),
    PR01=PR01Check(),
    PR02=PR02Check(),
    PR03=PR03Check(),
    PR04=PR04Check(),
    PR05=PR05Check(),
    PR06=PR06Check(),
)


class Validator:
    def __init__(self, docstring: Node, ignore: list = None) -> None:
        self.docstring = docstring
        self.ignore = ignore if ignore is not None else []
        self.checks = [
            _CHECKS[check] for check in _CHECKS.keys() if check not in self.ignore
        ]

    def validate(self) -> Generator[Error, None, None]:
        self._is_validated = True

        for check in self.checks:
            # print("Running ", check.__class__.__name__)
            for error in check.validate(self.docstring):
                yield error
                if error.terminate:
                    return


class ErrorFormatter:
    def __init__(self):
        self._errors: Mapping[str, Iterable[Error]] = defaultdict(list)

    def add_error(self, file: str, error: Error) -> None:
        self._errors[file].append(error)

    def _format_error(self, file: str, error: Error):
        return "{}:{}:{}:{}:{}: {} {}\n".format(
            file,
            error.start.line,
            error.start.column,
            error.end.line,
            error.end.column,
            error.code,
            error.message,
        )

    def write(self, output: io.TextIOBase) -> None:
        for file, errors in self._errors.items():
            for error in errors:
                output.write(self._format_error(file, error))


class DetailedErrorFormatter(ErrorFormatter):
    def _format_error(self, file: str, error: Error) -> str:
        line = str(error.start.line)
        docstring = error.docstring
        if docstring:
            error_start = error.start.normalize(docstring.start)
            offending_lines = []

            for i in range(max(0, error_start.line - 2), error_start.line + 1):
                if i == 0 and re.match("^\s*$", docstring.lines[i]):
                    continue

                offending_lines.append(
                    "{} | {}\n".format(
                        docstring.start.line + i,
                        docstring.lines[i],
                        # if i > 0
                        # else (" " * docstring.start.column) + '"""',  # FIXME!
                    )
                )
            offending_line = "".join(offending_lines)

            line_pad = (" " * len(line)) + " | " + (" " * error.start.column)
            underline_len = error.end.column - error.start.column
            if underline_len == 0:
                underline_len = 1
            underline = line_pad + ("^" * underline_len)
            if error.suggestion:
                line_mark = line_pad + (" " * (underline_len - 1)) + "|\n"
                suggestion = (
                    "\n"
                    + line_mark
                    + line_pad
                    + (" " * (underline_len - 1))
                    + error.suggestion
                )
            else:
                suggestion = ""

            return "error[{}]: {}\n{}{}{}\n".format(
                error.code, error.message, offending_line, underline, suggestion
            )
        else:
            return super()._format_error(file, error)
