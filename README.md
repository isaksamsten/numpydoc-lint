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
          E = h.diagnostics.severities["error"],
          W = h.diagnostics.severities["warning"],
          I = h.diagnostics.severities["information"],
          H = h.diagnostics.severities["hint"],
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

# Errors

## Global

| Code  | Message                                     |
| ----- | ------------------------------------------- |
| E0001 | Missing blank line before section           |
| E0002 | Section underline is too short or too long. |
| E0003 | Unexpected section `{section}`.             |

## Parameters

| Code  | Message                                                                             |
| ----- | ----------------------------------------------------------------------------------- |
| E0101 | Parameter `{parameter}` type should not finish with `.`.                            |
| E0102 | Parameter `{parameter}` uses wrong type `{wrong_type}` instead of `{correct_type}`. |
| E0103 | Parameter `{parameter}` uses empty choice.                                          |

## See Also

| Code  | Message                                                       |
| ----- | ------------------------------------------------------------- |
| E1001 | Malformed item in `See Also`.                                 |
| E1002 | Unexpected comma or period after function list in `See Also`. |
| E1003 | Malformed `See Also` entry.                                   |

# Warnings

## Global

| Code  | Message                                |
| ----- | -------------------------------------- |
| W0001 | Docstring contains unexpected section. |

## Parameters

| Code  | Message                                                                           |
| ----- | --------------------------------------------------------------------------------- |
| W0101 | Parameter `{parameter}` should be documented.                                     |
| W0102 | Parameter `{parameter}` does not exist in the declaration.                        |
| W0103 | Parameter `{documented_parameter}` should be swapped with `{declared_parameter}`. |
| W0104 | Parameter `{parameter}` should have a type.                                       |
| W0105 | Parameter `{parameter}` has no description.                                       |
| W0106 | Parameter `{parameter}` requires a space between name and type.                   |

## Returns

| Code  | Message                                            |
| ----- | -------------------------------------------------- |
| W0401 | Single return `{return}` should only use the type. |
| W0402 | Return `{return}` has no description.              |

# Information

## Global

| Code  | Message                                                    |
| ----- | ---------------------------------------------------------- |
| I0001 | Docstring should start on a new line.                      |
| I0002 | Docstring should not have blank lines before end quote     |
| I0003 | Docstring should not contain double line breaks.           |
| I0004 | Docstring line should not start with tabs.                 |
| I0005 | Section `{actual}` should be swapped with `{expected}`.    |
| I0006 | Deprecation warning should precede extended summary.       |
| I0007 | Summary should only contain a single deprecation warning.  |
| I0008 | reST directives must be followed by two colon.             |
| I0009 | Summary does not start with a capital letter               |
| I0010 | Summary does not end with a period.                        |
| I0011 | Summary contains heading whitespaces.                      |
| I0012 | Summary must start with infinitive verb, not third person. |
| I0013 | Summary should fit in a single line                        |

## Parameters

| Code  | Message                                                                 |
| ----- | ----------------------------------------------------------------------- |
| I0101 | Parameter `{parameter}` description should start with uppercase letter. |
| I0102 | Parameter `{parameter}` description should end with period.             |
| I0103 | Parameter `{parameter}` description has empty prefix lines.             |
| I0104 | Parameter `{parameter}` description has empty suffix lines.             |
| I0105 | Paramter `{parameter}` specify optional multiple times.                 |

## Returns

| Code  | Message                                                           |
| ----- | ----------------------------------------------------------------- |
| I0401 | Return `{return}` description should start with uppercase letter. |
| I0402 | Return `{return}` description should end with period.             |

# Hints

## Global

| Code  | Message                             |
| ----- | ----------------------------------- |
| H0000 | Missing docstring in public {type}. |
| H0001 | No extended summary found.          |
| H0002 | No examples section found.          |
| H0003 | No summary found.                   |
| H0004 | No yields section found.            |
| H0005 | No return section found.            |

# TODO

[ ] Add tests.

[ ] Add `--fix` argument to fix simple errors.

[ ] Add `pre-commit` hook support.
