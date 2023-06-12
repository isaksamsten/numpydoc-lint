# numpydoc-lint

Highlight errors in your [numpydoc](https://numpydoc.readthedocs.io) formatted
Python docstrings.

## Installation

```shell
$ git clone git@github.com/isaksamsten/numpydoc-lint
$ cd numpydoc-lint
$ pipx install .
```

## Usage

```
usage: numpydoc_lint [-h] [--format {simple,full}] [--ignore [IGNORE ...]] [--select [SELECT ...]] [--exclude [EXCLUDE ...]] [--include-private] [--exclude-magic] [--stdin-filename STDIN_FILENAME] [input]

Lint numpydoc comments

positional arguments:
  input

options:
  -h, --help            show this help message and exit
  --format {simple,full}
  --ignore [IGNORE ...]
  --select [SELECT ...]
  --exclude [EXCLUDE ...]
  --include-private
  --exclude-magic
  --stdin-filename STDIN_FILENAM
```

| Argument          | Values                                                                                          |
| ----------------- | ----------------------------------------------------------------------------------------------- |
| `format`          | `simple` (single line, simple to parse) or `full` (multiple lines, show context and suggestion) |
| `ignore`          | Error codes                                                                                     |
| `select`          | Error codes                                                                                     |
| `exclude`         | File paths                                                                                      |
| `include-private` | Include functions/classes and constants with prefix underscore                                  |
| `exclude-magic`   | Exclude magic methods (e.g., `__add__`)                                                         |

The `input` is zero or more file paths. If no path is specified, lint code on `stdin`.

## Examples

With simple output:

```
$ numpydoc-lint src/ --format=simple --exclude "src/*/test.py" --ignore GL ES RT
src/numpydoc_lint/numpydoc.py:79:4:79:71: PR01 Parameter `l` should be documented.
src/numpydoc_lint/numpydoc.py:92:4:92:8: PR09 Parameter `data` description should end with period.
src/numpydoc_lint/numpydoc.py:92:4:92:8: PRE02 Parameter `data` description has empty suffix lines.
```

With full output:

```
$ numpydoc-lint src/ --format=full --ignore GL ES RT
error[PR06]: Parameter `a` uses empty choice.
   --> src/numpydoc_lint/test.py:128:7
126 |     Parameters
127 |     ----------
128 |     a :{}
    |        ^^
    |         |
    |         Insert choices.
error[PR06]: Parameter `q` uses wrong type.
   --> src/numpydoc_lint/test.py:130:8
128 |     a :{}
129 |         test a
130 |     q : integer
    |         ^^^^^^^
    |               |
    |               Use `int` instead of `integer`.
```

# Editor integration

We can integrate `numpydoc-lint` with our favorite editor Neovim using `null-ls` and a custom source.

```lua
local h = require("null-ls.helpers")
local methods = require("null-ls.methods")
local DIAGNOSTICS = methods.internal.DIAGNOSTICS

local numpydoc_lint = h.make_builtin({
  name = "numpydoc-lint",
  meta = {
    url = "https://github.com/isaksamsten/numpydoc-lint/",
    description = "Find errors in Numpydoc formatted docstrings.",
  },
  method = DIAGNOSTICS,
  filetypes = { "python" },
  generator_opts = {
    command = "numpydoc-lint",
    args = { "--stdin-filename", "$FILENAME" },
    format = "line",
    check_exit_code = function(code)
      return code == 1
    end,
    to_stdin = true,
    ignore_stderr = true,
    on_output = h.diagnostics.from_pattern(
      [[(%d+):(%d+):(%d+):(%d+): ((%u)%w+) (.*)]],
      { "row", "col", "end_row", "end_col", "code", "severity", "message" },
      {
        severities = {
          G = h.diagnostics.severities["information"],
          S = h.diagnostics.severities["information"],
          P = h.diagnostics.severities["information"],
          R = h.diagnostics.severities["information"],
          Y = h.diagnostics.severities["information"],
          E = h.diagnostics.severities["warning"],
        },
      }
    ),
  },
  factory = h.generator_factory,
})
```

Use `numpydoc_lint` where you setup your `null-ls` sources.

# Why numpydoc-lint instead of numpydoc validate?

1. `numpydoc` requires the python module to be compiled, as such it's hard to
   integrate with your editor. `numpydoc-lint` uses
   [Parso](https://parso.readthedocs.io) from
   [Jedi](https://jedi.readthedocs.io) to parse source code.

2. **TODO** `numpydoc-lint` can be integrated with pre-commit hooks.

3. `numpydoc-lint` can be integrated into your editor of choice.

4. `numpydoc-lint` provides better error messages.

5. **TODO** `numpydoc-lint` can fix common errors.

## Error messages

### Errors

Errors that result in incorrectly parsed docstrings.

| Code   | Message                       |
| ------ | ----------------------------- |
| `ER01` | No blank line before section. |

### Global warnings

| Code    | Message                                                 |
| ------- | ------------------------------------------------------- |
| `GL01`  | Not a single blank line after `"""`                     |
| `GL02`  | Not a single blank line before end `"""`                |
| `GL03`  | Multiple consecutive line breaks.                       |
| `GL05`  | No tab characters before first letter.                  |
| `GL06`  | Docstring contains unknown section.                     |
| `GL07`  | Sections are in wrong order.                            |
| `GL08`  | Docstring is missing.                                   |
| `GL09`  | Deprecation does not start the extended summary.        |
| `GL10`  | reST directives does not end with `::`.                 |
| `GLE01` | Extended summary contains multiple deprecated warnings. |

### Parameter warnings

| Code   | Message                                                                     |
| ------ | --------------------------------------------------------------------------- |
| `PR01` | Validate that all parameters are documented.                                |
| `PR02` | Validate that all documented parameters exists.                             |
| `PR03` | Validate that the documented and declared parameters are in the same order. |
| `PR03` | Validate that parameters have a declared type.                              |

# TODO

[ ] Add tests.

[ ] Add `--fix` argument to fix simple errors.

[ ] Add `pre-commit` hook support.
