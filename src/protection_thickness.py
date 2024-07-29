import numpy as np

class InsulationThermalProperties:
    def thickness_protection(self, board_perimeter, section_area, protection_thermal_conductivity, protection=1256):
        return (board_perimeter * protection_thermal_conductivity) / (section_area * protection)

