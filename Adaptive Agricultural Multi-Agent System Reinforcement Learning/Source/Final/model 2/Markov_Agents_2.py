import ast
import random
import csv
import copy
import math
import sys

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

import Visualizer_2 as visual
CALORIES_PER_PERSON = 1000
BETA= 0.6
ALPHA=0.6
GAMMA=0.6
@dataclass
class cell:
    height: float
    



@dataclass
class Community:
    position: int
    population: int
    calories: float
    seeds: List[seed_system.Seed]
    Qtable:Dict
    food: list[seed_system.Food]
    tension: float = 0.0
    memory: dict = field(default_factory=dict)
    id: str= ""
    caravane: bool = False
    cant_children: int = 0
    
def give_seed_to_community(taker: Community, giver: Community, cant_seeds):
    for i in range(cant_seeds):
        if len(giver.seeds) > 0:
            seed = giver.seeds.pop(0)
            
            taker.seeds.append(seed)
        else:
            break
def give_food_to_community(taker: Community, giver: Community, cant_food):
    for i in range(cant_food):
        if len(giver.food) > 0:
            food = giver.food.pop(0)
            giver.calories -= food.calories * food.amount
            taker.food.append(food)
            taker.calories += food.calories * food.amount
        else:
            break

def init_memory():
    memory={}
    memory["varieties"]={}
    memory["cells"]={}
    return memory

def init_Community_prototype(grid):
    
    seeds=seed_system.generateRandomSeeds(5,3900)
    init_transitions(grid)
    qtable=init_Qtable(grid)
    food=seed_system.generateRandomFood(20)
    com=Community(position=(43,32), population=10, calories=15000, seeds=seeds, Qtable=qtable, food=food)
    com.memory=init_memory()
    com.id="1"
    com.cant_children=0
    return com

