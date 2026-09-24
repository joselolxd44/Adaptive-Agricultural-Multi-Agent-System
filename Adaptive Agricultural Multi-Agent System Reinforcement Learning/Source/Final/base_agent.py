


from dataclasses import dataclass
import enum
from typing import Dict, Tuple, List
import random

import copy
import math
import sys
import gc
from pathlib import Path
from dataclasses import dataclass, field

# Add Final/ to Python path
sys.path.append(
    str(Path(__file__).resolve().parent.parent)
)

import Procedural_Seed_Evolution_System as seed_system
CALORIES_PER_PERSON=2000


class Role(enum.Enum):
    COMMUNITY = 0
    HAMAN = 1
    HURIN = 2


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
    role: Role= Role.COMMUNITY
    def get_variety_memory(self,varietyID,heighMetrics=None):
        if varietyID not in self.memory["varieties"]:
            variety=seed_system.getVarietyById(varietyID,heighMetrics)
            self.memory["varieties"][varietyID] = {
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
        return self.memory["varieties"][varietyID]
    def get_tension(self):
        daily_need = self.population * CALORIES_PER_PERSON

        if daily_need <= 0:
            return 1.0

        reserve_days = min(self.calories / daily_need,100)
        
        tension = 1 / (1 + math.exp(3 * (reserve_days - 1.5)))

        return max(0.01, min(tension, 0.99))
    
    
    
            
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
    import markov
    seeds=seed_system.generateRandomSeeds(5,3900)
    markov.init_transitions(grid)
    qtable=markov.init_Qtable(grid)
    food=seed_system.generateRandomFood(20)
    com=Community(position=(41,34), population=10, calories=15000, seeds=seeds, Qtable=qtable, food=food)
    com.memory=init_memory()
    com.id="1"
    com.cant_children=0
    return com

def init_Community_from_parent( parent: Community):
    
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
    def community_elimination(self,com,i,map_loader,states,visits):
        print("Community has die")
        if i > 995:
            map_loader.visualizar_mapa_concurrencia(states, visits)
        self.kill_community(com)
        #Free memory
        if i<=490:
            com.seeds.clear()
            com.food.clear()
            com.Qtable.clear()
            com.memory.clear()
            del com 
    def initialization(self,states):
        self.add_community(init_Community_prototype(states))
        print("Civilization revived")
    def is_empty(self):
        if self.cantCommunities==0:
            return True
            

def is_community_dead(com:Community):
    com.population= min(com.population,com.population+round((com.calories- com.population*1000)/1000))
    if(com.population<=0):
        return True
    return False


def community_maintenance(com: Community):
    com.calories-=com.population*1000*(2-com.tension*2)
    com.calories=max(1,com.calories)
    com.tension=com.get_tension()

def community_increment(com):
    increase=0
    if (com.tension<0.75 and com.calories>3000+com.population*5000)or com.calories>com.population*10000 :
        increase+=round(min(random.randint(1,com.population*2),round((com.calories-com.population*3000)/1000)))
        com.population+=increase
        com.calories-=increase*3000
def iteration_printing(com,i,action,reward):
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
def food_storage(com:Community):
    if com.calories>500000 :
        com.calories=random.randrange(400000,500000)
        
    if  len(com.food)>200:
        com.food=com.food[0:random.randint(30,200)]
        com.seeds= com.seeds[0:random.randint(30,200)]
        
    com_weight_limit= com.population*20000
    
    food_weight=0
    for f in com.food:
        if( (food_weight+f.weight)>com_weight_limit):
            del com.food[com.food.index(f):]
            gc.collect()
            break
        food_weight+=f.weight
def get_total_food_value(food):
        total_calories=0
        for f in food:
            total_calories+=f.calories*f.amount
        return total_calories


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
        
def set_best_variety_by_height_in_memory(com,variety,reward):
    if com.position not in com.memory["cells"]:
        com.memory["cells"][com.position]={
            "best_variety":0,
            "reward_history":[]
        }
    com.memory["cells"][com.position]["best_variety"]=variety.varietyID
    com.memory["cells"][com.position]["reward_history"].append(reward)



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


def get_reward(com, height, food, varietyID):
    tension = com.get_tension()

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

    variety_memory = com.get_variety_memory( varietyID)

    best_efficiency = variety_memory.get("best_efficiency", 0.0)

    if efficiency > best_efficiency:
        variety_memory["best_efficiency"] = efficiency

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

        height_penalty = min(height_distance / tolerance, 1.0)

    uncertainty = 1 / math.sqrt(seeds_used + 1)

    reward = (
        1.0 * relative_efficiency
        + 0.3 * tension * uncertainty
        - 0.2 * height_penalty
    )

    return reward


def cultivate(com: Community, board, heightMetrics,writer):
    height=board[com.position]["height"]
    varieties=[]
    max_reward=float("-inf")
    crop_seeds=[]
    crop_food=[]
    
    selected_seeds=get_seeds_by_variety_incertitude(com,height)
    SEED_MAX_AMOUNT = com.population * 50 - len(com.seeds)
    for i,s in enumerate(selected_seeds):
        new_seeds, food = seed_system.seedReproduction(heightMetrics,s, height,SEED_MAX_AMOUNT)
        crop_seeds.extend(new_seeds)
        
        crop_food.extend(food)
        variety_memory=com.get_variety_memory(s.parentVariety.varietyID,heightMetrics)
        update_max_amount_by_variety(com,food,variety_memory,height,new_seeds)
        if s.parentVariety.varietyID not in varieties:
            varieties.append(s.parentVariety)
        seed_system.writeSeedCSVLine(writer,i , s, food,new_seeds,com.seeds)
    
    
  
    

    com.seeds.extend(crop_seeds)
    com.food = crop_food
    com.calories += get_total_food_value(crop_food)
    
    
    if len(varieties)==0:
        return 0  
    for v in varieties:
        reward=get_reward(com,height,crop_food,v.varietyID)
        if reward>max_reward:
            max_reward=reward
            set_best_variety_by_height_in_memory(com,v,reward)
            
    return max_reward



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
        