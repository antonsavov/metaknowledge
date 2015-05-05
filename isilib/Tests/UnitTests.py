import isilib.Classes.RecordCollection

import unittest
import os.path

class simpleCollectionTest(unittest.TestCase):
    def setUp(self, s):
        self.RC = RecordCollection(s)
    def test_size(self, n):
        assertEqual(len(self.RC._Records), n)

class testTest(unittest.TestCase):
    def test_basic(self):
        print('Testing')


if __name__ == '__main__':
    currentPath = os.path.dirname(os.path.realpath(__file__))
