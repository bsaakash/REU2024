import numpy as np
import matplotlib.pyplot as plt


# FIRE CURVE: CREATE SEPARATE MODULE
class ISO834FireCurve:
    # inputs: time array (hours)
    # outputs: .time, .firetemp (hours, degrees Celsius)
    def __init__(self, t):
        self.time = t

    def firetemp(self):
        return 20 + 345 * np.log10(8 * self.time + 1)


class ASTME119FireCurve:
    # inputs: time array (hours)
    # outputs: .time, .firetemp (hours, degrees Celsius)
    def __init__(self, t):
        self.time = t

    def firetemp(self):
        return (
            20
            + 750 * (1 - np.exp(-3.79553 * np.sqrt(self.time / 60)))
            + 170.41 * np.sqrt(self.time / 60)
        )


class ExternalFireCurve:
    # inputs: time array (hours)
    # outputs: .time, .firetemp (hours, degrees Celsius)
    def __init__(self, t):
        self.time = t

    def firetemp(self):
        return 20 + 660 * (
            1 - 0.686 * np.exp(-0.32 * self.time) - 0.313 * np.exp(-3.8 * self.time)
        )


class HydrocarbonFireCurve:
    # inputs: time array (hours)
    # outputs: .time, .firetemp (hours, degrees Celsius)
    def __init__(self, t):
        self.time = t

    def firetemp(self):
        return 20 + 1080 * (
            1 - 0.325 * np.exp(-0.167 * self.time) - 0.675 * np.exp(-2.5 * self.time)
        )


