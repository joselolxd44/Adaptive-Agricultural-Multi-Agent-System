

import base_agent 

import math
import random
import re


import DataMapLoad

CALORIES_PER_PERSON = 2000
BETA= 0.6
ALPHA=0.6
GAMMA=0.6



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
                    "prob": round(possibility["probability"],2),
                    "reward": round(-possibility["cost"],2)
                })
        
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


def choose_colony_action(com: base_agent.Community, colony_states):

    tension = com.get_tension()
    state = com.position

    actions = {
        action: possibilities
        for action, possibilities in colony_states[state].items()
        if action != "acces"
    }

    if com.caravane:
        epsilon = 0.85

        if com.calories > com.population * 8000:
            com.caravane = False
    else:
        epsilon = max(0.1, tension)

    if random.random() > epsilon:
        return random.choice(list(actions.keys()))

    return get_best_QValue(com, state)



def choose_action(com: base_agent.Community, states):
    tension = com.get_tension()
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
def step_colony(state, action, colony_states):
    if state not in colony_states:
        return state, -50

    if action not in colony_states[state]:
        return state, -50

    possible_results = colony_states[state][action]

    cumulative_prob = 0.0
    rand = random.random()

    for possibility in possible_results:
        cumulative_prob += possibility["prob"]

        if rand < cumulative_prob:
            return possibility["next_state"], possibility["reward"]

    return state, -50

def get_best_QValue(com: base_agent.Community, state):
    value= max(com.Qtable[state],key=com.Qtable[state].get)
    if value==0:
        return (0,0)
    return value





def updateQ(com,state,action,next_state:int,reward):
    if next_state not in com.Qtable:
        # Inicializar el estado si no existe
        com.Qtable[next_state] = {}
        print(f"Inicializando estado {next_state} en Q-table")
    if len(com.Qtable[next_state])!=0:
        max_future_value=max(com.Qtable[next_state].values())
    else:
        max_future_value=0.0
    new_qvalue=com.Qtable[state][action] + ALPHA * (reward + GAMMA * max_future_value - com.Qtable[state][action])
    old_qvalue=com.Qtable[state][action]
    com.Qtable[state][action] = new_qvalue
    return new_qvalue == old_qvalue

def markov_process(com, states, heightMetrics, writer, previous_reward,q_is_the_same=False):

    com.tension = com.get_tension()

    action = choose_action(com,states)

    next_state, reward = execute_action(com, action,heightMetrics,states,writer)

    previous_reward += reward

    qsame = updateQ(com,com.position,action,next_state,previous_reward)
    q_is_the_same=qsame
    com.position = next_state

    return action

def is_community_colony(com: base_agent.Community,board_position):
    id=com.id[:-1]
    id_colony=board_position["colony_id"]
    return id==id_colony
    
    

def execute_action(com: base_agent.Community, action, heightMetrics, board,writer):
    new_pos=com.position
    if action == (0,0):
        if "is_colony" in board[com.position]:
            if not board[com.position]["is_colony"]:
                reward = base_agent.cultivate(com, board,heightMetrics, writer)
            else:
                if is_community_colony(com,board[com.position]):
                    reward = base_agent.cultivate(com, board,heightMetrics, writer)
                else:
                    reward = -1.0
        else:
            reward = base_agent.cultivate(com,board,heightMetrics,writer)
        
    else:
        new_pos,reward = step(com.position, action,board)
        
        reward = max(-1.0, min(0.0, reward / 10.0))
    
    return new_pos, reward


def execute_colony_action(
    com,
    action,
    heightMetrics,
    colony_states,
    states,
    writer
):
    if action == (0, 0):
        reward = base_agent.cultivate(
            com,
            states,
            heightMetrics,
            writer
        )

        return com.position, reward

    new_pos, reward = step_colony(
        com.position,
        action,
        colony_states
    )

    return new_pos, reward

def markov_process(com,states,heightMetrics,writer,previous_reward):
    com.tension=com.get_tension()
    action=choose_action(com,states)
    next_state,reward=execute_action(com, action,heightMetrics, states,writer)
    previous_reward+=reward
    updateQ(com,com.position,action,next_state,previous_reward)
    com.position=next_state
    return action, reward


def markov_colony_process(
    com,
    colony_states,
    states,
    heightMetrics,
    writer,
    previous_reward
):
    com.tension = com.get_tension()

    action = choose_colony_action(
        com,
        colony_states
    )

    next_state, reward = execute_colony_action(
        com,
        action,
        heightMetrics,
        colony_states,
        states,
        writer
    )

    previous_reward += reward

    qchanged = updateQ(
        com,
        com.position,
        action,
        next_state,
        previous_reward
    )

    com.position = next_state

    return action, previous_reward, qchanged

def main():
    grid=DataMapLoad.generate_grid()
    states=init_transitions(grid)
    print(states)


if __name__ == "__main__":
    main()
    
    