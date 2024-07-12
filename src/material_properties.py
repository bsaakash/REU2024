from typing import Protocol


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

    def yield_strength(self, temperature, epsilon=0):
        return

    def modulus_of_elasticity(self, temperature, epsilon=0):
        return

    def proportional_limit(self, temperature, epsilon=0):
        return

class SteelThermalProperties(ThermalProperties):
    def __init__(self) -> None:
        super().__init__()

    def thermal_conductivity(self, temperature, epsilon=0):
        return

    def thermal_strain(self, temperature, epsilon=0):
        return

    def specific_heat(self, temperature, epsilon=0):
        return

    def density(self, temperature, epsilon=0):
        raise NotImplementedError


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
