import random
import csv
from dataclasses import dataclass, field
from typing import Dict, Tuple, List
import DataMapLoad as data_map
import Procedural_Seed_Evolution_System as seed_system
import math

CALORIES_PER_PERSON = 1000
BETA= 0.6
ALPHA=0.6
GAMMA=0.6
VARIANCE_MIN_SAMPLES = 50
@dataclass
class cell:
    height: float
    

@dataclass
class Civilization:
    position: int
    population: int
    calories: float
    seeds: List[seed_system.Seed]
    Qtable:Dict
    food: list[seed_system.Food]
    tension: float = 0.0
    memory={}

states=[0,1,2,3,4,5,6,7,8,9]

def board_setup_prototyipe(states):
    board={}
    i=10
    for state in states:
        
        board[state] = cell(height=i)
        i+=10
    return board

def init_states_protype():
    states=[0,1,2,3,4,5,6,7,8,9]
    
    return states



def init_actions_prototype():
    actions=["cultivate", "right", "left"]
    return actions

transitions={
    0:{
        "right":[(0.5,0,-2000),(0.5,1,-2000)],
        "left":[(0.2,0,-3000),(0.8,-1,-10000)],
        "cultivate":[(1,0,0)]
    },
    1:{
        "right":[(0.2,0,-1000),(0.8,1,-2000)],
        "left":[(0.2,0,-2200),(0.8,-1,-3100)],
        "cultivate":[(1,0,0)]
    },
    2:{
        "right":[(0.2,0,-1100),(0.8,1,-2000)],
        "left":[(0.2,0,-200),(0.8,-1,-1000)],
        "cultivate":[(1,0,0)]
    },
    3:{
        "right":[(0.2,0,-1000),(0.8,1,-2000)],
        "left":[(0.2,0,-2000),(0.8,-1,-3100)],
        "cultivate":[(1,0,0)]
    },
    4:{
        "right":[(0.2,0,-1000),(0.8,1,-2000)],
        "left":[(0.2,0,-2000),(0.8,-1,-3100)],
        "cultivate":[(1,0,0)]
    },
    5:{
        "right":[(0.2,0,-1000),(0.8,1,-2000)],
        "left":[(0.2,0,-2000),(0.8,-1,-3100)],
        "cultivate":[(1,0,0)]
    },
    6:{
        "right":[(0.2,0,-1000),(0.8,1,-2000)],
        "left":[(0.2,0,-2000),(0.8,-1,-3100)],
        "cultivate":[(1,0,0)]
    },
    7:{
        "right":[(0.2,0,-1000),(0.8,1,-2000)],
        "left":[(0.2,0,-2000),(0.8,-1,-3100)],
        "cultivate":[(1,0,0)]
    },
    8:{
        "right":[(0.2,0,-1000),(0.8,1,-2000)],
        "left":[(0.2,0,-2000),(0.8,-1,-3100)],
        "cultivate":[(1,0,0)]
    },
    9:{
        "right":[(0.2,0,-1000),(0.8,1,-2000)],
        "left":[(0.2,0,-2000),(0.8,-1,-3100)],
        "cultivate":[(1,0,0)]
    }
}

def init_Qtable(states, actions):
    Q = {}
    for state in states:
        Q[state] = {}
        for action in actions:
            Q[state][action] = 0.0
    return Q

def init_memory():
    memory={}
    memory["varieties"]={}
    memory["cells"]={}
    return memory

def init_civilization_prototype():
    seeds=seed_system.generateRandomSeeds(5,20)
    qtable=init_Qtable(init_states_protype(), init_actions_prototype())
    food=seed_system.generateRandomFood(20)
    civ=Civilization(position=0, population=10, calories=15000, seeds=seeds, Qtable=qtable, food=food)
    civ.memory=init_memory()
    return civ

def get_tension(civ):
    daily_need = civ.population * CALORIES_PER_PERSON

    if daily_need <= 0:
        return 1.0

    reserve_days = min(civ.calories / daily_need,100)
    
    tension = 1 / (1 + math.exp(3 * (reserve_days - 1.5)))

    return max(0.01, min(tension, 0.99))
def get_best_QValue(civ, state):
    return max(civ.Qtable[state],key=civ.Qtable[state].get)


# def choose_action(civ, actions, states):
#     tension=get_tension(civ)
#     state=civ.position
#     if random.random() > tension:  
#         return random.choice(actions)
#     else:
#         return get_best_QValue(civ, state)

