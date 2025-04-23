import unittest
from src.core.subprocess_runner import SubprocessRunner

class TestSubprocessRunner(unittest.TestCase):
    def setUp(self):
        self.runner = SubprocessRunner()

    def test_run_command_success(self):
        command = ["echo", "Hello, World!"]
        output = self.runner.run_command(command)
        self.assertEqual(output.strip(), "Hello, World!")

    def test_run_command_failure(self):
        command = ["non_existent_command"]
        with self.assertRaises(Exception):
            self.runner.run_command(command)

if __name__ == '__main__':
    unittest.main()