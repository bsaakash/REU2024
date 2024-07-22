from typing import Protocol
import numpy as np


class FireCurve(Protocol):
    def get_temperature(self, time):
        raise NotImplementedError

    def get_time_from_temperature(self, temperature_value):
        diff = np.diff(self.temperature)
        increasing_end = np.argmax(diff <= 0) + 1
        if increasing_end == 1 and diff[0] > 0:
            increasing_end = len(self.temperature)
        increasing_part = self.temperature[:increasing_end]
        closest_index = np.argmin(np.abs(increasing_part - temperature_value))
        return self.time[closest_index]


class ISO834FireCurve(FireCurve):
    def __init__(self) -> None:
        self.time = np.arange(185)

    def get_temperature(self):
        self.temperature = 20 + 345 * np.log10(8 * self.time + 1)
        return self.temperature


class ASTME119FireCurve(FireCurve):
    def __init__(self) -> None:
        self.time = np.arange(185)

    def get_temperature(self):
        self.temperature = (
            20
            + 750 * (1 - np.exp(-3.79553 * np.sqrt(self.time / 60)))
            + 170.41 * np.sqrt(self.time / 60)
        )
        return self.temperature


class ExternalFireCurve(FireCurve):
    def __init__(self) -> None:
        self.time = np.arange(185)

    def get_temperature(self):
        self.temperature = 20 + 660 * (
            1 - 0.686 * np.exp(-0.32 * self.time) - 0.313 * np.exp(-3.8 * self.time)
        )
        return self.temperature


class HydrocarbonFireCurve(FireCurve):
    def __init__(self) -> None:
        self.time = np.arange(185)

    def get_temperature(self):
        self.temperature = 20 + 1080 * (
            1 - 0.325 * np.exp(-0.167 * self.time) - 0.675 * np.exp(-2.5 * self.time)
        )
        return self.temperature


