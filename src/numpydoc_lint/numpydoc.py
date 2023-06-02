import re
import sys
from abc import ABCMeta, abstractproperty
from typing import List, Optional, Tuple
from ._model import (
    DocString,
    DocStringName,
    DocStringSummary,
    DocStringSection,
    DocStringParagraph,
    DocStringParameter,
    Error,
    Parameter,
    Name,
    Pos,
)

import parso

# FIXME: These have been generated by AI. Checka and replace as needed.
_MAGIC_METHODS = [
    "__abs__",
    "__add__",
    "__and__",
    "__bool__",
    "__ceil__",
    "__class__",
    "__delattr__",
    "__dir__",
    "__divmod__",
    "__doc__",
    "__eq__",
    "__float__",
    "__floor__",
    "__floordiv__",
    "__format__",
    "__ge__",
    "__getattribute__",
    "__getnewargs__",
    "__gt__",
    "__hash__",
    "__index__",
    "__init__",
    "__init_subclass__",
    "__int__",
    "__invert__",
    "__le__",
    "__lshift__",
    "__lt__",
    "__mod__",
    "__mul__",
    "__ne__",
    "__neg__",
    "__new__",
    "__or__",
    "__pos__",
    "__pow__",
    "__radd__",
    "__rand__",
    "__rdivmod__",
    "__reduce__",
    "__reduce_ex__",
    "__repr__",
    "__rfloordiv__",
    "__rlshift__",
    "__rmod__",
    "__rmul__",
    "__ror__",
    "__round__",
    "__rpow__",
    "__rrshift__",
    "__rshift__",
    "__rsub__",
    "__rtruediv__",
    "__rxor__",
    "__setattr__",
    "__sizeof__",
    "__str__",
    "__sub__",
    "__subclasshook__",
    "__truediv__",
    "__trunc__",
    "__xor__",
    "__init_subclass__",
]
SUMMARY_SIGNATURE_PATTERN = re.compile(r"^([\w., ]+=)?\s*[\w\.]+\(.*\)$")


class Reader:
    def __init__(self, data):
        self._lines = data
        self._current_line = 0

    def __getitem__(self, n):
        return self._lines[n]

    def read(self):
        if not self.eof():
            out = self[self._current_line]
            self._current_line += 1
            return out
        else:
            return ""

    def eof(self):
        return self._current_line >= len(self._lines)

    def read_to_condition(self, condition_func):
        start = self._current_line
        for line in self[start:]:
            if condition_func(line):
                return self[start : self._current_line]
            self._current_line += 1
            if self.eof():
                return self[start : self._current_line + 1]
        return []

    def read_to_next_unindented_line(self):
        def is_unindented(line):
            return line.strip() and (len(line.lstrip()) == len(line))

        return self.read_to_condition(is_unindented)

    def read_to_next_blank(self):
        result = [self.read_next()]
        while self.peek().strip() and not self.eof():
            result.append(self.read_next())
        return result

    def read_to_eof(self):
        data = self._lines[self._current_line :]
        self._current_line = len(self._lines)
        return data

    def is_at_section(self):
        if self.eof():
            return False

        l1 = self.peek().strip()  # e.g. Parameters
        if not l1.strip():
            return False

        if l1.startswith(".. index::"):
            return True

        l2 = self.peek(1).strip()  # ---------- or ==========
        if len(l2) >= 3 and (set(l2) in ({"-"}, {"="})) and len(l2) != len(l1):
            # TODO: add as error
            pass
        return l2.startswith("-" * len(l1)) or l2.startswith("=" * len(l1))

    def read_next(self):
        line = self._lines[self._current_line]
        self._current_line += 1
        return line

    def read_to_next_header(self):
        result = [self.read_next()]
        while not self.is_at_section() and not self.eof():
            result.append(self.read_next())
        return result

    def peek(self, n=0):
        if 0 <= self._current_line + n < len(self._lines):
            return self[self._current_line + n]
        else:
            return ""

    def is_empty(self):
        return not "".join(self._lines).strip()


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


