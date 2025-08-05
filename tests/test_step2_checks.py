# tests/test_step2_checks.py

import unittest
from unittest.mock import MagicMock, patch

from zymosoft_assistant.gui.step2_checks import Step2Checks


class TestStep2ChecksReset(unittest.TestCase):
    def setUp(self):
        # Using None for the parent avoids the need for a QApplication instance in these non-GUI tests
        self.parent = None
        self.main_window = MagicMock()
        self.main_window.session_data = {}  # Mock session data

        # We need to patch the super().__init__ call in StepFrame to avoid creating a QWidget
        with patch("zymosoft_assistant.gui.step_frame.StepFrame.__init__", return_value=None), \
             patch("zymosoft_assistant.gui.step2_checks.Step2Checks.create_widgets", return_value=None):
            self.step2_checks = Step2Checks(self.parent, self.main_window)

        # Mocking UI elements and other attributes required for the reset function
        self.step2_checks.folder_display_label = MagicMock()
        self.step2_checks.start_analysis_button = MagicMock()
        self.step2_checks.progress_bar = MagicMock()
        self.step2_checks.progress_label = MagicMock()
        self.step2_checks._show_initial_state = MagicMock()
        self.step2_checks.main_window = MagicMock()
        self.step2_checks.main_window.edit_config_action = MagicMock()

    def test_reset_clears_zymosoft_path(self):
        self.step2_checks.zymosoft_path = "some/path"
        self.step2_checks.reset()
        self.assertEqual("", self.step2_checks.zymosoft_path)

    def test_reset_clears_check_results(self):
        self.step2_checks.check_results = {"key": "value"}
        self.step2_checks.reset()
        self.assertEqual({}, self.step2_checks.check_results)

    def test_reset_sets_installation_valid_to_false(self):
        self.step2_checks.installation_valid = True
        self.step2_checks.reset()
        self.assertFalse(self.step2_checks.installation_valid)

    def test_reset_sets_analysis_done_to_false(self):
        self.step2_checks.analysis_done = True
        self.step2_checks.reset()
        self.assertFalse(self.step2_checks.analysis_done)

    def test_reset_sets_analysis_in_progress_to_false(self):
        self.step2_checks.analysis_in_progress = True
        self.step2_checks.reset()
        self.assertFalse(self.step2_checks.analysis_in_progress)

    def test_reset_resets_config_checker_to_none(self):
        self.step2_checks.config_checker = MagicMock()
        self.step2_checks.reset()
        self.assertIsNone(self.step2_checks.config_checker)

    def test_reset_resets_file_validator_to_none(self):
        self.step2_checks.file_validator = MagicMock()
        self.step2_checks.reset()
        self.assertIsNone(self.step2_checks.file_validator)

    def test_reset_updates_folder_display_label_text(self):
        mock_label = self.step2_checks.folder_display_label
        self.step2_checks.reset()
        mock_label.setText.assert_called_once_with("Aucun dossier sélectionné")

    @patch("zymosoft_assistant.gui.step2_checks.COLOR_SCHEME",
           {"border": "#ddd", "background_light": "#f8f9fa", "text_secondary": "#666"})
    def test_reset_updates_folder_display_label_style(self):
        mock_label = self.step2_checks.folder_display_label
        self.step2_checks.reset()
        # The string must match exactly, including leading/trailing whitespace from the triple-quoted string in the source
        expected_stylesheet = f"""
            QLabel {{
                padding: 15px;
                border: 2px dashed #ddd;
                border-radius: 8px;
                background-color: #f8f9fa;
                color: #666;
                font-size: 12pt;
            }}
        """
        mock_label.setStyleSheet.assert_called_once_with(expected_stylesheet)

    def test_reset_hides_start_analysis_button(self):
        mock_button = self.step2_checks.start_analysis_button
        self.step2_checks.reset()
        mock_button.setVisible.assert_called_once_with(False)

    def test_reset_resets_progress_bar_value(self):
        mock_bar = self.step2_checks.progress_bar
        self.step2_checks.reset()
        mock_bar.setValue.assert_called_once_with(0)

    def test_reset_clears_progress_label_text(self):
        mock_label = self.step2_checks.progress_label
        self.step2_checks.reset()
        mock_label.setText.assert_called_once_with("")

    def test_reset_calls_show_initial_state(self):
        mock_show_initial = self.step2_checks._show_initial_state
        self.step2_checks.reset()
        mock_show_initial.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
