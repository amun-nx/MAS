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

# Directions possible 
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

# States the robot can be in 
STATES = {
    "EXPLORING": 0,
    "RESEARCHING": 1,
    "FOUND": 2,
    "GOAL": 3,
    "FINISHED": 4
}

# Pattern definition in the case where a box or a key is discovered
PATTERN = np.zeros((5,5))

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
        # Own map 
        self.map = np.ones((self.h, self.w)) * -1  #unknown cells are represented by -1
        # State of the agent
        self.state = STATES["EXPLORING"]

        # Attributes used for box and key research
        self.pos = None
        self.pos2 = None

        # All the keys and boxes found by all the agent
        self.keys_found = []
        self.boxes_found = []

        # Position of the agent's key and position and other attributes
        self.key_pos = None
        self.box_pos = None
        self.flag = False
        self.goal_pos = None

        
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

    # Method used when the agent is exploring the area
    def explore(self, startegy = "RANDOM"):

        # First strategy implemented, random search
        if startegy == "RANDOM":
            
            # Value of the cell on which the robot stands 
            val = self.pattern()

            # --- Compute movement ---
            move = 0  # default: stand still

            # Case where we are on a known or an unknown space
            if val == 0 or val == -1:
                move = np.random.randint(1, 9)
                dx, dy = DIRECTIONS[move]
                nx, ny = self.x + dx, self.y + dy

                # Is the movement in the boudary and not a known space
                def is_valid(nx, ny):
                    out_of_bounds = nx < 0 or nx >= self.w or ny < 0 or ny >= self.h
                    if out_of_bounds:
                        return False
                    else:
                        if self.map[ny, nx] == 0:
                            return False
                        return True

                # Choose a random candidate among the possible movement
                if not is_valid(nx, ny):
                    candidates = []
                    for m, (dx, dy) in DIRECTIONS.items():
                        nx2, ny2 = self.x + dx, self.y + dy
                        if is_valid(nx2, ny2):
                            candidates.append(m)

                    move = np.random.choice(candidates) if candidates else np.random.randint(1, 9)
                
                self.map[self.y, self.x] = 0  # mark as free cell

            # Print for debugging purpose
            print("agent id",self.agent_id, "cell val:", val,"state:", self.state)

            # Case where an object is nearby
            if val == 0.25 or val == 0.3:
                self.state = STATES["RESEARCHING"]
                return
            return move
        
        # Other strategy to be added later

    # Method used when the agent finds a special value in the map (either 0.3 or 0.25)
    def research(self):
        # print("researching...")
        # Remember starting position
        if self.pos is None:
            self.pos = (self.x, self.y)

        # Update values to be used
        val = self.pattern()

        # If we are in the outer layer of the object
        if self.pos and not self.pos2: 
            # Research pattern if move brings us to a the previous position
            if val == 0 or (val==0.25 and self.pos != (self.x, self.y)) or (val==0.3 and self.pos != (self.x, self.y)):
                direction = tuple(x-y for x,y in zip(self.pos,(self.x, self.y))) 
                move = [k for k,v in DIRECTIONS.items() if v == direction][0]
                return move
            
            # Research if we got into the second layer
            if val == 0.5 or val == 0.6:
                if self.pos2 is None:
                    self.pos2 = (self.x, self.y)
                return   #stand still 
            
            # Finding Exploration cell possible
            candidates = []
            for m, (dx, dy) in DIRECTIONS.items():
                nx2, ny2 = self.x + dx, self.y + dy
                if self.map[ny2, nx2] == -1:
                    candidates.append(m)
            if candidates:
                move = np.random.choice(candidates) 
                return move
        
        # Case where we are in the second layer of an object
        if self.pos and self.pos2:

            # Returning to the previous position
            if val == 0 or val == 0.25 or val == 0.3 or (val==0.5 and self.pos2 != (self.x, self.y)) or (val==0.6 and self.pos2 != (self.x, self.y)):
                direction = tuple(x-y for x,y in zip(self.pos2,(self.x, self.y))) 
                move = [k for k,v in DIRECTIONS.items() if v == direction][0]
                return move
            
            # Actions to do when a key or a box is found/ State is changed
            if val == 1 and (self.map[self.pos2[1], self.pos2[0]] == 0.5 or self.map[self.pos2[1], self.pos2[0]] == 0.6):
                self.state = STATES["FOUND"]
                # print("Key found at position:", (self.x, self.y))
                self.pos = None
                self.pos2 = None
                return  #stand still to analyze surroundings
            
            candidates = []
            for m, (dx, dy) in DIRECTIONS.items():
                nx2, ny2 = self.x + dx, self.y + dy
                if self.map[ny2, nx2] == -1:
                    candidates.append(m)
            if candidates:
                move = np.random.choice(candidates) 
                return move

    # Method used to turn the map area of the keys or boxes into 0            
    def pattern(self):
        H, W = self.map.shape
        h, w = PATTERN.shape

        def safe_paste(cy, cx):
            H, W = self.map.shape
            h, w = PATTERN.shape

            # demi-tailles du pattern
            hy = h // 2
            hx = w // 2

            # coordonnées théoriques du collage centré
            y1 = cy - hy
            y2 = cy + hy + 1
            x1 = cx - hx
            x2 = cx + hx + 1

            # coordonnées réelles (clampées aux bords)
            map_y1 = max(0, y1)
            map_y2 = min(H, y2)
            map_x1 = max(0, x1)
            map_x2 = min(W, x2)

            # partie du PATTERN à coller
            pat_y1 = map_y1 - y1
            pat_y2 = pat_y1 + (map_y2 - map_y1)
            pat_x1 = map_x1 - x1
            pat_x2 = pat_x1 + (map_x2 - map_x1)

            # collage sécurisé centré
            self.map[map_y1:map_y2, map_x1:map_x2] = \
                PATTERN[pat_y1:pat_y2, pat_x1:pat_x2]
            
        val = self.msg.get("cell_val")

        if val is not None:

            self.map[self.y, self.x] = val
            
            # --- Update map with PATTERN if keys found ---
            if self.keys_found:
                for k in self.keys_found:
                    if k is not None:
                        ky, kx = k[1], k[0]
                        safe_paste(ky, kx)

            # --- Same for boxes ---
            if self.boxes_found:
                for k in self.boxes_found:
                    if k is not None : 
                        ky, kx = k[1], k[0]
                        safe_paste(ky, kx)

            # --- Normal exploration ---        
            if val*self.map[self.y, self.x] < 0:
                return val
            else :
                return self.map[self.y, self.x] 

    # Method used when a key and a box are found
    def goal(self):

        # The goal is to go to the key
        if self.flag == False:
            self.goal_pos = self.key_pos

        # The goal is to go to the box
        if (self.x, self.y) == self.key_pos:
            self.goal_pos = self.box_pos
            self.flag = True
        
        # Changing the state to indicate that the exploration is finished
        if (self.x, self.y) == self.box_pos and self.flag== True:
            self.state = STATES["FINISHED"]
            print("GOAL COMPLETED!" * 3)
            return

        # Compute the normalized  movement 
        direction = tuple(x-y for x,y in zip(self.goal_pos,(self.x, self.y))) 
        x = direction[0]//abs(direction[0]) if direction[0]!=0 else 0
        y = direction[1]//abs(direction[1]) if direction[1]!=0 else 0
        move = [k for k,v in DIRECTIONS.items() if v == (x,y)][0]
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
            # print("State : ", agent.state)
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



