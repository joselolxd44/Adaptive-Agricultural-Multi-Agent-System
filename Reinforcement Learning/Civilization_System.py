from dataclasses import dataclass
from Agent_MDP_System import Agent

@dataclass
class Civilization:
    civilization_id: int
    population: int
    ai_agent: Agent
    food: 


def create_civilization(civilization_id, population, ai_agent):

    