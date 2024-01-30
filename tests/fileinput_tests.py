import sys
import os
import unittest
sys.path.append("..\\unblock")
from unblock.fileinput import input


class TestFileinput(unittest.IsolatedAsyncioTestCase):

    async def test_input(self):
        dt = r"tests\data"
        files = ["multiline_text.txt", "sample_text.txt"]
        expected_lines = ['line1\n', 'line2\n', 'line3\n', 'A quick brown fox jumps over the lazy log']
        actual_lines = []
        file_paths = [os.path.join(dt, f) for f in files]
        async with await input(files = file_paths, encoding="utf-8") as fi:
            async for line in fi:
                actual_lines.append(line)
        self.assertListEqual(expected_lines, actual_lines)

if __name__ == "__main__":
    unittest.main()