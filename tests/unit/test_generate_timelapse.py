import unittest
from unittest import TestCase
from src.timelapsegeo import generate_timelapse


class TimelapseArguments:
    cached_frames_folder = ""
    output_filename = ""
    framerate = 0.0

class TestGenerateTimelapse(TestCase):
    def test_generate_timelapse_no_framerate(self):
        args = TimelapseArguments()
        args.cached_frames_folder = "tests/unit/data/test3"
        args.output_filename = "output.mp4"
        args.framerate = -1.0
        print("Running test_generate_timelapse_no_framerate")
        self.assertEqual(generate_timelapse(args), False)

    def test_generate_timelapse(self):
        print("Running test_generate_timelapse")
        # Case 1 False: The folder is empty
        print("Running Case 1")
        args = TimelapseArguments()
        args.cached_frames_folder = "tests/unit/data/test1"
        args.output_filename = "output.mp4"
        args.framerate = 10.0
        self.assertEqual(generate_timelapse(args), False)
        # Case 2 False: The folder contains only one frame
        print("Running Case 2")
        args.cached_frames_folder = "tests/unit/data/test2"
        self.assertEqual(generate_timelapse(args), False)
        # Case 3 False: The folder contains two frames but not the same size
        print("Running Case 3")
        args.cached_frames_folder = "tests/unit/data/test3"
        self.assertEqual(generate_timelapse(args), False)
        # Case 4 True: The folder contains two frames the same size
        print("Running Case 4")
        args.cached_frames_folder = "tests/unit/data/test4"
        self.assertEqual(generate_timelapse(args), True)
        # Case 5 False: The folder does not exist
        print("Running Case 5")
        args.cached_frames_folder = "tests/unit/data/test5"
        self.assertEqual(generate_timelapse(args), False)

        # Remove output.mp4 generated if exists
        import os
        if os.path.exists("output.mp4"):
            os.remove("output.mp4")


if __name__ == '__main__':
    unittest.main()