_PYTHON_VERSION = "{}.{}.{}".format(*sys.version_info)


def _format_raw_doc(doc: str):
    doc_lines = doc.splitlines()  # if not re.match("^\s*#", line)]
    while doc_lines and re.match("^\s*#|^\s*$", doc_lines[0]):
        doc_lines.pop(0)

    doc = "\n".join(doc_lines)
    first_delim = doc.find('"')
    last_delim = doc.rfind('"')

    first_r = doc.find("r")
    first_delim_len = 3
    if first_r > -1 and first_delim - first_r == 1:  # r-string
        first_delim = first_r
        first_delim_len = 4
        doc = doc.encode("utf-8").decode("raw_unicode_escape")
    else:
        doc = doc.encode("utf-8").decode("unicode_escape")

    doc = doc[:first_delim] + doc[first_delim + first_delim_len : last_delim - 2]
    return (
        first_delim,
        doc.splitlines(),
        doc,
    )


def _get_docstring_node(node):
    if node.type == "file_input":
        node = node.children[0]
    elif node.type in ("funcdef", "classdef"):
        node = node.children[node.children.index(":") + 1]
        if node.type == "suite":  # Normally a suite
            node = node.children[1]  # -> NEWLINE stmt
    else:  # ExprStmt
        simple_stmt = node.parent
        simple_stmt = simple_stmt.get_next_sibling()
        if simple_stmt.start_pos[0] == node.start_pos[0] + 1:
            node = simple_stmt
        else:
            return None

    if node.type == "simple_stmt":
        node = node.children[0]
    if node.type == "string":
        return node
    return None


# https://github.com/numpy/numpydoc/blob/3d4a5831f9f64246404a6dac5c5059a71b020952/numpydoc/docscrape.py#LL273C5-L291C6
_ROLE = r":(?P<role>(py:)?\w+):"
_FUNC_BACK_TICK = r"`(?P<name>(?:~\w+\.)?[a-zA-Z0-9_\.-]+)`"
_FUNC_PLAIN = r"(?P<name2>[a-zA-Z0-9_\.-]+)"
_FUNC_NAME = r"(" + _ROLE + _FUNC_BACK_TICK + r"|" + _FUNC_PLAIN + r")"
_FUNC_NAME_EXT = _FUNC_NAME.replace("role", "rolenext")
_FUNC_NAME_EXT = _FUNC_NAME_EXT.replace("name", "namenext")
_DESCRIPTION = r"(?P<description>\s*:(\s+(?P<desc>\S+.*))?)?\s*$"
_FUNC_PATTERN = re.compile(r"^\s*" + _FUNC_NAME + r"\s*")
_LINE_PATTERN = re.compile(
    r"^\s*"
    + r"(?P<allfuncs>"
    + _FUNC_NAME  # group for all function names
    + r"(?P<morefuncs>([,]\s+"
    + _FUNC_NAME_EXT
    + r")*)"
    + r")"
    + r"(?P<trailing>[,\.])?"  # end of "allfuncs"
    + _DESCRIPTION  # Some function lists have a trailing comma (or period)  '\s*'
)


# TODO: proper return value
def _parse_see_also(
    data: List[str],
    *,
    start: Pos,
    indent: int,
    errors: List[Error],
) -> List[DocStringParameter]:
    def parse_item_name(text):
        match = _FUNC_PATTERN.match(text)
        if not match:
            # TODO: add as error
            raise ParseError(f"Failed to parse {text}")

        role = match.group("role")
        name = match.group("name") if role else match.group("name2")
        return name, role, match.end()

    items = []
    rest = []
    for i, line in enumerate((line[indent:] for line in data)):
        if not line.strip():
            continue

        match = _LINE_PATTERN.match(line)
        description = None
        if match:
            description = match.group("desc")
            if match.group("trailing") and description:
                errors.flag(
                    message="Unexpected comma or period after function list",
                    line=start.line + i,
                )

        if not description and line.startswith(" "):
            rest.append(line.strip())
        elif match:
            funcs = []
            text = match.group("allfuncs")
            while True:
                if not text.strip():
                    break

                name, role, match_end = parse_item_name(text)
                funcs.append((name, role))
                text = text[match_end:].strip()
                if text and text[0] == ",":
                    text = text[1:].strip()

            if description:
                rest = [description]
            else:
                rest = []

            # TODO:
            # 1) add details with line number etc for the functions and names
            # 2) rest as DocStringParagraph
            items.append((funcs, rest))
        else:
            pass
            # errors.flag(
            #     message="Error parsing See also", line=start.line + i, abort=True
            # )

    return items


