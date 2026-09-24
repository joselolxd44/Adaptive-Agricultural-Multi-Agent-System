
import ast
import gc
import random
import csv

import math
import sys
import math
from collections import deque
from copy import deepcopy
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Tuple, List

import pandas as pd

# Add Final/ to Python path
sys.path.append(
    str(Path(__file__).resolve().parent.parent)
)

import Procedural_Seed_Evolution_System as seed_system
import DataMapLoad as map_loader
import enum
import Visualizer_3 as visual
import base_agent
import markov
CALORIES_PER_PERSON = 1000

#max distance of a colony from its central point, at that point the haman community will not be able to keep expanding the colony
FINAL_MAX_DISTANCE=4
INITIAL_MAX_DISTANCE=2
BETA= 0.6
ALPHA=0.6
GAMMA=0.6
@dataclass
class cell:
    height: float
    





def join_communities(parent1: base_agent.Community, parent2: base_agent.Community):
    new_population = parent1.population + parent2.population
    new_calories = parent1.calories + parent2.calories
    new_seeds = parent1.seeds + parent2.seeds
    new_food = parent1.food + parent2.food
    new_Qtable = {**parent1.Qtable, **parent2.Qtable}
    
    new_community = base_agent.Community(
        position=parent1.position,
        population=new_population,
        calories=new_calories,
        seeds=new_seeds,
        Qtable=new_Qtable,
        food=new_food
    )
    
    new_community.memory = {**parent1.memory, **parent2.memory}
    
    return new_community

@dataclass
class Colony:
    id: str

    haman: base_agent.Community
    hurin: base_agent.Community

    central_point: Tuple[int, int]

    distance: float

    territory: dict

    radius: int

    # State space shared by Hanan and Hurin
    states: dict = field(default_factory=dict)

    # Q-table shared by Hanan and Hurin
    qtable: dict = field(default_factory=dict)

    # Distance from central point for each state
    distances: dict = field(default_factory=dict)

    def get_distance_haman_hurin(self):

        return math.sqrt(
                ( self.haman.position[0]
                - self.hurin.position[0]) ** 2
            +
                ( self.haman.position[1]
                - self.hurin.position[1] ) ** 2
        )
    
    def subcomunity_analysis(self,transitions):
        interest_in_expansion=False
        qtable={}
        colony_sites=probe_colony_sites(self.hurin,transitions,states)
        if colony_sites:
            son=base_agent.init_Community_from_parent(self)
    def hurin_analysis(self,states,transitions):
        #hurin can only analyse the territory once he's at the frontier in order to create the expansion with 
        if(get_distance(self.hurin.position,self.central_point)==INITIAL_MAX_DISTANCE):
            colony_sites=probe_colony_sites(self.hurin,transitions,states)
            if colony_sites:
                #Haman has a found good colony sites outside of the actual colony, it will create a subcomunity to  explore, however and bases in the possible actions it will be forced to explore outside of the colony
                base_agent.init_Community_from_parent(self.haman)
            
        
                
        

def get_distance(a: tuple, b: tuple):

        return math.sqrt(
                ( a[0]
                - b[0]) ** 2
                +
                ( a[1]
                - b[1]) ** 2
        )


def divide_community(com: base_agent.Community):

    haman = base_agent.Community(
        id=com.id + "a",
        role=base_agent.Role.HAMAN,
        position=com.position,
        population=com.population // 2,
        calories=0,
        food=[],
        seeds=[],
        Qtable=com.Qtable,
        cant_children=0,
        memory=com.memory
    )

    base_agent.give_food_to_community(
        haman,
        com,
        len(com.food) // 2
    )

    base_agent.give_seed_to_community(
        haman,
        com,
        len(com.seeds) // 2
    )

    haman.calories = base_agent.get_total_food_value(
        haman.food
    )

    hurin = base_agent.Community(
        id=com.id + "b",
        role=base_agent.Role.HURIN,
        position=com.position,
        population=com.population // 2,
        food=[],
        seeds=[],
        calories=0,
        Qtable=com.Qtable,
        cant_children=0,
        memory=com.memory
    )

    base_agent.give_food_to_community(
        hurin,
        com,
        len(com.food)
    )

    base_agent.give_seed_to_community(
        hurin,
        com,
        len(com.seeds)
    )

    hurin.calories = base_agent.get_total_food_value(
        hurin.food
    )

    return haman, hurin

