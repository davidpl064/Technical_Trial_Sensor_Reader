import numpy as np
class SensorInfrared():
    def __init__(self, min_value_range: int, max_value_range: int):
        self._min_value_range = min_value_range
        self._max_value_range = max_value_range
        self._last_data = np.random.randint(min_value_range, max_value_range + 1, size=1, dtype=np.uint16)

    def generate_data_mock(self):
        # Mock sensor data readings as a random process (probably not the real behaviour but enough for testing purposes)
        self._last_data = np.random.randint(self._min_value_range, self._max_value_range + 1, size=1, dtype=np.uint16)

    def get_data(self):
        return self._last_data