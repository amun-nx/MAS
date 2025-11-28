__author__ = "Aybuke Ozturk Suri, Johvany Gustave"
__copyright__ = "Copyright 2023, IN512, IPSA 2024"
__credits__ = ["Aybuke Ozturk Suri", "Johvany Gustave"]
__license__ = "Apache License 2.0"
__version__ = "1.0.0"

from network import Network
from my_constants import *

from threading import Thread
import numpy as np
from time import sleep

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

class Agent:
    """ Class that implements the behaviour of each agent based on their perception and communication with other agents """
    def __init__(self, server_ip):

        #DO NOT TOUCH THE FOLLOWING INSTRUCTIONS
        self.network = Network(server_ip=server_ip)
        self.agent_id = self.network.id
        self.running = True
        self.network.send({"header": GET_DATA})
        self.msg = {}
        env_conf = self.network.receive()
        self.nb_agent_expected = 0
        self.nb_agent_connected = 0
        self.x, self.y = env_conf["x"], env_conf["y"]   #initial agent position
        self.w, self.h = env_conf["w"], env_conf["h"]   #environment dimensions
        cell_val = env_conf["cell_val"] #value of the cell the agent is located in
        print(cell_val)
        Thread(target=self.msg_cb, daemon=True).start()
        # print("hello")
        self.wait_for_connected_agent()

        #TODO: DEINE YOUR ATTRIBUTES HERE
        self.map = np.ones((self.h, self.w)) * -1  #unknown cells are represented by -1
        self.state = STATES["EXPLORING"]
        self.pos = None
        self.pos2 = None

        
    def msg_cb(self): 
        """ Method used to handle incoming messages """
        while self.running:
            msg = self.network.receive()
            self.msg = msg
            if msg["header"] == MOVE:
                self.x, self.y =  msg["x"], msg["y"]
                print(self.x, self.y)
            elif msg["header"] == GET_NB_AGENTS:
                self.nb_agent_expected = msg["nb_agents"]
            elif msg["header"] == GET_NB_CONNECTED_AGENTS:
                self.nb_agent_connected = msg["nb_connected_agents"]

            print("hellooo: ", msg)
            # print("agent_id ", self.agent_id)
            

    def wait_for_connected_agent(self):
        self.network.send({"header": GET_NB_AGENTS})
        check_conn_agent = True
        while check_conn_agent:
            if self.nb_agent_expected == self.nb_agent_connected:
                print("both connected!")
                check_conn_agent = False

                  

    #TODO: CREATE YOUR METHODS HERE...
    def explore(self):
        # Update map if needed
        val = self.msg.get("cell_val")
        if val is not None:
            self.map[self.y, self.x] = val

        move = 0  #default is to stand still
        
        if val == 0:
            # Choose random move (1–8)
            move = np.random.randint(1, 9)

            # Compute next cell
            dx, dy = DIRECTIONS[move]
            nx, ny = self.x + dx, self.y + dy

            # Check if this move is allowed
            def is_valid(nx, ny):
                out_of_bounds = nx < 0 or nx >= self.w or ny < 0 or ny >= self.h
                # hit_obstacle = self.map[ny, nx] != -1
                # return not (out_of_bounds or hit_obstacle)
                return not out_of_bounds

            # If not allowed → pick another random allowed direction
            if not is_valid(nx, ny):

                # all possible moves except the bad one
                candidates = []

                for m, (dx, dy) in DIRECTIONS.items():
                    nx2, ny2 = self.x + dx, self.y + dy
                    if is_valid(nx2, ny2):
                        candidates.append(m)

                if candidates:
                    move = np.random.choice(candidates) 
                else:
                    move = np.random.randint(1, 9)  # No valid moves, pick any (will stay in place)
        if val == 0.25 or val == 0.3:
            self.state = STATES["RESEARCHING"]
            return 

        # print("Current Position:", (self.x, self.y))
        # print("Moving in direction:", move)
        return move

    def research(self):
        print("researching...")
        # Remember starting position
        if self.pos is None:
            self.pos = (self.x, self.y)

        # Update map
        val = self.msg.get("cell_val")
        self.map[self.y, self.x] = val

        if self.pos and not self.pos2: 
            # Research pattern if move brings us to a known case
            if val == 0 or (val==0.25 and self.pos != (self.x, self.y)) or (val==0.3 and self.pos != (self.x, self.y)):
                direction = tuple(x-y for x,y in zip(self.pos,(self.x, self.y))) 
                print("direction:", direction)
                move = [k for k,v in DIRECTIONS.items() if v == direction][0]
                print("returning to previous pos:", self.pos, "move:", move)
                return move
            
            # Research if we got closer
            if val == 0.5 or val == 0.6:
                if self.pos2 is None:
                    self.pos2 = (self.x, self.y)
                return   #stand still to analyze surroundings
            
            # Finding Exploration cell possible
            candidates = []
            for m, (dx, dy) in DIRECTIONS.items():
                nx2, ny2 = self.x + dx, self.y + dy
                if self.map[ny2, nx2] == -1:
                    candidates.append(m)
            if candidates:
                move = np.random.choice(candidates) 
                return move
            
        if self.pos and self.pos2:
            if val == 0 or val == 0.25 or val == 0.3 or (val==0.5 and self.pos2 != (self.x, self.y)) or (val==0.6 and self.pos2 != (self.x, self.y)):
                direction = tuple(x-y for x,y in zip(self.pos2,(self.x, self.y))) 
                print("direction:", direction)
                move = [k for k,v in DIRECTIONS.items() if v == direction][0]
                print("returning to previous pos:", self.pos2, "move:", move)
                return move
            
                        # Research found key or box
            if val == 1:
                self.state = STATES["FOUND_KEY"]
                print("Key found at position:", (self.x, self.y))
                self.pos = None
                return  #stand still to analyze surroundings
            
            candidates = []
            for m, (dx, dy) in DIRECTIONS.items():
                nx2, ny2 = self.x + dx, self.y + dy
                if self.map[ny2, nx2] == -1:
                    candidates.append(m)
            if candidates:
                move = np.random.choice(candidates) 
                print("Candidates found 2")
                return move
            

        

            
 
if __name__ == "__main__":
    from random import randint
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--server_ip", help="Ip address of the server", type=str, default="localhost")
    args = parser.parse_args()

    agent = Agent(args.server_ip)
    
    try:    #Manual control test0
        while True:
            print("Agent : ", agent.agent_id)
            # # cmds = {"header": int(input("0 <-> Broadcast msg\n1 <-> Get data\n2 <-> Move\n3 <-> Get nb connected agents\n4 <-> Get nb agents\n5 <-> Get item owner\n"))}
            # cmds = {"header": None}
            # # cmds['header'] = 2
            # if cmds["header"] == BROADCAST_MSG:
            #     cmds["Msg type"] = int(input("1 <-> Key discovered\n2 <-> Box discovered\n3 <-> Completed\n"))
            #     cmds["position"] = (agent.x, agent.y)
            #     cmds["owner"] = randint(0,3) # TODO: specify the owner of the item
            # elif cmds["header"] == MOVE:
            #     cmds["direction"] = int(input("0 <-> Stand\n1 <-> Left\n2 <-> Right\n3 <-> Up\n4 <-> Down\n5 <-> UL\n6 <-> UR\n7 <-> DL\n8 <-> DR\n"))
            #     # cmds["direction"] = agent.avancer()
            #     # print("Moving in direction: ", cmds["direction"])
            # agent.network.send(cmds)
    except KeyboardInterrupt:
        pass
# it is always the same location of the agent first location



