import numpy as np
import matplotlib.pyplot as plt

# STANDARD FIRE CURVE
class ISO834FireCurve:
    def __init__(self, t):
        self.time = t
    def firetemp(self):
        return 20 + 345 * np.log10(8 * self.time + 1)

# EUROCODE REDUCTION FACTOR MODULE
class SteelReductionFactors:
    def __init__(self, temperature_steel):
        self.steel_element_temperature = temperature_steel
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

    # Eurocode reduction factors
    def interpolate_reduction_factor_effective_yield_strength(self):
        return np.interp(
            self.steel_element_temperature,
            self.eurocode_temperatures,
            self.reduction_factor_for_effective_yield_strength,
        )

    def interpolate_reduction_factor_proportional_limit(self):
        return np.interp(
            self.steel_element_temperature,
            self.eurocode_temperatures,
            self.reduction_factor_for_proportional_limit,
        )

    def interpolate_reduction_factor_youngs_modulus(self):
        return np.interp(
            self.steel_element_temperature,
            self.eurocode_temperatures,
            self.reduction_factor_for_youngs_modulus,
        )

# MATERIAL MODULE
class SteelMaterialProperty:
    def __init__(
        self,
        temperature_steel,
        room_temperature_yield_strength=50,
        proportional_limit=65,
        room_temperature_youngs_modulus=29000,
    ):
        self.steel_temperature = temperature_steel
        self.room_temperature_youngs_modulus = room_temperature_youngs_modulus
        self.room_temperature_yield_strength = room_temperature_yield_strength
        self.proportional_limit = proportional_limit
        return

    # VERIFY specific heat and thermal conductivity to the Eurocode
    def specific_heat(self):
        # Define the specific heat constant for the time step
        if 20 <= self.steel_temperature < 600:
            specific_heat = (
                425
                + 0.773 * self.steel_temperature
                - 1.69 * (10 ** (-3)) * self.steel_temperature**2
                + 2.22 * (10 ** (-6)) * self.steel_temperature**3
            )
            # applies when the steel temperature is greater than or equal to 20 degrees Celsius and less than 600 degrees Celsius
        elif 600 <= self.steel_temperature < 735:
            specific_heat = 666 + 13002 / (738 - self.steel_temperature)
            # applies when the steel temperature is greater than or equal to 600 degrees Celsius and less than 735 degrees Celsius
        elif 735 <= self.steel_temperature < 900:
            specific_heat = 545 + 17820 / (self.steel_temperature - 731)
            # applies when the steel temperature is greater than or equal to 735 degrees Celsius and less than 900 degrees Celsius
        elif 900 <= self.steel_temperature <= 1200:
            specific_heat = 650
            # applies when the steel temperature is greater than or equal to 900 degrees Celsius and less than or equal to 1200 degrees Celsius
        else:
            specific_heat = None
        return specific_heat

    def thermal_conductivity(self):
        # Define the thermal conductivity for the time step
        if 20 <= self.steel_temperature < 800:
            thermal_conductivity = 54 - 0.0333 * self.steel_temperature
            # applies when the steel temperature is greater than or equal to 20 degrees Celsius and less than 800 degrees Celsius
        elif 800 <= self.steel_temperature <= 1200:
            thermal_conductivity = 27.3
            # applies when the steel temperature is greater than or equal to 800 degrees Celsius and less than or equal to 1200 degrees Celsius
        else:
            thermal_conductivity = None
        return thermal_conductivity

    def density(self):
        return 7850


    def effective_yield_strength(self):
        reduction_factors = SteelReductionFactors(self.steel_temperature)
        return (
            self.room_temperature_youngs_modulus
            * reduction_factors.interpolate_reduction_factor_effective_yield_strength()
        )

    def effecive_proportional_limit(self):
        reduction_factors = SteelReductionFactors(self.steel_temperature)
        return (
            self.proportional_limit
            * reduction_factors.interpolate_reduction_factor_proportional_limit()
        )

    def effective_youngs_modulus(self):
        reduction_factors = SteelReductionFactors(self.steel_temperature)
        return (
            self.room_temperature_youngs_modulus
            * reduction_factors.interpolate_reduction_factor_youngs_modulus()
        )
    
