# TODO

[x] Module docstring with comments before does not work.
[x] One line docstrings are always flagged as not first line
[ ] `__init__` missing docstring warning should be flagged on the class name.
[ ] Don't flag non-existing parameters as out-of-order.
[ ] Support multiple parameters on the same declaration
`x1, x2 : array-like`.
[x] Improve parsing of sections, so we can warn when the heading is not using
the exact case
[ ] Improve error message for parameter order.
[ ] Improve naming of error codes

## Suggested error codes

- Errors, Warnings and Information
- Number code sections in order, e.g.,
  - E01 - Parameter Errors
  - E00 - Global errors
  - W02 - Attribute warnings
- Incrementally number errors, warning and information
  - E0101 - `optional` specified multiple times.
  - W0001 - Docstring does not start directly below """
