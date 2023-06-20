from numpydoc_lint._error import _ERRORS
import re
from collections import defaultdict

TYPE_MAPPING = {
    "00": "Global",
    "01": "Parameters",
    "04": "Returns",
    "05": "Yields",
    "10": "See Also",
}
SEVERITY_MAPPING = {"I": "Information", "W": "Warnings", "E": "Errors", "H": "Hints"}


if __name__ == "__main__":
    # TYPE -> SEVERITY -> (code, message)
    table = defaultdict(lambda: defaultdict(list))
    for code, message in _ERRORS.items():
        match = re.match(r"([I|W|E|H])(\d{2})(\d{2})", code)
        if match:
            severity = match.group(1)
            type = match.group(2)
            table[severity][type].append((code, message))

    for severity in ["E", "W", "I", "H"]:
        if severity in table:
            print(f"# {SEVERITY_MAPPING[severity]}")
            for type, messages in sorted(table[severity].items()):
                print(f"## {TYPE_MAPPING[type]}")
                print("| Code | Message |")
                print(" | --- | --- | ")
                for code, message in messages:
                    print(f"| {code} | {message} | ")
