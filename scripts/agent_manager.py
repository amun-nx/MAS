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
    "KEY_NBOX": 5
}

class agent_manager:
    def __init__(self):
        self.map = None
        self.agents = []


    
    def receive_data():
        pass

    def send_commands():
        pass

def run_agent(server_ip):
    agent = Agent(server_ip)
    try:
        while True:
            cmds = {}
            if agent.state == STATES["EXPLORING"]:
                cmds['header'] = MOVE
                cmds['direction'] = agent.explore()
                agent.network.send(cmds)
            elif agent.state == STATES["RESEARCHING"]:
                cmds['header'] = MOVE
                cmds['direction'] = agent.research()
            # elif agent.state == STATES["FOUND_KEY"]:
            #     cmds['header'] = BROADCAST_MSG
            #     cmds["Msg type"] = KEY_DISCOVERED
            #     cmds["position"] = (agent.x, agent.y)
            #     cmds["owner"] = np.random.randint(0,3) # TODO: specify the owner of the item
            #     agent.network.send(cmds)
            # elif agent.state == STATES["FOUND_BOX"]:
            #     cmds['header'] = BROADCAST_MSG
            #     cmds["Msg type"] = BOX_DISCOVERED
            #     cmds["position"] = (agent.x, agent.y)
            #     cmds["owner"] = np.random.randint(0,3) # TODO: specify the owner of the item
            #     agent.network.send(cmds)
            # if 'cell_val' in agent.msg:
            #     print(agent.msg['cell_val'])
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
