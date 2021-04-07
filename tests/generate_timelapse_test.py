from src.timelapsegeo import generate_timelapse


def test_generate_timelapse_no_framerate():
    assert not generate_timelapse("data/generate_timelapse_tests/test3", "output.mp4", -1)


def test_generate_timelapse():
    # Case 1 False: The folder is empty
    assert not generate_timelapse("data/generate_timelapse_tests/test1", "output.mp4", 10)
    # Case 2 False: The folder contains only one frame
    assert not generate_timelapse("data/generate_timelapse_tests/test2", "output.mp4", 10)
    # Case 3 False: The folder contains two frames but not the same size
    assert not generate_timelapse("data/generate_timelapse_tests/test3", "output.mp4", 10)
    # Case 4 True: The folder contains two frames the same size
    assert generate_timelapse("data/generate_timelapse_tests/test4", "output.mp4", 10)

