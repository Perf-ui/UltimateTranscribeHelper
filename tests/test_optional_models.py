import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from omnizart.desktop import muscriptor, optional_models, yourmt3


class OptionalModelsTest(unittest.TestCase):
    def test_muscriptor_requires_companion_config(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(muscriptor, "model_folder", return_value=Path(directory)):
            weights = Path(directory) / "model.safetensors"
            weights.touch()
            self.assertIsNone(muscriptor.model_checkpoint())
            (Path(directory) / "config.json").touch()
            self.assertEqual(muscriptor.model_checkpoint(), weights)
            (Path(directory) / "other.safetensors").touch()
            self.assertIsNone(muscriptor.model_checkpoint())

    def test_failed_install_never_marks_environment_ready(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(optional_models, "environment", return_value=Path(directory)), patch.object(optional_models.subprocess, "run") as run:
            run.return_value.returncode = 1
            run.return_value.stdout = "installation failed"
            with self.assertRaisesRegex(RuntimeError, "installation failed"):
                optional_models.install("YourMT3")
            self.assertFalse(optional_models.ready("YourMT3"))

    def test_yourmt3_repairs_old_environment_and_pins_transformers(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(optional_models, "environment", return_value=Path(directory)), patch.object(optional_models.subprocess, "run") as run:
            python = optional_models.python_path("YourMT3")
            python.parent.mkdir(parents=True)
            python.touch()
            marker = Path(directory) / ".ready"
            marker.write_text("ready", encoding="utf-8")
            self.assertFalse(optional_models.ready("YourMT3"))
            run.return_value.returncode = 0
            optional_models.install("YourMT3")
            self.assertIn("transformers==4.43.4", run.call_args_list[1].args[0])
            self.assertTrue(optional_models.ready("YourMT3"))

    def test_yourmt3_uses_isolated_interpreter(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(yourmt3, "ready", return_value=True), patch.object(yourmt3, "python_path", return_value=Path("isolated-python")), patch.object(yourmt3.subprocess, "run") as run:
            target = Path(directory) / "out.mid"
            target.touch()
            run.return_value.returncode = 0
            yourmt3.transcribe("input.wav", target)
            self.assertEqual(run.call_args.args[0][:4], ["isolated-python", "-m", "mt3_infer.cli", "transcribe"])


if __name__ == "__main__":
    unittest.main()
