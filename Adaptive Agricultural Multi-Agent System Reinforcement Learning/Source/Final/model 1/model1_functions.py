from __future__ import annotations
from typing import TYPE_CHECKING



    
import gc
import random
import csv
import copy
import math
import sys

from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Tuple, List

import pandas as pd

# Add Final/ to Python path
sys.path.append(
    str(Path(__file__).resolve().parent.parent)
)
import markov 
import Procedural_Seed_Evolution_System as seed_system
import DataMapLoad as map_loader
import base_agent
import Visualizer as visual

CALORIES_PER_PERSON = 2000
BETA= 0.6
ALPHA=0.6
GAMMA=0.6
@dataclass
class cell:
    height: float
    








def can_reproduce(com: base_agent.Community, civ: base_agent.Civilization):
    if com.calories>100000 and len(com.food)>200 and com.population>1000 and civ.cantCommunities<6: return True
    return False
    
def community_reproduction(com: base_agent.Community, civ: base_agent.Civilization):
    
    if(can_reproduce(com, civ)):
        son=base_agent.init_Community_from_parent(com)
        civ.add_community(son)
        print("Community has been split")
        return True
    


                            
    



def main():
    
   #GENERAL
    states=map_loader.generate_grid()
    visualizer = visual.SimulationVisualizer(states)
    civilization=base_agent.Civilization()
    heightMetrics=seed_system.generateHeightMetrics()

    with open("agent_learning_seed_data.csv", "w", newline="") as csvFile:
        writer = csv.writer(csvFile)

        for j in range(100):
            visits = {}
            n=0
            
            seed_system.writeSeedCSVHeader(writer)
            
            civilization.initialization(states)
            
            for i in range(1000):
                
                #GENERAL
                current_actions={}
                rewards=[]
                for com in civilization.communities:
                    
                    #MARKOV PROCESS
                    reward=0
                    action= markov.markov_process(com,states,heightMetrics,writer,reward)
                    
                    
                    #VISUALIZER
                    visits[com.position] = visits.get(com.position, 0) + 1
                    current_actions[com.id] = {"action": action,"reward": reward}
                    rewards.append(reward)
                    
                    
                    if(base_agent.is_community_dead(com)):
                        civilization.community_elimination(com,i,map_loader,states,visits)
                        break 
                        
                        
                    base_agent.community_maintenance(com)
                    base_agent.community_increment(com)
                    community_reproduction(com, civilization)
                    base_agent.food_storage(com)
                    
                    base_agent.iteration_printing(com,i,action,reward)
                    n=i
                #for each 10 iterations the visualzier changesS
                if i % 10 == 0:
                    visualizer.draw(
                        civilization,
                        i,
                        visits,
                        rewards,
                        current_actions
                    )
                
            if n>995:
                map_loader.visualizar_mapa_concurrencia(states,visits)
                break
            
        base_agent.print_varieties_memory(com)
        base_agent.print_Qvalues(com)
        
        map_loader.visualizar_mapa_concurrencia(states,visits)
        
    
    
    

if __name__ == "__main__":
    main()
    
    