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
    def __init__(self) -> None:
        super().__init__()
        self.eurocode_temperatures = np.array(
        [20, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200]
    )
        self.reduction_factor_for_effective_yield_strength = np.array(
        [
            1.000,
            1.000,
            1.000,
            1.000,
            1.000,
            0.780,
            0.470,
            0.230,
            0.110,
            0.060,
            0.040,
            0.020,
            0.000,
        ]
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
    def yield_strength(self, temperature, room_temperature_yield_strength=50, epsilon=0):
        interpolate_reduction_factor_effective_yield_strength = np.interp(
            temperature,
            self.eurocode_temperatures,
            self.reduction_factor_for_effective_yield_strength,
        )
        return (
            room_temperature_yield_strength 
            * interpolate_reduction_factor_effective_yield_strength
        )

    def modulus_of_elasticity(self, temperature, room_temperature_youngs_modulus=29000, epsilon=0):
        interpolate_reduction_factor_youngs_modulus = np.interp(
            temperature,
            self.eurocode_temperatures,
            self.reduction_factor_for_youngs_modulus,
        )
        return (
            room_temperature_youngs_modulus
            * interpolate_reduction_factor_youngs_modulus
        )

    def proportional_limit(self, temperature, room_temperature_proportional_limit=65, epsilon=0):
        interpolate_reduction_factor_proportional_limit = np.interp(
            temperature,
            self.eurocode_temperatures,
            self.reduction_factor_for_proportional_limit,
        )
        return (
            room_temperature_proportional_limit
            * interpolate_reduction_factor_proportional_limit
        )

class SteelThermalProperties(ThermalProperties):
    def __init__(self) -> None:
        super().__init__()

    def thermal_conductivity(self, temperature, epsilon=0):
        if 20 <= temperature < 800:
            thermal_conductivity = 54 - 0.0333 * temperature
            # applies when the steel temperature is greater than or equal to 20 degrees Celsius and less than 800 degrees Celsius
        elif 800 <= temperature <= 1200:
            thermal_conductivity = 27.3
            # applies when the steel temperature is greater than or equal to 800 degrees Celsius and less than or equal to 1200 degrees Celsius
        else:
            thermal_conductivity = None
        return thermal_conductivity

    def thermal_strain(self, temperature, epsilon=0):
        
        # FIX WITH BUCHANAN

        if 20 <= temperature < 750:
            thermal_strain = (
                1.2 * (10 ** (-5)) * temperature
                + 0.4 * (10 ** (-8)) * temperature**2
                - 2.416 * (10 ** (-4))
            )
            # applies when the steel temperature is greater than or equal to 20 degrees Celsius and less than 750 degrees Celsius
        elif 750 <= temperature <= 860:
            thermal_strain = 1.1 * (10**(-2))
            # applies when the steel temperature is greater than or equal to 750 degrees Celsius and less than or equal to 860 degrees Celsius
        elif 860 < temperature <= 1200:
            thermal_strain = 2 * (10**(-5)) * temperature - 6.2 * (10**(-3))
            # applies when the steel temperature is greater than 860 degrees Celsius and less than or equal to 1200 degrees Celsius
        else:
            thermal_strain = None
        return thermal_strain

    def specific_heat(self, temperature, epsilon=0):
        if 20 <= temperature < 600:
            specific_heat = (
                425
                + 0.773 * temperature
                - 1.69 * (10 ** (-3)) * temperature**2
                + 2.22 * (10 ** (-6)) * temperature**3
            )
            # applies when the steel temperature is greater than or equal to 20 degrees Celsius and less than 600 degrees Celsius
        elif 600 <= temperature < 735:
            specific_heat = 666 + 13002 / (738 - temperature)
            # applies when the steel temperature is greater than or equal to 600 degrees Celsius and less than 735 degrees Celsius
        elif 735 <= temperature < 900:
            specific_heat = 545 + 17820 / (temperature - 731)
            # applies when the steel temperature is greater than or equal to 735 degrees Celsius and less than 900 degrees Celsius
        elif 900 <= temperature <= 1200:
            specific_heat = 650
            # applies when the steel temperature is greater than or equal to 900 degrees Celsius and less than or equal to 1200 degrees Celsius
        else:
            specific_heat = None
        return specific_heat

    def density(self, temperature, epsilon=0):
        return 7850
        # raise NotImplementedError

class InsulationThermalProperties(ThermalProperties):
    def __init__(self) -> None:
        super().__init__()

    def thermal_conductivity(self, temperature, epsilon=0):
        return

    def thermal_strain(self, temperature, epsilon=0):
        raise NotImplementedError

    def specific_heat(self, temperature, epsilon=0):
        return

    def density(self, temperature, epsilon=0):
        return