class ParametricFireCurve(FireCurve):
    # inputs: occupancy type, 
    #         thermal conductivity, 
    #         density,
    #         specific heat, 
    #         base length of window, height of window, 
    #         length 1 of room, length 2 of room, height of room, 
    #         fuel load energy density, 
    #         reference ventilation factor, 
    #         reference sqrt of thermal inertia,
    #         fuel load, derived ventilation factor
    # outputs: .growth_rate, 
    #          .thermal_inertia, 
    #          .t_star (fictitious duration, hours), 
    #          .maxfiretemp (degrees Celsius), 
    #          .time_array (hours), 
    #          .firetemp (degrees Celsius)
    def __init__(
        self,
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
        self.thermal_conductivity = thermal_conductivity
        self.density = density
        self.specific_heat = specific_heat
        self.window_base = window_base
        self.window_height = window_height
        self.room_length1 = room_length1
        self.room_length2 = room_length2
        self.room_height = room_height
        self.floor_fuel_load_energy_density = floor_fuel_load_energy_density
        self.reference_surface_area_of_unit_length = F_ref
        self.reference_breadth_of_beam = b_ref
        self.time_step_seconds = time_step_seconds
       
       
        self.sqrt_thermal_inertia = np.sqrt(
            self.thermal_conductivity * self.density * self.specific_heat
        )  # sqrt(thermal inertia) ((W*s^0.5)/((m^2)*K))

        self.room_floor_area = self.room_length1 * self.room_length2
        self.window_area = self.window_base * self.window_height  # m^2
        self.window_opening_height = (self.window_base * (self.window_height**2)) / self.window_area  # m

        self.room_total_internal_surface_area = 2 * (
            self.room_length1 * self.room_length2
            + self.room_length1 * self.room_height
            + self.room_length2 * self.room_height
        )  # m^2 for all floors

        self.ventilation_factor = (
            self.window_area
            * np.sqrt(self.window_opening_height)
            / self.room_total_internal_surface_area
        )  # m^0.5

        self.fuel_load_energy_density_per_unit_area_internal_room_surface = (
            self.floor_fuel_load_energy_density
            * self.room_floor_area
            / self.room_total_internal_surface_area
        )  # MJ/m^2

        self.duration = max(
            [
                (0.2e-3)
                * self.fuel_load_energy_density_per_unit_area_internal_room_surface
                / self.ventilation_factor,
                self.ventilation_controlled_fire_duration,
            ]
        )
        # output: the duration of the burning period (hours), which is the maximum betweent the 

        if self.duration == self.ventilation_controlled_fire_duration:
            c = "fuel-controlled"
        elif (
            self.duration
            == (0.2e-3)
            * self.fuel_load_energy_density_per_unit_area_internal_room_surface
            / self.ventilation_factor
        ):
            c = "ventilation-controlled"
        self.control = c

        self.fictitious_ratio = (
            self.ventilation_factor / self.reference_surface_area_of_unit_length
        ) ** 2 / (self.sqrt_thermal_inertia / self.reference_breadth_of_beam) ** 2
        # multiply by the time to get the fictitious time

        self.fictitious_time = self.fictitious_ratio * self.duration  # hours
        # find x for the decay period calculations

        self.t_star_minutes = self.fictitious_time * 60  # minutes
        if self.duration > self.ventilation_controlled_fire_duration:
            x = 1.0
        elif self.duration == self.ventilation_controlled_fire_duration:
            x = (
                self.ventilation_controlled_fire_duration
                * self.fictitious_ratio
                / self.fictitious_time
            )
        self.x = x

        self.time_steps_coefficient = 3600 / self.time_step_seconds

        self.rounded_fictitous_duration = (
            np.ceil(self.fictitious_time * self.time_steps_coefficient)
            / self.time_steps_coefficient
        )

        self.max_fire_temp = 20 + 1325 * (
            1
            - 0.324 * np.exp(-0.2 * self.rounded_fictitous_duration)
            - 0.204 * np.exp(-1.7 * self.rounded_fictitous_duration)
            - 0.472 * np.exp(-19 * self.rounded_fictitous_duration)
        )

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
        self.total_fictitious_duration = self.t_star_total
        # round the total fictitious duration

        self.rounded_total_fictitous_duration = (
            np.ceil(self.total_fictitious_duration * self.time_steps_coefficient)
            / self.time_steps_coefficient
        )

        t = np.linspace(
            0,
            self.rounded_total_fictitous_duration,
            int(
                self.time_steps_coefficient * self.rounded_total_fictitous_duration
            ),
        )
        self.time_array = t
        # output: time array from t = 0 to t = total fictitious duration (hours)

    def fire_temp(self):
        fire_temp = []
        for t in self.time_array:
            # equation for Temperature during burning period, where t is the fictitious time (in hours)
            if t <= self.rounded_fictitous_duration:
                T = 20 + 1325 * (
                    1
                    - 0.324 * np.exp(-0.2 * t)
                    - 0.204 * np.exp(-1.7 * t)
                    - 0.472 * np.exp(-19 * t)
                )
            else:
                if self.rounded_fictitous_duration <= 0.5:
                    T = self.max_fire_temp - 625 * (
                        t - self.rounded_fictitous_duration * self.x
                    )  # applies for max rounded fictitious duration less than or equal to 0.5
                elif 0.5 < self.rounded_fictitous_duration <= 2.0:
                    T = self.max_fire_temp - 250 * (
                        3 - self.rounded_fictitous_duration
                    ) * (
                        t - self.rounded_fictitous_duration * self.x
                    )  # applies for max rounded fictitious duration greater than 0.5 and less than or equal to 2.0
                else:
                    T = self.max_fire_temp - 250 * (
                        t - self.rounded_fictitous_duration * self.x
                    )  # applies for max rounded fictitious duration greater than 2.0
            fire_temp.append(T)
        return np.array(
            fire_temp
        )  # consider condition, doesn't drop beneath 20 (room temp)