def probe_colony_sites(
    com: base_agent.Community,
    transitions,
    states,
    max_distance=4,
    min_observations=5,
    min_mean_reward=0.3,
    max_std_reward=0.15
):
    """
    Looks and saves all the position who have a estable rewards and possibility for a colony, being limited by the INITIAL_MAX_DISTANCE
    """

    start = com.position

    distances = {
        start: 0
    }

    queue = deque([
        start
    ])

    while queue:
        haman_territory=False
        current = queue.popleft()
        #current=(x,y)
        current_distance = distances[current]

        # Ya no exploramos más allá del límite
        if current_distance >= max_distance+1:
            continue
        if current_distance==max_distance:
            haman_territory=True
        #if current in colon

        if "is_colony" in states[current]:
            if states[current]["is_colony"]:
                continue
        
        
        # transitions[state][action] = [
        #     {
        #         "next_state": ...,
        #         "prob": ...,
        #         "reward": ...
        #     }
        # ]

        for action, possibilities in transitions[current].items():

            if action == (0, 0):
                continue

            for possibility in possibilities:

                next_state = possibility["next_state"]

                if next_state not in distances:
                    
                    distances[next_state] = current_distance + 1

                    queue.append(next_state)

    colony_sites = set()

    for position, distance in distances.items():

        if position == start:
            continue

        cell_memory = com.memory["cells"].get(position)

        if cell_memory is None:
            continue

        reward_history = cell_memory.get(
            "reward_history",
            []
        )

        if len(reward_history) < min_observations:
            continue


        mean_reward = (
            sum(reward_history)
            / len(reward_history)
        )

        #standar deviation
        variance = sum(
            (reward - mean_reward) ** 2
            for reward in reward_history
        ) / len(reward_history)

        std_reward = math.sqrt(variance)

        good_reward = (
            mean_reward >= min_mean_reward
        )

        stable_reward = (
            std_reward <= max_std_reward
        )

        if good_reward and stable_reward:

            colony_sites.add(position)

    return colony_sites



def build_colony_territory(transitions, scanned_sites):
    """
    Creates territory of the colony
    territory:
        space where haman and hurin are free to move

    frontier_markers:
        espace where only haman is free to move and can decide if it's good enough to be added to territory, as long as the distance is not superior to FINAL_MAX_DISTANCE
    """

    territory = {}

    
    for position in scanned_sites:

        if position in transitions:
            territory[position] = deepcopy(
                transitions[position]
            )

    frontier = set()

    for position in territory:

        for action, possibilities in transitions[position].items():

            # No necesitamos "stay"
            if action == (0, 0):
                continue

            for possibility in possibilities:

                next_state = possibility["next_state"]

                if (
                    next_state in transitions
                    and next_state not in territory
                ):
                    frontier.add(next_state)

    
    frontier_markers = {
        position: "HANAN_ONLY"
        for position in frontier
    }

    return territory, frontier_markers


from collections import deque
import copy


def get_reachable_positions(transitions, central_point, max_distance):
    """
    Returns all states reachable from central_point through the
    transition graph in at most max_distance steps. Only the haman comunnity can have a max distance+1
    """

    distances = {
        central_point: 0
    }

    queue = deque([central_point])

    while queue:

        current = queue.popleft()
        current_distance = distances[current]

        if current_distance >= max_distance+1:
            continue

        if current not in transitions:
            continue

        for action, possibilities in transitions[current].items():

            # Do not expand through the stay action
            if action == (0, 0):
                continue

            for possibility in possibilities:

                next_state = possibility.get("next_state")

                if next_state is None:
                    continue

                if next_state not in distances:

                    distances[next_state] = (current_distance + 1)
                    queue.append(next_state)

    return distances

def build_colony_transitions(
    states,
    transitions,
    central_point,
    max_distance=FINAL_MAX_DISTANCE
    
):
    """
    Creates the state space available to the colony.

    The structure of each state remains the same as in the
    original states dictionary.
    """
    #dd
    distances = get_reachable_positions(
        transitions,
        central_point,
        max_distance
    )

    colony_transitions = {}

    for position in distances:

        if position in states:
            #position = (x,y)
            colony_transitions[position] = copy.deepcopy(
                transitions[position]
            )
            
            distance=get_distance(position,central_point)
            if(distance==FINAL_MAX_DISTANCE+1):
                colony_transitions[position]["acces"]=base_agent.Role.HAMAN
            else:
                colony_transitions[position]["acces"]=base_agent.Role.COMMUNITY
            

    return colony_transitions, distances


