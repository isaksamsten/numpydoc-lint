import sys
import re
from typing import Iterable, Optional
from abc import ABCMeta, abstractproperty
import parso

from dataclasses import dataclass

SUMMARY_SIGNATURE_PATTERN = re.compile(r"^([\w., ]+=)?\s*[\w\.]+\(.*\)$")


def strip_blank_lines(l):
    """Remove leading and trailing blank lines from a list of lines."""
    while l and not l[0].strip():
        del l[0]
    while l and not l[-1].strip():
        del l[-1]
    return l


class Reader:
    r"""A line-based string reader.

    Parameters
    ----------
    data : str
        String with lines separated by '\n'.

    """

    def __init__(self, data):
        if isinstance(data, list):
            self._str = data
        else:
            self._str = data.split("\n")  # store string as list of lines

        self.reset()

    def __getitem__(self, n):
        return self._str[n]

    def reset(self):
        self._l = 0  # current line nr

    def read(self):
        if not self.eof():
            out = self[self._l]
            self._l += 1
            return out
        else:
            return ""

    def seek_next_non_empty_line(self):
        for l in self[self._l :]:
            if l.strip():
                break
            else:
                self._l += 1

    def eof(self):
        return self._l >= len(self._str)

    def read_to_condition(self, condition_func):
        start = self._l
        for line in self[start:]:
            if condition_func(line):
                return self[start : self._l]
            self._l += 1
            if self.eof():
                return self[start : self._l + 1]
        return []

    def read_to_next_empty_line(self):
        self.seek_next_non_empty_line()

        def is_empty(line):
            return not line.strip()

        return self.read_to_condition(is_empty)

    def read_to_next_unindented_line(self):
        def is_unindented(line):
            return line.strip() and (len(line.lstrip()) == len(line))

        return self.read_to_condition(is_unindented)

    # def strip(self, doc):
    #     i = 0
    #     j = 0
    #     for i, line in enumerate(doc):
    #         if line.strip():
    #             break
    #
    #     for j, line in enumerate(doc[::-1]):
    #         if line.strip():
    #             break
    #
    #     return doc[i : len(doc) - j]

    def is_at_section(self):
        self.seek_next_non_empty_line()

        if self.eof():
            return False

        l1 = self.peek().strip()  # e.g. Parameters

        if l1.startswith(".. index::"):
            return True

        l2 = self.peek(1).strip()  # ---------- or ==========
        if len(l2) >= 3 and (set(l2) in ({"-"}, {"="})) and len(l2) != len(l1):
            snip = "\n".join(self._str[:2]) + "..."
            self._error_location(
                f"potentially wrong underline length... \n{l1} \n{l2} in \n{snip}",
                error=False,
            )
        return l2.startswith("-" * len(l1)) or l2.startswith("=" * len(l1))

    def read_to_next_section(self):
        section = self.read_to_next_empty_line()

        while not self.is_at_section() and not self.eof():
            if not self.peek(-1).strip():  # previous line was empty
                section += [""]

            section += self.read_to_next_empty_line()

        return section

    def peek(self, n=0):
        if self._l + n < len(self._str):
            return self[self._l + n]
        else:
            return ""

    def is_empty(self):
        return not "".join(self._str).strip()


def strip_empty_lines(contents):
    i = 0
    j = 0
    for i, line in enumerate(contents):
        if line.strip():
            break

    for j, line in enumerate(contents[::-1]):
        if line.strip():
            break

    return contents[i : len(contents) - j]


class ParseError(Exception):
    def __str__(self):
        message = self.args[0]
        if hasattr(self, "docstring"):
            message = f"{message} in {self.docstring!r}"
        return message


@dataclass
class Pos:
    """Represent a Line:Column position."""

    line: int
    column: int

    def move_line(self, *, line=None, column=None):
        return Pos(
            self.line + line if line is not None else self.line,
            column if column is not None else self.column,
        )

    def move_column(self, *, line=None, column=None):
        return Pos(
            line if line is not None else self.line,
            self.column + column if column is not None else self.column,
        )

    def move(self, *, line=None, column=None, absolute_line=None, absolute_column=None):
        if line is not None:
            line = self.line + line
        elif absolute_line is not None:
            line = absolute_line
        else:
            line = self.line

        if column is not None:
            column = self.column + column
        elif absolute_column is not None:
            column = absolute_column
        else:
            column = self.column
        return Pos(line, column)

    def normalize(self, relative: "Pos"):
        return Pos(
            line=self.line - relative.line,
            column=self.column,
        )


