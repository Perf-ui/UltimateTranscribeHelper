"""Regression coverage for overlapping windows and short recordings."""
import math
import unittest
import numpy as np

from omnizart.music.prediction import create_batches, merge_batches


class BatchRegressionTests(unittest.TestCase):
    def test_short_and_overlapping_inputs_keep_every_frame(self):
        for length in (1, 9, 10, 11, 31):
            with self.subTest(length=length):
                data = np.arange(length, dtype=np.float32).reshape(-1, 1)
                batches = create_batches(data, timesteps=10, b_size=2, step_size=4)
                expected = 1 + max(0, math.ceil((length - 10) / 4))
                self.assertEqual(sum(map(len, batches)), expected)
                result = merge_batches([np.asarray(batch) for batch in batches], step_size=4)
                np.testing.assert_array_equal(result[:length], data)

    def test_empty_input_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "no feature frames"):
            create_batches(np.empty((0, 2)), timesteps=10)


if __name__ == "__main__":
    unittest.main()