def init_Community_from_parent(grid, parent: Community):
    
    son_qtable = copy.deepcopy(parent.Qtable)
    son_memory = copy.deepcopy(parent.memory)
    
    
    son_population = parent.population // 4  
    if son_population < 2: 
        son_population = 2
    
    son = Community(
        position=parent.position, 
        population=son_population, 
        calories=0, 
        seeds=[], 
        Qtable=son_qtable, 
        food=[]
    )
    son.memory = son_memory
    
    
    give_seed_to_community(son, parent, len(parent.seeds) // 2)
    give_food_to_community(son, parent, len(parent.food) // 2)
    
    
    son.caravane = True 
    parent.cant_children += 1
    son.id = f"{parent.id}.{parent.cant_children}"
    return son
    

def join_communities(parent1: Community, parent2: Community):
    new_population = parent1.population + parent2.population
    new_calories = parent1.calories + parent2.calories
    new_seeds = parent1.seeds + parent2.seeds
    new_food = parent1.food + parent2.food
    new_Qtable = {**parent1.Qtable, **parent2.Qtable}
    
    new_community = Community(
        position=parent1.position,
        population=new_population,
        calories=new_calories,
        seeds=new_seeds,
        Qtable=new_Qtable,
        food=new_food
    )
    
    new_community.memory = {**parent1.memory, **parent2.memory}
    
    return new_community

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

def get_visible_communities(
    community,
    civilization,
    grid,
    radius=4
):
    """
    Returns communities visible from the current
    position of the community.
    """

    visible_cells = get_visible_cells(
        grid,
        community.position,
        radius
    )

    visible_communities = []

    for other in civilization.communities:

        if other is community:
            continue

        if other.position in visible_cells:
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
    radius=4
):
    """
    Detects visible communities and performs one information
    exchange per pair and simulation turn.
    """

    visible_communities = get_visible_communities(
        community,
        civilization,
        grid,
        radius
    )

    if not visible_communities:
        return 0.0

    other = random.choice(visible_communities)

    # Create an order-independent pair identifier
    pair = tuple(sorted([
        community.id,
        other.id
    ]))

    # Already exchanged information this turn
    if pair in processed_contacts:
        return 0.0

    processed_contacts.add(pair)

    # Exchange information
    reward = exchange_information(
        community,
        other
    )

    # Register the communication location
    register_interaction_zone(
        interaction_zones,
        community.position,
        reward=1.0,
        radius=0
    )

    print(
        f"COMMUNICATION: "
        f"{community.id} <-> {other.id} "
        f"at {community.position}"
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
            
def exchange_qtables(com1, com2):
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

@dataclass
class Civilization:
    communities: List[Community]
    cantCommunities: int = 0
    
    def __init__(self):
        self.communities = []
        self.cantCommunities = 0
    def add_community(self, community: Community):
        self.communities.append(community)
        self.cantCommunities = len(self.communities)
    def kill_community(self, community: Community):
        if community in self.communities:
            self.communities.remove(community)
            self.cantCommunities = len(self.communities)

states=[0,1,2,3,4,5,6,7,8,9]

def board_setup_prototyipe(states):
    board={}
    i=10
    for state in states:
        
        board[state] = cell(height=i)
        i+=10
    return board

# def init_states_protype():
#     states=[0,1,2,3,4,5,6,7,8,9]
    
#     return states



def init_actions_prototype():
    actions=["cultivate", "right", "left"]
    return actions

# transitions={
#     0:{
#         "right":[(0.5,0,-2000),(0.5,1,-2000)],
#         "left":[(0.2,0,-3000),(0.8,-1,-10000)],
#         "cultivate":[(1,0,0)]
#     },
#     1:{
#         "right":[(0.2,0,-1000),(0.8,1,-2000)],
#         "left":[(0.2,0,-2200),(0.8,-1,-3100)],
#         "cultivate":[(1,0,0)]
#     },
#     2:{
#         "right":[(0.2,0,-1100),(0.8,1,-2000)],
#         "left":[(0.2,0,-200),(0.8,-1,-1000)],
#         "cultivate":[(1,0,0)]
#     },
#     3:{
#         "right":[(0.2,0,-1000),(0.8,1,-2000)],
#         "left":[(0.2,0,-2000),(0.8,-1,-3100)],
#         "cultivate":[(1,0,0)]
#     },
#     4:{
#         "right":[(0.2,0,-1000),(0.8,1,-2000)],
#         "left":[(0.2,0,-2000),(0.8,-1,-3100)],
#         "cultivate":[(1,0,0)]
#     },
#     5:{
#         "right":[(0.2,0,-1000),(0.8,1,-2000)],
#         "left":[(0.2,0,-2000),(0.8,-1,-3100)],
#         "cultivate":[(1,0,0)]
#     },
#     6:{
#         "right":[(0.2,0,-1000),(0.8,1,-2000)],
#         "left":[(0.2,0,-2000),(0.8,-1,-3100)],
#         "cultivate":[(1,0,0)]
#     },
#     7:{
#         "right":[(0.2,0,-1000),(0.8,1,-2000)],
#         "left":[(0.2,0,-2000),(0.8,-1,-3100)],
#         "cultivate":[(1,0,0)]
#     },
#     8:{
#         "right":[(0.2,0,-1000),(0.8,1,-2000)],
#         "left":[(0.2,0,-2000),(0.8,-1,-3100)],
#         "cultivate":[(1,0,0)]
#     },
#     9:{
#         "right":[(0.2,0,-1000),(0.8,1,-2000)],
#         "left":[(0.2,0,-2000),(0.8,-1,-3100)],
#         "cultivate":[(1,0,0)]
#     }
# }

def init_transitions(grid):
    directions = [
        (-1, 0),
        (1, 0),
        (0, -1),
        (0, 1),
        (-1, -1),
        (-1, 1),
        (1, -1),
        (1, 1)
    ]
    transitions={}
    
    
    for (x, y), cell in grid.items():
        state = (x, y)
        transitions[state] = {}
        for v, action in cell["actions"].items():
            neighbor_key=v
            transitions[state][neighbor_key] = []
            for possibility in action:
                transitions[state][neighbor_key].append({
                    "next_state": possibility["key"],
                    "prob": possibility["probability"],
                    "reward": -possibility["cost"]
                })
        transitions[state][(0,0)] = [{1.0, float(cell["stay_cost"]), state}]
    return transitions
    
    
def init_Qtable(states: dict):
    Q = {}
    
    for (x,y), cell in states.items():
        state = (x, y)
        Q[state] = {}
        for action_key, action in cell["actions"].items():
            if action_key==(0,0):
                Q[state][action_key] = 0.1
            else:
                Q[state][action_key] = 0.0
    
   
    return Q



def get_tension(com):
    daily_need = com.population * CALORIES_PER_PERSON

    if daily_need <= 0:
        return 1.0

    reserve_days = min(com.calories / daily_need,100)
    
    tension = 1 / (1 + math.exp(3 * (reserve_days - 1.5)))

    return max(0.01, min(tension, 0.99))
def get_best_QValue(com, state):
    value= max(com.Qtable[state],key=com.Qtable[state].get)
    if value==0:
        return (0,0)
    return value

# def get_best_QValue(com, state):
   
#     best_index = 0
#     best_value = float('-inf')
    
#     for i, action in enumerate(com.Qtable[state].keys()):
#         q_value = com.Qtable[state][action]
#         if q_value > best_value:
#             best_value = q_value
#             best_index = i
    
#     return best_index  


# def choose_action(com, actions, states):
#     tension=get_tension(com)
#     state=com.position
#     if random.random() > tension:  
#         return random.choice(actions)
#     else:
#         return get_best_QValue(com, state)

def choose_action(com: Community, states):
    tension = get_tension(com)
    state = com.position
    actions=states[state]["actions"]
    
    
    if com.caravane:
        epsilon = 0.85  
        
        if com.calories > com.population * 8000:
            com.caravane = False
    else:
        epsilon = max(0.1, tension)

    if random.random() < epsilon:
        accion_aleatoria = random.choice(list(actions.items()))
        return accion_aleatoria[0]
    action_key = get_best_QValue(com, state)
    
    return action_key
import ast
def step(state,action,transitions):
    
    posible_results=transitions[state]["actions"][(action[0],action[1])]
    
    cumulative_prob=0.0
    rand=random.random()
    
    for possibility in posible_results:
        cumulative_prob += possibility["probability"]
        if rand < cumulative_prob:
            return possibility["key"], -possibility["cost"]
    
    # return to same state with a penalty
    return state, -50


    
def get_food_by_height(food,height):
    food_by_height=[]
    for f in food:
        if f.parentSeed.originalHeight==height:
            food_by_height.append(f)
    return food_by_height
    
def get_food_by_variety(food,id_variety):
    food_by_variety=[]
    for f in food:
        if f.parentSeed.parentVariety.varietyID==id_variety:
            food_by_variety.append(f)
    return food_by_variety
def get_seeds_by_variety(seeds,id_variety):
    seeds_by_variety=[]
    for f in seeds:
        if f.parentVariety.varietyID==id_variety:
            seeds_by_variety.append(f)
    return seeds_by_variety
                        
def get_variety_memory(com,varietyID,heighMetrics=None):
    
    if varietyID not in com.memory["varieties"]:
        variety=seed_system.getVarietyById(varietyID,heighMetrics)
        com.memory["varieties"][varietyID] = {
            "id":variety.varietyID,
            "name":variety.name,
            "range": f"{variety.minHeightZone}|{variety.maxHeightZone}",
            "best_height":0.0,
            "best_calories_amount":0.0,
            "best_efficiency":0.0,
            "tolerance":0.0,
            "relative_lost":0.0,
            "incertitude":1.0,
            "exploration_value":0.0 
        }
    return com.memory["varieties"][varietyID]
    
        
    
def get_reward(com, height, food, varietyID):
    tension = get_tension(com)

    variety_food = [
        f for f in food
        if f.parentSeed.parentVariety.varietyID == varietyID
    ]

    if len(variety_food) == 0:
        return -0.5

    total_calories = get_total_food_value(variety_food)

    seeds_used = len(set(id(f.parentSeed) for f in variety_food))

    if seeds_used <= 0:
        seeds_used = 1

    efficiency = total_calories / seeds_used
    
    
    variety_memory = get_variety_memory(com, varietyID)

    best_efficiency = variety_memory.get("best_efficiency", 0.0)
    
    if efficiency>best_efficiency:
        variety_memory["best_efficiency"]=efficiency


    if best_efficiency <= 0:
        relative_efficiency = 1.0
    else:
        relative_efficiency = efficiency / best_efficiency

    relative_efficiency = min(relative_efficiency, 2.0)

    if variety_memory["best_height"] == 0:
        height_penalty = 0.0
    else:
        height_distance = abs(height - variety_memory["best_height"])
        tolerance = max(variety_memory.get("tolerance", 20.0), 1.0)
        height_penalty = height_distance / tolerance

    uncertainty = 1 / math.sqrt(seeds_used + 1)

    reward = (
        1.0 * relative_efficiency
        + 0.3 * tension * uncertainty
        - 0.2 * height_penalty
    )

    return reward
def get_alternative_reward(com,height,food,varietyID):
    pertinent_food=get_food_by_variety(com.food,varietyID)
    pertinent_food=get_food_by_height(com.food,height)
    return get_total_food_value(pertinent_food)

def get_total_food_value(food):
    total_calories=0
    for f in food:
        total_calories+=f.calories*f.amount
    return total_calories
def get_incertitude_by_convergence(efficiency1, efficiency2,upper_umbral=10.0,down_umbral=0.01): 
    
    dif = abs(efficiency1 - efficiency2)
    
    if dif >= upper_umbral:
        return 1.0
    
    if dif <= down_umbral:
        return 0.0
    
    incertitude_difference=(dif) / (upper_umbral-down_umbral)
    incertitude =  incertitude_difference
    
    return incertitude           

def update_max_amount_by_variety(com,food,variety_memory,height,seeds):
    variety_seeds=get_seeds_by_variety(seeds,variety_memory["id"])
    variety_food=get_food_by_variety(food,variety_memory["id"])
    total_calories=get_total_food_value(variety_food)
    if len(variety_seeds)<=0:
        return
    efficiency = total_calories / len(variety_seeds)
    
    if efficiency> variety_memory["best_efficiency"]:
        variety_memory["best_height"]=height
        incertitude=get_incertitude_by_convergence(efficiency,variety_memory["best_efficiency"])
        variety_memory["best_height"]=height
        variety_memory["best_calories_amount"]=total_calories
        variety_memory["incertitude"]=incertitude
        variety_memory["best_efficiency"]=efficiency
        
def set_best_variety_by_height_in_memory(com,variety):
    if com.position not in com.memory["cells"]:
        com.memory["cells"][com.position]={
            "best_variety":0
        }
    com.memory["cells"][com.position]["best_variety"]=variety.varietyID


# def select_seeds_by_incertitude(com: Community,height):
#     selected_seeds=[]
#     for varietyID,variety in com.memory["varieties"].items():
#         optim_space=variety["best_height"]
#         incertitude=variety["incertitude"]
#         if incertitude<0.5:
#             range=optim_space+(2*optim_space*(variety["incertitude"]))
#             distance=min(abs(height-optim_space+range),abs(height-optim_space-range))
#             if height <= optim_space+range and height>= optim_space-range:
#                 seeds_by_variety=get_seeds_by_variety(com.seeds,varietyID)
#                 amount= seeds_by_variety*(incertitude/0.1+distance)
                
def get_seeds_by_variety_incertitude(com: Community, height):
    selected_seeds = []
    
    for varietyID, variety in com.memory["varieties"].items():
        optim_space = variety["best_height"]
        incertitude = variety["incertitude"]
        available_seeds = get_seeds_by_variety(com.seeds, varietyID)
            
        if incertitude < 0.5:  
            rango = optim_space *(10+ (2 * optim_space * incertitude))
            limite_sup = optim_space + rango
            limite_inf = optim_space - rango
            
            if height < limite_inf:
                distancia = limite_inf - height
            elif height > limite_sup:
                distancia = height - limite_sup
            else:
                distancia = 0  
            
            
            factor = (1+incertitude) / (1 + distancia)
            amount = len(available_seeds) * factor
        else:
            amount = round(len(available_seeds)*com.tension)
        if amount>0:
            selected_seeds.extend(get_seeds_by_amount(com,amount,varietyID))
    if selected_seeds==[] or com.tension>0.5:
        amount = round(len(com.seeds) * com.tension)
        selected_seeds.extend(com.seeds[:amount])
        com.seeds = com.seeds[amount:]
    elif com.tension>0.75:
        selected_seeds=com.seeds
        com.seeds=[]
        
    
    return selected_seeds
            

def get_seeds_by_amount(com: Community, amount, varietyID):
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

def cultivate(com, board, heightMetrics,writer):
    height=board[com.position]["height"]
    varieties=[]
    max_reward=float("-inf")
    crop_seeds=[]
    crop_food=[]
    
    selected_seeds=get_seeds_by_variety_incertitude(com,height)
    for i,s in enumerate(selected_seeds):
        new_seeds, food = seed_system.seedReproduction(heightMetrics,s, height)
        crop_seeds.extend(new_seeds)
        
        crop_food.extend(food)
        variety_memory=get_variety_memory(com,s.parentVariety.varietyID,heightMetrics)
        update_max_amount_by_variety(com,food,variety_memory,height,new_seeds)
        if s.parentVariety.varietyID not in varieties:
            varieties.append(s.parentVariety)
        seed_system.writeSeedCSVLine(writer,i , s, food,new_seeds,com.seeds)
    
    
    LIMITE_OBJETOS_MAX = com.population * 50  # Ejemplo: máximo 50 objetos de semilla por habitante
    
    if len(crop_seeds) > LIMITE_OBJETOS_MAX:
        random.shuffle(crop_seeds)
        crop_seeds = crop_seeds[:LIMITE_OBJETOS_MAX] # Truncamos el exceso de objetos
        
    if len(crop_food) > LIMITE_OBJETOS_MAX:
        crop_food = crop_food[:LIMITE_OBJETOS_MAX]

    com.seeds.extend(crop_seeds)
    com.food = crop_food
    com.calories += get_total_food_value(crop_food)
    
    
    if len(varieties)==0:
        return 0  
    for v in varieties:
        reward=get_reward(com,height,crop_food,v.varietyID)
        if reward>max_reward:
            max_reward=reward
            set_best_variety_by_height_in_memory(com,v)
            
    return max_reward
    
def move(com,action,board):
    
    return 10, 10
    
def updateQ(com,state,action,next_state:int,reward):

    # Make sure the current state exists
    if state not in com.Qtable:
        com.Qtable[state] = {}

    # Make sure the current action exists
    if action not in com.Qtable[state]:
        com.Qtable[state][action] = 0.0

    # Make sure the next state exists
    if next_state not in com.Qtable:
        com.Qtable[next_state] = {}

    # Get the best future value
    if len(com.Qtable[next_state]) > 0:
        max_future_value = max(
            com.Qtable[next_state].values()
        )
    else:
        max_future_value = 0.0

    current_value = com.Qtable[state][action]

    # Q-learning update
    com.Qtable[state][action] = (
        current_value
        + ALPHA * (
            reward
            + GAMMA * max_future_value
            - current_value
        )
    )

def execute_action(com, action, heightMetrics, board,writer):
    new_pos=com.position
    if action == (0,0):
        reward = cultivate(com, board, heightMetrics,writer)
    else:
        new_pos,reward = step(com.position, action,board)
        reward=(reward*com.population)
    
    return new_pos, reward

def print_varieties_memory(com):
    print("\n========== VARIETY MEMORY ==========\n")

    varieties_memory = com.memory.get("varieties", {})

    if len(varieties_memory) == 0:
        print("No variety memory stored.\n")
        return

    for variety_id, memory in varieties_memory.items():

        print(f"Variety ID: {variety_id}")
        print(f"  Name: {memory.get('name', 'Unknown')}")
        print(f"  Range: {memory.get('range', 'Unknown')}")
        print(f"  Best Height: {memory.get('best_height', 'Unknown')}")
        print(f"  Best Calories Amount: {memory.get('best_calories_amount', 'Unknown')}")
        print(f"  Best Efficiency: {memory.get('best_efficiency', 'Unknown')}")
        print(f"  Tolerance: {memory.get('tolerance', 'Unknown')}")
        print(f"  Relative Lost: {memory.get('relative_lost', 'Unknown')}")
        print(f"  Incertitude: {memory.get('incertitude', 'Unknown')}")
        print(f"  Exploration Value: {memory.get('exploration_value', 'Unknown')}")

        print("-----------------------------------")

    print("\n====================================\n")

def print_Qvalues(com):
    print(com.Qtable)

def print_memory(com):
    for i in range(10):
        print(com.memory["cells"][com.position]["best_variety"])

def main():
    
    
    states=map_loader.generate_grid()
    
    visualizer = visual.SimulationVisualizer(states)
    
    civilization=Civilization()
    heightMetrics=seed_system.generateHeightMetrics()
    
    #board=board_setup_prototyipe(states)
    
    with open("agent_learning_seed_data.csv", "w", newline="") as csvFile:
        writer = csv.writer(csvFile)

        
        flag=True
        
        for j in range(100):
            visits = {}
            interaction_zones = init_interaction_zones()
            n=0
            seed_system.writeSeedCSVHeader(writer)
            civilization.add_community(init_Community_prototype(states))
            print("Civilization revived")
            for i in range(2000):
                current_actions={}
                rewards=[]
                processed_contacts = set()
                for com in civilization.communities:
                    com.tension=get_tension(com)
                    action=choose_action(com,states)

                    old_position = com.position

                    next_state,reward=execute_action(com, action,heightMetrics, states,writer)
                    
                    
                    
                    com.position=next_state
                    interaction_reward = process_information_exchange(
                        com,
                        civilization,
                        states,
                        interaction_zones,
                        processed_contacts
                    )
                    visits[com.position] = visits.get(com.position, 0) + 1
                    reward += interaction_reward
                    updateQ(com,old_position,action,next_state,reward)
                    current_actions[com.id] = {
                        "action": action,
                        "reward": reward
                    }
                    rewards.append(reward)
                    
                    if i % 10 == 0 and i > 1900:
                        visualizer.draw(
                            civilization,
                            i,
                            visits=visits,
                            rewards=rewards,
                            current_actions=current_actions
                        )

                    
                    com.population= min(com.population,com.population+round((com.calories- com.population*1000)/1000))
                    if(com.population<=0):
                        print("Community has die")
                        if i > 1995:
                            map_loader.visualizar_mapa_concurrencia(states, visits)
                        
                        # 1. Eliminarla de la lista de la civilización
                        civilization.kill_community(com)
                        
                        # 2. VACIAR SUS ESTRUCTURAS INTERNAS (Esto libera la RAM de golpe)
                        if j<=1990:
                            com.seeds.clear()
                            com.food.clear()
                            com.Qtable.clear()
                            com.memory.clear()
                            
                            # 3. Eliminar la referencia local del bucle
                            del com 
                        
                        # 4. Romper el ciclo de este agente para pasar al siguiente vivo
                        break 
                        
                        
                        
                    
                    com.calories-=com.population*1000*(2-com.tension*2)
                    com.calories=max(1,com.calories)
                    com.tension=get_tension(com)
                    increase=0
                    if (com.tension<0.75 and com.calories>3000+com.population*5000)or com.calories>com.population*10000 :
                        increase+=round(min(random.randint(1,com.population*2),round((com.calories-com.population*3000)/1000)))
                        com.population+=increase
                        com.calories-=increase*3000
                        if com.calories>100000 and len(com.food)>200 and com.population>1000 and civilization.cantCommunities<20:
                            son=init_Community_from_parent(states,com)
                            civilization.add_community(son)
                            print("Community has been split")
                    
                    if com.calories>500000 :
                        com.calories=random.randrange(400000,500000)
                        
                    if  len(com.food)>200:
                        com.food=com.food[0:random.randint(30,200)]
                        com.seeds= com.seeds[0:random.randint(30,200)]
                    
                    
                
                    print(
                        "Community:", com.id,
                        "Turn:", i,
                        "| Pos:", com.position,
                        "| Food:", round(com.calories, 2),
                        "| Seeds:", len(com.seeds),
                        "| Population:", com.population,
                        "| Tension:",com.tension,
                        "| Action:", action,
                        "| Reward:", round(reward, 2),   
                    )
                    n=i
            if n>1995:
                map_loader.visualizar_mapa_concurrencia(states,visits)
                break
            
        print_varieties_memory(com)
        print_Qvalues(com)
        
        map_loader.visualizar_mapa_concurrencia(states,visits)
    
    

if __name__ == "__main__":
    main()
    
    