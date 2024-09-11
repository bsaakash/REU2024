import numpy as np
from params import *
from column_config import *
import fire_curves
import material_properties
import thermal_analyses
from parse_section_factor import get_section_properties

# TODO  implement the real column demand based on the database.
# load = E * (A * dead_load + B * live_load)

# steel material parameters:
room_temperature_modulus = 200000  # MPa
# room_temperature_yield_strength = 220  # MPa
# alpha = 12e-6  # coefficient of thermal expansion (1/°C)
steel_room_temperature_density = 7850  # kg/m^3 STEEL
room_temperature_specific_heat = 460  # J/kg K
convective_heat_transfer_coefficient = 35  # W/m^2 K
material_emissivity = 0.7
# thermal_conductivity = 45.8  # W/mK
# density = steel_room_temperature_density  # kg/m^3
# specific_heat = room_temperature_specific_heat  # J/kg K

section_properties = get_section_properties(section_size)
A = section_properties.A / (12 * 3.281) ** 2
I = section_properties.Ix / (12 * 3.281) ** 4
contour_protection_section_factor = section_properties.contour_protection_section_factor
board_protection_section_factor = section_properties.board_protection_section_factor

# A = 130 / ((12*3.281)**2)  # cross-sectional area in m^2
# I = 1150 / ((12*3.281)**4)  # m^4, using W14X342 column

# L, DCR, e become our

# parametric fire parameters:
occupancy = "office"
concrete_thermal_conductivity = 1.6
concrete_density = 2300
concrete_specific_heat = 980
window_base = 3  # m
window_height = 2  # m
# dims = room_geometry.RoomDimension(room_length1, room_length2, room_height)
# room_length1 = dims.length1()
# room_length2 = dims.length2()
# room_height = dims.height()

# fire temperature:
# time = np.arange(0, 180 * 60, 5)

fire_curve = fire_curves.ParametricFireCurve(
    zeta,
    occupancy,
    concrete_thermal_conductivity,
    concrete_density,
    concrete_specific_heat,
    window_base,
    window_height,
    room_length1,
    room_length2,
    room_height,
    fire_load_fuel_energy_density,
)
fire_temperature = fire_curve.fire_temp()
time = fire_curve.time_array_seconds

# fire_curve = fire_curves.ISO834FireCurve()
# fire_temperature = fire_curve.get_temperature()
# time = fire_curve.time


# print(f"{max(fire_temperature) = }")
# print(f"{max(time) = }")


# steel temperature:
# protected case
# inputs: time (seconds), fire_temperature, contour_protection_section_factor=210
# thermal_analysis = thermal_analyses.SimplifiedUnprotected()
# steel_temperature = thermal_analysis.get_component_temperature(
#        time*3600,      # in seconds
#        fire_temperature,
#        contour_protection_section_factor=210,
#        )
# print(f"{max(steel_temperature) = }")

# unprotected case
# inputs: time (seconds), fire_temperature, convective_heat_transfer_coefficient, material_emissivity, fire_emissivity, contour_protection_section_factor=210, board_protection_section_factor=153, SB_coefficient=56.7 * 10 ** (-12),
thermal_analysis = thermal_analyses.SimplifiedUnprotected()
steel_temperature = thermal_analysis.get_component_temperature(
    time,  # in seconds
    fire_temperature,
    convective_heat_transfer_coefficient,
    material_emissivity,
    fire_emissivity=1.0,
    contour_protection_section_factor=contour_protection_section_factor,
    board_protection_section_factor=board_protection_section_factor,
    SB_coefficient=56.7e-12,
)
# print(f"{max(steel_temperature) = }")


# reduction factor for elastic modulus:
mech_mat_prop = material_properties.SteelMechanicalProperties(
    steel_room_temp_modulus=room_temperature_modulus
)
effective_elastic_modulus = mech_mat_prop.elastic_modulus(
    steel_temperature, epsilon_steel_modulus
)
# print(f"{min(effective_elastic_modulus) = }")


# column analysis:
# initial_temp = steel_temperature[0]  # temperature change (°C)
# time_step = np.diff(time)
# delta_steel_temp = np.diff(steel_temperature)
# delta_F = effective_elastic_modulus[1:] * alpha * delta_steel_temp * A  # MN
# F = sigma * A  # MN
# internal_force = np.zeros(len(steel_temperature))
# internal_force[1:] = np.cumsum(delta_F)
# print(f"{max(internal_force) = }")


# failure evaluation:
capacity = np.pi**2 * effective_elastic_modulus * I / L**2  # MN
demand = (
    DCR * capacity[0]
)  # * L / (np.sqrt(L**2 - (e * L) ** 2))  # + max(internal_force)
if min(capacity) > demand:
    out = 0
else:
    out = 1
# print(out)
with open("results.out", "w") as f:
    f.write(f"{out}")

# print(f"{max(capacity) = }")
# print(f"{min(capacity) = }")
# print(f"{(demand) = }")

# plt.plot(steel_temperature, effective_elastic_modulus)
# plt.show()

# plt.plot(steel_temperature, capacity)
# plt.show()

# DCR_range = np.linspace(0, 1, 101)
# critical_temps_array = np.zeros_like(DCR_range)
# for j, DCR in enumerate(DCR_range):
#     demand = (DCR * capacity[0] * L / (np.sqrt(L**2 - (e * L) ** 2))) + 0*internal_force
#     for i in range(len(demand)):
#         if demand[i] >= capacity[i]:
#             critical_temp = steel_temperature[i]
#             critical_temps_array[j] = critical_temp
#             critical_time = time[i]
#             critical_demand = demand[i]
#             print(f"Temperature at failure: {critical_temp} °C")
#             print(f"Time at failure: {critical_time / 60} minutes")
#             print(f"Critical load: {critical_demand} Meganewtons")
#             break
#         else:
#             critical_temp = "DNE"
#             critical_time = "DNE"
#             critical_demand = "DNE"

# plt.plot(DCR_range, critical_temps_array)
# plt.show()