class ParametricFireCurve:
    # inputs: occupancy type, thermal conductivity, density, specific heat, base length of window, height of window, length 1 of room,
    #         length 2 of room, height of room, fuel load energy density, reference ventilation factor, reference sqrt of thermal inertia,
    #         fuel load, derived ventilation factor
    # outputs: .growth_rate, .thermal_inertia, .t_star (fictitious duration, hours), .maxfiretemp (degrees Celsius), .time_array (hours), .firetemp (degrees Celsius)
    def __init__(
        self,
        occupancy,
        k,
        p,
        c_p,
        B,
        H,
        l1,
        l2,
        H_r,
        e_f,
        F_ref=0.04,
        b_ref=1160,
        time_step_seconds=30,
    ):  # can set defaults to allow any order of input parameters
        occupancy_data = {
            "dwelling": ("medium", 20 / 60),
            "hospital": ("medium", 20 / 60),
            "hotel": ("medium", 20 / 60),
            "library": ("fast", 15 / 60),
            "office": ("medium", 20 / 60),
            "classroom": ("medium", 20 / 60),
            "shopping center": ("fast", 15 / 60),
            "theatre": ("fast", 15 / 60),
            "transport": ("slow", 25 / 60),
        }
        fire_growth_rate, t_lim_h = occupancy_data[occupancy]
        self.growth_rate = fire_growth_rate
        self.ventilation_controlled_fire_duration = t_lim_h
        self.thermal_conductivity = k
        self.density = p
        self.specific_heat = c_p
        self.window_base = B
        self.window_height = H
        self.room_length1 = l1
        self.room_length2 = l2
        self.room_height = H_r
        self.floor_fuel_load_energy_density = e_f
        self.reference_surface_area_of_unit_length = F_ref
        self.reference_breadth_of_beam = b_ref
        self.time_step_seconds = time_step_seconds

    def sqrt_thermal_inertia(self):
        b = np.sqrt(
            self.thermal_conductivity * self.density * self.specific_heat
        )  # sqrt(thermal inertia) ((W*s^0.5)/((m^2)*K))
        return b

    def room_floor_area(self):
        A_f = self.room_length1 * self.room_length2
        return A_f

    def window_area(self):
        A_v = self.window_base * self.window_height  # m^2
        return A_v

    def window_opening_height(self):
        H_v = (self.window_base * (self.window_height**2)) / self.window_area  # m
        return H_v

    def room_total_internal_surface_area(self):
        A_t = 2 * (
            self.room_length1 * self.room_length2
            + self.room_length1 * self.room_height
            + self.room_length2 * self.room_height
        )  # m^2 for all floors
        return A_t

    def ventilation_factor(self):
        F_v = (
            self.window_area
            * np.sqrt(self.window_opening_height)
            / self.room_total_internal_surface_area
        )  # m^0.5
        return F_v

    def fuel_load_energy_density_per_unit_area_internal_room_surface(self):
        e_t = (
            self.floor_fuel_load_energy_density
            * self.room_floor_area
            / self.room_total_internal_surface_area
        )  # MJ/m^2
        return e_t

        # solve for the duration of burning period, governed by ventilation-controlled or fuel-controlled

    def duration(self):
        return max(
            [
                (0.2e-3)
                * self.fuel_load_energy_density_per_unit_area_internal_room_surface
                / self.ventilation_factor,
                self.ventilation_controlled_fire_duration,
            ]
        )  # hours

    def control(self):
        if self.duration == self.ventilation_controlled_fire_duration:
            c = "fuel-controlled"
        elif (
            self.duration
            == (0.2e-3)
            * self.fuel_load_energy_density_per_unit_area_internal_room_surface
            / self.ventilation_factor
        ):
            c = "ventilation-controlled"
        return c

    def fictitious_ratio(self):
        r = (
            self.ventilation_factor / self.reference_surface_area_of_unit_length
        ) ** 2 / (self.sqrt_thermal_inertia / self.reference_breadth_of_beam) ** 2
        return r

    def fictitious_time(self):
        t_star = self.fictitious_ratio * self.duration  # hours
        return t_star

        # find x for the decay period calculations

    def x(self):
        self.t_star_min = self.fictitious_time * 60  # minutes
        if self.duration > self.ventilation_controlled_fire_duration:
            x = 1.0
        elif self.duration == self.ventilation_controlled_fire_duration:
            x = (
                self.ventilation_controlled_fire_duration
                * self.fictitious_ratio
                / self.fictitious_time
            )
        return x

    def time_steps_coefficient(self):
        return 3600 / self.time_step_seconds

    def rounded_fictitous_duration(self):  # round the fictitious duration
        return np.ceil(self.fictitious_time() * self.time_steps_coefficient()) / self.time_steps_coefficient()

    def max_fire_temp(self):
        return 20 + 1325 * (
            1
            - 0.324 * np.exp(-0.2 * self.rounded_fictitous_duration)
            - 0.204 * np.exp(-1.7 * self.rounded_fictitous_duration)
            - 0.472 * np.exp(-19 * self.rounded_fictitous_duration)
        )

    def total_fictitious_duration(self):
        # find the total fictitious duration
        if self.rounded_fictitous_duration <= 0.5:
            self.t_star_total = (
                self.max_fire_temp - 20
            ) / 625 + self.rounded_fictitous_duration * self.x
        elif 0.5 < self.rounded_fictitous_duration <= 2.0:
            self.t_star_total = (self.max_fire_temp - 20) / (
                250 * (3 - self.rounded_fictitous_duration)
            ) + self.rounded_fictitous_duration * self.x
        elif self.rounded_fictitous_duration > 2.0:
            self.t_star_total = (
                self.max_fire_temp - 20
            ) / 250 + self.rounded_fictitous_duration * self.x
        return self.t_star_total

        # round the total fictitious duration

    def rounded_total_fictitous_duration(self):  # round the fictitious duration
        d = self.time_steps_coefficient()
        return np.ceil(self.total_fictitious_duration() * d) / d
          # ceil; see standard library numpy
        

        # derive the time array from t = 0 to t = total fictitious duration

    def time_array(self):
        t = np.linspace(
            0,
            self.rounded_total_fictitous_duration,
            int(self.time_steps_coefficient * self.rounded_total_fictitous_duration),
        )
        return t

    def firetemp(self):
        fire_temperatures = []
        for t in self.time_array:
            if t <= self.t_star:
                T = 20 + 1325 * (
                    1
                    - 0.324 * np.exp(-0.2 * t)
                    - 0.204 * np.exp(-1.7 * t)
                    - 0.472 * np.exp(-19 * t)
                )
            else:
                if self.t_star <= 0.5:
                    T = self.max_fire_temp - 625 * (
                        t - self.t_star * self.x
                    )  # applies for t_star_max less than or equal to 0.5
                elif 0.5 < self.t_star <= 2.0:
                    T = self.max_fire_temp - 250 * (3 - self.t_star) * (
                        t - self.t_star * self.x
                    )  # applies for t_star_max greater than 0.5 and less than or equal to 2.0
                else:
                    T = self.max_fire_temp - 250 * (
                        t - self.t_star * self.x
                    )  # applies for t_star_max greater than 2.0
            fire_temperatures.append(T)
        return np.array(
            fire_temperatures
        )  # consider condition, doesn't drop beneath 20 (room temp)


# insert decay equation here, from page 65
# consider the temperature that is passed into the parametic curve is the fictitious time in hours, self.t_star
# this need be rounded up to the nearest 5s or 30s, then use


