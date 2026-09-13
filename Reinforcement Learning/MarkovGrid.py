import random

# -----------------------------
# CONFIGURACIÓN
# -----------------------------

rows, cols = 4, 4

start_state = (3, 0)
goal_state = (0, 3)
blocked_states = [(1, 2)]

actions = {
    "up": (-1, 0),
    "down": (1, 0),
    "left": (0, -1),
    "right": (0, 1)
}

alpha = 0.1
gamma = 0.9
epsilon = 0.2
episodes = 500

# -----------------------------
# ESTADOS
# -----------------------------

states = []
for r in range(rows):
    for c in range(cols):
        if (r, c) not in blocked_states:
            states.append((r, c))

# -----------------------------
# TRANSITIONS
# -----------------------------

transitions = {}

for state in states:
    transitions[state] = {}

    for action, (dr, dc) in actions.items():
        nr, nc = state[0] + dr, state[1] + dc
        next_state = (nr, nc)

        # Validación de límites y obstáculo
        if (
            nr < 0 or nr >= rows or
            nc < 0 or nc >= cols or
            next_state in blocked_states
        ):
            next_state = state  # se queda

        # Recompensas
        if next_state == goal_state:
            reward = 10
        elif next_state == state:
            reward = -2  # choque
        else:
            reward = -1  # movimiento normal

        transitions[state][action] = [(next_state, 1.0, reward)]

# -----------------------------
# Q-TABLE
# -----------------------------

Q = {}
for state in states:
    Q[state] = {}
    for action in actions:
        Q[state][action] = 0.0

# -----------------------------
# FUNCIONES
# -----------------------------

def step(state, action):
    next_state, prob, reward = transitions[state][action][0]
    return next_state, reward

def choose_action(state):
    if random.random() < epsilon:
        return random.choice(list(actions.keys()))
    return max(Q[state], key=Q[state].get)

def update_q(state, action, reward, next_state):
    best_future_q = max(Q[next_state].values())
    Q[state][action] += alpha * (
        reward + gamma * best_future_q - Q[state][action]
    )

# -----------------------------
# ENTRENAMIENTO
# -----------------------------

for ep in range(episodes):
    state = start_state

    while state != goal_state:
        action = choose_action(state)
        next_state, reward = step(state, action)

        update_q(state, action, reward, next_state)

        state = next_state

# -----------------------------
# RESULTADOS
# -----------------------------

print("\nQ-table final:\n")
for state in Q:
    print(state, Q[state])

print("\nPolítica aprendida:\n")
for state in states:
    best_action = max(Q[state], key=Q[state].get)
    print(state, "->", best_action)