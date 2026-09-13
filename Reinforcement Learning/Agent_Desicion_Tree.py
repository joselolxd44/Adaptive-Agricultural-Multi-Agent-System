import random
import csv
from dataclasses import dataclass, field
from typing import Dict, Tuple, List
from sklearn.tree import DecisionTreeRegressor
import pandas as pd
import Procedural_Seed_Evolution_System as seed_system
import math

Cell = Tuple[int, int]
rows, cols = 4, 4

start_state = (3, 0)
blocked_states = [(1, 2)]

actions = {
    "up": (-1, 0),
    "down": (1, 0),
    "left": (0, -1),
    "right": (0, 1),
    "cultivate": (0, 0)
}

states = [(r, c) for r in range(rows) for c in range(cols) if (r, c) not in blocked_states]



for r in range(rows):
    for c in range(cols):
        if (r, c) not in blocked_states:
            states.append((r, c))



transitions = {}


for state in states:
    transitions[state] = {}

    for action, (dr, dc) in actions.items():
        if action == "cultivate":
            transitions[state][action] = [
                (state, 1.0, 1000)
            ]
            continue
        else:
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
        

def get_QTable(rows,cols,states, blocked_states,actions):
    Q = {}
    for state in states:
        Q[state] = {}
        for action in actions:
            Q[state][action] = 0.0
                
    return Q
        

# =========================
# DATOS BASE
# =========================



@dataclass
class Civilization:
    position: tuple
    food: []
    seeds: List[seed_system.Seed]
    memory: Dict = field(default_factory=dict)
    alive: bool = True
    Qtable: Dict = field(default_factory=dict)
    calories: float = 0.0
    tension: float = 0.0
    population: int = 1


# =========================
# TABLERO
# =========================

def create_board(rows, cols):
    board = {}

    for r in range(rows):
        for c in range(cols):
            board[(r, c)] = {
                "height": random.uniform(0, 100)
            }

    return board


# =========================
# MEMORIA
# =========================



def init_memory(board):
    memory = {
        "cells": {},
        "varieties": {}
    }

    for cell in board:
        memory["cells"][cell] = {
            "known": False,
            "estimated_height": 0.0,
            "estimated_travel_cost": 0.0,
            "estimated_crop_reward": 0.0,  # ← AÑADE ESTA LÍNEA
            "confidence": 0.0,
            "visits": 0
        }

    return memory

def get_memory(civ, cell):
    """
    Obtiene la memoria para una celda específica.
    Si la celda no existe en la memoria, la inicializa.
    """
    # Asegurar que la estructura de memoria existe
    if "cells" not in civ.memory:
        civ.memory["cells"] = {}
    
    # Si la celda no existe, crearla con valores por defecto
    if cell not in civ.memory["cells"]:
        civ.memory["cells"][cell] = {
            "known": False,
            "estimated_height": 0.0,
            "estimated_travel_cost": 0.0,
            "estimated_crop_reward": 0.0,
            "confidence": 0.0,
            "visits": 0
        }
    
    return civ.memory["cells"][cell]

def update_memory_after_visit(civ, board, cell, travel_cost, crop_reward):
    # Usar get_memory en lugar de acceder directamente
    mem = get_memory(civ, cell)
    
    real_height = board[cell]["height"]
    mem["known"] = True
    mem["visits"] += 1
    mem["confidence"] = min(1.0, mem["visits"] / 5)

    lr = 1 / mem["visits"]

    mem["estimated_height"] += lr * (real_height - mem["estimated_height"])
    mem["estimated_travel_cost"] += lr * (travel_cost - mem["estimated_travel_cost"])
    mem["estimated_crop_reward"] += lr * (crop_reward - mem["estimated_crop_reward"])
# =========================
# FEATURES
# =========================

def action_to_id(action):
    return {
        "up": 0,
        "down": 1,
        "left": 2,
        "right": 3,
        "cultivate": 4
    }[action]

def empty_variety_memory():

    return {
        "attempts": 0,
        "avg_food": 0.0,
        "avg_calories": 0.0,
        "avg_children": 0.0,
        "success_rate": 0.0,
        "best_known_height": 0.0,
        "best_known_reward": 0.0,
        "prior_crop_reward": 10.0,
        "found_heights": [],
        "avg_found_heights": 0.0
    }

def get_variety_memory(civ, variety_id):

    if variety_id not in civ.memory["varieties"]:

        civ.memory["varieties"][variety_id] = (
            empty_variety_memory()
        )
        update_varieties_memory(civ)
        return civ.memory["varieties"][variety_id]
    return civ.memory["varieties"][variety_id]

