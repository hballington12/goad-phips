import unittest
from src.plotting.plot_manager import PlotManager

class TestPlotManager(unittest.TestCase):
    def setUp(self):
        self.plot_manager = PlotManager()

    def test_initialization(self):
        self.assertIsNotNone(self.plot_manager)

    # Additional tests for plotting functionalities can be added here

if __name__ == '__main__':
    unittest.main()