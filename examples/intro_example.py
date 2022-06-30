"""
This is an ilustrative example of simpy library.
It's taken from oficial documentation of the library
and serves as an introduction of the main workflow.
"""

import simpy

# First example
def example(env):
    value = yield env.timeout(1, value=42)
    print('now=%d, value=%d' % (env.now, value))


if __name__ == "__main__":
    env = simpy.Environment()
    p = env.process(example(env))
    env.run()