def restrict_colony_actions(colony_states):
    """
    Removes actions that lead outside the colony state space.
    The global transitions remain untouched.
    """

    allowed_states = set(colony_states.keys())

    for position in colony_states:

        actions = colony_states[position]
        actions_to_remove = []

        for action, possibilities in list(actions.items()):

            # Metadata, not an action
            if action == "acces":
                continue

            # Stay action
            if action == (0, 0):
                continue

            valid_possibilities = [
                possibility
                for possibility in possibilities
                if possibility["next_state"] in allowed_states
            ]

            if not valid_possibilities:
                actions_to_remove.append(action)
            else:
                actions[action] = valid_possibilities

        for action in actions_to_remove:
            del actions[action]

    return colony_states




def build_colony_qtable(parent_qtable, colony_states):

    colony_qtable = {}

    for state, state_data in colony_states.items():

        colony_qtable[state] = {}

        for action in state_data:

            # Metadata, not an action
            if action == "acces":
                continue

            if state in parent_qtable and action in parent_qtable[state]:
                colony_qtable[state][action] = parent_qtable[state][action]
            else:
                colony_qtable[state][action] = 0.0

    return colony_qtable


def establish_colony(
    com: base_agent.Community,
    states,
    transitions
):
    """
    Establishes a colony around the community position.

    Hanan and Hurin share:
        - the same state space
        - the same Q-table
        - the same memory
    """

    central_point = com.position

   
    
    colony_states, distances = build_colony_transitions(
        states,
        transitions,
        central_point,
        FINAL_MAX_DISTANCE
    )

    # Remove actions that leave the colony
    colony_states = restrict_colony_actions(
        colony_states
    )

    colony_qtable = build_colony_qtable(
        com.Qtable,
        colony_states
    )

   
    haman, hurin = divide_community(com)

  
    haman.Qtable = colony_qtable
    hurin.Qtable = colony_qtable

    haman.memory = com.memory
    hurin.memory = com.memory

    colony = Colony(
        id=com.id,
        haman=haman,
        hurin=hurin,
        central_point=central_point,
        distance=0,
        territory=colony_states,
        radius=INITIAL_MAX_DISTANCE
    )

    colony.states = colony_states
    colony.qtable = colony_qtable
    colony.distances = distances
    
    
    mark_colony_states(
        states,
        transitions,
        colony
    )

    return colony

def mark_colony_states(states,transitions, colony):
    """
    Marks all states belonging to a colony.

    These states cannot be used for independent agricultural
    cultivation outside the colony.
    """

    for position in colony.states:

        if position not in states:
            continue

        states[position]["is_colony"] = True
        states[position]["colony_id"] = colony.id
       


def unmark_colony_states(states, transitions,colony):
    """
    Removes the colony marker from all states belonging to the colony.
    """

    for position in colony.states:

        if position not in states:
            continue

        states[position]["is_colony"] = False
        states[position]["colony_id"] = ""
        


def colony_member_died(colony, dead_community):
    """
    If either Hanan or Hurin dies, the surviving half becomes
    an independent Community again.
    """

    if dead_community is colony.haman:
        survivor = colony.hurin

    elif dead_community is colony.hurin:
        survivor = colony.haman

    else:
        return None

    survivor.role = base_agent.Role.COMMUNITY

    return survivor
def is_best_qvalue_in_area(com, colony):

    current_values = [
        value
        for action, value in com.Qtable.get(
            com.position,
            {}
        ).items()
        if action != (0, 0)
    ]

    if not current_values:
        return False

    return max(current_values) >= colony.best_qvalue

def get_visible_cells(grid, position, radius=4):
    """
    Returns the cells visible from a given position.

    Visibility is blocked when a higher cell is encountered
    along the line of sight.
    """

    x0, y0 = position

    if position not in grid:
        return set()

    origin_height = grid[position]["height"]

    visible_cells = {position}

    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):

            if dx == 0 and dy == 0:
                continue

            # Ignore cells outside the square radius
            distance = max(
                abs(dx),
                abs(dy)
            )

            if distance > radius:
                continue

            # Move from the community toward the target cell
            for step in range(1, distance + 1):

                x = round(
                    x0 + dx * step / distance
                )

                y = round(
                    y0 + dy * step / distance
                )

                key = (x, y)

                if key not in grid:
                    break

                cell_height = grid[key]["height"]

                visible_cells.add(key)

                # Higher terrain blocks what is behind it
                if cell_height > origin_height:
                    break

    return visible_cells

