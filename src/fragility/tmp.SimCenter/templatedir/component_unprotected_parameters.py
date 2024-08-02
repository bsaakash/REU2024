# geometric inputs for calculating the section factors:
    # area of the cross-section: A
    # depth of the beam: d
    # thickness of the web: t_w
    # width of the flange: b_f
    # thickness of the flange: t_f
    # top of the flange + radius section of web: k
    # half thickness of web + radius section of flange: k_1
    # radius, using the flange: r = k - t_f
    # radius1, using the web: r1 = k_1 - t_w/2
    # board protection thickness: t


class ComponentUnprotectedParameters:
    def __init__(
        self,
        F=2*d + 4*b_f - 2*t_w,      # could also add "+ np.pi*r + np.pi*r_1 - 4*r - 4*r_1" to factor in the radii at the flange-web junction
        V=A,
        F_b=(b_f+d)*2,
        V_b=(b_f+d+t)*t,
        section_type="I-section",
        convective_heat_transfer_coefficient=25,    # note: this depends on the type of fire; ise 25 for standard fire, use 50 for hydrocarbon fire, use 35 for all parametric fires
        stefan_boltzmann_coefficient=56.7 * 10 ** (-12),
        fire_emissivity=1.0,      # 1.0 for fire, specified by the Eurocode (CEN, 2002b)
        material_emissivity=0.7,  # 0.7 for steel, specified by the Eurocode (CEN, 2005b)
    ):

        self.section_type = section_type

        self.section_surface_area_of_unit_length_member = F
        self.section_volume_per_unit_length_member = V
        self.section_surface_area_of_unit_length_board_protection = F_b
        self.section_volume_per_unit_length_board_protection = V_b

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
        self.correction_factor = k_sh

        self.convective_heat_transfer_coeff = convective_heat_transfer_coefficient
        self.stefan_boltzmann_coefficient = stefan_boltzmann_coefficient

        self.fire_emissivity = fire_emissivity
        self.material_emissivity = material_emissivity

        self.resultant_emissivity = self.fire_emissivity * self.material_emissivity