_NAME_TYPE_PATTERN = re.compile("^\s*(?P<name>.*?)(?:\s*:\s*(?:(?P<type>.*?)\s*)?)?$")

# Split type declaration:
# a, b or c -> a | b | c
# {"A", "B"} or int -> {"A", "B"} | int
# A or B of shape (1, 2) -> A | B of shape (1, 2)
_TYPE_PATTERN = re.compile(r"(?:\s*)(\{.*\}|.+?)(?:\s*(?:,(?![^()]*\))|or|$))")


def _parse_parameter_list(
    data: List[str],
    *,
    start: Pos,
    indent: int,
    # errors: Errors,
    single_element_is_type: bool = False,
) -> List[DocStringParameter]:
    params = []
    reader = Reader([line[indent:] for line in data])
    while not reader.eof():
        parameter_start = start.move(line=reader._current_line)
        header_str = reader.read()
        if not header_str.strip():
            continue

        header = re.match(_NAME_TYPE_PATTERN, header_str)
        if header.group("name"):
            name = DocStringName(
                start=start.move(
                    line=reader._current_line + 1, column=header.start("name")
                ),
                end=start.move(
                    line=reader._current_line + 1, column=header.end("name")
                ),
                value=header.group("name"),
            )
        else:
            name = None
        optional = 0
        if header.group("type"):
            types = []

            for type in re.finditer(_TYPE_PATTERN, header.group("type")):
                type = DocStringName(
                    start=start.move(
                        line=reader._current_line + 1,
                        column=header.start("type") + type.start(1),
                    ),
                    end=start.move(
                        line=reader._current_line + 1,
                        column=header.start("type") + type.end(1),
                    ),
                    value=type.group(1),
                )

                if type.value == "optional":
                    optional += 1
                else:
                    types.append(type)
        else:
            types = None

        if types is None and single_element_is_type:
            name, types = None, [name]

        description_start = start.move(line=reader._current_line)
        description = reader.read_to_next_unindented_line()
        params.append(
            DocStringParameter(
                start=parameter_start,
                end=start.move(line=reader._current_line),
                header=header_str,
                name=name,
                types=types,
                optional=optional,
                description=DocStringParagraph(
                    start=description_start,
                    end=start.move(line=reader._current_line),
                    data=description,
                ),
            )
        )

    return params


def _parse_summary_extended_summary(reader: Reader, start: Pos) -> DocStringSummary:
    summary = DocStringParagraph(
        start=start,
        end=start.move(line=reader._current_line),
        data=reader.read_to_next_blank(),
    )
    extended_start = start.move(line=reader._current_line)
    extended_data = reader.read_to_eof()
    extended_content = DocStringParagraph(
        start=extended_start,
        end=start.move(line=reader._current_line),
        data=extended_data,
    )

    return DocStringSummary(content=summary, extended_content=extended_content)


def _parse_summary(*, reader: Reader, start: Pos) -> DocStringSummary:
    if reader.is_at_section():
        summary = DocStringSummary(content=None, extended_content=None)
    else:
        start = start.move_line(line=reader._current_line)
        content = reader.read_to_next_header()
        summary = _parse_summary_extended_summary(Reader(content), start)
    return summary