def get_visible_colonies(
    community,
    civilization,
    grid,
    position_index,
    radius=4
):
    visible_cells = get_visible_cells(
        grid,
        community.position,
        radius
    )

    visible_communities = []

    for position in visible_cells:
        for other in position_index.get(position, ()):
            if other is not community:
                visible_communities.append(other)

    return visible_communities

def init_interaction_zones():
    """
    Stores the accumulated importance of locations
    where communities exchange information.
    """
    return {}

def calculate_information_gain(com1, com2):
    """
    Estimates how much new agricultural knowledge
    com1 can obtain from com2.
    """

    memory1 = com1.memory["varieties"]
    memory2 = com2.memory["varieties"]

    gain = 0.0

    for variety_id, knowledge in memory2.items():

        if variety_id not in memory1:
            gain += 1.0
            continue

        own = memory1[variety_id]

        if (
            knowledge.get("best_efficiency", 0.0)
            > own.get("best_efficiency", 0.0)
        ):
            gain += 0.5

        if (
            knowledge.get("best_calories_amount", 0.0)
            > own.get("best_calories_amount", 0.0)
        ):
            gain += 0.5

    return gain

def exchange_qtables(com1, com2):

    if len(com1.Qtable) > len(com2.Qtable):
        small = com2.Qtable
        large = com1.Qtable
        first = com2
        second = com1
    else:
        small = com1.Qtable
        large = com2.Qtable
        first = com1
        second = com2

    for state, actions1 in small.items():

        actions2 = large.get(state)

        if actions2 is None:
            continue

        for action, q1 in actions1.items():

            if action not in actions2:
                continue

            q2 = actions2[action]

            average = (q1 + q2) * 0.5

            first.Qtable[state][action] = average
            second.Qtable[state][action] = average
            
def exchange_variety_memory(com1, com2):
    
    memory1 = com1.memory["varieties"]
    memory2 = com2.memory["varieties"]

    variety_ids = set(memory1) | set(memory2)

    for variety_id in variety_ids:

        if variety_id not in memory1:
            memory1[variety_id] = copy.deepcopy(
                memory2[variety_id]
            )
            continue

        if variety_id not in memory2:
            memory2[variety_id] = copy.deepcopy(
                memory1[variety_id]
            )
            continue

        v1 = memory1[variety_id]
        v2 = memory2[variety_id]

        best_efficiency = max(
            v1.get("best_efficiency", 0.0),
            v2.get("best_efficiency", 0.0)
        )

        best_calories = max(
            v1.get("best_calories_amount", 0.0),
            v2.get("best_calories_amount", 0.0)
        )

        uncertainty = min(
            v1.get("incertitude", 1.0),
            v2.get("incertitude", 1.0)
        )

        v1["best_efficiency"] = best_efficiency
        v2["best_efficiency"] = best_efficiency

        v1["best_calories_amount"] = best_calories
        v2["best_calories_amount"] = best_calories

        v1["incertitude"] = uncertainty
        v2["incertitude"] = uncertainty
        

    
def exchange_information(com1, com2):
    """
    Exchanges knowledge between two communities
    and returns the information gain.
    """

    gain_1 = calculate_information_gain(
        com1,
        com2
    )

    gain_2 = calculate_information_gain(
        com2,
        com1
    )

    exchange_qtables(
        com1,
        com2
    )

    exchange_variety_memory(
        com1,
        com2
    )

    return gain_1 + gain_2
def process_information_exchange(
    community,
    civilization,
    grid,
    interaction_zones,
    processed_contacts,
    position_index,
    radius=4
):
    visible_communities = get_visible_colonies(
        community,
        civilization,
        grid,
        position_index,
        radius
    )

    if not visible_communities:
        return 0.0

    other = random.choice(visible_communities)

    pair = tuple(sorted([
        community.id,
        other.id
    ]))

    if pair in processed_contacts:
        return 0.0

    processed_contacts.add(pair)

    reward = exchange_information(
        community,
        other
    )

    register_interaction_zone(
        interaction_zones,
        community.position,
        reward=1.0,
        radius=0
    )

    return reward

def register_interaction_zone(
    interaction_zones,
    position,
    reward=1.0,
    radius=0
):
    """
    Registers a communication event at a specific position.

    radius=0 means only the exact communication cell is marked.
    """

    x0, y0 = position

    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):

            key = (x0 + dx, y0 + dy)

            interaction_zones[key] = (
                interaction_zones.get(key, 0.0)
                + max(reward, 1.0)
            )
            