# MATERIAL MODULE
class MaterialProperty:
    def __init__(self, T_s):
        self.steel_temperature = T_s
        return self.steel_temperature

    def specific_heat(self):
        # Define the specific heat constant for the time step
        if 20 <= self.steel_temperature < 600:
            specific_heat = (
                425
                + 0.773 * self.steel_temperature
                - 1.69 * (10 ^ (-3)) * self.steel_temperature**2
                + 2.22 * (10 ^ (-6)) * self.steel_temperature**3
            )
            # applies when the steel temperature is greater than or equal to 20 degrees Celsius and less than 600 degrees Celsius
        elif 600 <= self.steel_temperature < 735:
            specific_heat = 666 + 13002 / (738 - self.steel_temperature)
            # applies when the steel temperature is greater than or equal to 600 degrees Celsius and less than 735 degrees Celsius
        elif 735 <= self.steel_temperature < 900:
            specific_heat = 545 + 17820 / (self.steel_temperature - 731)
            # applies when the steel temperature is greater than or equal to 735 degrees Celsius and less than 900 degrees Celsius
        elif 900 <= self.steel_temperature < 1200:
            specific_heat = 650
            # applies when the steel temperature is greater than or equal to 900 degrees Celsius and less than or equal to 1200 degrees Celsius
        return specific_heat

    def thermal_conductivity(self):
        # Define the thermal conductivity for the time step
        if 20 <= self.steel_temperature < 800:
            thermal_conductivity = 54 - 0.0333 * self.steel_temperature
            # applies when the steel temperature is greater than or equal to 20 degrees Celsius and less than 800 degrees Celsius
        elif 800 <= self.steel_temperature <= 1200:
            thermal_conductivity = 27.3
            # applies when the steel temperature is greater than or equal to 800 degrees Celsius and less than or equal to 1200 degrees Celsius
        return thermal_conductivity

    def density(self):
        return

    def youngs_modulus(self):
        return

    def yield_strength(self):
        return


# PROTECTIVE MATERIAL MODULE
class ProtectionProperty:
    def __init__(
        self,
        thickness_of_insulation,
        specific_heat_insulation,
        density_of_insulation,
        thermal_conductivity_of_insulation,
    ):
        self.thickness = thickness_of_insulation
        self.specific_heat = specific_heat_insulation
        self.density = density_of_insulation
        self.thermal_conductivity = thermal_conductivity_of_insulation


# STEEL TEMP MODULE
class ProtectedSteelTemperature:
    def __init__(
        self,
        T_f0,
        T_f,
        T_s,
        t0,
        t,
        protection,
        section_type,
        F,
        V,
        # specific_heat_insulation,  # potentially create separate classes (unprotected // protected)
        # density_insulation,
        # thermal_conductivity_insulation,
        # thickness_insulation,
        convective_heat_transfer_coefficient,
        stefan_boltzmann_coefficient=56.7 * 10 ^ (-12),
    ):
        self.fire_initial_temperature = T_f0
        self.fire_final_temperature = T_f
        self.steel_temperature = T_s

        self.time_initial = t0
        self.time_final = t

        self.protection_type = protection
        self.section_type = section_type

        self.convective_heat_transfer_coeff = convective_heat_transfer_coefficient
        self.stefan_boltzmann_coefficient = stefan_boltzmann_coefficient

        self.section_surface_area_of_unit_length_member = F
        self.section_volume_per_unit_length_member = V

        # self.insulation_specific_heat = specific_heat_insulation
        # self.insulation_density = density_insulation
        # self.insulation_thermal_conductivity = thermal_conductivity_insulation
        # self.insulation_thickness = thickness_insulation

    def delta_t(self):
        delta_t = self.time_final - self.time_initial
        if delta_t * ParametricFireCurve.time_steps_coefficient <= 30:
            d = delta_t
        elif delta_t * ParametricFireCurve.time_steps_coefficient > 30:
            d = "Error. Time step is greater than 30 seconds. Time array is not properly spaced for protected case."
        return d

    def delta_T_f(self):
        return self.fire_final_temperature - self.fire_initial_temperature

    def section_factor(self):
        self.contour_protection_section_factor = (
            self.section_surface_area_of_unit_length_member
            / self.section_volume_per_unit_length_member
        )
        return self.contour_protection_section_factor

    def protection_constant(self):
        phi = (ProtectionProperty.density * ProtectionProperty.specific_heat) / (
            MaterialProperty.density * MaterialProperty.specific_heat
        )
        return phi

    def temperature_change_protected_steel_member(self):
        temperature_change_per_time_step = (
            (ProtectionProperty.thermal_conductivity * self.section_factor)
            / (
                ProtectionProperty.thickness
                * ProtectionProperty.density
                * ProtectionProperty.specific_heat
            )
        ) * (self.fire_temperature - self.steel_temperature) / (
            1 + self.protection_constant / 3
        ) * (
            self.time_final - self.time_initial
        ) - (
            np.exp(self.protection_constant / 10) - 1
        ) * (
            self.fire_final_temperature - self.fire_initial_temperature
        )
        return temperature_change_per_time_step


