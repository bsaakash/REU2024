from typing import Protocol
import pandas as pd


class ComponentGeometry(Protocol):
    def __init__(self) -> None:
        pass

all_section_database = pd.read_csv('AllSectionDatabase.csv')

# geometric inputs for calculating the section factors:
    # area of the cross-section: A
    # depth of the beam: d
    # thickness of the web: t_w
    # width of the flange: b_f
    # thickness of the flange: t_f
    # board protection thickness: t

class SectionProperties(ComponentGeometry):
    def __init__(self, section_size, A, d, bf, tw, tf):
        self.section_size = section_size
        self.A = A
        self.d = d
        self.bf = bf
        self.tw = tw
        self.tf = tf
        self.Ix = Ix
        self.Iy = Iy

def get_section_properties(section_size):
    info = all_section_database[all_section_database['section size'] == section_size]
    if info.empty:
        return "No information found for the given section size"
    else:
        section_properties = SectionProperties(
            section_size = section_size,
            A = info['A'].values[0],
            d = info['d'].values[0],
            bf = info['bf'].values[0],
            tw = info['tw'].values[0],
            tf = info['tf'].values[0],
            Ix = info['Ix'].values[0],
            Iy = info['Iy'].values[0],
        )
        return section_properties
    


# import the csv file for specific (?) building

class ComponentProperties(ComponentGeometry):
    def __init__(self, element_id, l):
        self.element_id = element_id
        self.l = l
        self.axial_DCR = axial_DCR
        self.flexure_DCR = flexure_DCR
        self.story_drift = story_drift
    
def get_component_properties(element_id):
    info = all_section_database[all_section_database['section size'] == section_size]
    if info.empty:
        return "No information found for the given section size"
    else:
        section_properties = SectionProperties(
            section_size = section_size,
            A = info['A'].values[0],
            d = info['d'].values[0],
            bf = info['bf'].values[0],
            tw = info['tw'].values[0],
            tf = info['tf'].values[0]
        )
        return section_properties