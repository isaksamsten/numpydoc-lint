from ._model import Error, Pos


_ERRORS = {
    # Hints
    # Global
    "H0000": "Missing docstring in public {type}.",
    "H0001": "No extended summary found.",
    "H0002": "No examples section found.",
    "H0003": "No summary found.",
    "H0004": "No yields section found.",
    "H0005": "No return section found.",
    # Information
    # Global
    "I0001": "Docstring should start on a new line.",
    "I0002": "Docstring should not have blank lines before end quote",
    "I0003": "Docstring should not contain double line breaks.",
    "I0004": "Docstring line should not start with tabs.",
    "I0005": "Section `{actual}` should be swapped with `{expected}`.",
    "I0006": "Deprecation warning should precede extended summary.",
    "I0007": "Summary should only contain a single deprecation warning.",
    "I0008": "reST directives must be followed by two colon.",
    "I0009": "Summary does not start with a capital letter",
    "I0010": "Summary does not end with a period.",
    "I0011": "Summary contains heading whitespaces.",
    "I0012": "Summary must start with infinitive verb, not third person.",
    "I0013": "Summary should fit in a single line",
    # Parameters
    "I0101": "Parameter `{parameter}` description should start with uppercase letter.",
    "I0102": "Parameter `{parameter}` description should end with period.",
    "I0103": "Parameter `{parameter}` description has empty prefix lines.",
    "I0104": "Parameter `{parameter}` description has empty suffix lines.",
    "I0105": "Paramter `{parameter}` specify optional multiple times.",
    # Returns
    "I0401": "Return `{return}` description should start with uppercase letter.",
    "I0402": "Return `{return}` description should end with period.",
    # Warnings
    # Global
    "W0001": "Docstring contains unexpected section.",
    # Parameters
    "W0101": "Parameter `{parameter}` should be documented.",
    "W0102": "Parameter `{parameter}` does not exist in the declaration.",
    "W0103": (
        "Parameter `{documented_parameter}` should "
        "be swapped with `{declared_parameter}`."
    ),
    "W0104": "Parameter `{parameter}` should have a type.",
    "W0105": "Parameter `{parameter}` has no description.",
    "W0106": "Parameter `{parameter}` requires a space between name and type.",
    # Returns
    "W0401": "Single return `{return}` should only use the type.",
    "W0402": "Return `{return}` has no description.",
    # Errors
    # Global
    "E0001": "Missing blank line before section",
    "E0002": "Section underline is too short or too long.",
    "E0003": "Unexpected section `{section}`.",
    # See Also
    "E1001": "Malformed item in `See Also`.",
    "E1002": "Unexpected comma or period after function list in `See Also`.",
    "E1003": "Malformed `See Also` entry.",
    # Parameter
    "E0101": "Parameter `{parameter}` type should not finish with `.`.",
    "E0102": (
        "Parameter `{parameter}` uses wrong type `{wrong_type}` "
        "instead of `{correct_type}`."
    ),
    "E0103": "Parameter `{parameter}` uses empty choice.",
}


def make_error(
    code, start: Pos, end: Pos = None, suggestion: str = None, message_args: dict = None
) -> Error:
    message = _ERRORS.get(code)
    if message is None:
        raise ValueError(f"Unkown code {code}")

    return Error(
        code=code,
        message=message if message_args is None else message.format(**message_args),
        suggestion=suggestion,
        start=start,
        end=end,
    )