def update_varieties_memory(civ):
    for seed in civ.seeds:
        for variety_id, variety_memory in civ.memory["varieties"].items():
            if seed.parentVariety.varietyID == variety_id:
                variety_memory["found_heights"].append(seed.originalHeight)
                variety_memory["avg_found_heights"] = sum(variety_memory["found_heights"]) / len(variety_memory["found_heights"])

    
def build_features_from_memory(civ, board, action):
    movements = {
        "up": (-1, 0),
        "down": (1, 0),
        "left": (0, -1),
        "right": (0, 1),
        "cultivate": (0, 0)
    }

    current_cell = civ.position
    dr, dc = movements[action]
    target_cell = (current_cell[0] + dr, current_cell[1] + dc)

    if target_cell not in board:
        target_cell = current_cell

    cell_memory = civ.memory["cells"][target_cell]

    # =========================
    # Q-TABLE COMO RIESGO
    # =========================
   
    
    Q_Value = civ.Qtable.get(current_cell, {}).get(action, 0.0)
    
    
    
    # =========================
    # MEMORIA DE VARIEDAD
    # =========================

    if len(civ.seeds) > 0:
        selected_seed = civ.seeds[0]
        original_height = selected_seed.originalHeight
        variety_id = selected_seed.parentVariety.varietyID
        has_seed = 1

        variety_memory = get_variety_memory(civ, variety_id)

    else:
        variety_id = -1
        has_seed = 0

        variety_memory = {
            "attempts": 0,
            
            "avg_calories": 0.0,
            "avg_children": 0.0,
            
            "best_known_height": 0.0,
            "best_known_reward": 0.0
        }

    # =========================
    # BENEFICIO PERCIBIDO DE PLANTAR
    # =========================

    if variety_memory["attempts"] > 0:
        estimated_crop_benefit = (
            variety_memory["avg_food"] * 2
            + variety_memory["avg_calories"] * 0.01
            + variety_memory["avg_children"] * 5
        )

        distance_to_best_known_height = abs(
            cell_memory["estimated_height"]
            - variety_memory["best_known_height"]
        )

    else:
        estimated_crop_benefit = 0.0
        distance_to_best_known_height = 999.0

    return {
        # Estado general
        "food": civ.food,
        "calories": civ.calories,
        "seed_count": len(civ.seeds),
        "has_seed": has_seed,

        # Memoria de celda
        "cell_known": int(cell_memory["known"]),
        "estimated_height": cell_memory["estimated_height"],
        
        "cell_visits": cell_memory["visits"],

        # Q-table / riesgo espacial
        "estimated_travel_cost": Q_Value,
        

        # Memoria de variedad
        "variety_id": variety_id,
        "variety_attempts": variety_memory["attempts"],
        
        "variety_avg_calories": variety_memory["avg_calories"],
        "variety_avg_children": variety_memory["avg_children"],
        
        "variety_best_known_height": variety_memory["best_known_height"],
        "variety_best_known_reward": variety_memory["best_known_reward"],

        # Pensamiento agrícola estimado
        "estimated_crop_benefit": estimated_crop_benefit,
        "distance_to_best_known_height": distance_to_best_known_height,

        # Acción candidata
        "action_id": action_to_id(action)
    }


# =========================
# SIMULADOR REAL
# =========================

def simulate_seed_result(seed, height, heightMetrics):
    seeds=[]
    food=[]
    
    seeds, food=seed_system.seedReproduction(heightMetrics, seed, height)
    return seeds, food

def update_q_table(civ, state, action, travel_reward, next_state, alpha=0.2, gamma=0.9):
    if state not in civ.Qtable:
        civ.Qtable[state] = {}

    if next_state not in civ.Qtable:
        civ.Qtable[next_state] = {}

    for a in ["up", "down", "left", "right"]:
        civ.Qtable[state].setdefault(a, 0.0)
        civ.Qtable[next_state].setdefault(a, 0.0)

    old_q = civ.Qtable[state][action]
    best_next_q = max(civ.Qtable[next_state].values())

    civ.Qtable[state][action] = old_q + alpha * (
        travel_reward + gamma * best_next_q - old_q
    )

def step(state,action):
    posible_results=transitions[state][action]
    
    cumulative_prob=0.0
    rand=random.random()
    
    for next_state, prob, travel_cost in posible_results:
        cumulative_prob+=prob
        
        if rand<cumulative_prob:
            return next_state, travel_cost

