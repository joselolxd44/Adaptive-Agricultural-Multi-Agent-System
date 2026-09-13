import random
from dataclasses import dataclass, field
from typing import Dict, Tuple, List

import pandas as pd
from sklearn.tree import DecisionTreeRegressor

Cell = Tuple[int, int]


# =========================================================
# SEED
# =========================================================

@dataclass
class Seed:
    variety_id: int

    # SOLO EL SIMULADOR CONOCE ESTO
    influenceShot: float
    chaos: float
    mutability: float

    minHeightZone: float
    maxHeightZone: float

    kcal_base: float
    food_base_amount: int


# =========================================================
# CIVILIZATION
# =========================================================

@dataclass
class Civilization:
    position: Cell
    food: float
    seeds: List[Seed]

    memory: Dict = field(default_factory=dict)

    alive: bool = True


# =========================================================
# BOARD
# =========================================================

def create_board(rows, cols):
    board = {}

    for r in range(rows):
        for c in range(cols):
            board[(r, c)] = {
                "height": random.uniform(0, 100)
            }

    return board


# =========================================================
# MEMORY
# =========================================================

def empty_variety_memory():
    return {
        "attempts": 0,
        "avg_food": 0.0,
        "avg_calories": 0.0,
        "avg_children": 0.0,
        "success_rate": 0.0,
        "best_known_height": 0.0,
        "best_known_reward": 0.0
    }


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
            "confidence": 0.0,
            "visits": 0
        }

    return memory


def get_variety_memory(civ, variety_id):
    if variety_id not in civ.memory["varieties"]:
        civ.memory["varieties"][variety_id] = empty_variety_memory()

    return civ.memory["varieties"][variety_id]


# =========================================================
# UPDATE MEMORY
# =========================================================

def update_memory_after_visit(
    civ,
    board,
    cell,
    travel_cost
):
    real_height = board[cell]["height"]

    mem = civ.memory["cells"][cell]

    mem["known"] = True
    mem["visits"] += 1

    mem["confidence"] = min(
        1.0,
        mem["visits"] / 5
    )

    lr = 1 / mem["visits"]

    mem["estimated_height"] += lr * (
        real_height - mem["estimated_height"]
    )

    mem["estimated_travel_cost"] += lr * (
        travel_cost - mem["estimated_travel_cost"]
    )


def update_variety_memory(
    civ,
    seed,
    height,
    food_amount,
    calories,
    children_count,
    reward
):
    mem = get_variety_memory(
        civ,
        seed.variety_id
    )

    mem["attempts"] += 1

    n = mem["attempts"]

    lr = 1 / n

    mem["avg_food"] += lr * (
        food_amount - mem["avg_food"]
    )

    mem["avg_calories"] += lr * (
        calories - mem["avg_calories"]
    )

    mem["avg_children"] += lr * (
        children_count - mem["avg_children"]
    )

    success = 1 if food_amount > 0 else 0

    mem["success_rate"] += lr * (
        success - mem["success_rate"]
    )

    if reward > mem["best_known_reward"]:
        mem["best_known_reward"] = reward
        mem["best_known_height"] = height


# =========================================================
# ACTION ID
# =========================================================

def action_to_id(action):
    return {
        "up": 0,
        "down": 1,
        "left": 2,
        "right": 3,
        "cultivate": 4
    }[action]


# =========================================================
# BUILD FEATURES
# =========================================================

