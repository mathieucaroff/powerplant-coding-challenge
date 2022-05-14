from dataclasses import dataclass
import itertools

@dataclass
class Plant:
    name: str
    type: str
    efficiency: float
    pmin: int
    pmax: int
    p: float = 0

@dataclass
class Problem:
    load: int
    gazprice: float
    kerosineprice: float
    windpower: float
    powerplants: list[Plant]

    def merit(self, plant):
        """
        The merit is highest for the cheapest energy. This method is intended to sort plants first by merit-order and by size in case of equal merit.
        """
        cost_efficency = 0
        if plant.type == "gasfired":
            cost_efficency = plant.efficiency / self.gazprice
        elif plant.type == "turbojet":
            cost_efficency = plant.efficiency / self.kerosineprice
        return (
            plant.type == "windturbine",
            cost_efficency,
            plant.pmax,
        )

    def maximum_power(self, plant):
        """
        Yields the maximum power produced by a plant. This function especially
        takes care of the case of the wind-dependant windturbines.
        """
        if plant.type == "windturbine":
            return round(plant.pmax * self.windpower, 1)
        return plant.pmax

    def plant_supports(self, plant, load):
        if load == 0:
            return True
        if plant.type == "windturbine":
            return load == self.maximum_power(plant)
        return plant.pmin <= load <= plant.pmax

    def plant_cost(self, plant, power):
        cost = 0
        if plant.type == "gasfired":
            cost = power * self.gazprice / plant.efficiency
        elif plant.type == "turbojet":
            cost = power * self.kerosineprice / plant.efficiency
        return cost

def result(plant_list):
    return [
        dict(
            name=plant.name,
            p=plant.p,
        )
        for plant in plant_list
    ]

def solve(problem_data):
    fuel = problem_data["fuels"]
    problem = Problem(
        load=problem_data["load"],
        gazprice=fuel["gas(euro/MWh)"],
        kerosineprice=fuel["kerosine(euro/MWh)"],
        windpower=fuel["wind(%)"] / 100,
        powerplants=[Plant(**data) for data in problem_data["powerplants"]]
    )

    # first step: add the power plant which will be used at maximum power
    power = 0
    unused_plant_list = []
    # sort plants by decreasing merit order
    problem.powerplants.sort(key=problem.merit, reverse=True)
    for k, plant in enumerate(problem.powerplants):
        plant.p = problem.maximum_power(plant)
        power += plant.p
        if power > problem.load:
            power -= plant.p
            plant.p = 0
            unused_plant_list.append(plant)

    remaining_load = problem.load - power
    if remaining_load == 0:
        print("CONSTRAINTS SOLVED AT THE FIRST STEP")
        return result(problem.powerplants)

    # second step:
    # fiddle with the remaining power plants hoping to find one which can match
    # the remaing load
    for plant in unused_plant_list:
        if problem.plant_supports(plant, remaining_load):
            plant.p = round(remaining_load, 1)
            print("CONSTRAINTS SOLVED AT THE SECOND STEP")
            return result(problem.powerplants)

    # third step:
    # disregard the previous work and brut-force the problem, taking advantage
    # of the small number of plant

    # we compute the worst cost
    best_cost = sum(
        problem.plant_cost(plant, problem.maximum_power(plant))
        for plant in problem.powerplants
    )
    best_result = result(problem.powerplants)
    solved = False
    for status_list in itertools.product(*[(0, 1)]*len(problem.powerplants)):
        used_plant_list = []
        for status, plant in zip(status_list, problem.powerplants):
            if status == 0:
                plant.p = 0
            else:
                used_plant_list.append(plant)

        pmin = 0
        pmax = 0
        power = 0
        adjustable_plant_list = []
        for plant in used_plant_list:
            if plant.type == "windturbine":
                # windturbine
                plant.p = problem.maximum_power(plant)
                pmin += plant.p
                pmax += plant.p
                power += plant.p
            else:
                # gasfired and turbojet
                pmin += plant.pmin
                pmax += plant.pmax
                plant.p = plant.pmin
                power += plant.p
                adjustable_plant_list.append(plant)

        if pmin > problem.load or pmax < problem.load:
            # disregard this plan, continue to the next one
            continue

        # sort the remaining plants by merit-order
        # go through the plants and adjust the power
        adjustable_plant_list.sort(key=problem.merit, reverse=True)
        for plant in adjustable_plant_list:
            power -= plant.p
            plant.p = plant.pmax
            power += plant.p
            if power >= problem.load:
                power -= plant.p
                plant.p = problem.load - power
                power += plant.p # thus `power` is equal to `problem.load`
                break
        else:
            # this should never happen
            assert False, "internal error"

        # compute the cost of the solution
        cost = sum(
            problem.plant_cost(plant, plant.p)
            for plant in problem.powerplants
        )
        if cost < best_cost:
            best_cost = cost
            best_result = result(problem.powerplants)
            solved = True

    if solved:
        print("CONSTRAINTS SOLVED AT THE THIRD STEP")
    else:
        print("FAILED TO SOLVE THE CONSTRAINTS")
    return best_result
