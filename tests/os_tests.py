import sys
import unittest
sys.path.append("..\\unblock")
from unblock.os import scandir, walk


class TestOS(unittest.IsolatedAsyncioTestCase):

    async def test_scandir(self):
        dt = r"tests\data"
        expected_results = {"multiline_text.txt" : (False, True), "sample_text.txt" : (False, True), "Test Dir" : (True, False), "test.zip" : (False, True)}
        actual_results = {}
        async with await scandir(dt) as it:
            async for entry in it:
                actual_results[entry.name] = (await entry.is_dir(), await entry.is_file())
        self.assertDictEqual(expected_results, actual_results)

    async def test_walk(self):
        dt = r"tests\data"
        expected_roots = ['tests\data', 'tests\data\Test Dir']
        expected_files = ['multiline_text.txt', 'sample_text.txt', 'test.zip', 'sample_text.txt']
        expected_dirs = ['Test Dir']
        actual_roots = []
        actual_files = []
        actual_dirs = []
        async for root, dirs, files in walk(dt):
            actual_roots.append(root)
            actual_files.extend(files)
            actual_dirs.extend(dirs)
        self.assertListEqual(expected_roots, actual_roots)
        self.assertListEqual(expected_files, actual_files)
        self.assertListEqual(expected_dirs, actual_dirs)


if __name__ == "__main__":
    unittest.main()