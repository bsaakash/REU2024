# from pathlib import Path
# import numpy as np
# import matplotlib.pyplot as plt
import pandas as pd
# import thermal_analyses

# column_database_path = Path("/Users/emilynakamura/Downloads/NHERI/Technical/AutoSDAPlatform/ColumnDatabase.csv").resolve()

# column_dataframe = pd.read_csv(column_database_path)

class SectionProperties:
    def __init__(self, section_size, weight, A, d, bf, tw, tf, Ix, Iy, F, V, Fb, Vb, contour_protection_section_factor, board_protection_section_factor, ksh):
        self.section_size = section_size
        self.weight = weight
        self.A = A
        self.d = d
        self.bf = bf
        self.tw = tw
        self.tf = tf
        self.Ix = Ix
        self.Iy = Iy
        self.F = F
        self.V = V
        self.Fb = Fb
        self.Vb = Vb
        self.contour_protection_section_factor = contour_protection_section_factor
        self.board_protection_section_factor = board_protection_section_factor
        self.ksh = ksh

def get_section_properties(section_size):
    column_dataframe = pd.read_csv("ColumnDatabase.csv")
    # Filter the dataframe for the given section size
    section_row = column_dataframe[column_dataframe['section size'] == section_size]
    if section_row.empty:
        return f"Section size {section_size} not found in the data."
    else:
        weight = section_row['weight'].values[0]
        A = section_row['A'].values[0]
        d = section_row['d'].values[0]
        bf = section_row['bf'].values[0]
        tw = section_row['tw'].values[0]
        tf = section_row['tf'].values[0]
        Ix = section_row['Ix'].values[0]
        Iy = section_row['Iy'].values[0]
        F = (2 * d + 4 * bf - 2 * tw) * 0.254
        V = A * 0.254**2
        Fb = 2 * (bf + d) * 0.254
        Vb = V
        contour_protection_section_factor = F / V
        board_protection_section_factor = Fb / Vb
        ksh = (
        0.9
        * board_protection_section_factor
        / contour_protection_section_factor
        )
        section_properties = SectionProperties(
        section_size,
        weight,
        A,
        d,
        bf,
        tw,
        tf,
        Ix,
        Iy,
        F,
        V,
        Fb,
        Vb,
        contour_protection_section_factor,
        board_protection_section_factor,
        ksh,
        )
        return section_properties
    
if __name__ == "__main__":
    # get = get_section_properties('W33X221')
    # print(get.A)

    ksh = []
    A = []
    weight = []
    d = []
    bf = []
    board_protection_section_factor = []
    contour_protection_section_factor = []

    # column_database_path = Path("/Users/emilynakamura/Downloads/NHERI/Technical/AutoSDAPlatform/ColumnDatabase.csv").resolve()

    column_dataframe = pd.read_csv("ColumnDatabase.csv")

    for section_size in column_dataframe['section size']:
        section_properties = get_section_properties(section_size)
        ksh.append(section_properties.ksh)
        weight.append(section_properties.weight)
        A.append(section_properties.A)
        d.append(section_properties.d)
        bf.append(section_properties.bf)
        board_protection_section_factor.append(section_properties.board_protection_section_factor)
        contour_protection_section_factor.append(section_properties.contour_protection_section_factor)

    # # protected case
    # # inputs: time (seconds), fire_temperature, contour_protection_section_factor=210
    #     thermal_analysis = thermal_analyses.SimplifiedUnprotected()
    #     steel_temperature = thermal_analysis.get_component_temperature(
    #        time*3600,      # in seconds
    #        fire_temperature,
    #        contour_protection_section_factor=210,
    #        )
    # # print(f"{max(steel_temperature) = }")

    # # unprotected case
    # # inputs: time (seconds), fire_temperature, convective_heat_transfer_coefficient, material_emissivity, fire_emissivity, contour_protection_section_factor=210, board_protection_section_factor=153, SB_coefficient=56.7 * 10 ** (-12),
    #     thermal_analysis = thermal_analyses.SimplifiedUnprotected()
    #     steel_temperature = thermal_analysis.get_component_temperature(
    #         time,      # in seconds
    #         fire_temperature,
    #         convective_heat_transfer_coefficient,
    #         material_emissivity,
    #         fire_emissivity=1.0,
    #         contour_protection_section_factor=210,
    #         board_protection_section_factor=153,
    #         SB_coefficient=56.7e-12,)
    # # print(f"{max(steel_temperature) = }")

    # #    print(f"{section_size}: {section_properties.ksh}")

    # # plt.hist(ksh, bins=50)
    # # plt.show()

    # # print(np.mean(ksh))

    # # plt.scatter(weight, ksh)
    # # plt.show()

    # # plt.scatter(d, ksh)
    # # plt.show()

    # # plt.scatter(bf, ksh)
    # # plt.show()

    # # plt.hist(board_protection_section_factor, bins=50)
    # # plt.show()

    # # plt.hist(contour_protection_section_factor, bins=50)
    # # plt.show()

    # # plt.scatter(board_protection_section_factor, contour_protection_section_factor)
    # # plt.show()

    # # print(np.corrcoef(contour_protection_section_factor, board_protection_section_factor))

    # # plt.scatter(contour_protection_section_factor, ksh)
    # # plt.show()

