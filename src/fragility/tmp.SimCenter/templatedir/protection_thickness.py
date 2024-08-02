import numpy as np
import fire_curves
import material_properties
import thermal_analyses

class InsulationThermalProperties:
    def thickness_protection(self, time_to_failure_ISO834, failure_temperature, room_temperature_yield_strength, board_perimeter, section_area, protection_thermal_conductivity, protection=1256):
        utilization_ratio = material_properties.yield_strength(failure_temperature)/room_temperature_yield_strength
        if utilization_ratio < 0.013:
            utilization_ratio = 0.013
        critical_temperature = 39.19 * np.log(1/(0.9674 * utilization_ratio ** 3.833) - 1) + 482
        temp_after_30_min = 
        delta_T = section_factor * 
        return (board_perimeter * protection_thermal_conductivity) / (section_area * protection)

