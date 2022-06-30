"""
Basic Transportation model with 
a clock to visualize env time in datetime
format.

There are som other details such as
load and unload time for vehicle.
"""


import datetime
import simpy 
import numpy as np
import argparse    
import matplotlib.pyplot as plt
import os



class Clock():
    def __init__(self, env, start_date=None):
        self.env = env
        self.start_date = (
            start_date if start_date 
            else datetime.datetime.now()
            ) 

    @property
    def current_date(self):
        return (
            datetime.timedelta(seconds = self.env.now) + 
            self.start_date
            )


def compute_distance(from_node, to_node):
    return np.sqrt((from_node.x-to_node.x)**2 + (from_node.y-to_node.y)**2)


class DemandNode():
    def __init__(self, env, clock, id, x, y):
        self.env = env
        self.clock = clock
        self.id = id
        self.x = x
        self.y = y

        self.unloaded_vehicles = 0
        self.entry_queu = []


    def on_entered(self, vehicle):
        print(f"{self.clock.current_date} - Vehicle {vehicle.id} entered on node {type(self).__name__}-{self.id}")
        self.entry_queu.append(vehicle)
        yield self.env.timeout(1)

    def process_vehicle(self, vehicle):
        print(f"{self.clock.current_date} - Vehicle {vehicle.id} processing on node {type(self).__name__}-{self.id}")
        yield self.env.process(vehicle.unload())
        self.unloaded_vehicles = self.unloaded_vehicles+1
        vehicle.loaded = False
        return vehicle

    def on_exited(self, vehicle):
        print(f"{self.clock.current_date} - Vehicle {vehicle.id} exited from node {type(self).__name__}-{self.id}")

        yield self.env.timeout(1)

    def __call__(self):
        while True:
            if len(self.entry_queu)>0:
                vehicle = self.entry_queu[0]
                vehicle = yield self.env.process(self.process_vehicle(vehicle))
                self.entry_queu.remove(vehicle)
                vehicle.idle = True
            else:
                yield self.env.timeout(1)


class SourceNode():
    def __init__(self, env, clock, id, x, y):
        self.env = env
        self.clock = clock
        self.id = id
        self.x = x
        self.y = y
    
        self.loaded_vehicles = 0

        self.entry_queu = []

    def on_entered(self, vehicle):
        print(f"{self.clock.current_date} - Vehicle {vehicle.id} entered on node {type(self).__name__}-{self.id}")
        self.entry_queu.append(vehicle)
        yield self.env.timeout(1)

    def process_vehicle(self, vehicle):
        print(f"{self.clock.current_date} - Vehicle {vehicle.id} start processing on node {type(self).__name__}-{self.id}")
        yield self.env.process(vehicle.load())
        print(f"{self.clock.current_date} - Vehicle {vehicle.id} end processing on node {type(self).__name__}-{self.id}")
        self.loaded_vehicles = self.loaded_vehicles+1
        vehicle.loaded = True
        return vehicle

    def on_exited(self, vehicle):
        print(f"{self.clock.current_date} - Vehicle {vehicle.id} exited from node {type(self).__name__}-{self.id}")
        yield self.env.timeout(1)

    def __call__(self):
        while True:
            if len(self.entry_queu)>0:
                vehicle = self.entry_queu[0]
                vehicle = yield self.env.process(self.process_vehicle(vehicle))
                self.entry_queu.remove(vehicle)
                vehicle.idle = True
            else:
                yield self.env.timeout(1)


class Vehicle():
    
    def __init__(
            self, 
            env:simpy.Environment, 
            clock:Clock, 
            id:int, 
            current_node,
            speed:float=100., # km/hs
            load_time:float=5, # minutes
            unload_time:float=5 # minutes
            ):

        self.env = env
        self.clock = clock
        self.id = id
        self.current_node = current_node
        self.speed = speed/(60*60) # convert km/hs to km/s
        self.load_time = load_time*60
        self.unload_time = unload_time*60
        self.loaded = True
        self.idle = True
        self.content = []
        

    def move(self, to_node):
        yield self.env.process(self.current_node.on_exited(self))

        print(f"{self.clock.current_date} - {type(self).__name__}-{self.id} - moving from {type(self.current_node).__name__}-{self.current_node.id} to {type(to_node).__name__}-{to_node.id}")
        dist = compute_distance(self.current_node,to_node) # km
        yield self.env.timeout(dist/self.speed)
        self.current_node = to_node

        yield self.env.process(self.current_node.on_entered(self))
        
    def load(self):
        yield self.env.timeout(self.load_time)

    def unload(self):
        yield self.env.timeout(self.unload_time)



