import unittest
from unittest.mock import patch, mock_open

from zymosoft_assistant.scripts.processAcquisitionLog import findLastAcquisition


class TestFindLastAcquisition(unittest.TestCase):
    def test_find_last_acquisition_valid_case(self):
        log_data = (
            "Initializing system...\n"
            "Starting acquisition at time 12:00\n"
            "Reference wells A1 A12 H12 re-aligned."
        )
        with patch("builtins.open", mock_open(read_data=log_data)):
            line, line_number = findLastAcquisition("dummy_path.log")
        self.assertEqual("Starting acquisition at time 12:00", line)
        self.assertEqual(1, line_number)

    def test_find_last_acquisition_no_matches(self):
        log_data = "Initializing system...\nSystem ready.\nNo acquisition found."
        with patch("builtins.open", mock_open(read_data=log_data)):
            line, line_number = findLastAcquisition("dummy_path.log")
        self.assertIsNone(line)
        self.assertIsNone(line_number)

    def test_find_last_acquisition_only_reference_wells(self):
        log_data = (
            "Reference wells A1 A12 H12 re-aligned.\n"
            "Initializing done.\nSystem ready."
        )
        with patch("builtins.open", mock_open(read_data=log_data)):
            line, line_number = findLastAcquisition("dummy_path.log")
        self.assertIsNone(line)
        self.assertIsNone(line_number)

    def test_find_last_acquisition_multiple_matches(self):
        log_data = (
            "Starting acquisition at time 10:00\n"
            "Reference wells aligned.\n"
            "Starting acquisition at time 14:30\n"
            "System shutdown."
        )
        with patch("builtins.open", mock_open(read_data=log_data)):
            line, line_number = findLastAcquisition("dummy_path.log")
        self.assertEqual("Starting acquisition at time 14:30", line)
        self.assertEqual(2, line_number)

    def test_find_last_acquisition_file_not_found(self):
        with patch("builtins.open", side_effect=FileNotFoundError):
            with self.assertRaises(ValueError) as context:
                findLastAcquisition("dummy_path.log")
            self.assertIn("Erreur lors de la recherche de la dernière acquisition", str(context.exception))

    def test_find_last_acquisition_empty_file(self):
        log_data = ""
        with patch("builtins.open", mock_open(read_data=log_data)):
            line, line_number = findLastAcquisition("dummy_path.log")
        self.assertIsNone(line)
        self.assertIsNone(line_number)
