from typing import Protocol
import numpy as np
from material_properties import (
    ThermalProperties,
    SteelThermalProperties,
    InsulationThermalProperties,
)


class ComponentTemperature(Protocol):
    def get_time(self, start=0.0, end=185*60.0):
        self.start_time = start
        self.end_time = end
        self.time = np.arange(start, end, self.time_interval)
        return self.time

    def get_time_from_temperature(self, temperature_value):
        diff = np.diff(self.temperature)
        increasing_end = np.argmax(diff <= 0) + 1
        if increasing_end == 1 and diff[0] > 0:
            increasing_end = len(self.temperature)
        increasing_part = self.temperature[:increasing_end]
        closest_index = np.argmin(np.abs(increasing_part - temperature_value))
        return self.time[closest_index]

    def get_component_temperature(self):
        raise NotImplementedError


class SimplifiedUnprotected(ComponentTemperature):
    def __init__(self, time_interval=5.0):
        self.time_interval = time_interval
        super().__init__()

    def get_component_temperature(self, SteelThermalProperties):
        return


class SimplifiedProtected(ComponentTemperature):
    def __init__(self, time_interval=30.0):
        self.time_interval = time_interval
        self.get_time()
        super().__init__()

    def get_component_temperature(
        self, SteelThermalProperties, InsulationThermalProperties
    ):
        return
