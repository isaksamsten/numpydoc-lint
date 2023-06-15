import io
from collections import defaultdict
from ._model import Pos
from typing import Generator, Iterable, Mapping, Tuple

from .check._base import Error
from .numpydoc import Node
from ._config import Config


# TODO: should get a `Config` object as parameter
class Validator:
    def __init__(self, config: Config = None) -> None:
        self.config = config
        self.checks = self.config.get_checks()

    def validate(self, node: Node) -> Generator[Error, None, None]:
        if self.config.is_node_excluded(node):
            return

        # First we let the node validate it self for possible errors.
        any_errors = False
        for error in node.validate():
            if not node.is_error_ignored(
                error.code
            ) and not self.config.is_error_ignored(error.code):
                yield error
                any_errors = True

        if any_errors and node.skip_remaining_on_error:
            return

        # Then, we parse the docstring and report any errors in the docstring,
        # We define errores as those warnings that would result in incorrect rendering.
        docstring, errors = node.parse_docstring()
        for error in errors:
            if not node.is_error_ignored(
                error.code
            ) and not self.config.is_error_ignored(error.code):
                yield error

        # Finally, if the docstring could be parsed and exists, we run all
        # checks, ignoring those checks that the user excludes.
        #
        # NOTE: the `checks` array should only contain the checks explicitly
        # requested by the user.
        if docstring:
            for check in self.checks:
                if not node.is_error_ignored(
                    check.name
                ) and not self.config.is_error_ignored(check.name):
                    for error in check.validate(node, docstring):
                        yield error


class ErrorFormatter:
    def __init__(self):
        self._errors: Mapping[str, Iterable[Tuple[Node, Error]]] = defaultdict(list)

    def add_error(self, file: str, node: Node, error: Error) -> None:
        self._errors[file].append((node, error))

    def _format_error(self, file: str, node: Node, error: Error):
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
            for node, error in errors:
                output.write(self._format_error(file, node, error))

    @property
    def has_errors(self):
        return len(self._errors) > 0

    @property
    def errors(self):
        return sum(len(errors) for errors in self._errors.values())


class DetailedErrorFormatter(ErrorFormatter):
    def _format_error(self, file: str, node: Node, error: Error) -> str:
        if node.has_docstring:
            line = str(error.start.line)
            docstring = node.node.get_code().splitlines()
            while not docstring[0].strip():
                docstring.pop(0)

            start = Pos(*node.node.start_pos)

            error_start = error.start.normalize(start)
            offending_lines = []

            for i in range(max(0, error_start.line - 2), error_start.line + 1):
                offending_lines.append("{} | {}\n".format(start.line + i, docstring[i]))

            offending_line = "".join(offending_lines)

            line_pad = (" " * len(line)) + " | " + (" " * (error.start.column - 1))
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

            return "error[{}]: {}\n{}:{}:{}\n{}{}{}\n".format(
                error.code,
                error.message,
                (" " * len(line)) + "--> " + file,
                error.start.line,
                error.start.column,
                offending_line,
                underline,
                suggestion,
            )
        else:
            return super()._format_error(file, node, error)
