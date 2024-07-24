from typing import Protocol
import numpy as np


class MechanicalProperties(Protocol):
    def yield_strength(self, temperature, epsilon):
        raise NotImplementedError

    def modulus_of_elasticity(self, temperature, epsilon):
        raise NotImplementedError

    def proportional_limit(self, temperature, epsilon):
        raise NotImplementedError


class ThermalProperties(Protocol):
    def __init__(self) -> None:
        super().__init__()

    def thermal_conductivity(self, temperature, epsilon):
        raise NotImplementedError

    def thermal_strain(self, temperature, epsilon):
        raise NotImplementedError

    def specific_heat(self, temperature, epsilon):
        raise NotImplementedError

    def density(self, temperature, epsilon):
        raise NotImplementedError


class SteelMechanicalProperties(MechanicalProperties):
    def __init__(self, steel_room_temp_yield_strength=220, steel_room_temp_modulus=200000, steel_room_temp_proportional_limit=345) -> None:
        super().__init__()
        self.room_temperature_yield_strength = steel_room_temp_yield_strength
        self.room_temperature_modulus = steel_room_temp_modulus
        self.room_temperature_proportional_limit = steel_room_temp_proportional_limit
        self.eurocode_temperatures = np.array(
            [20, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200]
        )
        self.reduction_factor_for_proportional_limit = np.array(
            [
                1.000,
                1.000,
                0.807,
                0.613,
                0.420,
                0.360,
                0.180,
                0.075,
                0.050,
                0.0375,
                0.0250,
                0.0125,
                0.0000,
            ]
        )

    def yield_strength(self, temperature, epsilon=0):
        T = temperature
        self.reduction_factor_yield = (
            1.2
            * (np.exp(1.61 - 1.68e-3 * T - 3.36e-6 * T**2 + 0.35 * epsilon))
            / (np.exp(1.61 - 1.68e-3 * T - 3.36e-6 * T**2 + 0.35 * epsilon) + 1)
        )
        return self.reduction_factor_yield * self.room_temperature_yield_strength

    def elastic_modulus(self, temperature, epsilon=0):
        T = temperature
        self.reduction_factor_modulus = (
            1.1
            * (np.exp(2.54 - 2.69e-3 * T - 2.83e-6 * T**2 + 0.36 * epsilon))
            / (np.exp(2.54 - 2.69e-3 * T - 2.83e-6 * T**2 + 0.36 * epsilon) + 1)
        )
        return self.reduction_factor_modulus * self.room_temperature_modulus

    def proportional_limit(self, temperature):
        interpolate_reduction_factor_proportional_limit = np.interp(
            temperature,
            self.eurocode_temperatures,
            self.reduction_factor_for_proportional_limit,
        )
        return (
            self.room_temperature_proportional_limit
            * interpolate_reduction_factor_proportional_limit
        )


class SteelThermalProperties(ThermalProperties):
    def __init__(self) -> None:
        super().__init__()
#TODO
    def thermal_conductivity(self, temperature, epsilon=0):
        T = temperature
        return np.exp(
            -2.72 + 1.89e-3 * T - 0.195e-6 * T**2 + 0.209 * epsilon
        )

    def thermal_strain(self, temperature, epsilon=0):
        T = temperature
        if 20 <= T < 750:
            deterministic_thermal_strain = (
                1.2 * (10 ** (-5)) * T
                + 0.4 * (10 ** (-8)) * T**2
                - 2.416 * (10 ** (-4))
            )
            thermal_strain = (np.sqrt(deterministic_thermal_strain) - 1.28e-3 + (3.96e-6) * T + 0.0039*epsilon)**2
            # applies when the steel temperature is greater than or equal to 20 degrees Celsius and less than 750 degrees Celsius
        elif 750 <= T <= 860:
            deterministic_thermal_strain = 1.1 * (10 ** (-2))
            thermal_strain = (np.sqrt(deterministic_thermal_strain) + (1.69 + 0.64*(T - 750) - 1.7*(T - 750)**0.81 + 3.7*epsilon)*(10**-3))**2
            # applies when the steel temperature is greater than or equal to 750 degrees Celsius and less than or equal to 860 degrees Celsius
        elif 860 < T <= 1200:
            deterministic_thermal_strain = 2 * (10 ** (-5)) * T - 6.2 * (10 ** (-3))
            thermal_strain = (np.sqrt(deterministic_thermal_strain) - 2.32e-3 + (0.173e-6) * (T - 860) + 0.0037*epsilon)**2
            # applies when the steel temperature is greater than 860 degrees Celsius and less than or equal to 1200 degrees Celsius
        else:
            raise ValueError
        return thermal_strain

#TODO
    def specific_heat(self, temperature, epsilon=0):
        T = temperature
        return 1700 - np.exp(
            6.81 - 1.61e-3 * T + 0.44e-6 * T**2 + 0.213 * epsilon
        )
#TODO    
    def density(self, temperature, epsilon=0):
        T = temperature
        return np.exp(-2.028 + 7.83 * T ** (-0.0065) + 0.122 * epsilon)


class InsulationThermalProperties(ThermalProperties):
    def __init__(self) -> None:
        super().__init__()

    def thermal_conductivity(self, temperature, epsilon=0):
        T = temperature
        return np.exp(-2.72 + (1.89e-3) * T - (0.195e-6) * T**2 + 0.209 * epsilon)

    def thermal_strain(self, temperature, epsilon=0):
        raise NotImplementedError

    def specific_heat(self, temperature, epsilon=0):
        T = temperature
        return 1700 - np.exp(6.81 - (1.61e-3) * T + (0.44e-6) * T**2 + 0.213 * epsilon)

    def density(self, temperature, epsilon=0):
        T = temperature
        return np.exp(-2.028 + 7.83 * T ** (-0.0065) + 0.122 * epsilon)