def _parse_sections(
    *,
    reader: Reader,
    errors: List[Error],
    start: Pos,
    indent: int,
) -> list[DocStringSection]:
    sections = {}
    while not reader.eof():
        line = reader._current_line

        if reader.peek(-1).strip():
            errors.append(
                Error(
                    start=start.move(line=line),
                    code="ER01",
                    message="Missing blank line before section",
                )
            )
            # errors.flag(
            #     "ER01",
            #     "Missing blank line before section `{}`".format(reader.peek().strip()),
            #     line=start.move(line=line),
            # )

        data = reader.read_to_next_header()
        if not data:
            sections = []
            break

        column = len(data[0]) - len(data[0].lstrip()) + 1

        if len(data) > 1:
            name = data[0].strip()
            underline = data[1].strip()
            if len(name) == len(underline):
                valid = re.match(r"^-*$", underline) and len(name) == len(underline)

                if name in (
                    "Parameters",
                    "Other Parameters",
                    "Attributes",
                    "Methods",
                ):
                    contents = _parse_parameter_list(
                        data[2:],
                        start=start.move(line=line),
                        indent=indent,
                    )
                elif name in (
                    "Returns",
                    "Yields",
                    "Raises",
                    "Warns",
                    "Receives",
                ):
                    contents = _parse_parameter_list(
                        data[2:],
                        start=start.move(line=line),
                        indent=indent,
                        single_element_is_type=True,
                    )
                elif name == "See Also":
                    contents = _parse_see_also(
                        data[2:],
                        start=start.move(line=line),
                        errors=errors,
                        indent=indent,
                    )
                else:
                    contents = strip_empty_lines(data[:2])  # TODO: skip
                sections[name] = DocStringSection(
                    name=name,
                    valid_heading=valid,
                    start_header=start.move_line(line=line, column=column),
                    end_header=start.move_line(line=line, column=column + len(name)),
                    contents=contents,
                    start_contents=start.move_line(line=line),
                    end_contents=start.move_line(line=len(data) - 2),
                )
    return sections


def parse_docstring(node: parso.python.tree.Node) -> Tuple[DocString, List[Error]]:
    errors = []
    start = Pos(node.start_pos[0], node.start_pos[1] + 1)
    end = Pos(node.end_pos[0], node.end_pos[1] + 1)
    indent, lines, raw = _format_raw_doc(node.get_code())
    print(lines)
    reader = Reader(lines)
    summary = _parse_summary(reader=reader, start=start)
    sections = _parse_sections(reader=reader, errors=errors, start=start, indent=indent)
    return (
        DocString(
            start=start,
            end=end,
            indent=indent,
            summary=summary,
            sections=sections,
            raw=raw,
            lines=lines,
        ),
        errors,
    )


class Node(metaclass=ABCMeta):
    def __init__(self, node, filename):
        self.node = node
        self.docstring_node = _get_docstring_node(self.node)
        # if docstring_node is not None:
        #     self._docstring = parse_docstring(docstring_node)
        # else:
        #     self._docstring = None

        self._name = None
        self.filename = filename
        self._noqa = []

    def parse_docstring(self) -> Tuple[Optional[DocString], List[Error]]:
        return (
            parse_docstring(self.docstring_node)
            if self.docstring_node is not None
            else (
                None,
                [
                    Error(
                        start=self.start,
                        end=self.end,
                        code="GL08",
                        message="Missing docstring in public method",
                    )
                ],
            )
        )

    @property
    def private(self):
        return (
            self.name
            and self.name.value
            and self.name.value.startswith("_")
            and not self.magic
        )

    @property
    def magic(self):
        return self.name and self.name.value and self.name.value in _MAGIC_METHODS

    @property
    def has_docstring(self):
        return self.docstring_node is not None

    @property
    def noqa(self) -> List[str]:
        return self._noqa

    @abstractproperty
    def type(self):
        pass

    @property
    def name(self) -> Name:
        if self._name is None:
            start_line, start_col = self.node.name.start_pos
            end_line, end_col = self.node.name.end_pos
            self._name = Name(
                value=self.node.name.value,
                start=Pos(start_line, start_col + 1),
                end=Pos(end_line, end_col + 1),
            )
        return self._name

    @property
    def start(self):
        line, col = self.node.start_pos
        return Pos(line, col + 1)

    @property
    def end(self):
        line, col = self.node.end_pos
        return Pos(line, col + 1)


