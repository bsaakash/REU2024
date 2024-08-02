from typing import Protocol
from material_properties import MechanicalProperties, SteelMechanicalProperties


class Component(MechanicalProperties, Protocol):
    def capacity(self, component_temperature):
        raise NotImplementedError

    def demand(self, component_temperature):
        raise NotImplementedError

    def failure(self, demand, capacity):
        return capacity <= demand

    def get_failure_temperature(
        self, component_temperature_history, save_history=False
    ):
        self.failure_temperature = None
        demand_history = []
        capacity_history = []
        for temp in component_temperature_history:
            demand = self.demand(temp)
            capacity = self.capacity(temp)
            if save_history:
                demand_history.append(demand)
                capacity_history.append(capacity)
            failure = self.failure(demand=demand, capacity=capacity)
            if failure:
                self.failure_temperature = temp
        return self.failure_temperature, demand_history, capacity_history


class SteelColumn(SteelMechanicalProperties, Component):
    def __init__(self) -> None:
        super().__init__()

    def capacity(self, component_temperature):
        return

    def demand(self, component_temperature):
        return


class SteelBeam(SteelMechanicalProperties, Component):
    def __init__(self) -> None:
        super().__init__()

    def capacity(self, component_temperature):
        return

    def demand(self, component_temperature):
        return