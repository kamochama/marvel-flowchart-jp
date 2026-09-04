from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / "index.html"


def function_body(source: str, name: str) -> str:
    match = re.search(
        rf"(?:function\s+{re.escape(name)}\s*\(|(?:window\.)?{re.escape(name)}\s*=\s*function\s*\()",
        source,
    )
    if not match:
        raise AssertionError(f"function {name} was not found")
    parameter_start = source.find("(", match.start())
    depth = 0
    parameter_end = None
    for index in range(parameter_start, len(source)):
        char = source[index]
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                parameter_end = index
                break
    if parameter_end is None:
        raise AssertionError(f"function {name} has unbalanced parameters")
    opening = source.find("{", parameter_end)
    if opening < 0:
        raise AssertionError(f"function {name} body was not found")
    quote = None
    escaped = False
    depth = 0
    for index in range(opening, len(source)):
        char = source[index]
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in "'\"`":
            quote = char
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[opening : index + 1]
    raise AssertionError(f"function {name} has unbalanced braces")


class MobileShellContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = INDEX.read_text(encoding="utf-8")

    def test_mobile_store_has_single_state_source(self) -> None:
        body = function_body(self.source, "createMobileUiStore")
        self.assertIn("getState", body)
        self.assertIn("subscribe", body)
        self.assertIn("setGoals", body)
        self.assertIn("setSheet", body)

    def test_mobile_store_normalizes_invalid_view_and_sheet(self) -> None:
        self.assertIn("view==='chart'", self.source)
        self.assertIn("sheet==='closed'", self.source)
        self.assertIn("window.marvelMobileUiStore", self.source)


if __name__ == "__main__":
    unittest.main()
