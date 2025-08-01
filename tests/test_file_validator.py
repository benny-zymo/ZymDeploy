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


class TestFileValidatorAcquisitionFolder(unittest.TestCase):
    @patch("zymosoft_assistant.core.file_validator.os.path.isdir")
    @patch("zymosoft_assistant.core.file_validator.os.listdir")
    @patch("builtins.open", new_callable=unittest.mock.mock_open, read_data='profil="Layer"')
    def test_validate_acquisition_folder_valid(self, mock_open, mock_listdir, mock_isdir):
        mock_isdir.return_value = True
        mock_listdir.return_value = ["test.zym"]

        result = FileValidator.validate_acquisition_folder("/valid/path", is_expert_mode=False, plate_type="nanofilm")
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["errors"], [])

    @patch("zymosoft_assistant.core.file_validator.os.path.isdir")
    @patch("zymosoft_assistant.core.file_validator.os.listdir")
    @patch("builtins.open", new_callable=unittest.mock.mock_open, read_data='profil="Dot"')
    def test_validate_acquisition_folder_valid_expert(self, mock_open, mock_listdir, mock_isdir):
        def isdir_side_effect(path):
            return "/Image" in path or path == "/valid/path"
        mock_isdir.side_effect = isdir_side_effect
        mock_listdir.return_value = ["test.zym"]

        result = FileValidator.validate_acquisition_folder("/valid/path", is_expert_mode=True, plate_type="micro_depot")
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["errors"], [])

    def test_validate_acquisition_folder_nonexistent(self):
        with patch("os.path.isdir", return_value=False):
            result = FileValidator.validate_acquisition_folder("/invalid/path", is_expert_mode=False, plate_type="nanofilm")
            self.assertFalse(result["is_valid"])
            self.assertIn("Le dossier sélectionné est invalide ou n'existe pas.", result["errors"])

    @patch("zymosoft_assistant.core.file_validator.os.path.isdir")
    @patch("zymosoft_assistant.core.file_validator.os.listdir")
    def test_validate_acquisition_folder_missing_image_in_expert_mode(self, mock_listdir, mock_isdir):
        def isdir_side_effect(path):
            if path == "/valid/path":
                return True
            if "/Image" in path:
                return False
            return True
        mock_isdir.side_effect = isdir_side_effect
        mock_listdir.return_value = ["test.zym"]
        with patch("builtins.open", unittest.mock.mock_open(read_data='profil="Layer"')):
            result = FileValidator.validate_acquisition_folder("/valid/path", is_expert_mode=True, plate_type="nanofilm")
            self.assertFalse(result["is_valid"])
            self.assertIn("Mode expert: Le dossier doit contenir un sous-dossier 'Image'.", result["errors"])

    @patch("zymosoft_assistant.core.file_validator.os.path.isdir", return_value=True)
    @patch("zymosoft_assistant.core.file_validator.os.listdir", return_value=["data.csv"])
    def test_validate_acquisition_folder_missing_zym_file(self, mock_listdir, mock_isdir):
        result = FileValidator.validate_acquisition_folder("/valid/path", is_expert_mode=False, plate_type="nanofilm")
        self.assertFalse(result["is_valid"])
        self.assertIn("Aucun fichier .zym trouvé dans le dossier.", result["errors"])

    @patch("zymosoft_assistant.core.file_validator.os.path.isdir", return_value=True)
    @patch("zymosoft_assistant.core.file_validator.os.listdir", return_value=["test.zym"])
    @patch("builtins.open", new_callable=unittest.mock.mock_open, read_data='profil="Invalid"')
    def test_validate_acquisition_folder_invalid_profile(self, mock_open, mock_listdir, mock_isdir):
        result = FileValidator.validate_acquisition_folder("/valid/path", is_expert_mode=False, plate_type="nanofilm")
        self.assertFalse(result["is_valid"])
        self.assertIn('Le fichier .zym ne contient pas de profil valide (profil="Layer" ou profil="Dot").', result["errors"])

    @patch("zymosoft_assistant.core.file_validator.os.path.isdir", return_value=True)
    @patch("zymosoft_assistant.core.file_validator.os.listdir", return_value=["test.zym"])
    @patch("builtins.open")
    def test_validate_acquisition_folder_read_error(self, mock_open, mock_listdir, mock_isdir):
        mock_open.side_effect = IOError("Test read error")
        result = FileValidator.validate_acquisition_folder("/valid/path", is_expert_mode=False, plate_type="nanofilm")
        self.assertFalse(result["is_valid"])
        self.assertIn("Erreur de lecture du fichier .zym: Test read error", result["errors"])
