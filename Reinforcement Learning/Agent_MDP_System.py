from dataclasses import dataclass
import random
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import Procedural_Seed_Evolution_System as seed_system

rows=4
cols=4

board = np.zeros((rows, cols))

blocked = (1, 2)
goal = (0, 3)
agent = (3, 0)

board[blocked] = -1
board[goal] = 2
board[agent] = 1

plt.imshow(board)

plt.show()


@dataclass
class Agent:
    agent_id: int
    Q: dict

@dataclass
class Civilization:
    position: tuple
    food: float
    seeds: list[seed_system.Seed]
    alive: bool = True
    agent: Agent = None
    
def get_QTable(rows,cols,states, blocked_states,actions):
    Q = {}
    for state in states:
        Q[state] = {}
        for action in actions:
            Q[state][action] = 0.0
                
    return Q

def setAgent(agent_id: int,QTable: dict) -> Agent:
    agent=Agent(agent_id, {})
    agent.Q=QTable
    return agent


def step(civ, action, board, heightMetrics):
    reward = 0

    if action == "cultivate":
        cell_height = board[civ.position]["height"]
        reward = cultivate(civ, heightMetrics, cell_height)

    elif action in ["up", "down", "left", "right"]:
        reward = move_civilization(civ, action, board)

    return get_state(civ, board), reward

def choose_action(state,search_rate,Q,actions):
    if random.random() < search_rate:
        return random.choice(list(actions.keys()))
    return max(Q[state],key=Q[state].get)

def update_q(state,action,reward,next_state,agent,alpha,gamma):
    best_future_q = max(agent.Q[next_state].values())
    agent.Q[state][action] += alpha * (
        reward + gamma * best_future_q - agent.Q[state][action]
    )

def act(state,alpha,gamma,civ,actions,transitions):
    action= choose_action(state,0.4)
    next_state, reward=step(state,action,transitions,civ)
    update_q(state,action,reward,next_state,civ,alpha,gamma)
    
fig, ax = plt.subplots()

def update(frame):
    ax.clear()

    board = np.zeros((rows, cols))

    board[blocked] = -1
    board[goal] = 2

    agent_pos = path[frame]
    board[agent_pos] = 1

    ax.imshow(board)

    ax.set_title(f"Step {frame}")
    ani = animation.FuncAnimation(
    fig,
    update,
    frames=len(path),
    interval=500,
    repeat=False
    )

    plt.show()

def cultivate(civ, heightMetrics, cell_height):
    if len(civ.seeds) == 0:
        return -50

    seed = civ.seeds.pop(0)

    children, produced_food = seed_system.seedReproduction(
        heightMetrics,
        seed,
        cell_height
    )

    food_amount = sum(f.amount for f in produced_food)
    total_calories = sum(f.calories for f in produced_food)
    children_count = len(children)

    civ.food += food_amount
    civ.seeds.extend(children)

    reward = (
        food_amount * 2
        + total_calories * 0.01
        + children_count * 5
    )

    if food_amount == 0:
        reward -= 10

    if children_count == 0:
        reward -= 15

    if civ.food <= 0:
        civ.alive = False
        reward -= 100

    return reward


def train_agent(civ,episodes,actions,states,alpha,gamma,transitions):
    state=random.choice(states)
    for episode in range(episodes):
        act(state,alpha,gamma,civ,actions,transitions)




if __name__ == "__main__":
    train_agent()