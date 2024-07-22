import numpy as np
from column_analysis_parameters import *
import fire_curves

# input parameters
room_temperature_modulus = 200  # GPa
room_temperature_yield_strength = 220  # MPa
alpha = 12e-6  # coefficient of thermal expansion (1/°C)
room_temperature_density = 7850  # kg/m^3
room_temperature_specific_heat = 460  # J/kg K
convective_heat_transfer_coefficient = 25  # W/m^2 K
material_emissivity = 0.7


DCR = 0.04940482
e = 0.00300645
A = 130 / (3.281**2)  # cross-sectional area in m^2
L = 13 / 3.281  # m
I = 1150 / (3.281**4)  # m^4, using W14X342 column


occupancy = "office"
thermal_conductivity = 45.8  # W/mK
density = room_temperature_density  # kg/m^3
specific_heat = room_temperature_specific_heat  # J/kg K
window_base = 3 / 3.281  # m
window_height = 5 / 3.281  # m
room_length1 = 20 / 3.281  # m
room_length2 = 20 / 3.281  # m
room_height = 13 / 3.281  # m
floor_fuel_load_energy_density = 128000  # MJ/m^2


class SteelMaterialProperty:
    def __init__(
        self,
        steel_temperature,
    ):
        self.steel_temperature = steel_temperature
        return

    def effective_yield_strength(self, room_temperature_yield_strength, epsilon_yield):
        T = self.steel_temperature
        self.reduction_factor_yield = (
            1.2
            * (np.exp(1.61 - 1.68e-3 * T - 3.36e-6 * T**2 + 0.35 * epsilon_yield))
            / (np.exp(1.61 - 1.68e-3 * T - 3.36e-6 * T**2 + 0.35 * epsilon_yield) + 1)
        )
        return self.reduction_factor_yield * room_temperature_yield_strength

    def effective_elastic_modulus(self, room_temperature_modulus, epsilon_modulus):
        T = self.steel_temperature
        self.reduction_factor_modulus = (
            1.1
            * (np.exp(2.54 - 2.69e-3 * T - 2.83e-6 * T**2 + 0.36 * epsilon_modulus))
            / (np.exp(2.54 - 2.69e-3 * T - 2.83e-6 * T**2 + 0.36 * epsilon_modulus) + 1)
        )
        return self.reduction_factor_modulus * room_temperature_modulus

    def effective_density(self, epsilon_density):
        T = self.steel_temperature
        return np.exp(-2.028 + 7.83 * T ** (-0.0065) + 0.122 * epsilon_density)

    def effective_specific_heat(self, epsilon_specific_heat):
        T = self.steel_temperature
        return 1700 - np.exp(
            6.81 - 1.61e-3 * T + 0.44e-6 * T**2 + 0.213 * epsilon_specific_heat
        )

    def effective_thermal_conductivity(self, epsilon_thermal_conductivity):
        T = self.steel_temperature
        return np.exp(
            -2.72 + 1.89e-3 * T - 0.195e-6 * T**2 + 0.209 * epsilon_thermal_conductivity
        )


class UnprotectedSteelTemp:
    def __init__(self):
        pass

    def get_component_temperature(
        time,
        fire_temp,
        #       density,
        #       specific_heat,
        convective_heat_transfer_coefficient,
        material_emissivity,
        fire_emissivity=1.0,
        contour_protection_section_factor=210,
        board_protection_section_factor=153,
        SB_coefficient=56.7 * 10 ** (-12),
    ):

        correction_factor_for_shadow_effect = (
            0.9 * contour_protection_section_factor / board_protection_section_factor
        )
        resultant_emissivity = fire_emissivity * material_emissivity

        steel_temp = np.zeros(len(fire_temperature))
        steel_temp[0] = fire_temp[0]
        time_diffs = np.diff(time)
        for i in range(1, len(steel_temp)):
            material_prop = SteelMaterialProperty(steel_temp[i - 1])
            density = material_prop.effective_density(epsilon_density)
            specific_heat = material_prop.effective_specific_heat(epsilon_specific_heat)
            time_step = time_diffs[i - 1]
            delta_T = (
                time_step
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


# fire temperature
# time = np.arange(0, 180 * 60, 5)
fire_curve = fire_curves.ParametricFireCurve(
    occupancy,
    thermal_conductivity,
    density,
    specific_heat,
    window_base,
    window_height,
    room_length1,
    room_length2,
    room_height,
    floor_fuel_load_energy_density,
)
fire_temperature = fire_curve.fire_temp()
time = fire_curve.time_array
print(fire_temperature)

# steel temperature
# inputs: contour_protection_section_factor=210, board_protection_section_factor=153, density=7850, c=700, hc=25, fire_emissivity=1.0, material_emissivity=0.7, SB_coefficient=56.7 * 10 ** (-12),
steel_temperature = UnprotectedSteelTemp.get_component_temperature(
    time, fire_temperature, convective_heat_transfer_coefficient, material_emissivity
)


# reduction factors
material_properties = SteelMaterialProperty(steel_temperature)
effective_elastic_modulus = material_properties.effective_elastic_modulus(
    room_temperature_modulus, epsilon_modulus
)


# column analysis
initial_temp = steel_temperature[0]  # temperature change (°C)
time_step = np.diff(time)
delta_steel_temp = np.concatenate(([steel_temperature[0]], np.diff(steel_temperature)))
sigma = effective_elastic_modulus * alpha * delta_steel_temp  # GPa
F = sigma * A * 10**3  # MN
internal_force = np.zeros(len(F))
for i in range(0, len(F) - 1):
    internal_force[i] = np.sum(F[:i])


# failure evaluation
capacity = np.pi**2 * effective_elastic_modulus * I / L**2 * 10**3  # MN
demand = (DCR * capacity[0] * L / (np.sqrt(L**2 - (e * L) ** 2))) + internal_force

for i in range(len(demand)):
    if demand[i] >= capacity[i]:
        critical_temp = steel_temperature[i]
        critical_time = time[i]
        critical_demand = demand[i]
        print(f"Temperature at failure: {critical_temp} °C")
        print(f"Time at failure: {critical_time / 60} minutes")
        print(f"Critical load: {critical_demand} Meganewtons")
        break
    else:
        critical_temp = "DNE"
        critical_time = "DNE"
        critical_demand = "DNE"
