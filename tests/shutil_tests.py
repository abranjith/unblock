import sys
import shutil
from tempfile import NamedTemporaryFile
import unittest
sys.path.append("..\\unblock")
from unblock.shutil import get_terminal_size, copyfileobj


class TestShutil(unittest.IsolatedAsyncioTestCase):

    async def test_terminalsize(self):
        expected = shutil.get_terminal_size()
        actual = await get_terminal_size()
        self.assertEqual(expected.lines, actual.lines, "shutil.get_terminal_size lines mismatch")
        self.assertEqual(expected.columns, actual.columns, "shutil.get_terminal_size columns mismatch")

    async def test_copy(self):
        with NamedTemporaryFile() as fd1:
            fd1.write(b'A quick brown fox jumps over the lazy log')
            fd1.seek(0)
            with NamedTemporaryFile() as fd2:
                await copyfileobj(fd1, fd2)
                fd2.seek(0)
                copied_data = fd2.read1()
                self.assertEqual(copied_data, b'A quick brown fox jumps over the lazy log')


if __name__ == "__main__":
    unittest.main()