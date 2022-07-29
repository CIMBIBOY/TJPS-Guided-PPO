from cnn_arch import get_cnn_model
import numpy as np
import random
from collections import deque
from environment import WarehouseEnvironment

class Agent:
    def __init__(self, enviroment, model):
        
        # Initialize atributes
        self._state_size = enviroment.n_states
        self._action_space = enviroment.action_space()
        self._action_size = enviroment.n_actions
        
        self.expirience_replay = deque(maxlen=2000)
        
        # Initialize discount and exploration rate
        self.gamma = 0.6
        self.epsilon = 0.1
        
        # Build networks
        self.q_network = model
        self.target_network = model
        # self.alighn_target_model()

    def store(self, state, action, reward, next_state, terminated):
        self.expirience_replay.append((state, action, reward, next_state, terminated))
    
    def _build_compile_model(self):
        model = get_cnn_model(48,48,4,4)
        return model

    def alighn_target_model(self):
        self.target_network.set_weights(self.q_network.get_weights())
    
    def act(self, state):
        if np.random.rand() <= self.epsilon:
            return random.choice(self._action_space)
        
        q_values = self.q_network.predict(state)
        return np.argmax(q_values[0])

    def retrain(self, batch_size):
        minibatch = random.sample(self.expirience_replay, batch_size)
        
        for state, action, reward, next_state, terminated in minibatch:
            
            target = self.q_network.predict(state)
            
            if terminated:
                target[0][action] = reward
            else:
                t = self.target_network.predict(next_state)
                target[0][action] = reward + self.gamma * np.amax(t)
            
            self.q_network.fit(state, target, epochs=1, verbose=0)


if __name__ == '__main__':
    from environment import WarehouseEnvironment
    from deep_q_learning import Agent
    from cnn_arch import get_cnn_model

    env = WarehouseEnvironment()
    agent = Agent(env, get_cnn_model(48,48,4,4))

    batch_size = 32
    num_of_episodes = 100
    timesteps_per_episode = 1000
    agent.q_network.summary()