def exchange_qtables(com1: base_agent.Community, com2: base_agent.Community):
    """
    Exchanges Q-values between two communities.

    Only states already present in both Q-tables are exchanged.
    This avoids copying or processing the entire Q-table unnecessarily.
    """

    common_states = (
        set(com1.Qtable.keys())
        & set(com2.Qtable.keys())
    )

    for state in common_states:

        common_actions = (
            set(com1.Qtable[state].keys())
            & set(com2.Qtable[state].keys())
        )

        for action in common_actions:

            q1 = com1.Qtable[state][action]
            q2 = com2.Qtable[state][action]

            average = (q1 + q2) / 2.0

            com1.Qtable[state][action] = average
            com2.Qtable[state][action] = average


def get_seeds_by_amount(com: base_agent.Community, amount, varietyID):
    selected_seeds = []
    i = 0

    for seed in com.seeds[:]:
        if i >= amount:
            break

        if seed.parentVariety.varietyID == varietyID:
            selected_seeds.append(seed)
            com.seeds.remove(seed)
            i += 1

    return selected_seeds  

def can_reproduce(com: base_agent.Community, civ: base_agent.Civilization):
    if com.calories>100000 and len(com.food)>200 and com.population>1000 and civ.cantCommunities<6: return True
    return False
    
def community_reproduction(com: base_agent.Community, civ: base_agent.Civilization):
    
    if(can_reproduce(com, civ)):
        son=base_agent.init_Community_from_parent(com)
        civ.add_community(son)
        print("base_agent.Community has been split")
        return True



def try_settle_colony(colony, states, transitions, civilization):

    colony_states = colony.states

    haman = colony.haman
    hurin = colony.hurin

    if not is_best_qvalue_in_area(
        haman,
        colony_states
    ):
        return False

    if not is_best_qvalue_in_area(
        hurin,
        colony_states
    ):
        return False

    return True
def build_community_position_index(civilization):
    index = {}

    for com in civilization.communities:
        index.setdefault(com.position, []).append(com)

    return index