def choose_action(civ, actions, states):
    tension = get_tension(civ)
    state = civ.position

    epsilon = max(0.1, tension)

    if random.random() < epsilon:
        return random.choice(actions)

    return get_best_QValue(civ, state)

def step(state,action):
    posible_results=transitions[state][action]
    
    cumulative_prob=0.0
    rand=random.random()
    
    for prob,movement,reward in posible_results:
        cumulative_prob+=prob
        next_state=state+movement
        if next_state<len(states) and next_state>=0:
            
            if rand<cumulative_prob:
                return next_state, reward
            
        else:
            continue
    
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
                        
def get_variety_memory(civ,varietyID,heighMetrics=None):
    
    if varietyID not in civ.memory["varieties"]:
        variety=seed_system.getVarietyById(varietyID,heighMetrics)
        civ.memory["varieties"][varietyID] = {
            "id":variety.varietyID,
            "name":variety.name,
            "range": f"{variety.minHeightZone}|{variety.maxHeightZone}",
            "best_height":0.0,
            "best_calories_amount":0.0,
            "best_efficiency":0.0,
            "tolerance":0.0,
            "relative_lost":0.0,
            "incertitude":1.0,
            "exploration_value":0.0,
            
            "count": 0,
            "mean_efficiency": 0.0,
            "variance": 0.0,
            "std": 0.0,
            "M2": 0.0,

            "successes": 0,
            "failures": 0,
            "posterior": 0.5,
            "confidence_level": 0.95,
            "confidence_low": 0.0,
            "confidence_high": 0.0,
            
            
        }
    return civ.memory["varieties"][varietyID]

import math

def update_confidence_interval(variety_memory):

    ic = get_confidence_interval(
        variety_memory["mean_efficiency"],
        variety_memory["std"],
        variety_memory["count"],
        variety_memory["confidence_level"]
    )

    variety_memory["confidence_low"] = ic["lower"]
    variety_memory["confidence_high"] = ic["upper"]

def get_confidence_interval(mean, std, n, confidence_level=0.95):

    if n <= VARIANCE_MIN_SAMPLES:
        return {
            "confidence_level": confidence_level,
            "lower": mean,
            "upper": mean,
            "range": 0.0
        }

    z_values = {
        0.90: 1.645,
        0.95: 1.96,
        0.99: 2.576
    }

    z = z_values.get(confidence_level, 1.96)

    margin = z * (std / math.sqrt(n))

    lower = mean - margin
    upper = mean + margin

    return {
        "confidence_level": confidence_level,
        "lower": lower,
        "upper": upper,
        "range": upper - lower
    }
   
def update_variance(variety_memory, efficiency):

    count = variety_memory["count"] + 1

    mean = variety_memory["mean_efficiency"]

    delta = efficiency - mean

    mean += delta / count

    delta2 = efficiency - mean

    M2 = variety_memory["M2"] + delta * delta2

    if count > VARIANCE_MIN_SAMPLES:
        variance = M2 / (count - 1)
    else:
        variance = 0.0

    std = math.sqrt(variance)

    variety_memory["count"] = count
    variety_memory["mean_efficiency"] = mean
    variety_memory["M2"] = M2
    variety_memory["variance"] = variance
    variety_memory["std"] = std       
    
def get_reward(civ, height, food, varietyID):
    tension = get_tension(civ)

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
    
    
    variety_memory = get_variety_memory(civ, varietyID)

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
def get_alternative_reward(civ,height,food,varietyID):
    pertinent_food=get_food_by_variety(civ.food,varietyID)
    pertinent_food=get_food_by_height(civ.food,height)
    return get_total_food_value(pertinent_food)

def get_total_food_value(food):
    total_calories=0
    for f in food:
        total_calories+=f.calories*f.amount
    return total_calories

def get_incertitude_by_convergence(efficiency,variety_memory):

    mean = variety_memory["mean_efficiency"]
    std = variety_memory["std"]

    if std <= 0:
        return 1.0

    z = abs(efficiency - mean) / std

    incertitude = min(1.0, z / 3.0)

    return incertitude

def update_bayes(variety_memory, efficiency):

    if variety_memory["count"] < 50:
        return

    lower = variety_memory["confidence_low"]

    if efficiency < lower:
        variety_memory["failures"] += 1
    else:
        variety_memory["successes"] += 1

    successes = variety_memory["successes"]
    failures = variety_memory["failures"]

    alpha = successes + 1
    beta = failures + 1

    variety_memory["posterior"] = (
        alpha / (alpha + beta)
    )
    
