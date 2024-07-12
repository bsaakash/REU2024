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
            1
            - 0.686 * np.exp(-0.32 * self.time)
            - 0.313 * np.exp(-3.8 * self.time)
        )
        return self.temperature


class HydrocarbonFireCurve(FireCurve):
    def __init__(self) -> None:
        self.time = np.arange(185)

    def get_temperature(self):
        self.temperature = 20 + 1080 * (
            1
            - 0.325 * np.exp(-0.167 * self.time)
            - 0.675 * np.exp(-2.5 * self.time)
        )
        return self.temperature


class ParametricFireCurve(FireCurve):
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
        H_v = (self.window_base * (self.window_height**2)) / self.window_area()  # m
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
            self.window_area()
            * np.sqrt(self.window_opening_height())
            / self.room_total_internal_surface_area()
        )  # m^0.5
        return F_v

    def fuel_load_energy_density_per_unit_area_internal_room_surface(self):
        e_t = (
            self.floor_fuel_load_energy_density
            * self.room_floor_area()
            / self.room_total_internal_surface_area()
        )  # MJ/m^2
        return e_t

        # solve for the duration of burning period, governed by ventilation-controlled or fuel-controlled

    def duration(self):
        return max(
            [
                (0.2e-3)
                * self.fuel_load_energy_density_per_unit_area_internal_room_surface()
                / self.ventilation_factor(),
                self.ventilation_controlled_fire_duration,
            ]
        )  # hours

    def control(self):
        if self.duration == self.ventilation_controlled_fire_duration:
            c = "fuel-controlled"
        elif (
            self.duration()
            == (0.2e-3)
            * self.fuel_load_energy_density_per_unit_area_internal_room_surface()
            / self.ventilation_factor()
        ):
            c = "ventilation-controlled"
        return c

    def fictitious_ratio(self):
        r = (
            self.ventilation_factor() / self.reference_surface_area_of_unit_length
        ) ** 2 / (self.sqrt_thermal_inertia() / self.reference_breadth_of_beam) ** 2
        return r

    def fictitious_time(self):
        t_star = self.fictitious_ratio() * self.duration()  # hours
        return t_star

        # find x for the decay period calculations

    def x(self):
        self.t_star_minutes = self.fictitious_time() * 60  # minutes
        if self.duration() > self.ventilation_controlled_fire_duration:
            x = 1.0
        elif self.duration() == self.ventilation_controlled_fire_duration:
            x = (
                self.ventilation_controlled_fire_duration
                * self.fictitious_ratio()
                / self.fictitious_time()
            )
        return x

    def time_steps_coefficient(self):
        return 3600 / self.time_step_seconds

    def rounded_fictitous_duration(self):  # round the fictitious duration
        return (
            np.ceil(self.fictitious_time() * self.time_steps_coefficient())
            / self.time_steps_coefficient()
        )

    def max_fire_temp(self):
        return 20 + 1325 * (
            1
            - 0.324 * np.exp(-0.2 * self.rounded_fictitous_duration())
            - 0.204 * np.exp(-1.7 * self.rounded_fictitous_duration())
            - 0.472 * np.exp(-19 * self.rounded_fictitous_duration())
        )

    def total_fictitious_duration(self):
        # find the total fictitious duration
        if self.rounded_fictitous_duration() <= 0.5:
            self.t_star_total = (
                self.max_fire_temp() - 20
            ) / 625 + self.rounded_fictitous_duration() * self.x
        elif 0.5 < self.rounded_fictitous_duration() <= 2.0:
            self.t_star_total = (self.max_fire_temp() - 20) / (
                250 * (3 - self.rounded_fictitous_duration())
            ) + self.rounded_fictitous_duration() * self.x()
        elif self.rounded_fictitous_duration() > 2.0:
            self.t_star_total = (
                self.max_fire_temp() - 20
            ) / 250 + self.rounded_fictitous_duration() * self.x
        return self.t_star_total

        # round the total fictitious duration

    def rounded_total_fictitous_duration(self):  # round the fictitious duration
        return (
            np.ceil(self.total_fictitious_duration() * self.time_steps_coefficient())
            / self.time_steps_coefficient()
        )
        # ceil; see standard library numpy

        # derive the time array from t = 0 to t = total fictitious duration

    def time_array(self):
        t = np.linspace(
            0,
            self.rounded_total_fictitous_duration(),
            int(
                self.time_steps_coefficient() * self.rounded_total_fictitous_duration()
            ),
        )
        return t

    def fire_temperature(self):
        fire_temperatures = []
        for t in self.time_array():
            if t <= self.rounded_fictitous_duration():
                T = 20 + 1325 * (
                    1
                    - 0.324 * np.exp(-0.2 * t)
                    - 0.204 * np.exp(-1.7 * t)
                    - 0.472 * np.exp(-19 * t)
                )
            else:
                if self.rounded_fictitous_duration() <= 0.5:
                    T = self.max_fire_temp() - 625 * (
                        t - self.rounded_fictitous_duration() * self.x()
                    )  # applies for max rounded fictitious duration less than or equal to 0.5
                elif 0.5 < self.rounded_fictitous_duration() <= 2.0:
                    T = self.max_fire_temp() - 250 * (
                        3 - self.rounded_fictitous_duration()
                    ) * (
                        t - self.rounded_fictitous_duration() * self.x()
                    )  # applies for max rounded fictitious duration greater than 0.5 and less than or equal to 2.0
                else:
                    T = self.max_fire_temp() - 250 * (
                        t - self.rounded_fictitous_duration() * self.x()
                    )  # applies for max rounded fictitious duration greater than 2.0
            fire_temperatures.append(T)
        return np.array(
            fire_temperatures
        )  # consider condition, doesn't drop beneath 20 (room temp)
