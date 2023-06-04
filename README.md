# numpydoc-lint

Highlight errors in your [numpydoc](https://numpydoc.readthedocs.io) formatted
Python docstrings.

## Installation

```shell
$ git clone git@github.com/isaksamsten/numpydoc-lint
$ cd numpydoc-lint
$ pip install .
```

## Usage

```
python -m numpydoc_lint [-h] [--format {simple,full}] [--ignore [IGNORE ...]] [--select [SELECT ...]] [--exclude [EXCLUDE ...]] [--include-private] [--exclude-magic] [input ...]
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
$ python -m numpydoc_lint src/numpydoc_lint/**/*.py --format=simple --exclude src/*/test.py --ignore GL ES RT
src/numpydoc_lint/numpydoc.py:79:4:79:71: PR01 Parameter `l` should be documented.
src/numpydoc_lint/numpydoc.py:92:4:92:8: PR09 Parameter `data` description should end with period.
src/numpydoc_lint/numpydoc.py:92:4:92:8: PRE02 Parameter `data` description has empty suffix lines.
```

With full output:

```
$ python -m numpydoc_lint src/numpydoc_lint/**/*.py --format=full --ignore GL ES RT
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

# Why numpydoc-lint instead of numpydoc validate?

1. `numpydoc` requires the python module to be compiled, as such its hard to
   integrate with your editor. `numpydoc-lint` uses the
   [Parso](https://parso.readthedocs.io) from [Jedi](https://jedi.readthedocs.io) to parse
   source code.

2. **TODO** `numpydoc-lint` can be integrated with pre-commit hooks.

3. `numpydoc-lint` can be integrated into your editor of choice.

4. `numpydoc-lint` provides better error messages.

5. **TODO** `numpydoc-lint` can fix common errors.

## Error messages

### Errors

Errors that result in incorrectly parsed docstrings.

| Code   | Message                       |
| ------ | ----------------------------- |
| `ER01` | Docstring is missing.         |
| `ER02` | No blank line before section. |

### Global warnings

| `GL01` | Not a single blank line after `"""`|
| `GL02` | Not a single blank line before end `"""` |
| `GL03` | Multiple consecutive line breaks. |

# TODO

[ ] Add tests.

[ ] Add `--fix` argument to fix simple errors.

[ ] Add `pre-commit` hook support.
