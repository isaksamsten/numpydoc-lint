import re
import io
from .numpydoc import Docstring, Pos, Section
from typing import Optional, Generator, Iterable, Mapping
from abc import ABCMeta, abstractmethod, abstractproperty
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
    """
    Error dataclass.

    Parameters
    ----------
    start_pos : Pos
        The start position.
    end_pos : Pos
        The end position.
    """

    def __init__(
        self,
        *,
        docstring: Docstring,
        start: Pos = None,
        end: Pos = None,
    ) -> None:
        self.start = start if start is not None else docstring.start
        self.end = end if end is not None else self.start
        self.docstring = docstring

    @abstractproperty
    def code(self) -> str:
        """
        Error code.

        Returns
        -------
        str
            The error code. By default ``self.___class__.__name__``.
        """
        return self.__class__.__name__.upper()

    @abstractproperty
    def message(self) -> str:
        """
        Message.

        Returns
        -------
        str
            The message.
        """
        pass

    @property
    def details(self) -> Optional[str]:
        """
        Details on the error.

        Returns
        -------
        Optional[str]
            The details.
        """
        return None

    @property
    def suggestion(self) -> str:
        """
        A suggestion.

        Returns
        -------
        str
            The suggestion to fix the error.
        """
        return None

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
        return False


class GL08(Error):
    @property
    def message(self) -> str:
        return f"The {self.docstring.type} does not have a docstring"

    @property
    def terminate(self) -> bool:
        return True


class GL01(Error):
    @property
    def message(self):
        return "Docstring should start on a new line."

    @property
    def suggestion(self):
        return ""


class GL02(Error):
    @property
    def message(self):
        return "Docstring should end one line before the closing quotes."


class GL03(Error):
    @property
    def message(self):
        return "Docstring should not contain double line breaks."


class GL04(Error):
    @property
    def message(self):
        return "Docstring line should not start with tabs."


class GL06(Error):
    def __init__(self, *, docstring: Docstring, section: Section):
        super().__init__(start=section.start, end=section.end, docstring=docstring)
        self.section = section

    @property
    def message(self):
        return f"Docstring contains unexpected section ('{self.section.name}')"


class GL07(Error):
    def __init__(
        self, docstring: Docstring, expected_section: str, actual_section: Section
    ) -> None:
        super().__init__(
            docstring=docstring, start=actual_section.start, end=actual_section.end
        )
        self.expected_section = expected_section

    @property
    def message(self):
        return "Sections are in the wrong order"

    @property
    def suggestion(self):
        return f"Section should be `{self.expected_section}`"


def empty_prefix_lines(doc: Docstring):
    i = None
    if doc.has_docstring:
        for i, row in enumerate(doc.docstring_lines):
            if row.strip():
                break
    return i


def empty_suffix_lines(doc: Docstring):
    i = None
    if doc.has_docstring:
        for i, row in enumerate(reversed(doc.docstring_lines)):
            if row.strip():
                break
    return i


class Check(metaclass=ABCMeta):
    """Abstract docstring check."""

    @abstractmethod
    def validate(self, doc: Docstring) -> Generator[Error, None, None]:
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

    def validate(self, doc: Docstring) -> Optional[Error]:
        if not doc.has_docstring:
            yield GL08(start=doc.start, end=doc.end, docstring=doc)


class GL01Check(Check):
    """Check for too many/few empty prefix lines."""

    def validate(self, doc: Docstring) -> Optional[Error]:
        if empty_prefix_lines(doc) != 1 and "\n" in doc.raw_docstring:
            yield GL01(start=doc.start, docstring=doc)


class GL02Check(Check):
    def validate(self, doc: Docstring) -> Optional[Error]:
        if empty_suffix_lines(doc) != 1 and "\n" in doc.raw_docstring:
            yield GL02(start=doc.end.move_line(line=-1), docstring=doc)


class GL03Check(Check):
    def validate(self, doc: Docstring) -> Optional[Error]:
        prev = True
        for i, row in enumerate(doc.docstring_lines):
            if not prev and not row.strip() and i < len(doc.docstring_lines) - 1:
                yield GL03(start=doc.start.move_line(line=i), docstring=doc)
            prev = row.strip()
        return None


class GL04Check(Check):
    def validate(self, doc: Docstring) -> Optional[Error]:
        for i, line in enumerate(doc.docstring_lines):
            first = next(re.finditer("^\s*(\t)", line), None)
            if first:
                yield GL04(
                    start=doc.start.move_line(line=i, column=first.start(0)),
                    end=doc.start.move_line(line=i, column=first.end(0)),
                    docstring=doc,
                )


class GL06Check(Check):
    def validate(self, doc: Docstring) -> Optional[Error]:
        for section in doc.section_titles:
            if section.name not in _ALLOWED_SECTIONS:
                yield GL06(docstring=doc, section=section)


class GL07Check(Check):
    def validate(self, doc: Docstring) -> Generator[Error, None, None]:
        expected_sections = [
            section for section in _ALLOWED_SECTIONS if section in doc.section_titles
        ]
        actual_sections = [
            section
            for section in doc.section_titles
            if section.name in _ALLOWED_SECTIONS
        ]
        for expected_section, actual_section in zip(expected_sections, actual_sections):
            if expected_section != actual_section.name:
                yield GL07(
                    docstring=doc,
                    expected_section=expected_section,
                    actual_section=actual_section,
                )


_CHECKS = OrderedDict(
    GL08=GL08Check(),
    GL01=GL01Check(),
    GL02=GL02Check(),
    GL03=GL03Check(),
    GL04=GL04Check(),
    GL06=GL06Check(),
    GL07=GL07Check(),
)


class Validator:
    def __init__(self, docstring: Docstring, ignore: list = None) -> None:
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
        return "{}:{}:{}: {} {}\n".format(
            file,
            error.start.line,
            error.start.column,
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
        if docstring.has_docstring:
            error_start = error.start.normalize(docstring.start)
            offending_lines = []

            for i in range(max(0, error_start.line - 2), error_start.line + 1):
                offending_lines.append(
                    "{} | {}\n".format(
                        docstring.start.line + i, docstring.docstring_lines[i]
                    )
                )
            offending_line = "".join(offending_lines)

            line_pad = (" " * len(line)) + " | " + (" " * error.start.column)
            underline_len = error.end.column - error.start.column
            if underline_len == 0:
                underline_len = 1
            underline = line_pad + ("^" * underline_len) + "\n"
            if error.suggestion:
                line_mark = line_pad + (" " * (underline_len - 1)) + "|\n"
                suggestion = (
                    line_mark
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