def update_max_amount_by_variety(civ,food,variety_memory,height,seeds):
    variety_seeds=get_seeds_by_variety(seeds,variety_memory["id"])
    variety_food=get_food_by_variety(food,variety_memory["id"])
    total_calories=get_total_food_value(variety_food)
    if len(variety_seeds)<=0:
        return
    efficiency = total_calories / len(variety_seeds)
    
    update_variance(variety_memory,efficiency)

    update_bayes(variety_memory,efficiency)
    
    update_confidence_interval(variety_memory)

    if efficiency > variety_memory["best_efficiency"]:
        variety_memory["best_height"]=height
        incertitude=get_incertitude_by_convergence(efficiency,variety_memory)
        variety_memory["best_height"]=height
        variety_memory["best_calories_amount"]=total_calories
        variety_memory["incertitude"]=incertitude
        variety_memory["best_efficiency"]=efficiency
        
def set_best_variety_by_height_in_memory(civ,variety):
    if civ.position not in civ.memory["cells"]:
        civ.memory["cells"][civ.position]={
            "best_variety":0
        }
    civ.memory["cells"][civ.position]["best_variety"]=variety.varietyID


# def select_seeds_by_incertitude(civ: Civilization,height):
#     selected_seeds=[]
#     for varietyID,variety in civ.memory["varieties"].items():
#         optim_space=variety["best_height"]
#         incertitude=variety["incertitude"]
#         if incertitude<0.5:
#             range=optim_space+(2*optim_space*(variety["incertitude"]))
#             distance=min(abs(height-optim_space+range),abs(height-optim_space-range))
#             if height <= optim_space+range and height>= optim_space-range:
#                 seeds_by_variety=get_seeds_by_variety(civ.seeds,varietyID)
#                 amount= seeds_by_variety*(incertitude/0.1+distance)
                
def get_seeds_by_variety_incertitude(civ: Civilization, height):
    selected_seeds = []
    

    
    for varietyID, variety in civ.memory["varieties"].items():
        optim_space = variety["best_height"]
        incertitude = variety["incertitude"]
        available_seeds = get_seeds_by_variety(civ.seeds, varietyID)
            
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
            
            
            #factor = (1+incertitude) / (1 + distancia)
            posterior = variety["posterior"]
            factor = ((1 + incertitude)* posterior) / (1 + distancia)
            
            amount = len(available_seeds) * factor
        else:
            amount = round(len(available_seeds)*civ.tension)
        if amount>0:
            selected_seeds.extend(get_seeds_by_amount(civ,amount,varietyID))
    if selected_seeds==[] or civ.tension>0.5:
        amount = round(len(civ.seeds) * civ.tension)
        selected_seeds.extend(civ.seeds[:amount])
        civ.seeds = civ.seeds[amount:]
    elif civ.tension>0.75:
        selected_seeds=civ.seeds
        civ.seeds=[]
        
    
    return selected_seeds
            

def get_seeds_by_amount(civ: Civilization, amount, varietyID):
    selected_seeds = []
    i = 0

    for seed in civ.seeds[:]:
        if i >= amount:
            break

        if seed.parentVariety.varietyID == varietyID:
            selected_seeds.append(seed)
            civ.seeds.remove(seed)
            i += 1

    return selected_seeds  

def cultivate(civ, board, heightMetrics,writer):
    height=board[civ.position].height
    varieties=[]
    max_reward=float("-inf")
    crop_seeds=[]
    crop_food=[]
    
    selected_seeds=get_seeds_by_variety_incertitude(civ,height)
    for i,s in enumerate(selected_seeds):
        new_seeds, food = seed_system.seedReproduction(heightMetrics,s, height)
        crop_seeds.extend(new_seeds)
        
        crop_food.extend(food)
        variety_memory=get_variety_memory(civ,s.parentVariety.varietyID,heightMetrics)
        update_max_amount_by_variety(civ,food,variety_memory,height,new_seeds)
        if s.parentVariety.varietyID not in varieties:
            varieties.append(s.parentVariety)
        seed_system.writeSeedCSVLine(writer,i , s, food,new_seeds,civ.seeds)
    civ.seeds.extend(crop_seeds)
    civ.food=crop_food
    civ.calories+=get_total_food_value(crop_food)
    if len(varieties)==0:
        return 0  
    for v in varieties:
        reward=get_reward(civ,height,crop_food,v.varietyID)
        if reward>max_reward:
            max_reward=reward
            set_best_variety_by_height_in_memory(civ,v)
    return max_reward
    
