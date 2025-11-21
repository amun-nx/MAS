from agent import Agent
import argparse 
import time
from multiprocessing import Process

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
            # Ici tu peux mettre ta logique manuelle ou automatique
            time.sleep(1)
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