def _find_noqa(prefix: str) -> List[str]:
    prefix = prefix.strip()
    if prefix:
        prefix = prefix.splitlines()[-1].strip()
        match = re.match(r"#\s+noqa:\s+([\w,\s]+)", prefix)
        if match:
            return re.findall("\w+", match.group(1))

    return []


class Module(Node):
    def __init__(self, node, filename):
        super().__init__(node, filename)
        if self.has_docstring:
            child = self.node.children[0]
            if child.type == "simple_stmt":
                prefix = child.children[0].prefix
                self._noqa = _find_noqa(prefix)

    @property
    def name(self):
        return None

    @property
    def type(self):
        return "module"


class Constant(Node):
    def __init__(self, node, filename):
        super().__init__(node, filename)
        child = self.node.children[0]
        self._noqa = _find_noqa(child.prefix)

    @property
    def name(self):
        return self.node.children[0].value

    @property
    def type(self):
        return "constant"


def _wrap_parameters(params: List[parso.python.tree.Param]):
    return [
        Parameter(
            start=Pos(param.start_pos[0], param.start_pos[1] + 1),
            end=Pos(param.end_pos[0], param.end_pos[1] + 1),
            name=param.name.value,
            default=param.default.get_code(include_prefix=False)
            if param.default is not None
            else None,
            annotation=param.annotation.get_code(include_prefix=False)
            if param.annotation is not None
            else None,
            star_count=param.star_count,
        )
        for param in params
    ]


class Class(Node):
    def __init__(self, node, filename):
        super().__init__(node, filename)
        child = self.node.children[0]
        self._noqa = _find_noqa(child.prefix)

    @property
    def parameters(self):
        init = None
        for func in self.node.iter_funcdefs():
            name = func.children[1]
            if name.type == "name" and name.value == "__init__":
                init = func
                break
        if init:
            return _wrap_parameters(init.get_params()[1:])  # exclude self
        else:
            return []

    @property
    def attributes(self):
        return None

    @property
    def type(self):
        return "class"


class FunctionDocstring(Node):
    def __init__(self, node, filename):
        super().__init__(node, filename)
        child = self.node.children[0]
        self._noqa = _find_noqa(child.prefix)

    @property
    def parameters(self):
        return _wrap_parameters(self.node.get_params())

    @property
    def type(self):
        return "function"

    @property
    def returns(self):
        return len(list(self.node.iter_return_stmts()))

    @property
    def yields(self):
        return len(list(self.node.iter_yield_exprs()))

    @property
    def raises(self):
        return len(list(self.node.iter_raise_stmts()))


class Method(FunctionDocstring):
    @property
    def parameters(self):
        return _wrap_parameters(self.node.get_params()[1:])

    @property
    def type(self):
        return "method"


class Parser:
    def __init__(self, python_version=None) -> None:
        self.python_version = python_version or _PYTHON_VERSION

    def _load_grammar(self) -> parso.Grammar:
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
        errors = [
            f"{error.start_pos}: {error.message}" for error in grammar.iter_errors(node)
        ]
        if errors:
            raise ValueError("\n".join(errors))

        return node

    def iter_docstring(self, file):
        code = file.read()
        filename = file.name if hasattr(file, "name") else "<unkown>"
        module = self._parse(code).get_root_node()
        yield Module(module, filename)

        # FIXME
        # for const in module._search_in_scope("expr_stmt"):
        #     yield Constant(const)

        for func in module.iter_funcdefs():
            yield FunctionDocstring(func, filename)

        for klass in module.iter_classdefs():
            yield Class(klass, filename)
            for func in klass.iter_funcdefs():
                yield Method(func, filename)