def build_features_from_memory(
    civ,
    board,
    action
):
    movements = {
        "up": (-1, 0),
        "down": (1, 0),
        "left": (0, -1),
        "right": (0, 1),
        "cultivate": (0, 0)
    }

    current_cell = civ.position

    dr, dc = movements[action]

    target_cell = (
        current_cell[0] + dr,
        current_cell[1] + dc
    )

    if target_cell not in board:
        target_cell = current_cell

    cell_memory = civ.memory["cells"][target_cell]

    # =====================================
    # SEED MEMORY
    # =====================================

    if len(civ.seeds) > 0:

        seed = civ.seeds[0]

        variety_id = seed.variety_id

        variety_memory = get_variety_memory(
            civ,
            variety_id
        )

        has_seed = 1

    else:

        variety_id = -1

        variety_memory = empty_variety_memory()

        has_seed = 0

    # =====================================
    # DISTANCE TO BEST KNOWN HEIGHT
    # =====================================

    if variety_memory["attempts"] > 0:

        distance_to_best_known_height = abs(
            cell_memory["estimated_height"]
            - variety_memory["best_known_height"]
        )

    else:

        distance_to_best_known_height = 999

    return {

        # =============================
        # GENERAL
        # =============================

        "food": civ.food,
        "seed_count": len(civ.seeds),
        "has_seed": has_seed,

        # =============================
        # CELL MEMORY
        # =============================

        "cell_known": int(
            cell_memory["known"]
        ),

        "estimated_height":
            cell_memory["estimated_height"],

        "estimated_travel_cost":
            cell_memory["estimated_travel_cost"],

        "cell_confidence":
            cell_memory["confidence"],

        "cell_visits":
            cell_memory["visits"],

        # =============================
        # VARIETY MEMORY
        # =============================

        "variety_id":
            variety_id,

        "variety_attempts":
            variety_memory["attempts"],

        "variety_avg_food":
            variety_memory["avg_food"],

        "variety_avg_calories":
            variety_memory["avg_calories"],

        "variety_avg_children":
            variety_memory["avg_children"],

        "variety_success_rate":
            variety_memory["success_rate"],

        "variety_best_known_height":
            variety_memory["best_known_height"],

        "variety_best_known_reward":
            variety_memory["best_known_reward"],

        # =============================
        # ECOLOGICAL ESTIMATION
        # =============================

        "distance_to_best_known_height":
            distance_to_best_known_height,

        # =============================
        # ACTION
        # =============================

        "action_id":
            action_to_id(action)
    }


# =========================================================
# REAL SIMULATION
# =========================================================

def seed_height_distance(seed, height):

    if height < seed.minHeightZone:
        return seed.minHeightZone - height

    if height > seed.maxHeightZone:
        return height - seed.maxHeightZone

    return 0.0


def simulate_seed_result(seed, height):

    distance = seed_height_distance(
        seed,
        height
    )

    adaptation = 1 / (
        1 + distance * 0.05
    )

    noise = (
        random.uniform(-1, 1)
        * seed.chaos
    )

    food_amount = round(
        seed.food_base_amount
        * adaptation
        * (1 + noise * 0.3)
    )

    calories = (
        seed.kcal_base
        * adaptation
        * (1 + noise * 0.2)
    )

    food_amount = max(
        0,
        food_amount
    )

    calories = max(
        0,
        calories
    )

    children_count = random.randint(
        0,
        2
    )

    return (
        food_amount,
        calories,
        children_count
    )


# =========================================================
# EXECUTE MOVE
# =========================================================

def execute_move(
    civ,
    board,
    action
):
    movements = {
        "up": (-1, 0),
        "down": (1, 0),
        "left": (0, -1),
        "right": (0, 1)
    }

    current_cell = civ.position

    dr, dc = movements[action]

    target_cell = (
        current_cell[0] + dr,
        current_cell[1] + dc
    )

    if target_cell not in board:

        civ.food -= 10

        return (
            -20,
            current_cell,
            10,
            0
        )

    current_height = board[current_cell]["height"]

    target_height = board[target_cell]["height"]

    height_diff = abs(
        target_height - current_height
    )

    travel_cost = (
        1 + height_diff * 0.15
    )

    fail_probability = min(
        0.6,
        height_diff * 0.01
    )

    # =========================
    # FAIL
    # =========================

    if random.random() < fail_probability:

        civ.food -= (
            travel_cost * 1.5
        )

        if civ.food <= 0:

            civ.alive = False

            return (
                -100,
                current_cell,
                travel_cost,
                0
            )

        return (
            -10 - travel_cost,
            current_cell,
            travel_cost,
            0
        )

    # =========================
    # SUCCESS
    # =========================

    civ.position = target_cell

    civ.food -= travel_cost

    if civ.food <= 0:

        civ.alive = False

        return (
            -100,
            target_cell,
            travel_cost,
            0
        )

    return (
        -travel_cost,
        target_cell,
        travel_cost,
        0
    )


