import unittest
from unittest.mock import patch, MagicMock

from zymosoft_assistant.core.file_validator import FileValidator


class TestFileValidatorDirectoryStructure(unittest.TestCase):
    def setUp(self):
        self.base_path = "/mock/base/path"
        self.validator = FileValidator(self.base_path)

    @patch("zymosoft_assistant.core.file_validator.os.path.exists")
    @patch("zymosoft_assistant.core.file_validator.os.path.isdir")
    def test_validate_directory_structure_valid_structure(self, mock_isdir, mock_exists):
        mock_exists.side_effect = lambda path: True
        mock_isdir.side_effect = lambda path: True

        result = self.validator.validate_directory_structure()

        self.assertTrue(result["valid"])
        self.assertEqual(result["errors"], [])
        self.assertIn("bin", result["directories"])
        self.assertIn("etc", result["directories"])
        self.assertIn("Resultats", result["directories"])

    @patch("zymosoft_assistant.core.file_validator.os.path.exists")
    @patch("zymosoft_assistant.core.file_validator.os.path.isdir")
    def test_validate_directory_structure_missing_required_directory(self, mock_isdir, mock_exists):
        mock_isdir.side_effect = lambda path: "bin" not in path
        mock_exists.side_effect = lambda path: "bin" not in path

        result = self.validator.validate_directory_structure()

        self.assertFalse(result["valid"])
        self.assertIn("Dossier requis non trouvé:", result["errors"][0])
        self.assertFalse(result["directories"]["bin"]["exists"])

    @patch("zymosoft_assistant.core.file_validator.os.path.exists")
    @patch("zymosoft_assistant.core.file_validator.os.path.isdir")
    def test_validate_directory_structure_missing_workers_subdir(self, mock_isdir, mock_exists):
        def mock_exists_side_effect(path):
            if "bin" in path and "workers" not in path:
                return True
            if "workers" in path:
                return False
            return True

        mock_exists.side_effect = mock_exists_side_effect
        mock_isdir.side_effect = lambda path: "workers" not in path

        result = self.validator.validate_directory_structure()

        self.assertFalse(result["valid"])
        self.assertIn("Dossier workers/ non trouvé:", result["errors"][0])
        self.assertNotIn("workers", result["directories"])

    @patch("zymosoft_assistant.core.file_validator.os.path.exists")
    @patch("zymosoft_assistant.core.file_validator.os.path.isdir")
    def test_validate_directory_structure_missing_etc_subdirs(self, mock_isdir, mock_exists):
        def mock_exists_side_effect(path):
            if "etc/Interf" in path or "etc/Reflecto" in path:
                return False
            return True

        mock_exists.side_effect = mock_exists_side_effect
        mock_isdir.side_effect = lambda path: True

        result = self.validator.validate_directory_structure()

        self.assertTrue(result["valid"])
        expected_warning_interf = f"Sous-dossier etc/Interf/ non trouvé: {self.base_path}/etc/Interf"
        expected_warning_reflecto = f"Sous-dossier etc/Reflecto/ non trouvé: {self.base_path}/etc/Reflecto"
        self.assertIn(expected_warning_interf, result["warnings"])
        self.assertIn(expected_warning_reflecto, result["warnings"])
        self.assertFalse(result["directories"]["etc_Interf"]["exists"])
        self.assertFalse(result["directories"]["etc_Reflecto"]["exists"])

    @patch("zymosoft_assistant.core.file_validator.os.path.exists")
    def test_validate_directory_structure_invalid_base_path(self, mock_exists):
        mock_exists.return_value = False

        result = self.validator.validate_directory_structure()

        self.assertFalse(result["valid"])
        self.assertIn("Chemin d'installation non valide", result["errors"][0])