def execute_move(civ,board, action):
    current_cell = civ.position

    target_cell, travel_cost=step(civ.position,action)
    
    
    
    if target_cell == current_cell:
        travel_cost *= 1.5
    update_q_table(civ, current_cell, action, -travel_cost, target_cell)
    
    civ.position = target_cell
    civ.calories -= travel_cost

    if civ.calories <= 0:
        civ.alive = False
        return -100, target_cell, travel_cost, 0

    return -travel_cost, target_cell, travel_cost, 0


def execute_cultivate(civ, board,heightMetrics):
    if len(civ.seeds) == 0:
        civ.calories -= 5
        return -30, civ.position, 0, 0

    food=[]
    seed = civ.seeds.pop(0)
    height = board[civ.position]["height"]

    new_seeds, food = simulate_seed_result(seed, height, heightMetrics)

    civ.food.extend(food)
    civ.calories = sum(f.calories for f in civ.food)
    civ.seeds.extend(new_seeds)

    reward = (
        sum(f.calories for f in food) * 0.01
        + len(new_seeds) * 5
    )

    if len(food) == 0:
        reward -= 15

    if len(new_seeds) == 0:
        reward -= 5

    if civ.calories <= 0:
        civ.alive = False
        reward -= 100

    return reward, civ.position, 0, reward


def execute_action(civ, board, action, heightMetrics):
    if action == "cultivate":
        return execute_cultivate(civ, board, heightMetrics)

    return execute_move(civ, board, action)


# =========================
# GENERAR DATASET
# =========================

