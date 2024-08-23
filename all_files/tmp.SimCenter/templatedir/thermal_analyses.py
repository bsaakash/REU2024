from typing import Protocol
import numpy as np
import material_properties
# import component_geometries

#TODO       implement thickness as random variable


class ComponentTemperature(Protocol):
    def get_time(self, start=0.0, end=185 * 60.0):
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

    def get_component_temperature(
        self,
        time,
        fire_temp,
        convective_heat_transfer_coefficient,
        material_emissivity,
        fire_emissivity=1.0,
        contour_protection_section_factor=210,
        board_protection_section_factor=153,
        SB_coefficient=56.7e-12,
    ):
        correction_factor_for_shadow_effect = (
            0.9 * contour_protection_section_factor / board_protection_section_factor
        )
        resultant_emissivity = fire_emissivity * material_emissivity
        steel_temp = np.zeros_like(fire_temp)
        steel_temp[0] = fire_temp[0]
        time_diffs = np.diff(time)
        for i in range(1, len(steel_temp)):
            # steel thermal properties
            thermal_mat_prop = material_properties.SteelThermalProperties()
            density = thermal_mat_prop.density(steel_temp[i - 1])
            specific_heat = thermal_mat_prop.specific_heat(steel_temp[i - 1])
            # unprotected steel temperature calculations
            delta_t = time_diffs[i - 1]
            if delta_t > self.time_interval:
                raise ValueError("Error. Time step is greater than 5 seconds. Time array is not properly spaced for unprotected case.")
            delta_T = (
                delta_t
                * correction_factor_for_shadow_effect
                * contour_protection_section_factor
                / (density * specific_heat)
                * (
                    convective_heat_transfer_coefficient
                    * (fire_temp[i] - steel_temp[i - 1])
                    + SB_coefficient
                    * resultant_emissivity
                    * (fire_temp[i] ** 4 - steel_temp[i - 1] ** 4)
                )
            )
            steel_temp[i] = steel_temp[i - 1] + delta_T
        return steel_temp


class SimplifiedProtected(ComponentTemperature):
    def __init__(self, time_interval=30.0):
        self.time_interval = time_interval
        self.get_time()
        super().__init__()

    def get_component_temperature(
        self,
        time,
        fire_temp,
        contour_protection_section_factor=210,
    ):
        steel_temp = np.zeros_like(fire_temp)
        steel_temp[0] = fire_temp[0]
        time_diffs = np.diff(time)
        fire_temp_diffs = np.diff(fire_temp)
        for i in range(1, len(steel_temp)):
            # steel thermal properties
            steel_thermal_prop = material_properties.SteelThermalProperties()
            steel_density = steel_thermal_prop.density(steel_temp[i - 1])
            steel_specific_heat = steel_thermal_prop.specific_heat(steel_temp[i - 1])
            # insulation thermal properties
            insulation_thermal_prop = material_properties.InsulationThermalProperties()
            insulation_density = insulation_thermal_prop.density(steel_temp[i - 1])
            insulation_specific_heat = insulation_thermal_prop.specific_heat(steel_temp[i - 1])
            insulation_thermal_conductivity = insulation_thermal_prop.thermal_conductivity(steel_temp[i - 1])
            # insulation thickness
            insulation_thickness = 0
            # phi constant
            phi = (insulation_density * insulation_specific_heat) / (steel_density * steel_specific_heat) * insulation_thickness * contour_protection_section_factor
            # protected steel temperature calculations
            delta_Tf = fire_temp_diffs[i - 1]
            delta_t = time_diffs[i - 1]
            if delta_t > self.time_interval:
                raise ValueError("Error. Time step is greater than 30 seconds. Time array is not properly spaced for protected case.")
            delta_T = (
                insulation_thermal_conductivity
                / insulation_thickness
                * contour_protection_section_factor
                / (steel_density * steel_specific_heat)
                * ((fire_temp[i] - steel_temp[i - 1]) / (1 + phi / 3))
                * delta_t
                - (np.exp(phi / 10) - 1) * delta_Tf
            )
            steel_temp[i] = steel_temp[i - 1] + delta_T
        return steel_temp