def main():

    states = map_loader.generate_grid()
    visualizer = visual.SimulationVisualizer(states)
    
    civilization = base_agent.Civilization()
    heightMetrics = seed_system.generateHeightMetrics()
    transitions=markov.init_transitions(states)
    with open(
        "agent_learning_seed_data.csv",
        "w",
        newline=""
    ) as csvFile:

        writer = csv.writer(csvFile)

        flag = True

        for j in range(100):

            interaction_zones = init_interaction_zones()
            visits = {}
            n = 0

            seed_system.writeSeedCSVHeader(writer)

            civilization.add_community(
                base_agent.init_Community_prototype(states)
            )
            

            # Active colonies
            colonies = []

            print("Civilization revived")

            for i in range(1000):

                current_actions = {}
                rewards = []
                processed_contacts = set()

                # -------------------------------------------------
                # NORMAL COMMUNITIES
                # -------------------------------------------------

                for com in civilization.communities[:]:
                    position_index = build_community_position_index(civilization)
                    
                    interaction_reward = process_information_exchange(
                        com,
                        civilization,
                        states,
                        interaction_zones,
                        processed_contacts,
                        position_index
                    )

                    reward = interaction_reward

                    action,reward = markov.markov_process(
                        com,
                        states,
                        heightMetrics,
                        writer,
                        reward
                        
                    )
                    

                    visits[com.position] = (
                        visits.get(com.position, 0) + 1
                    )

                    current_actions[com.id] = {
                        "action": action,
                        "reward": reward
                    }

                    rewards.append(reward)

                    # -------------------------------------------------
                    # COMMUNITY DEATH
                    # -------------------------------------------------

                    if base_agent.is_community_dead(com):

                        civilization.community_elimination(
                            com,
                            i,
                            map_loader,
                            states,
                            visits
                        )

                        break
                        

                    # -------------------------------------------------
                    # COMMUNITY MAINTENANCE
                    # -------------------------------------------------

                    base_agent.community_maintenance(com)
                    base_agent.community_increment(com)

                    # -------------------------------------------------
                    # CHECK IF COMMUNITY CAN ESTABLISH A COLONY
                    # -------------------------------------------------

                    colony_sites = probe_colony_sites(
                        com,
                        transitions,
                        states,
                        max_distance=INITIAL_MAX_DISTANCE
                    )

                    if colony_sites:

                        colony = establish_colony(
                            com,
                            states,
                            transitions
                        )

                        colonies.append(colony)

                        civilization.communities.remove(com)

                        print(
                            f"COLONY ESTABLISHED: "
                            f"{com.id} "
                            f"at {colony.central_point}"
                        )

                        continue

                    community_reproduction(
                        com,
                        civilization
                    )

                    base_agent.food_storage(com)
                    

                    base_agent.iteration_printing(
                        com,
                        i,
                        action,
                        reward
                    )

                    n = i


                # -------------------------------------------------
                # COLONIES
                # -------------------------------------------------

                for  colony in colonies[:]:
                    haman = colony.haman
                    hurin = colony.hurin

                    # ---------------------------------------------
                    # HANAN
                    # ---------------------------------------------
                    position_index = build_community_position_index(civilization)
                    
                    interaction_reward = process_information_exchange(
                        haman,
                        civilization,
                        states,
                        interaction_zones,
                        processed_contacts,
                        position_index
                    )

                    reward = interaction_reward
                    qchanged_haman=False
                    
                    action_haman, reward, qchanged_haman = markov.markov_colony_process(
                        haman,
                        colony.states,
                        states,
                        heightMetrics,
                        writer,
                        reward
                    )
                    
                    if(qchanged_haman):
                        best_haman=is_best_qvalue_in_area(haman,colony.states)

                    visits[haman.position] = (
                        visits.get(haman.position, 0) + 1
                    )

                    current_actions[haman.id] = {
                        "action": action_haman,
                        "reward": reward
                    }

                    rewards.append(reward)

                    # ---------------------------------------------
                    # HURIN
                    # ---------------------------------------------

                    interaction_reward = process_information_exchange(
                        hurin,
                        civilization,
                        states,
                        interaction_zones,
                        processed_contacts,
                        position_index
                    )

                    
                    qchanged_hurin=False
                    action_hurin, reward, qchanged_hurin = markov.markov_colony_process(
                        hurin,
                        colony.states,
                        states,
                        heightMetrics,
                        writer,
                        interaction_reward
                    )
                    
                    

                    
                    visits[hurin.position] = (
                        visits.get(hurin.position, 0) + 1
                    )
                    

                    current_actions[hurin.id] = {
                        "action": action_hurin,
                        "reward": reward
                    }
                    
                    colony.hurin_analysis(states,transitions)

                    rewards.append(reward)
                    
                    if(qchanged_hurin and qchanged_haman):
                        try_settle_colony(colony,states, transitions,civilization,colonies)
                        

                    haman_dead = base_agent.is_community_dead(haman)

                    hurin_dead = base_agent.is_community_dead(hurin)

                    if haman_dead or hurin_dead:

                        dead = haman if haman_dead else hurin

                        survivor = colony_member_died(colony,dead)

                        # Remove colony territory marker
                        unmark_colony_states(states,transitions,colony)

                        # Remove colony
                        colonies.remove(colony)

                        # Survivor becomes normal community
                        if survivor is not None:civilization.add_community(survivor)

                        print(
                            f"COLONY DISSOLVED: "
                            f"{colony.central_point}"
                        )

                        continue


                    base_agent.community_maintenance(
                        haman
                    )

                    base_agent.community_maintenance(
                        hurin
                    )

                    base_agent.community_increment(
                        haman
                    )

                    base_agent.community_increment(
                        hurin
                    )

                    base_agent.food_storage(
                        haman
                    )

                    base_agent.food_storage(
                        hurin
                    )

                    base_agent.iteration_printing(
                        haman,
                        i,
                        action_haman,
                        current_actions[haman.id]["reward"]
                    )

                    base_agent.iteration_printing(
                        hurin,
                        i,
                        action_hurin,
                        current_actions[hurin.id]["reward"]
                    )

                    n = i

                # -------------------------------------------------
                # VISUALIZATION
                # -------------------------------------------------
                if i%10==0:
                    visualizer.draw(
                        civilization,
                        i,
                        visits,
                        rewards,
                        current_actions,
                        colonies
                    )
                if civilization.cantCommunities==0:
                    break

            if n > 995:

                map_loader.visualizar_mapa_concurrencia(
                    states,
                    visits
                )

                

        base_agent.print_varieties_memory(com)
        base_agent.print_Qvalues(com)

        map_loader.visualizar_mapa_concurrencia(
            states,
            visits
        )    
    
    
    

if __name__ == "__main__":
    main()
    
    