def generate_dataset(filename, episodes=200, turns=50):
    board = create_board(4, 4)

    rows = []

    actions = ["up", "down", "left", "right", "cultivate"]

    for _ in range(episodes):
        initial_seed = Seed(
            variety_id=1,
            influenceShot=1.0,
            chaos=0.0,
            mutability=0.0,
            minHeightZone=10,
            maxHeightZone=50,
            kcal_base=100,
            food_base_amount=5
        )

        civ = Civilization(
            position=(3, 0),
            food=50,
            seeds=[initial_seed]
        )

        civ.memory = init_memory(board)
        civ.memory[civ.position]["known"] = True
        civ.memory[civ.position]["estimated_height"] = board[civ.position]["height"]

        for _ in range(turns):
            if not civ.alive:
                break

            action = random.choice(actions)

            features_before = build_features_from_memory(civ, board, action)

            reward, reached_cell, travel_cost, crop_reward = execute_action(civ, board, action)

            update_memory_after_visit(
                civ,
                board,
                reached_cell,
                travel_cost,
                crop_reward
            )

            features_before["reward"] = reward
            rows.append(features_before)

    with open(filename, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


# =========================
# ENTRENAR ÁRBOL
# =========================

def train_tree(filename):
    data = pd.read_csv(filename)

    X = data.drop(columns=["reward"])
    y = data["reward"]

    model = DecisionTreeRegressor(
        max_depth=6,
        random_state=42
    )

    model.fit(X, y)

    return model


def predict_q(
    model,
    features
):
    if model is None:
        return 0.0

    X = pd.DataFrame([features])

    return model.predict(X)[0]

def calculate_tension(civ):
    calories_needed = civ.population * 1000

    ratio = sum(f.calories for f in civ.food) / calories_needed

    tension = 1 / (1 + math.exp(6 * (ratio - 1)))

    return tension
def calculate_dynamic_parameters(tension):
    gamma_min = 0.35
    gamma_max = 0.95

    beta_crop_min = 1.0
    beta_crop_max = 6.0

    beta_risk_min = 1.0
    beta_risk_max = 6.0

    gamma = gamma_max - (gamma_max - gamma_min) * tension

    beta_crop = (beta_crop_max - beta_crop_min) * tension

    beta_risk = (beta_risk_max - beta_risk_min) * (1-tension)

    return gamma, beta_crop, beta_risk

def calculate_final_q(
    civ,
    crop_reward,
    travel_cost_q,
    future_q,
    tension
):
    # Evitar división por cero
    current_food = max(civ.calories, 1.0)
    
    # ==========================================
    # NORMALIZACIÓN BASADA EN COMIDA ACTUAL
    # ==========================================
    
    # Cuánta comida necesitas para sobrevivir (población * necesidad por turno)
    food_need = civ.population * 1000
    
    # Ratio de necesidad (0 = mucha comida, 1 = hambre extrema)
    need_ratio = max(0, min(1, 1 - (current_food / food_need)))
    
    # Para valores pequeños, usaré una normalización que ESCALA con necesidad
    # Cuanto más hambre, más valioso es CADA punto de crop_reward
    
    # ==========================================
    # CROP REWARD: BENEFICIO EXPONENCIAL CON HAMBRE
    # ==========================================
    
    # Normalizar crop_reward relativo a la necesidad
    # Si crop_reward cubre toda la necesidad → valor alto
    crop_coverage = crop_reward / (food_need + 1)
    
    # EXPONENCIAL: cuando hay hambre (need_ratio alto), el valor explota
    # Usamos e^(need_ratio * 5) - 1 para que con need_ratio=1 dé factor ~147
    hunger_crop_multiplier = math.exp(need_ratio * 5) - 1
    
    # Valor final del crop: coverage * multiplicador de hambre
    # Si no hay hambre (need_ratio≈0) → valor normal
    # Si hay hambre y crop_reward es alto → valor BESTIAL
    crop_value = crop_coverage * (1 + hunger_crop_multiplier)
    
    # ==========================================
    # TRAVEL COST: PENALIZACIÓN QUE AUMENTA CON HAMBRE
    # ==========================================
    
    # Abs para asegurar positivo
    travel_abs = abs(travel_cost_q)
    
    # Normalizar travel cost relativo a la comida actual
    # Si tienes poca comida, viajar duele más
    travel_impact = travel_abs / (current_food + 100)
    
    # Multiplicador: con hambre, cada caloría perdida duele EXPONENCIALMENTE más
    hunger_travel_multiplier = math.exp(need_ratio * 3)  # Con need_ratio=1 → factor ~20
    
    travel_penalty = travel_impact * (1 + hunger_travel_multiplier)
    
    # ==========================================
    # FUTURE Q: DESCONTADO POR HAMBRE
    # ==========================================
    
    # Con hambre, el futuro vale MENOS (necesitas comida AHORA)
    future_discount = math.exp(-need_ratio * 4)  # Con need_ratio=1 → factor ~0.018
    
    # Asumiendo que future_q ya está en escala de Q (no calorías)
    # Lo normalizamos con tanh para mantener rango
    future_normalized = math.tanh(future_q / 100)  # Asumiendo que future_q típico entre -1000 y 1000
    future_value = future_normalized * future_discount
    
    # ==========================================
    # Q FINAL
    # ==========================================
    
    if travel_cost_q == 0:  # Es cultivar
        q_final = crop_value + future_value * 0.3  # El futuro importa poco cuando cultivas
    else:  # Es movimiento
        q_final = future_value - travel_penalty
    
    return q_final

def estimate_crop_reward(civ, variety_memory):
    attempts = variety_memory["attempts"]

    prior_reward = variety_memory["estimated_crop_reward"]

    observed_reward = (
        variety_memory["avg_food"] * 2
        + variety_memory["avg_calories"] * 0.01
        + variety_memory["avg_children"] * 10
    )

    confidence = attempts / (attempts + 5)
    estimated_optimal_distance= abs(civ.memory["cells"][civ.position]["estimated_height"]-variety_memory["avg_found_heights"])
    
    estimated_crop_reward = (
        (1 - confidence) * prior_reward
        + confidence * observed_reward + 
        ((1 + estimated_optimal_distance)) * 10
        
    )

    return estimated_crop_reward

def choose_action_with_q_tree(civ,board,model,epsilon=0.2):
    actions = ["up","down","left","right","cultivate"]

    # =========================
    # EXPLORATION
    # =========================
    civ.tension = calculate_tension(civ)
    
    if random.random() > civ.tension:
        return random.choice(actions)

    # =========================
    # EXPLOITATION
    # =========================

    best_action = None

    best_q = float("-inf")

    for action in actions:

        features = build_features_from_memory(civ,board,action)

        predicted_q = predict_q(model,features)
        
        travel_cost_q = civ.Qtable.get(civ.position, {}).get(action, 0.0)
        
        crop_reward= estimate_crop_reward(civ,get_variety_memory(civ, features["variety_id"]))
        
        
        QValue=calculate_final_q(civ,crop_reward, travel_cost_q, predicted_q, civ.tension)

        if QValue > best_q:

            best_q = QValue

            best_action = action

    return best_action

def choose_action_with_tree(civ, board, tree_model):
    actions = ["up", "down", "left", "right", "cultivate"]

    best_action = None
    best_score = float("-inf")

    for action in actions:
        features = build_features_from_memory(civ, board, action)

        X = pd.DataFrame([features])

        predicted_reward = tree_model.predict(X)[0]
        if action == "cultivate":
            q_risk = 0
        else:
            q_risk = civ.Qtable.get(state, {}).get(action, 0)
            
        predicted_reward += q_risk
        
        if predicted_reward > best_score:
            best_score = predicted_reward
            best_action = action

    return best_action

def best_future_q(
    civ,
    board,
    model
):
    actions = [
        "up",
        "down",
        "left",
        "right",
        "cultivate"
    ]

    if model is None:
        return 0.0

    values = []

    for action in actions:

        features = build_features_from_memory(
            civ,
            board,
            action
        )

        values.append(
            predict_q(
                model,
                features
            )
        )

    return max(values)


def analyze_environment(civ, board):
    for action in actions:
        target_cell, travel_cost = step(civ.position, action)
        if target_cell == civ.position and action != "cultivate":
            travel_cost *= 1.5
            dr, dc = actions[action]
            target_cell = (civ.position[0] + dr, civ.position[1] + dc)
            update_q_table(civ, civ.position, action, -travel_cost, target_cell)
            continue

        if target_cell in board:
            
            cell_memory = get_memory(civ, target_cell)
            
            if not cell_memory["known"]:
                cell_memory["estimated_height"] = board[target_cell]["height"] * random.uniform(0.8, 1.2)
                
            if target_cell == civ.position:
                cell_memory["known"] = True
                cell_memory["estimated_height"] = board[target_cell]["height"]
                
            else:
                update_q_table(civ, civ.position, action, -travel_cost, target_cell)

# =========================
# TEST
# =========================


# =========================================================
# TRAIN TREE
# =========================================================

def train_q_tree(
    experiences
):
    if len(experiences) < 20:
        return None

    data = pd.DataFrame(experiences)

    X = data.drop(
        columns=["target_q"]
    )

    y = data["target_q"]

    model = DecisionTreeRegressor(
        max_depth=6,
        random_state=42
    )

    model.fit(X, y)

    return model


# =========================================================
# MAIN RL LOOP
# =========================================================

def run_q_tree_rl_simulation():

    board = create_board(4, 4)
    
    heightMetrics=seed_system.generateHeightMetrics()

    seed = seed_system.setPrimalSeed(30,heightMetrics.varieties[0])
    

    civ = Civilization(
        position=(3, 0),
        food=seed_system.generateRandomFood(20),
        population=50,
        seeds=[seed],
        Qtable=get_QTable(rows, cols, states, blocked_states, actions)
    )
    civ.calories = sum(f.calories for f in civ.food)
    print(" Calories:", civ.calories)
    civ.tension = calculate_tension(civ)

    civ.memory = init_memory(board)

    # Usar get_memory en lugar de acceso directo
    current_mem = get_memory(civ, civ.position)
    (reward, reached_cell, travel_cost,  crop_reward ) = execute_cultivate(civ, board, heightMetrics)
    
    
    
    experiences = []

    model = None
    

    gamma = 0.9

    epsilon = 0.2

    for turn in range(200):
        
        if not civ.alive:
            break
        

        # =====================
        # ACTION
        # =====================
        
        analyze_environment(civ, board)
    

        action = choose_action_with_q_tree(
            civ,
            board,
            model,
            epsilon
        )
        print(" Calories:", civ.calories)
        

        # =====================
        # OLD FEATURES
        # =====================

        old_features = build_features_from_memory(
            civ,
            board,
            action
        )
        print(" Calories:", civ.calories)
        

        # =====================
        # EXECUTE
        # =====================

        (
            reward,
            reached_cell,
            travel_cost,
            crop_reward
        ) = execute_action(
            civ,
            board,
            action,
            heightMetrics
        )
        print(" Calories:", civ.calories)
        

        # =====================
        # UPDATE MEMORY
        # =====================

        update_memory_after_visit(
            civ,
            board,
            reached_cell,
            travel_cost,
            crop_reward
        )
        print(
            "Turn:", turn,
            "| Pos:", civ.position,
            "| Food:", round(civ.calories, 2),
            "| Seeds:", len(civ.seeds),
            "| Action:", action,
            "| Reward:", round(reward, 2),
            "| CropReward:", round(crop_reward, 2)
        )

        # =====================
        # FUTURE Q
        # =====================

        future_q = best_future_q(
            civ,
            board,
            model
        )  

        # =====================
        # BELLMAN
        # =====================

        target_q = (
            reward + crop_reward
            + gamma * future_q
        )

        # =====================
        # EXPERIENCE
        # =====================

        old_features["target_q"] = target_q

        experiences.append(
            old_features
        )

        # =====================
        # TRAIN
        # =====================

        model = train_q_tree(
            experiences
        )

        # =====================
        # DEBUG
        # =====================

        print(
            "Turn:", turn,
            "| Pos:", civ.position,
            "| Food:", round(civ.calories, 2),
            "| Seeds:", len(civ.seeds),
            "| Action:", action,
            "| Reward:", round(reward, 2),
            "| TargetQ:", round(target_q, 2)
        )


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    run_q_tree_rl_simulation()