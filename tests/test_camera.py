import os
import unittest
from unittest.mock import patch, MagicMock
from vyom.core import automation

class TestCamera(unittest.TestCase):
    def setUp(self):
        # Create a dummy uploads folder if it doesn't exist
        self.uploads_dir = 'uploads'
        if not os.path.exists(self.uploads_dir):
            os.makedirs(self.uploads_dir)

    @patch('cv2.VideoCapture')
    def test_capture_camera_image_success(self, mock_video_capture):
        # Mock the cv2.VideoCapture object
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, 'fake_frame')
        mock_video_capture.return_value = mock_cap

        # Mock cv2.imwrite to avoid actually writing a file
        with patch('cv2.imwrite') as mock_imwrite:
            filename, error = automation.capture_camera_image()

            # Assert that the correct functions were called
            mock_video_capture.assert_called_with(0)
            mock_cap.isOpened.assert_called_once()
            mock_cap.read.assert_called_once()
            mock_cap.release.assert_called_once()
            mock_imwrite.assert_called_once()

            # Assert that the function returns the correct values
            self.assertIsNotNone(filename)
            self.assertIsNone(error)
            self.assertTrue(filename.startswith('capture_'))
            self.assertTrue(filename.endswith('.jpg'))

            # Check that the file would have been saved in the correct directory
            saved_path = mock_imwrite.call_args[0][0]
            self.assertTrue(saved_path.startswith(self.uploads_dir))

    @patch('cv2.VideoCapture')
    def test_capture_camera_image_camera_not_opened(self, mock_video_capture):
        # Mock the cv2.VideoCapture object
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = False
        mock_video_capture.return_value = mock_cap

        filename, error = automation.capture_camera_image()

        self.assertIsNone(filename)
        self.assertEqual(error, "Could not open camera.")

    @patch('cv2.VideoCapture')
    def test_capture_camera_image_capture_failed(self, mock_video_capture):
        # Mock the cv2.VideoCapture object
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (False, None)
        mock_video_capture.return_value = mock_cap

        filename, error = automation.capture_camera_image()

        self.assertIsNone(filename)
        self.assertEqual(error, "Failed to capture frame.")

    def tearDown(self):
        # Clean up the dummy uploads folder and any created files
        for file in os.listdir(self.uploads_dir):
            os.remove(os.path.join(self.uploads_dir, file))
        if os.path.exists(self.uploads_dir):
            os.rmdir(self.uploads_dir)

if __name__ == '__main__':
    unittest.main()