class UnprotectedSteelTemperature:
    def __init__(
        self,
        T_f0,
        T_f,
        T_s,
        t0,
        t,
        protection,
        section_type,
        F,
        V,
        F_b,
        V_b,
        convective_heat_transfer_coefficient,
        fire_emissivity=1.0,
        material_emissivity=0.7,
        stefan_boltzmann_coefficient=56.7 * 10 ^ (-12),
    ):

        self.fire_initial_temperature = T_f0
        self.fire_final_temperature = T_f
        self.steel_temperature = T_s
        self.fire_temperature = T_f

        self.time_initial = t0
        self.time_final = t

        self.protection_type = protection
        self.section_type = section_type

        self.convective_heat_transfer_coeff = convective_heat_transfer_coefficient
        self.stefan_boltzmann_coefficient = stefan_boltzmann_coefficient

        self.section_surface_area_of_unit_length_member = F
        self.section_volume_per_unit_length_member = V
        self.section_surface_area_of_unit_length_board_protection = F_b
        self.section_volume_per_unit_length_board_protection = V_b

        self.fire_emissivity = fire_emissivity
        self.material_emissivity = material_emissivity

        self.steel_specific_heat = MaterialProperty.specific_heat
        self.steel_density = MaterialProperty.density

    def delta_t(self):
        delta_t = self.time_final - self.time_initial
        if delta_t * ParametricFireCurve.time_steps_coefficient <= 5:
            d = delta_t
        elif delta_t * ParametricFireCurve.time_steps_coefficient > 5:
            d = "Error. Time step is greater than 5 seconds. Time array is not properly spaced for unprotected case."
        return d

    def delta_T_f(self):
        return self.fire_temperature - self.fire_initial_temperature

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

    def temperature_change_unprotected_steel_member(self):
        k_sh = self.correction_factor()
        if hasattr(self, "k_sh"):
            # temperature_change_array = []
            temperature_change_per_time_step = (
                k_sh
                * self.contour_protection_section_factor
                / (self.steel_density * self.steel_specific_heat)
                * (
                    self.convective_heat_transfer_coeff
                    * (self.fire_temperature - self.steel_temperature)
                    + self.stefan_boltzmann_coefficient
                )
            )
        return temperature_change_per_time_step


# STEEL TEMPERATURE CALCULATION


# IMPORTING STUFF FROM DATABASE
class Element:
    def __init__(self):
        return


# DEMAND MODULE
class Demand:
    def __init__(self, dead_load, live_load, eccentricity, thermal_expansion_coefficient, cross_sectional_area):
        self.dead_load = dead_load
        self.live_load = live_load
        self.thermal_expansion_coefficient = thermal_expansion_coefficient
        self.cross_sectional_area = cross_sectional_area

    def internal_force(self):
        return self.thermal_expansion_coefficient * self.cross_sectional_area * temperature_change_array * youngs_modulus_of_elasticity

    def applied_column_load(self):
        P = 1.2 * self.dead_load + 1.6 * self.live_load
        return 

    def applied_beam_load(self):
        w = 1.2 * self.dead_load + 1.6 * self.live_load
        return

    def column(self):
        return

    def beam(self):
        return


# CAPACITY MODULE
class ColumnCapacity:
    def __init__(self, youngs_modulus_of_elasticity, moment_of_inertia, element_length, eccentricity):
        self.I = moment_of_inertia
        self.E = youngs_modulus_of_elasticity
        self.L = element_length
    
    def critical_buckling_load(self):
        P = np.pi**2 * self.E * self.I / (self.L**2)
        return

    def column(self):
        self
        return

class BeamCapacity:
    def __init__(self, youngs_modulus_of_elasticity, moment_of_inertia, element_length):
        r = P

    def column(self):
        self
        return



# FAILURE EVALUATION
class Failure:
    def __init__(self, P):
        r = P

    def column(self):
        self
        return

    def beam(self):
        return
