import numpy as np
from column_analysis_parameters import *

class ISO834FireCurve:
    def __init__(self, t):
        self.time = t

    def firetemp(self):
        return 20 + 345 * np.log10(8 * self.time + 1)


class SteelReductionFactors:
    def __init__(self, temperature_steel):
        self.steel_element_temperature = temperature_steel
        self.eurocode_temperatures = np.array(
            [20, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200]
        )
        self.reduction_factor_for_youngs_modulus = np.array(
            [
                1.000,
                1.000,
                0.900,
                0.800,
                0.700,
                0.600,
                0.310,
                0.130,
                0.090,
                0.0675,
                0.0450,
                0.0225,
                0.0000,
            ]
        )

    def interpolate_reduction_factor_youngs_modulus(self):
        return np.interp(
            self.steel_element_temperature,
            self.eurocode_temperatures,
            self.reduction_factor_for_youngs_modulus,
        )


class SteelMaterialProperty:
    def __init__(
        self,
        T,
        stiffness_reduction_factor,
        room_temperature_modulus=29000,  # ksi
    ):
        self.steel_temperature = T
        self.room_temperature_modulus = room_temperature_modulus
        self.stiffness_reduction_factor = stiffness_reduction_factor
        return

    def effective_elastic_modulus(self):
        return self.room_temperature_modulus * self.stiffness_reduction_factor


class UnprotectedSteelTemp:
    def __init__(self):
        pass

    def get_component_temperature(
        time,
        Tf,
        contour_protection_section_factor=210,
        board_protection_section_factor=153,
        rho=7850,
        c=700,
        hc=25,
        fire_emissivity=1.0,
        material_emissivity=0.7,
        SB_coefficient=56.7 * 10 ** (-12),
    ):

        ksh = 0.9 * contour_protection_section_factor / board_protection_section_factor
        resultant_emissivity = fire_emissivity * material_emissivity

        Ts = np.zeros(len(Tf))
        Ts[0] = Tf[0]
        time_diffs = np.diff(time)
        for i in range(1, len(Ts)):
            delta_t = time_diffs[i - 1]
            delta_T = (
                ksh
                * contour_protection_section_factor
                / (rho * c)
                * (
                    hc * (Tf[i] - Ts[i - 1])
                    + SB_coefficient
                    * resultant_emissivity
                    * (Tf[i] ** 4 - Ts[i - 1] ** 4)
                )
                * delta_t
            )
            Ts[i] = Ts[i - 1] + delta_T
        return Ts


# fire temperature
time = np.arange(0, 180 * 60, 5)
fire_curve = ISO834FireCurve(time / 60)
Tf = fire_curve.firetemp()


# steel temperature
# inputs: contour_protection_section_factor=210, board_protection_section_factor=153, rho=7850, c=700, hc=25, fire_emissivity=1.0, material_emissivity=0.7, SB_coefficient=56.7 * 10 ** (-12),
Ts = UnprotectedSteelTemp.get_component_temperature(time, Tf)


# reduction factors
reduction_factors = SteelReductionFactors(Ts)
elastic_modulus_reduction_factors = (
    reduction_factors.interpolate_reduction_factor_youngs_modulus()
)
elastic_modulus = SteelMaterialProperty(Ts, elastic_modulus_reduction_factors)
effective_elastic_modulus = elastic_modulus.effective_elastic_modulus()


# column analysis
initial_temp = Ts[0]  # temperature change (°C)
delta_t = np.diff(time)
delta_Ts = np.concatenate(([Ts[0]], np.diff(Ts)))
sigma = effective_elastic_modulus * alpha * delta_Ts
F = sigma * A
internal_force1 = np.zeros(len(F))
for i in range(0, len(F) - 1):
    internal_force1[i] = np.sum(F[:i])


# failure evaluation
capacity = (
    np.pi**2 * effective_elastic_modulus * I / L**2
)  # capacity over varying temperature, pinned pinned
# print(capacity)
demand = (DCR * capacity[0] * L * 1 / (np.sqrt(L**2 - (e * L) ** 2))) + internal_force1
# print(demand)

for i in range(len(demand)):
    if demand[i] >= capacity[i]:
        critical_temp = Ts[i]
        critical_time = time[i]
        critical_demand = demand[i]
        break

print(f"Temperature at failure: {critical_temp} °C")
print(f"Time at failure: {critical_time / 60} minutes")
print(f"Critical load: {critical_demand} kips")
