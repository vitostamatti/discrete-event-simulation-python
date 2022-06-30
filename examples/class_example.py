"""
This example shows an alternative of the intro_example.py
implementation using python classes.
"""

import simpy

# Second example
class Example():

    def __init__(self, env, delay=10):
        self.env = env
        self.delay = delay

    def process(self):
        print('Before timeout: now=%d' % (env.now))
        value = yield self.env.timeout(self.delay, value=42)
        print('After timeout: now=%d, value=%d' % (env.now, value))


if __name__ == "__main__":
    env = simpy.Environment()
    e = Example(env,delay=10)
    env.process(e.process())
    env.run()