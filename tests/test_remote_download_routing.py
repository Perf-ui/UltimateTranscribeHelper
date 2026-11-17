"""Regression tests for checkpoint download routing without network access."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch


# Loading this small module directly keeps these tests independent of the
# optional numerical and machine-learning dependencies.
spec = importlib.util.spec_from_file_location(
    "omnizart_remote", Path(__file__).resolve().parents[1] / "omnizart" / "remote.py"
)
remote = importlib.util.module_from_spec(spec)
spec.loader.exec_module(remote)


class DownloadRoutingTests(unittest.TestCase):
    def test_zero_bytes_is_not_displayed_as_terabytes(self):
        self.assertEqual(remote.format_byte(0), "0.00B")

    def test_github_asset_is_streamed_directly(self):
        url = "https://github.com/example/project/releases/download/v1/model"
        with patch.object(remote, "download", return_value=("model", False)) as download:
            with patch.object(remote.urllib.request, "build_opener", side_effect=AssertionError("Drive handler used")):
                result = remote.download_large_file_from_google_drive(
                    url, file_length=42, save_path="models", save_name="weights", unzip=True
                )
        self.assertEqual(result, ("model", False))
        download.assert_called_once_with(
            url, file_length=42, save_path="models", save_name="weights", unzip=True
        )

    def test_drive_id_still_uses_confirmation_handler(self):
        file_id = "a" * 33
        with patch.object(remote.urllib.request, "build_opener", side_effect=RuntimeError("Drive handler")):
            with self.assertRaisesRegex(RuntimeError, "Drive handler"):
                remote.download_large_file_from_google_drive(file_id)


if __name__ == "__main__":
    unittest.main()