# UNPROTECTED STEEL PARAMETERS
class UnprotectedSteelParameters:
    def __init__(
        self,
        F,
        V,
        F_b,
        V_b,
        section_type="I-section",
        convective_heat_transfer_coefficient=25,
        fire_emissivity=1.0,
        material_emissivity=0.7,
        stefan_boltzmann_coefficient=56.7 * 10 ** (-12),
    ):

        self.section_type = section_type

        self.convective_heat_transfer_coeff = convective_heat_transfer_coefficient
        self.stefan_boltzmann_coefficient = stefan_boltzmann_coefficient

        self.section_surface_area_of_unit_length_member = F
        self.section_volume_per_unit_length_member = V
        self.section_surface_area_of_unit_length_board_protection = F_b
        self.section_volume_per_unit_length_board_protection = V_b

        self.fire_emissivity = fire_emissivity
        self.material_emissivity = material_emissivity

    def correction_factor(self):
        self.board_protection_section_factor = (
            self.section_surface_area_of_unit_length_board_protection
            / self.section_volume_per_unit_length_board_protection
        )
        self.contour_protection_section_factor = (
            self.section_surface_area_of_unit_length_member
            / self.section_volume_per_unit_length_member
        )
        if self.section_type == "I-section":
            k_sh = (
                0.9
                * self.board_protection_section_factor
                / self.contour_protection_section_factor
            )
        else:
            k_sh = (
                self.board_protection_section_factor
                / self.contour_protection_section_factor
            )
        return k_sh

    def resultant_emissivity(self):
        return self.fire_emissivity * self.material_emissivity

# UNPROTECTED STEEL TEMPERATURE
class PublishedFireUnprotectedSteelTemperature:
    def __init__(
        self,
        fire_curve,
        t,
        F,
        V,
        F_b,
        V_b,
    ):
        self.fire_curve = fire_curve
        self.time_array = t
        self.F = F
        self.V = V
        self.F_b = F_b
        self.V_b = V_b

    def temperature_loop(self):
        fire_temperatures = self.fire_curve
        time_array = self.time_array

        delta_t = np.zeros(len(time_array) - 1)
        delta_T_s = np.zeros(len(time_array) - 1)
        T_s = np.zeros(len(time_array))

        T_s[0] = fire_temperatures[0]  # Initial temperature

        steel_specific_heat = np.zeros(len(time_array))
        steel_density = np.zeros(len(time_array))

        material_properties = SteelMaterialProperty(T_s[0])
        steel_specific_heat[0] = material_properties.specific_heat()
        steel_density[0] = material_properties.density()

        unprotected_parameters = UnprotectedSteelParameters(
            self.F, self.V, self.F_b, self.V_b
        )

        for i in range(len(time_array) - 1):
            delta_t[i] = time_array[i + 1] - time_array[i]
            if delta_t[i] > 5:
                raise ValueError("Error: delta_t is greater than 5 seconds.")
            
            steel_temperature = T_s[i]
            material_properties = SteelMaterialProperty(steel_temperature)
            steel_specific_heat[i] = material_properties.specific_heat()
            steel_density[i] = material_properties.density()
            
            delta_T_s[i] = (
            delta_t[i]
            * unprotected_parameters.correction_factor()
            * unprotected_parameters.contour_protection_section_factor
            * (
                unprotected_parameters.convective_heat_transfer_coeff
                * (fire_temperatures[i + 1] - T_s[i])
                + unprotected_parameters.stefan_boltzmann_coefficient
                * unprotected_parameters.resultant_emissivity()
                * (fire_temperatures[i + 1]**4 - T_s[i]**4)
                )
            / (steel_density[i] * steel_specific_heat[i])
            )
            T_s[i + 1] = T_s[i] + delta_T_s[i]
                  
        return T_s, delta_t, delta_T_s  


# Assume values for F, V, F_b, V_b
F = 100
V = 200
F_b = 50
V_b = 100

t = np.linspace(0, 180, 180) # Time in minutes

fire_curve = ISO834FireCurve(t)

reduction_factors = SteelReductionFactors(T_s)

steel_material_properties = SteelMaterialProperty(T_s)

F_y_effective = SteelMaterialProperty.effective_yield_strength()
E_effective = SteelMaterialProperty.effective_youngs_modulus()