# =========================================================
# EXECUTE CULTIVATE
# =========================================================

def execute_cultivate(
    civ,
    board
):
    if len(civ.seeds) == 0:

        civ.food -= 5

        return (
            -30,
            civ.position,
            0,
            0
        )

    seed = civ.seeds.pop(0)

    height = board[civ.position]["height"]

    (
        food_amount,
        calories,
        children_count
    ) = simulate_seed_result(
        seed,
        height
    )

    civ.food += food_amount

    for _ in range(children_count):

        child = Seed(
            variety_id=seed.variety_id,

            influenceShot=max(
                0,
                min(
                    1,
                    seed.influenceShot
                    + random.uniform(-0.1, 0.1)
                )
            ),

            chaos=max(
                0,
                min(
                    1,
                    seed.chaos
                    + random.uniform(-0.1, 0.1)
                )
            ),

            mutability=seed.mutability,

            minHeightZone=seed.minHeightZone,
            maxHeightZone=seed.maxHeightZone,

            kcal_base=seed.kcal_base,

            food_base_amount=
                seed.food_base_amount
        )

        civ.seeds.append(child)

    reward = (
        food_amount * 2
        + calories * 0.01
        + children_count * 5
    )

    if food_amount == 0:
        reward -= 15

    if children_count == 0:
        reward -= 5

    if civ.food <= 0:

        civ.alive = False

        reward -= 100

    update_variety_memory(
        civ,
        seed,
        height,
        food_amount,
        calories,
        children_count,
        reward
    )

    return (
        reward,
        civ.position,
        0,
        reward
    )


# =========================================================
# EXECUTE ACTION
# =========================================================

def execute_action(
    civ,
    board,
    action
):
    if action == "cultivate":
        return execute_cultivate(
            civ,
            board
        )

    return execute_move(
        civ,
        board,
        action
    )


# =========================================================
# PREDICT Q
# =========================================================

def predict_q(
    model,
    features
):
    if model is None:
        return 0.0

    X = pd.DataFrame([features])

    return model.predict(X)[0]


# =========================================================
# CHOOSE ACTION
# =========================================================

def choose_action_with_q_tree(
    civ,
    board,
    model,
    epsilon=0.2
):
    actions = [
        "up",
        "down",
        "left",
        "right",
        "cultivate"
    ]

    # =========================
    # EXPLORATION
    # =========================

    if random.random() < epsilon:
        return random.choice(actions)

    # =========================
    # EXPLOITATION
    # =========================

    best_action = None

    best_q = float("-inf")

    for action in actions:

        features = build_features_from_memory(
            civ,
            board,
            action
        )

        predicted_q = predict_q(
            model,
            features
        )

        if predicted_q > best_q:

            best_q = predicted_q

            best_action = action

    return best_action


# =========================================================
# FUTURE Q
# =========================================================

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

    seed = Seed(
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
        seeds=[seed]
    )

    civ.memory = init_memory(board)

    civ.memory["cells"][civ.position]["known"] = True

    civ.memory["cells"][civ.position][
        "estimated_height"
    ] = board[civ.position]["height"]

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

        action = choose_action_with_q_tree(
            civ,
            board,
            model,
            epsilon
        )

        # =====================
        # OLD FEATURES
        # =====================

        old_features = build_features_from_memory(
            civ,
            board,
            action
        )

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
            action
        )

        # =====================
        # UPDATE MEMORY
        # =====================

        update_memory_after_visit(
            civ,
            board,
            reached_cell,
            travel_cost
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
            "| Food:", round(civ.food, 2),
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