@dataclass(frozen=True, kw_only=True)
class Section:
    start_header: Pos
    end_header: Pos
    name: str
    valid_heading: bool
    contents: list[str]
    start_contents: Pos
    end_contents: Pos

    def __eq__(self, other) -> bool:
        if isinstance(other, str):
            return self.name == other
        else:
            return self.name == other.name

    def __hash__(self):
        return hash(self.name)


@dataclass(frozen=True, kw_only=True)
class Paragraph:
    start: Pos
    end: Pos
    data: list[str]


@dataclass(frozen=True, kw_only=True)
class Summary:
    content: Paragraph
    extended_content: Paragraph


_PYTHON_VERSION = "{}.{}.{}".format(*sys.version_info)


def format_raw_doc(doc: str):
    first_delim = doc.find('"')
    last_delim = doc.rfind('"')

    first_r = doc.find("r")
    first_delim_len = 3
    if first_r > -1 and first_delim - first_r == 1:  # r-string
        first_delim = first_r
        first_delim_len = 4
    return (
        first_delim,
        doc[:first_delim] + doc[first_delim + first_delim_len : last_delim - 2],
    )


class Docstring(metaclass=ABCMeta):
    def __init__(self, node):
        self.node = node
        self._doc_node = self.get_doc_node()

        self.indent, self._raw_docstring = (
            format_raw_doc(self._doc_node.get_code())
            if self._doc_node is not None
            else (None, None)
        )
        self._reader = (
            Reader(self._raw_docstring) if self._raw_docstring is not None else None
        )

        self._docstring = None
        self._docstring_lines = None
        self._sections = None
        self._summary = None
        self._extended_summary = None

    def get_doc_node(self):
        if self.node.type == "file_input":
            node = self.node.children[0]
        elif self.node.type in ("funcdef", "classdef"):
            node = self.node.children[self.node.children.index(":") + 1]
            if node.type == "suite":  # Normally a suite
                node = node.children[1]  # -> NEWLINE stmt
        else:  # ExprStmt
            simple_stmt = self.node.parent
            simple_stmt = simple_stmt.get_next_sibling()
            if simple_stmt.start_pos[0] == self.node.start_pos[0] + 1:
                node = simple_stmt
            else:
                return None

        if node.type == "simple_stmt":
            node = node.children[0]
        if node.type == "string":
            return node
        return None

    @property
    def has_docstring(self):
        return self.raw_docstring is not None

    @abstractproperty
    def type(self):
        pass

    @property
    def extended_summary(self):
        self.summary
        return self._extended_summary

    @property
    def summary(self) -> Summary:
        if self._summary is None:
            reader = self._reader
            reader.reset()
            if reader.is_at_section():
                self._summary = None
            else:
                start = self.start.move_line(line=reader._l)
                while True:
                    content = reader.read_to_next_empty_line()
                    summary_str = " ".join([s.strip() for s in content]).strip()
                    if SUMMARY_SIGNATURE_PATTERN.match(summary_str):
                        if not reader.is_at_section():
                            continue
                    else:
                        break
                content = Paragraph(
                    start=start, end=self.start.move(line=reader._l), data=content
                )
                if not reader.is_at_section():
                    start = self.start.move(line=reader._l)
                    extended_content = reader.read_to_next_section()
                    extended_content = Paragraph(
                        start=start,
                        end=self.start.move(line=reader._l),
                        data=extended_content,
                    )
                else:
                    extended_content = None

                self.start.move_line(line=reader._l)
                self._summary = Summary(
                    content=content, extended_content=extended_content
                )

        return self._summary

    @property
    def sections(self) -> list[Section]:
        if self._sections is None:
            self._sections = []
            self._reader.reset()
            while not self._reader.eof():
                line = self._reader._l
                data = self._reader.read_to_next_section()
                if not data:
                    self._sections = []
                    break

                column = len(data[0]) - len(data[0].lstrip())

                if len(data) > 1:
                    name = data[0].strip()
                    underline = data[1].strip()
                    if len(name) == len(underline):
                        valid_heading = re.match(r"^-*$", data[1]) is not None
                        self._sections.append(
                            Section(
                                name=name,
                                valid_heading=valid_heading,
                                start_header=self.start.move_line(
                                    line=line, column=column
                                ),
                                end_header=self.start.move_line(
                                    line=line, column=column + len(name)
                                ),
                                contents=strip_empty_lines(data[:2]),
                                start_contents=self.start.move_line(line=line),
                                end_contents=self.start.move_line(line=len(data) - 2),
                            )
                        )

        return self._sections

    def get_section(self, name) -> Optional[Section]:
        for section in self.sections:
            if section.name == name:
                return section

        return None

    @property
    def raw_docstring(self) -> str:
        return self._raw_docstring

    @property
    def docstring_lines(self) -> list[str]:
        if self.has_docstring and self._docstring_lines is None:
            self._docstring_lines = self.raw_docstring.split("\n")
        return self._docstring_lines

    @property
    def start(self) -> Pos:
        if self.has_docstring:
            line, column = self._doc_node.start_pos
        else:
            line, column = self.node.start_pos
        return Pos(line, column)

    @property
    def end(self) -> Pos:
        if self.has_docstring:
            line, column = self._doc_node.end_pos
        else:
            line, column = self.node.end_pos
        return Pos(line, column)

    @property
    def name(self):
        return self.node.name.value


