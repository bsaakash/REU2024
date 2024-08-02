import fire_curves
import material_properties
import thermal_analyses
import mechanical_analyses


# def analysis(
#     fire_curve,
#     thermal_properties,
#     insulation_thermal_properties,
#     mechanical_properties,
# ):
#     pass


if __name__ == "__main__":
    fire_curve = fire_curves.ISO834FireCurve()
    steel_mechanical_properties = (
        material_properties.SteelMechanicalProperties()
    )
    steel_thermal_properties = material_properties.SteelThermalProperties()
    insulation_thermal_properties = (
        material_properties.InsulationThermalProperties()
    )
    thermal_analysis = thermal_analyses.SimplifiedUnprotected()
    mechanical_analysis = mechanical_analyses.SteelColumn()

    component_temperature = thermal_analysis.get_component_temperature(
        steel_thermal_properties
    )

    # time = thermal_analysis.get_time(start=0, end=180)
    # fire_temperature = fire_curve.get_temperature()
    # print(fire_curve.get_time_from_temperature(1000))
    # component_temperature = thermal_analysis.get_temperature(
    #     time=time,
    #     fire_temperature=fire_temperature,
    #     thermal_properties=material_property.thermal_properties,
    # )
