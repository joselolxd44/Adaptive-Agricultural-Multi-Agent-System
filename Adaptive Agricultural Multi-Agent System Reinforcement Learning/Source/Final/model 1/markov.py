
import math
import random
import base_agent 

CALORIES_PER_PERSON = 2000
BETA= 0.6
ALPHA=0.6
GAMMA=0.6

def get_tension(com: base_agent.Community):
    daily_need = com.population * CALORIES_PER_PERSON

    if daily_need <= 0:
        return 1.0

    reserve_days = min(com.calories / daily_need,100)
    
    tension = 1 / (1 + math.exp(3 * (reserve_days - 1.5)))

    return max(0.01, min(tension, 0.99))

def choose_action(com: base_agent.Community, states):
    tension = get_tension(com)
    state = com.position
    actions=states[state]["actions"]
    
    
    if com.caravane:
        epsilon = 0.85  
        
        if com.calories > com.population * 8000:
            com.caravane = False
    else:
        epsilon = max(0.1, tension)

    if random.random() > epsilon:
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

def get_best_QValue(com: base_agent.Community, state):
    value= max(com.Qtable[state],key=com.Qtable[state].get)
    if value==0:
        return (0,0)
    return value

def execute_action(com: base_agent.Community, action, heightMetrics, board,writer):
    new_pos=com.position
    if action == (0,0):
        reward = base_agent.cultivate(com, board, heightMetrics,writer)
    else:
        new_pos,reward = step(com.position, action,board)
        
        reward = max(-1.0, min(0.0, reward / 10.0))
    
    return new_pos, reward





    