class ModuleDocstring(Docstring):
    @property
    def name(self):
        return None

    @property
    def type(self):
        return "module"


class ConstantDocstring(Docstring):
    @property
    def name(self):
        return self.node.children[0].value

    @property
    def type(self):
        return "constant"


class ClassDocstring(Docstring):
    @property
    def parameters(self):
        init = None
        for func in self.node.iter_funcdefs():
            name = func.children[1]
            if name.type == "name" and name.value == "__init__":
                init = func
                break
        return init.get_params()[1:]  # exclude self

    @property
    def attributes(self):
        return None

    @property
    def type(self):
        return "class"


class FunctionDocstring(Docstring):
    @property
    def parameters(self):
        return self.node.get_params()

    @property
    def type(self):
        return "function"


class MethodDocstring(FunctionDocstring):
    @property
    def parameters(self):
        return self.node.get_params()[1:]  # exclude self

    @property
    def type(self):
        return "method"


class DocstringParser:
    """[TODO:description].

    Attributes
    ----------
    python_version : [TODO:attribute]
    print_errors : [TODO:attribute]
    """

    def __init__(self, python_version=None, print_errors=False) -> None:
        self.python_version = python_version or _PYTHON_VERSION
        self.print_errors = print_errors

    def _load_grammar(self) -> parso.Grammar:
        """
        Parse the code using the grammar of the currently running Python interpreter.

        Returns
        -------
        parso.Grammar
            The grammar for the current Python version.
        """
        return parso.load_grammar(version=self.python_version)

    def _parse(self, code: str) -> Optional[parso.tree.BaseNode]:
        """Parse the Python code using the grammar of the current Python interpreter.

        Parameters
        ----------
        code : str
            The Python code.

        Returns
        -------
        Optional[parso.tree.BaseNode]
            The root node.
        """
        grammar = self._load_grammar()
        node = grammar.parse(code)
        errors: Iterable[parso.normalizer.Issue] = grammar.iter_errors(node)
        has_errors = False
        for error in errors:
            has_errors = True
            if not self.print_errors:
                return None
            print(f"{error.start_pos}: {error.message}")

        return None if has_errors else node

    def iter_docstring(self, code: str):
        module = self._parse(code).get_root_node()
        yield ModuleDocstring(module)

        for const in module._search_in_scope("expr_stmt"):
            yield ConstantDocstring(const)

        for func in module.iter_funcdefs():
            yield FunctionDocstring(func)

        for klass in module.iter_classdefs():
            yield ClassDocstring(klass)
            for func in klass.iter_funcdefs():
                yield MethodDocstring(func)
