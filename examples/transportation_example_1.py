# Basic Transportation model 

import simpy 
import numpy as np


def compute_distance(from_node, to_node):
    return np.sqrt((from_node.x-to_node.x)**2 + (from_node.y-to_node.y)**2)


class DemandNode():
    def __init__(self, env, id, x, y):
        self.env = env
        self.id = id
        self.x = x
        self.y = y

        self.unloaded_vehicles = 0

        self.entry_queu = []

    def on_entered(self, vehicle):
        print(f"{self.env.now:.2f} - Vehicle {vehicle.id} entered on node {self.id} - type {type(self).__name__}")
        self.entry_queu.append(vehicle)
        yield self.env.timeout(1)

    def process_vehicle(self, vehicle):
        yield self.env.timeout(np.random.uniform(5,10))
        self.unloaded_vehicles = self.unloaded_vehicles+1
        vehicle.loaded = False
        return vehicle

    def on_exited(self, vehicle):
        print(f"{self.env.now:.2f} - Vehicle {vehicle.id} exited from node {self.id} - type {type(self).__name__}")
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
    def __init__(self, env, id, x, y):
        self.env = env
        self.id = id
        self.x = x
        self.y = y
    
        self.loaded_vehicles = 0

        self.entry_queu = []

    def on_entered(self, vehicle):
        print(f"{self.env.now:.2f} - Vehicle {vehicle.id} entered on node {self.id} - type {type(self).__name__}")
        self.entry_queu.append(vehicle)
        yield self.env.timeout(1)

    def process_vehicle(self, vehicle):
        yield self.env.timeout(np.random.uniform(5,10))
        self.loaded_vehicles = self.loaded_vehicles+1
        vehicle.loaded = True
        return vehicle


    def on_exited(self, vehicle):
        print(f"{self.env.now:.2f} - Vehicle {vehicle.id} exited from node {self.id} - type {type(self).__name__}")
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
            id:int, 
            current_node,
            speed:float=1., 
            ):

        self.env = env
        self.id = id
        self.current_node = current_node
        self.speed = speed # km/hs
        self.loaded = True
        self.idle = True
        self.content = []
        

    def move(self, to_node):
        dist = compute_distance(self.current_node,to_node) # km
        yield self.env.process(self.current_node.on_exited(self))
        yield self.env.timeout(dist/self.speed)
        self.current_node = to_node
        yield self.env.process(self.current_node.on_entered(self))
        

class Router():

    def __init__(self, env, nodes, vehicles):
        self.env = env
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
                    yield self.env.process(vehicle.move(self.demand_nodes[idx_to_node]))
                elif vehicle.idle and not vehicle.loaded:
                    idx_to_node = np.random.choice(len(self.source_nodes))
                    vehicle.idle = False
                    yield self.env.process(vehicle.move(self.source_nodes[idx_to_node]))
                else:
                    yield self.env.timeout(1)
                

if __name__ == "__main__":

    env = simpy.Environment()
    source_node = SourceNode(env, id=0, x=0, y=0)
    demand_node = DemandNode(env, id=0, x=10, y=10)
    vehicle = Vehicle(env,id=0, current_node=source_node)
    router  = Router(env, nodes=[source_node,demand_node], vehicles = [vehicle])

    env.process(source_node()) 
    env.process(demand_node())
    env.process(router()) 

    env.run(until=1000)

    print("Total Unloaded Vehicles in demand node: ",demand_node.unloaded_vehicles)
    print("Total Loaded Vehicles in source node: ",source_node.loaded_vehicles)