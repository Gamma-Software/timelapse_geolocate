import unittest
from unittest import TestCase
from src.timelapsegeo import generate_timelapse


class TestGenerateTimelapse(TestCase):
    def test_generate_timelapse_no_framerate(self):
        print("Running test_generate_timelapse_no_framerate")
        self.assertEqual(generate_timelapse("data/test3", "output.mp4", -1), False)

    def test_generate_timelapse(self):
        print("Running test_generate_timelapse")
        # Case 1 False: The folder is empty
        print("Running Case 1")
        self.assertEqual(generate_timelapse("data/test1", "output.mp4", 10), False)
        # Case 2 False: The folder contains only one frame
        print("Running Case 2")
        self.assertEqual(generate_timelapse("data/test2", "output.mp4", 10), False)
        # Case 3 False: The folder contains two frames but not the same size
        print("Running Case 3")
        self.assertEqual(generate_timelapse("data/test3", "output.mp4", 10), False)
        # Case 4 True: The folder contains two frames the same size
        print("Running Case 4")
        self.assertEqual(generate_timelapse("data/test4", "output.mp4", 10), True)

        # Remove output.mp4 generated if exists
        import os
        if os.path.exists("output.mp4"):
            os.remove("output.mp4")


if __name__ == '__main__':
    unittest.main()
