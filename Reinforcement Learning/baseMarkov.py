
import random
import matplotlib.pyplot as plt

states = ["A", "B", "C"]
actions = ["go_A", "go_B","go_C"]

Q = {
    "A": {"go_A": 0.0, "go_B": 0.0, "go_C": 0.0},
    "B": {"go_A": 0.0, "go_B": 0.0, "go_C": 0.0},
    "C": {"go_A": 0.0, "go_B": 0.0, "go_C": 0.0}
}

alpha = 0.5
gamma = 0.1


transitions = {
    "A": {
        "go_A": [("A", 1.0, 0)],
        "go_B": [
            ("A", 0.1, 0),
            ("B", 0.8, 10),
            ("C", 0.1, -10)
        ],
        "go_C": [
            ("A", 0.1, 0),
            ("B", 0.1, -10),
            ("C", 0.8, 10)
        ]
    },
    "B": {
        "go_A": [
            ("A", 0.6, 10),
            ("B", 0.3, -10),
            ("C", 0.1, 0)
        ],
        "go_B": [
            ("A", 0.2, 0),
            ("B", 0.7, 10),
            ("C", 0.1, -10)
        ],
        "go_C": [
            ("A", 0.1, 0),
            ("B", 0.2, -10),
            ("C", 0.7, 10)
        ]
    },
    "C": {
        "go_A": [
            ("A", 0.5, 10),
            ("B", 0.4, -10),
            ("C", 0.1, 0)
        ],
        "go_B": [
            ("A", 0.2, 0),
            ("B", 0.6, 10),
            ("C", 0.2, -10)
        ],
        "go_C": [
            ("A", 0.1, 0),
            ("B", 0.3, -10),
            ("C", 0.6, 10)
        ]
    }
}


def step(state,action):
    posible_results=transitions[state][action]
    
    cumulative_prob=0.0
    rand=random.random()
    
    for next_state, prob, reward in posible_results:
        cumulative_prob+=prob
        
        if rand<cumulative_prob:
            return next_state, reward
    

def choose_action(state, search_rate):
    if random.random() < search_rate:
        return random.choice(actions)
    return max(Q[state],key=Q[state].get)

def updateQ(state,action,next_state,gamma,alpha,reward):
    if len(Q[next_state])!=0:
        max_future_value=max(Q[next_state].values())
    else:
        max_future_value=0.0
    Q[state][action]=Q[state][action]+alpha*(reward+gamma*(max_future_value-Q[state][action]))

history = {
    "A_go_A": [],
    "A_go_B": [],
    "A_go_C": [],
    "B_go_A": [],
    "B_go_B": [],
    "B_go_C": [],
    "C_go_A": [],
    "C_go_B": [],
    "C_go_C": []
}


state=random.choice(states)
for episode in range(100):
    action=choose_action(state,0.4)
    next_state, reward=step(state,action)
    
    updateQ(state,action,next_state,gamma,alpha,reward)
    state=next_state
    
    
    history["A_go_A"].append(Q["A"]["go_A"])
    history["A_go_B"].append(Q["A"]["go_B"])
    history["A_go_C"].append(Q["A"]["go_C"])

    history["B_go_A"].append(Q["B"]["go_A"])
    history["B_go_B"].append(Q["B"]["go_B"])
    history["B_go_C"].append(Q["B"]["go_C"])

    history["C_go_A"].append(Q["C"]["go_A"])
    history["C_go_B"].append(Q["C"]["go_B"])
    history["C_go_C"].append(Q["C"]["go_C"])
for state in states:
    plt.figure(figsize=(10, 5))

    for action in actions:
        key = f"{state}_{action}"
        plt.plot(history[key], label=action)

    plt.title(f"Q-values from state {state}")
    plt.xlabel("Episode")
    plt.ylabel("Q-value")
    plt.legend()
    plt.grid(True)
    plt.show()
    
