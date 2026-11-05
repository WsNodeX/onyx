import unittest

from onyx.__main__ import main


class TestCli(unittest.TestCase):
    def test_no_command_prints_help(self):
        self.assertEqual(main([]), 1)

    def test_missing_module_returns_2(self):
        code = main(["run", "this_module_does_not_exist:app"])
        self.assertEqual(code, 2)

    def test_missing_app_attr_returns_2(self):
        # examples.demo_app exists, but 'no_such_attr' does not.
        code = main(["run", "examples.demo_app:no_such_attr"])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
