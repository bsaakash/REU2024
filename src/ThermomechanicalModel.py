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
        self, occupancy, k, p, c_p, B, H, l1, l2, H_r, e_f, F_ref=0.04, b_ref=1160
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

        # b, the square root of thermal inertia
        b = np.sqrt(k * p * c_p)  # sqrt(thermal inertia) ((W*s^0.5)/((m^2)*K))
        self.thermal_inertia = b

        # Geometric properties of the room
        A_f = l1 * l2
        A_v = B * H  # m^2
        H_v = (B * (H**2)) / A_v  # m
        A_t = 2 * (l1 * l2 + l1 * H_r + l2 * H_r)  # m^2 for all floors
        F_v = A_v * np.sqrt(H_v) / A_t  # m^0.5
        e_t = e_f * A_f / A_t  # MJ/m^2

        # solve for the duration of burning period, governed by ventilation-controlled or fuel-controlled
        self.duration = max([(0.2e-3) * e_t / F_v, t_lim_h])  # hours
        if self.duration == t_lim_h:
            self.control = "fuel-controlled"
        elif self.duration == (0.2e-3) * e_t / F_v:
            self.control = "ventilation-controlled"
        r = (F_v / F_ref) ** 2 / (b / b_ref) ** 2
        self.t_star = r * self.duration  # hours

        # find x for the decay period calculations
        self.t_star_min = self.t_star * 60  # minutes
        if self.duration > t_lim_h:
            x = 1.0
        elif self.duration == t_lim_h:
            x = t_lim_h * r / self.t_star
        self.x = x

        # round the fictitious duration
        if self.t_star * 120 == int(self.t_star * 120):
            self.t_star = self.t_star
        elif self.t_star * 120 >= int(self.t_star * 120):
            self.t_star = self.t_star + 1 / 120
        elif self.t_star * 120 <= int(self.t_star * 120):
            self.t_star = self.t_star + 1 / 120

    def max_fire_temp(self):
        self.maxtemp = 20 + 1325 * (
            1
            - 0.324 * np.exp(-0.2 * self.t_star)
            - 0.204 * np.exp(-1.7 * self.t_star)
            - 0.472 * np.exp(-19 * self.t_star)
        )
        return self.maxtemp

    def time_array(self):
        # find the total fictitious duration
        if self.t_star <= 0.5:
            self.t_star_total = (self.maxtemp - 20) / 625 + self.t_star * self.x
        elif 0.5 < self.t_star <= 2.0:
            self.t_star_total = (self.maxtemp - 20) / (
                250 * (3 - self.t_star)
            ) + self.t_star * self.x
        elif self.t_star > 2.0:
            self.t_star_total = (self.maxtemp - 20) / 250 + self.t_star * self.x

        # round the total fictitious duration
        if self.t_star_total * 120 == int(self.t_star_total * 120):
            self.t_star_total = self.t_star_total
        elif self.t_star_total * 120 >= int(self.t_star_total * 120):
            self.t_star_total = self.t_star_total + 1 / 120
        elif self.t_star_total * 120 <= int(self.t_star_total * 120):
            self.t_star_total = (
                self.t_star_total + 1 / 120
            )  # ceil; see standard library numpy

        # derive the time array from t = 0 to t = total fictitious duration
        self.t = np.linspace(0, self.t_star_total, int(120 * self.t_star_total))
        return self.t

    def firetemp(self):
        fire_temperatures = []
        for t in self.t:
            if t <= self.t_star:
                T = 20 + 1325 * (
                    1
                    - 0.324 * np.exp(-0.2 * t)
                    - 0.204 * np.exp(-1.7 * t)
                    - 0.472 * np.exp(-19 * t)
                )
            else:
                if self.t_star <= 0.5:
                    T = self.maxtemp - 625 * (
                        t - self.t_star * self.x
                    )  # applies for t_star_max less than or equal to 0.5
                elif 0.5 < self.t_star <= 2.0:
                    T = self.maxtemp - 250 * (3 - self.t_star) * (
                        t - self.t_star * self.x
                    )  # applies for t_star_max greater than 0.5 and less than or equal to 2.0
                else:
                    T = self.maxtemp - 250 * (
                        t - self.t_star * self.x
                    )  # applies for t_star_max greater than 2.0
            fire_temperatures.append(T)
        return np.array(
            fire_temperatures
        )  # consider condition, doesn't drop beneath 20 (room temp)


# insert decay equation here, from page 65
# consider the temperature that is passed into the parametic curve is the fictitious time in hours, self.t_star
# this need be rounded up to the nearest 5s or 30s, then use


# STEEL TEMP MODULE
class SteelTemperature:
    def __init__(
        self, protection, h, b, T, t, F, V, F_b, V_b, p_s, c_s, h_c, sigma, eps
    ):
        if protection == "box-type":
            j = 1
        elif protection == "spray-on":
            H_p = 2 * (b + h)
        elif protection == "none":
            k = 1


# consider the temperature examples on page


# DEMAND MODULE
class Demand:
    def __init__(self, P):
        r = P

    def column(self):
        self
        return

    def beam(self):
        return


# CAPACITY MODULE
class Capacity:
    def __init__(self, P):
        r = P

    def column(self):
        self
        return

    def beam(self):
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
