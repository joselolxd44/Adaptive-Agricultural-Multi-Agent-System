import ast
import gc
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
import markov
import base_agent
import Visualizer_2 as visual
CALORIES_PER_PERSON = 1000
BETA= 0.6
ALPHA=0.6
GAMMA=0.6
@dataclass
class cell:
    height: float
    



# @dataclass
# class Community:
#     position: int
#     population: int
#     calories: float
#     seeds: List[seed_system.Seed]
#     Qtable:Dict
#     food: list[seed_system.Food]
#     tension: float = 0.0
#     memory: dict = field(default_factory=dict)
#     id: str= ""
#     caravane: bool = False
#     cant_children: int = 0
    

# def init_Community_from_parent(grid, parent: base_agent.Community):
    
#     son_qtable = copy.deepcopy(parent.Qtable)
#     son_memory = copy.deepcopy(parent.memory)
    
    
#     son_population = parent.population // 4  
#     if son_population < 2: 
#         son_population = 2
    
#     son = Community(
#         position=parent.position, 
#         population=son_population, 
#         calories=0, 
#         seeds=[], 
#         Qtable=son_qtable, 
#         food=[]
#     )
#     son.memory = son_memory
    
    
#     give_seed_to_community(son, parent, len(parent.seeds) // 2)
#     give_food_to_community(son, parent, len(parent.food) // 2)
    
    
#     son.caravane = True 
#     parent.cant_children += 1
#     son.id = f"{parent.id}.{parent.cant_children}"
#     return son
    

# def join_communities(parent1: base_agent.Community, parent2: base_agent.Community):
#     new_population = parent1.population + parent2.population
#     new_calories = parent1.calories + parent2.calories
#     new_seeds = parent1.seeds + parent2.seeds
#     new_food = parent1.food + parent2.food
#     new_Qtable = {**parent1.Qtable, **parent2.Qtable}
    
#     new_community = Community(
#         position=parent1.position,
#         population=new_population,
#         calories=new_calories,
#         seeds=new_seeds,
#         Qtable=new_Qtable,
#         food=new_food
#     )
    
#     new_community.memory = {**parent1.memory, **parent2.memory}
    
#     return new_community

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
                
def get_seeds_by_variety_incertitude(com: base_agent.Community, height):
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
        reward=markov.get_reward(com,height,crop_food,v.varietyID)
        if reward>max_reward:
            max_reward=reward
            set_best_variety_by_height_in_memory(com,v)
            
    return max_reward
    

# def updateQ(com,state,action,next_state:int,reward):

#     # Make sure the current state exists
#     if state not in com.Qtable:
#         com.Qtable[state] = {}

#     # Make sure the current action exists
#     if action not in com.Qtable[state]:
#         com.Qtable[state][action] = 0.0

#     # Make sure the next state exists
#     if next_state not in com.Qtable:
#         com.Qtable[next_state] = {}

#     # Get the best future value
#     if len(com.Qtable[next_state]) > 0:
#         max_future_value = max(
#             com.Qtable[next_state].values()
#         )
#     else:
#         max_future_value = 0.0

#     current_value = com.Qtable[state][action]

#     # Q-learning update
#     com.Qtable[state][action] = (
#         current_value
#         + ALPHA * (
#             reward
#             + GAMMA * max_future_value
#             - current_value
#         )
#     )

# def execute_action(com, action, heightMetrics, board,writer):
#     new_pos=com.position
#     if action == (0,0):
#         reward = cultivate(com, board, heightMetrics,writer)
#     else:
#         new_pos,reward = step(com.position, action,board)
#         reward=(reward*com.population)
    
#     return new_pos, reward




def community_maintenance(com: base_agent.Community):
    com.calories-=com.population*1000*(2-com.tension*2)
    com.calories=max(1,com.calories)
    com.tension=markov.get_tension(com)

def community_increment(com):
    increase=0
    if (com.tension<0.75 and com.calories>3000+com.population*5000)or com.calories>com.population*10000 :
        increase+=round(min(random.randint(1,com.population*2),round((com.calories-com.population*3000)/1000)))
        com.population+=increase
        com.calories-=increase*3000

def can_reproduce(com: base_agent.Community, civ: base_agent.Civilization):
    if com.calories>100000 and len(com.food)>200 and com.population>1000 and civ.cantCommunities<6: return True
    return False
    
def community_reproduction(com: base_agent.Community, civ: base_agent.Civilization):
    
    if(can_reproduce(com, civ)):
        son=base_agent.init_Community_from_parent(com)
        civ.add_community(son)
        print("Community has been split")
        return True
    
def build_community_position_index(civilization):
    index = {}

    for com in civilization.communities:
        index.setdefault(com.position, []).append(com)

    return index



                            
    


def main():
    
   
    states=map_loader.generate_grid()
    visualizer = visual.SimulationVisualizer(states)
    civilization=base_agent.Civilization()
    heightMetrics=seed_system.generateHeightMetrics()
    
    #board=board_setup_prototyipe(states)
    
    with open("agent_learning_seed_data.csv", "w", newline="") as csvFile:
        writer = csv.writer(csvFile)

        
        flag=True
        
        for j in range(100):
            interaction_zones = init_interaction_zones()
            visits = {}
            n=0
            seed_system.writeSeedCSVHeader(writer)
            
            civilization.add_community(base_agent.init_Community_prototype(states))
            print("Civilization revived")
            for i in range(1000):
                current_actions={}
                rewards=[]
                processed_contacts = set()
                for com in civilization.communities:
                    
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
                    action, reward= markov.markov_process(com,states,heightMetrics,writer,reward)
                    
                    
                    visits[com.position] = visits.get(com.position, 0) + 1
                    current_actions[com.id] = { "action": action, "reward": reward}
                    rewards.append(reward)
                    
                    if(base_agent.is_community_dead(com)):
                        civilization.community_elimination(com,i,map_loader,states,visits)
                        break 
                    
                    #We check if the community can supply for all the population, otherwise they die
                    base_agent.community_maintenance(com)
                    base_agent.community_increment(com)
                    community_reproduction(com, civilization)
                    base_agent.food_storage(com)
                    base_agent.iteration_printing(com,i,action,reward)
                    n=i
                if civilization.is_empty():
                    break
                #for each 10 iterations the visualzier changesS
                if i % 10 == 0:
                    visualizer.draw(
                        civilization,
                        i,
                        visits,
                        rewards,
                        current_actions
                    )

            if n>995:
                map_loader.visualizar_mapa_concurrencia(states,visits)
                break
            
        base_agent.print_varieties_memory(com)
        base_agent.print_Qvalues(com)
        
    map_loader.visualizar_mapa_concurrencia(states,visits)
        
    
    
    

if __name__ == "__main__":
    main()
    
    


