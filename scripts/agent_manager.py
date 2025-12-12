from agent import Agent
import argparse 
import time
from multiprocessing import Process
from multiprocessing import Manager
from my_constants import *
import numpy as np

offsets = [(-1, -1), (0, -1), (1, -1), (-1, 0), (0, 0), (1, 0), (-1, 1), (0, 1), (1, 1),(-2, -2), (-1, -2), (0, -2), (1, -2), (2, -2), (-2, -1), (2, -1), (-2, 0), (2, 0), (-2, 1), ( 2, 1), (-2, 2), (-1, 2), (0, 2), (1, 2), (2, 2)]

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
    "FOUND": 2,
    "GOAL": 3,
    "FINISHED" : 4
}

class agent_manager:
    def __init__(self):
        self.map = None
        self.agents = []      

def run_agent(server_ip, keys, boxes):
    agent = Agent(server_ip)
    step = 0

    try:
        while True:
            step +=1
            # print("Agent ID:", agent.agent_id)
            agent.keys_found = []
            agent.boxes_found = []
            cmds = {}
            goal = False 
            for key in keys : 
                agent.keys_found.append(key["Position"])
            for box in boxes :
                agent.boxes_found.append(box["Position"])
            for key in keys:
                for box in boxes:
                    # print("key pos:", key["Position"], "box pos:", box["Position"])
                    if key["Id"] == box["Id"] and key["Position"] is not None and box["Position"] is not None and key["Id"]==agent.agent_id:
                        goal = True
                        key_pos = key["Position"]
                        box_pos = box["Position"]
                        # print("WE HAVE A GOAL at position:", key["Position"], box["Position"], "for robot ", key["Id"])
            if goal == False: 
                # Exploring the environment
                if agent.state == STATES["EXPLORING"]:
                    cmds['header'] = MOVE
                    cmds['direction'] = agent.explore()
                    agent.network.send(cmds)
                
                # Researching an unknown either a box or a key
                elif agent.state == STATES["RESEARCHING"]:
                    flag = False
                    for key,box in zip(keys,boxes) :
                        for offset in offsets : 
                            if key["Position"] is not None :
                                x_key, y_key = key["Position"][0], key["Position"][1]
                                x_offset, y_offset = offset[0], offset[1]
                                if (x_key + x_offset == agent.x and y_key + y_offset==agent.y):
                                    flag = True
                            if box["Position"] is not None :
                                x_box, y_box = box["Position"][0], box["Position"][1]
                                x_offset, y_offset = offset[0], offset[1]
                                if (x_box + x_offset == agent.x and y_box + y_offset == agent.y) :
                                    flag = True
                    if flag == False:               
                        cmds['header'] = MOVE
                        cmds['direction'] = agent.research()
                        agent.network.send(cmds)
                    else :
                        agent.state = STATES["EXPLORING"]

                # If we find something, we get the owner and the type of the item
                elif agent.state == STATES["FOUND"]:
                    cmds['header'] = GET_ITEM_OWNER
                    agent.network.send(cmds)
                    try :
                        while agent.msg.get("owner") is None:
                            time.sleep(0.1)
                        if agent.msg.get("type") == KEY_TYPE:
                            for key in keys:    
                                if key["Id"] == agent.msg.get("owner"):
                                    key["Position"] = (agent.x, agent.y)
                        elif agent.msg.get("type") == BOX_TYPE:
                            for box in boxes:
                                if box["Id"] == agent.msg.get("owner"):
                                    box["Position"] = (agent.x, agent.y)
                    except KeyError:
                        pass
                    agent.state = STATES["EXPLORING"]
                
            elif goal == True and agent.state != STATES["FINISHED"]:
                agent.state = STATES["GOAL"]
                agent.key_pos = key_pos
                agent.box_pos = box_pos
                cmds['header'] = MOVE
                cmds['direction'] = agent.goal()
                agent.network.send(cmds)
                
            elif goal == True and agent.state == STATES["FINISHED"]:
                print(f"The Agent {agent.agent_id} accomplished his mission in {step}")
                step -=1

            time.sleep(0.1)
    except KeyboardInterrupt:
        agent.running = False
        print(f"Agent {agent.agent_id} stopping...")

if __name__ == "__main__":
    server_ip = "localhost"
    
    manager = Manager()

    keys = manager.list([
        manager.dict({ "Id": 0, "Position": None}),
        manager.dict({ "Id": 1, "Position": None}),
        manager.dict({ "Id": 2, "Position": None}),
        manager.dict({ "Id": 3, "Position": None}),
    ])

    boxes = manager.list([
        manager.dict({ "Id": 0, "Position": None}),
        manager.dict({ "Id": 1, "Position": None}),
        manager.dict({ "Id": 2, "Position": None}),
        manager.dict({ "Id": 3, "Position": None}),
    ])

    n = int(input("Nombre d'agents à lancer: "))
    processes = []

    for i in range(n):
        p = Process(target=run_agent, args=(server_ip,keys,boxes))
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