class Router():

    def __init__(self, env, clock, nodes, vehicles):
        self.env = env
        self.clock = clock
        self.nodes = nodes
        self.vehicles = vehicles

        self.source_nodes = [n for n in nodes if isinstance(n, SourceNode)]
        self.demand_nodes = [n for n in nodes if isinstance(n, DemandNode)]


    def __call__(self):
        while True:
            for vehicle in self.vehicles:
                if vehicle.idle and vehicle.loaded:
                    idx_to_node = np.random.choice(len(self.demand_nodes))
                    vehicle.idle = False
                    self.env.process(vehicle.move(self.demand_nodes[idx_to_node]))
                    yield self.env.timeout(0.1)
                elif vehicle.idle and not vehicle.loaded:
                    idx_to_node = np.random.choice(len(self.source_nodes))
                    vehicle.idle = False
                    self.env.process(vehicle.move(self.source_nodes[idx_to_node]))
                    yield self.env.timeout(0.1)
                else:
                    yield self.env.timeout(0.1)    



class Monitor():

    def __init__(self, clock):
        self.clock = clock
        self.metrics = {}

    def add_metric(self, name, unit=None, initial_value=None):
        self.metrics[name] = {
            "unit":unit,
            "name":name,
            "values":[{
                "time":self.clock.current_date,
                "value":initial_value
            }]
        }

    def record_metric(self, name, value):
        self.metrics[name]['values'].append = {
                "time":self.clock.current_date,
                "value":value
        }



def plot_nodes(demand_nodes, source_node, path):
    plt.figure()
    plt.scatter(
        [n.x for n in demand_nodes],
        [n.y for n in demand_nodes], 
        label='demand nodes'
        )
    plt.scatter([source_node.x],[source_node.y], label='source node')
    plt.legend()
    plt.title("Nodes")
    plt.savefig(os.path.join(path,'nodes.png'))


def plot_unloads(demand_nodes,path):
    plt.figure()
    plt.bar(
        [n.id for n in demand_nodes], 
        [n.unloaded_vehicles for n in demand_nodes], 
        label='unloaded vehicles'
        )
    plt.legend()
    plt.savefig(os.path.join(path,'unloads.png'))



parser = argparse.ArgumentParser(description='Excecute simulation of transportation model')

parser.add_argument('-v', '--vehicles', type=int, default=1,
                    help='number of vehicles to generate (default to 1)')

parser.add_argument('-n','--nodes', type=int, default=5,
                    help='number of demand nodes to generate (default to 5)')

parser.add_argument('-st','--simtime', type=float, default=1*24*60*60,
                    help='total simulation time expresed in seconds (default to 1 day)')

parser.add_argument('-p','--plot', type=str, default=".",
                    help='path where to save result plots. (default current work directory)')

if __name__ == "__main__":

    args = parser.parse_args()

    env = simpy.Environment()
    clock = Clock(env)
    monitor = Monitor(clock)

    source_node = SourceNode(env, clock, id=0, x=0, y=0)

    n_demand_nodes = args.nodes
    demand_nodes = [
        DemandNode(env, clock, id=i, x=np.random.uniform(-10,10), y=np.random.uniform(-10,10)) 
        for i in range(n_demand_nodes)
        ] 

    nodes = demand_nodes + [source_node]

    n_vehicles = args.vehicles
    vehicles = [Vehicle(env, clock, id=i, current_node=source_node) for i in range(n_vehicles)]

    router  = Router(env, clock, nodes=nodes, vehicles=vehicles)

    for n in nodes:
        env.process(n())
    env.process(router())

    sim_time = args.simtime # days*hours*minutes*seconds
    env.run(until=sim_time)

    plot_nodes(demand_nodes, source_node, args.plot)
    plot_unloads(demand_nodes, args.plot)