def move(civ,action,board):
    
    return 10, 10
    
def updateQ(civ,state,action,next_state:int,reward):
    if next_state not in civ.Qtable:
        # Inicializar el estado si no existe
        civ.Qtable[next_state] = {}
        print(f"Inicializando estado {next_state} en Q-table")
    if len(civ.Qtable[next_state])!=0:
        max_future_value=max(civ.Qtable[next_state].values())
    else:
        max_future_value=0.0
    civ.Qtable[state][action] = civ.Qtable[state][action] + ALPHA * (reward + GAMMA * max_future_value - civ.Qtable[state][action])


def execute_action(civ, action, heightMetrics, board,writer):
    new_pos=civ.position
    if action == "cultivate":
        reward = cultivate(civ, board, heightMetrics,writer)
    else:
        new_pos,reward = step(civ.position, action)
        reward=(reward/ (civ.population * CALORIES_PER_PERSON))
    
    return new_pos, reward

def print_varieties_memory(civ):
    print("\n========== VARIETY MEMORY ==========\n")

    varieties_memory = civ.memory.get("varieties", {})

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
        print(f"  Count: {memory.get('count', 'Unknown')}")
        print(f"  Mean Efficiency: {memory.get('mean_efficiency', 'Unknown')}")
        print(f"  Variance: {memory.get('variance', 'Unknown')}")
        print(f"  Std: {memory.get('std', 'Unknown')}")
        print(f"  Successes: {memory.get('successes', 'Unknown')}")
        print(f"  Failures: {memory.get('failures', 'Unknown')}")
        print(f"  Posterior: {memory.get('posterior', 'Unknown')}")
        ic = get_confidence_interval(
            memory.get('mean_efficiency', 0.0),
            memory.get('std', 0.0),
            memory.get('count', 0),
            memory.get('confidence_level', 0.95)
        )

        print(ic)
        
        

        print("-----------------------------------")

    print("\n====================================\n")

def print_Qvalues(civ):
    for i in range(len(civ.Qtable)):
        print(i,":",civ.Qtable[i])

def print_memory(civ):
    for i in range(10):
        print(civ.memory["cells"][civ.position]["best_variety"])

def main():
    civ=init_civilization_prototype()
    states=init_states_protype()
    actions=init_actions_prototype()
    
    heightMetrics=seed_system.generateHeightMetrics()
    board=board_setup_prototyipe(states)
    civ.position=7
    with open("agent_learning_seed_data.csv", "w", newline="") as csvFile:
        writer = csv.writer(csvFile)

        
        flag=True
        while(flag):
            seed_system.writeSeedCSVHeader(writer)
            for i in range(1000):
                if i==250:
                    day=0
                if i==999:
                    flag=False
                civ.tension=get_tension(civ)
                action=choose_action(civ,actions,states)
                next_state,reward=execute_action(civ, action,heightMetrics, board,writer)
                updateQ(civ,civ.position,action,next_state,reward)
                civ.position=next_state
                
                civ.population= min(civ.population,civ.population+round((civ.calories- civ.population*1000)/1000))
                if(civ.population<=0):
                    print("civilization has die")
                    break
                
                civ.calories-=civ.population*1000*(2-civ.tension*2)
                civ.calories=max(1,civ.calories)
                civ.tension=get_tension(civ)
                increase=0
                if (civ.tension<0.75 and civ.calories>3000+civ.population*5000)or civ.calories>civ.population*10000 :
                    increase+=round(min(random.randint(1,civ.population*2),round((civ.calories-civ.population*3000)/1000)))
                    civ.population+=increase
                    civ.calories-=increase*3000
                
                if civ.calories>500000 :
                    civ.calories=random.randrange(400000,500000)
                    
                if  len(civ.food)>200:
                    civ.food=civ.food[0:random.randint(30,200)]
                    civ.seeds= civ.seeds[0:random.randint(30,200)]
            
                print(
                    "Turn:", i,
                    "| Pos:", civ.position,
                    "| Food:", round(civ.calories, 2),
                    "| Seeds:", len(civ.seeds),
                    "| Population:", civ.population,
                    "| Tension:",civ.tension,
                    "| Action:", action,
                    "| Reward:", round(reward, 2),   
                )
            civ.population=20
            civ.food=seed_system.generateRandomFood(20)
            civ.calories=get_total_food_value(civ.food)
            print("Population revived")
        print_varieties_memory(civ)
        print_Qvalues(civ)
        print(civ.memory)
    
    
    

if __name__ == "__main__":
    main()
    
    