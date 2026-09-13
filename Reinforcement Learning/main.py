import random
import matplotlib.pyplot as plt
import Agent_MDP_System as agent_system

rows, cols = 4, 4

start_state = (3, 0)
goal_state = (0, 3)
blocked_states = [(1, 2)]

states = [(r, c) for r in range(rows) for c in range(cols) if (r, c) not in blocked_states]

actions = {
    "up": (-1, 0),
    "down": (1, 0),
    "left": (0, -1),
    "right": (0, 1),
    "cultivate": (0, 0)
}


for r in range(rows):
    for c in range(cols):
        if (r, c) not in blocked_states:
            states.append((r, c))



transitions = {}

for state in states:
    transitions[state] = {}

    for action, (dr, dc) in actions.items():
        nr, nc = state[0] + dr, state[1] + dc
        next_state = (nr, nc)

        
        if (
            nr < 0 or nr >= rows or
            nc < 0 or nc >= cols or
            next_state in blocked_states
        ):
            next_state = state  # se queda

        prob=1.0
        prob_1=prob*random.uniform(0.1, 0.8)
        rest=prob-prob_1
        
        prob_2=rest*random.uniform(0.1, 0.9)
        rest=rest-prob_2
        prob_3=rest
        
        posibility_1=(prob_1,random.uniform(1000, 2000))
        posibility_2=(prob_2,random.uniform(2000, 3000))
        posibility_3=(prob_3,random.uniform(1000, 2000))
        

        
        transitions[state][action] = [
            (next_state, posibility_1[0], posibility_1[1]),
            (next_state, posibility_2[0], posibility_2[1]),
            (state, posibility_3[0], posibility_3[1])
        ]
        


alpha = 0.1
gamma = 0.9
epsilon = 0.2
episodes = 500

QTable = agent_system.get_QTable(rows, cols, state, blocked_states, actions)
agent = agent_system.setAgent(1, QTable)
agent_system.train_agent(agent, episodes, actions, states, alpha, gamma, transitions)