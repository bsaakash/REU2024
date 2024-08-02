import pandas as pd

all_section_database = pd.read_csv("AllSectionDatabase.csv")

# geometric inputs for calculating the section factors:
# area of the cross-section: A
# depth of the beam: d
# thickness of the web: t_w
# width of the flange: b_f
# thickness of the flange: t_f
# board protection thickness: t


class SectionProperties:
    def __init__(self, section_size, A, d, bf, tw, tf):
        self.section_size = section_size
        self.A = A
        self.d = d
        self.bf = bf
        self.tw = tw
        self.tf = tf
        self.F = (2 * d + 4 * bf - 2 * tw) * 0.254
        self.V = A * 0.254**2
        self.Fb = 2 * (bf + d) * 0.254
        self.Vb = bf * d * 0.254**2
        self.contour_protection_section_factor = self.F / self.V
        self.board_protection_section_factor = self.Fb / self.Vb
        self.ksh = (
            0.9
            * self.board_protection_section_factor
            / self.contour_protection_section_factor
        )
def get_section_properties(section_size):
    info = all_section_database[all_section_database["section size"] == section_size]
    if info.empty:
        return "No information found for the given section size"
    else:
        section_properties = SectionProperties(
            section_size=section_size,
            A=info["A"].values[0],
            d=info["d"].values[0],
            bf=info["bf"].values[0],
            tw=info["tw"].values[0],
            tf=info["tf"].values[0],
        )
        return section_properties
