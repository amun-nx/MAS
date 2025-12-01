from agent import Agent
import argparse 
import time
from multiprocessing import Process
from my_constants import *
import numpy as np


DIRECTIONS = {
    LEFT:      (-1,  0),
    RIGHT:     ( 1,  0),
    UP:        ( 0, -1),
    DOWN:      ( 0,  1),
    UP_LEFT:   (-1, -1),
    UP_RIGHT:  ( 1, -1),
    DOWN_LEFT: (-1,  1),
    DOWN_RIGHT:( 1,  1)
}

STATES = {
    "EXPLORING": 0,
    "RESEARCHING": 1,
    "FOUND_KEY": 2,
    "FOUND_BOX": 3,
    "BOX_NKEY": 4,
    "KEY_NBOX": 5,
    "GOAL": 6
}

class agent_manager:
    def __init__(self):
        self.map = None
        self.agents = []      

def run_agent( server_ip):
    agent = Agent(server_ip)
    keys = [{ "Id": 0, "Position": None},
            { "Id": 1, "Position": None},
            { "Id": 2, "Position": None},
            { "Id": 3, "Position": None}]
    
    boxes = [{ "Id": 0, "Position": None,},
                { "Id": 1, "Position": None,},
                { "Id": 2, "Position": None,},
                { "Id": 3, "Position": None,}]

    try:
        while True:
            cmds = {}
            goal = False 
            for key in keys:
                for box in boxes:
                    if key["Id"] == box["Id"] and key["Position"] is not None and box["Position"] is not None:
                        goal = True
            if goal == False: 
                print("agent id",agent.agent_id,"agent state:", agent.state)
                if agent.state == STATES["EXPLORING"]:
                    cmds['header'] = MOVE
                    cmds['direction'] = agent.explore()
                    agent.network.send(cmds)
                elif agent.state == STATES["RESEARCHING"]:
                    cmds['header'] = MOVE
                    cmds['direction'] = agent.research()
                    agent.network.send(cmds)
                elif agent.state == STATES["FOUND_KEY"]:
                    cmds['header'] = GET_ITEM_OWNER
                    agent.network.send(cmds)
                    for key in keys:
                        try :
                            while agent.msg["Owner"] is None:
                                time.sleep(0.1)
                            if key["Id"] == agent.msg["owner"]:
                                key["Position"] = (agent.x, agent.y)
                        except KeyError:
                            pass
                    agent.state = STATES["EXPLORING"]
                elif agent.state == STATES["FOUND_BOX"]:
                    cmds['header'] = GET_ITEM_OWNER
                    agent.network.send(cmds)
                    try : 
                        for box in boxes:
                            while agent.msg["Owner"] is None:
                                time.sleep(0.1)
                            if box["Id"] == agent.msg["owner"]:
                                box["Position"] = (agent.x, agent.y)
                    except KeyError:
                        pass
                    agent.state = STATES["EXPLORING"]
            else : 
                agent.state = STATES["GOAL"]
                print("ON A UN GOAL")

            time.sleep(0.3)
    except KeyboardInterrupt:
        agent.running = False
        print(f"Agent {agent.agent_id} stopping...")

if __name__ == "__main__":
    server_ip = "localhost"
    n = int(input("Nombre d'agents à lancer: "))
    processes = []

    for i in range(n):
        p = Process(target=run_agent, args=(server_ip,))
        p.start()
        processes.append(p)

    try:
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        print("Stopping all agents...")
        for p in processes:
            p.terminate()
            p.join()
