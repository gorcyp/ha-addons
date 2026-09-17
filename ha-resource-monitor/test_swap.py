import tempfile
import unittest
from pathlib import Path
from server import read_swap


class SwapTests(unittest.TestCase):
    def parse(self, text):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "meminfo"
            path.write_text(text)
            return read_swap(path)

    def test_used_and_units(self):
        result = self.parse("SwapTotal: 2048 kB\nSwapFree: 512 kB\n")
        self.assertEqual(result["used"], 1572864)
        self.assertEqual(result["percent"], 75)

    def test_disabled(self):
        result = self.parse("SwapTotal: 0 kB\nSwapFree: 0 kB\n")
        self.assertTrue(result["available"])
        self.assertEqual(result["total"], 0)

    def test_missing_invalid_and_inconsistent(self):
        for content in ("", "SwapTotal: bad kB", "SwapTotal: 1 MB\nSwapFree: 0 kB",
                        "SwapTotal: 1 kB\nSwapFree: 2 kB"):
            with self.subTest(content=content):
                self.assertFalse(self.parse(content)["available"])

    def test_unreadable(self):
        self.assertFalse(read_swap(Path("/nonexistent/meminfo"))["available"])


if __name__ == "__main__":
    unittest.main()
