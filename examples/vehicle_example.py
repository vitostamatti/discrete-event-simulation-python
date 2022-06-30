"""
This example ilustrates a process that runs
until a simulation time is reached.
"""

import simpy
import numpy as np


class Vehicle():
    def __init__(
            self, 
            env:simpy.Environment, 
            min_speed:float=80., 
            max_speed:float=100., 
            fuel_consumption:float=10., 
            fuel_capacity:float=35.
        ):

        self.env = env
        self.min_speed = min_speed 
        self.max_speed = max_speed 
        self.fuel_consumption = fuel_consumption 
        self.fuel_capacity = fuel_capacity 
        self.fuel = fuel_capacity


    def drive(self):
        while True:
            print(f"Start Driving at {self.env.now}")
            travel_time = (self.fuel*self.fuel_consumption)/(np.random.randint(self.min_speed,self.max_speed))
            yield self.env.timeout(travel_time)
            print(f"Need refueling at {self.env.now}")

            print(f"Start refueling at {self.env.now}")
            yield self.env.timeout(np.random.uniform(0.05, 0.15))
            self.fuel = np.random.randint(self.fuel_capacity-5,self.fuel_capacity)
            print(f"Finished refueling at {self.env.now}: fuel now is {self.fuel}")



if __name__ == "__main__":
    env = simpy.Environment()
    v = Vehicle(env)
    env.process(v.drive())
    env.run(until=24)