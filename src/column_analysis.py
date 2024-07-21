import numpy as np
from column_analysis_parameters import *

# input parameters
room_temperature_modulus = 29000  # ksi
room_temperature_yield_strength = 50  # ksi
alpha = 12e-6  # coefficient of thermal expansion (1/°C)
room_temperature_density = 7850
room_temperature_specific_heat = 700
convective_heat_transfer_coefficient = 25
material_emissivity = 0.7


DCR = 0.04940482
e = 0.00300645
A = 130  # cross-sectional area in in²
L = 13 * 12  # in
I = 1150  # in^4, using W14X342 column


class ISO834FireCurve:
    def __init__(self, t):
        self.time = t

    def firetemp(self):
        return 20 + 345 * np.log10(8 * self.time + 1)


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
        return np.exp(-2.72 + 1.89e-3 * T - 0.195e-6 * T**2 + 0.209 * epsilon_thermal_conductivity)

class UnprotectedSteelTemp:
    def __init__(self):
        pass

    def get_component_temperature(
        time,
        fire_temp,
#        density,
#        specific_heat,
        convective_heat_transfer_coefficient,
        material_emissivity,
        fire_emissivity=1.0,
        contour_protection_section_factor=210,
        board_protection_section_factor=153,
        SB_coefficient=56.7 * 10 ** (-12),
    ):
        material_prop = SteelMaterialProperty(20)       # fix to update as the temperature changes.
        density = material_prop.effective_density(epsilon_density)
        specific_heat = material_prop.effective_specific_heat(epsilon_specific_heat)


        correction_factor_for_shadow_effect = (
            0.9 * contour_protection_section_factor / board_protection_section_factor
        )
        resultant_emissivity = fire_emissivity * material_emissivity

        steel_temp = np.zeros(len(Tf))
        steel_temp[0] = fire_temp[0]
        time_diffs = np.diff(time)
        for i in range(1, len(steel_temp)):
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
time = np.arange(0, 180 * 60, 5)
fire_curve = ISO834FireCurve(time / 60)
Tf = fire_curve.firetemp()


# steel temperature
# inputs: contour_protection_section_factor=210, board_protection_section_factor=153, density=7850, c=700, hc=25, fire_emissivity=1.0, material_emissivity=0.7, SB_coefficient=56.7 * 10 ** (-12),
steel_temperature = UnprotectedSteelTemp.get_component_temperature(time, Tf, convective_heat_transfer_coefficient, material_emissivity)


# reduction factors
material_properties = SteelMaterialProperty(steel_temperature)
effective_elastic_modulus = material_properties.effective_elastic_modulus(room_temperature_modulus, epsilon_modulus)


# column analysis
initial_temp = steel_temperature[0]  # temperature change (°C)
time_step = np.diff(time)
delta_steel_temp = np.concatenate(([steel_temperature[0]], np.diff(steel_temperature)))
sigma = effective_elastic_modulus * alpha * delta_steel_temp
F = sigma * A
internal_force = np.zeros(len(F))
for i in range(0, len(F) - 1):
    internal_force[i] = np.sum(F[:i])


# failure evaluation
capacity = (
    np.pi**2 * effective_elastic_modulus * I / L**2
)  # capacity over varying temperature, pinned pinned
# print(capacity)
demand = (DCR * capacity[0] * L * 1 / (np.sqrt(L**2 - (e * L) ** 2))) + internal_force
# print(demand)

for i in range(len(demand)):
    if demand[i] >= capacity[i]:
        critical_temp = steel_temperature[i]
        critical_time = time[i]
        critical_demand = demand[i]
        break

print(f"Temperature at failure: {critical_temp} °C")
print(f"Time at failure: {critical_time / 60} minutes")
print(f"Critical load: {critical_demand} kips")
