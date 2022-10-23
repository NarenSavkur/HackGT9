# -*- coding: utf-8 -*-
"""HackGT22.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1nfuMjJdlsbc17TlAZXgp-p6GswlG_p0g

1 - Transform class data into CSV with className, location, size, timing, day

2 - Preprocess data into heatmap of each granular location, draw regions based on whether the bus route hits the location and general logic

3 - Create Matrix of which regions will use the bus to travel other regions, and which regions will NOT use the bus to travel other regions (the matrix value of a -> b == matrix value of b -> a)

4 - Generate heatmap of each region for each time t = 30 mins and the net flow from regions A to B (really only need location flows on Matrix values that exist)

5 - use data from 4 and logic from matrix defined in 3 to train a Q-learning RL policy to allocate buses for each 30 mins of the day, each day of the week. Cost function is an efficiency formula that needs to be calculated.

*   each week is identical to the next week
*   train the week 10 times to get ideal distro for each time t for each day in the week

solution is the best distro with the best eff value at the end. (note -- have to retrain for each semester based on class scheduling info, but still computationally cheap)
"""

from rl.memory import SequentialMemory
from rl.policy import BoltzmannQPolicy
from rl.agents import DQNAgent
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.layers import Dense, Flatten
from tensorflow.keras.models import Sequential
from gym.spaces import Box, Discrete
from gym import Env
import io
import pandas as pd
import numpy as np

from google.colab import files
uploaded = files.upload()

data = pd.read_csv(io.BytesIO(uploaded['data.csv']))

print(data)

uniqLocs = data.drop_duplicates(subset=["Building"])
print(uniqLocs)

print(type(uniqLocs.loc[:, "Building"][0]))
print(uniqLocs.loc[:, "Building"][0])
a = uniqLocs.loc[:, "Building"][0]
print(a.rpartition(' '))

data.Building.str.split(' ').str[0].unique()

data['unique_building'] = data.Building.str.split(' ').str[0]
data.sample(7)

data.dtypes

# gold is 2431
# red is 24531
# blue is 13542
# green is 2456

locationToRegion = {'Scheller': 1, 'Guggenheim': 2, 'Instructional': 4, 'Skiles': 2, 'Weber': 2,
                    'College': 3, 'Boggs': 4, 'Engineering': 2, 'Van': 3, 'Klaus': 3, 'Clough': 2,
                    'Mason': 3, 'Allen': 3, 'Manufacture': 3, "O'Keefe": 1, 'Howey': 3, 'Paper': 5,
                    'D.M.': 2, 'Curran': 5, 'Ford': 3, 'Cherry': 3, 'East': 3, 'Molecular': 3, 'West':  3, "Willage": 5,
                    'Kendeda': 5, '575': 6, 'Whitaker': 3, 'Bunger-Henry': 3, 'Swann': 2, 'Habersham': 4,
                    'Daniel': 2, 'Old': 2, 'Pettit': 3, 'Stephen': 2, 'Brittain': 2, 'Groseclose': 4,
                    'ISyE': 4, 'Couch': 5, 'J.': 2}

data['region'] = data['unique_building'].map(locationToRegion)
print(data)

# how many total classes there are in each region
data['region'].value_counts().sort_index()

# how many total people there are in each region
data.groupby('region')['Size'].agg('sum')

table = pd.pivot_table(data, values='Size',
                       index=['region'],
                       #columns=['mon', 'tues', 'wed', 'thur', 'fri'],
                       aggfunc=np.sum,
                       fill_value=0,
                       observed=True)
print(table)


def f_group(x):
    d = {}
    d['Monday'] = x[x['mon'] == True]['Size'].sum()
    d['Tuesday'] = x[x['tues'] == True]['Size'].sum()
    d['Wednesday'] = x[x['wed'] == True]['Size'].sum()
    d['Thursday'] = x[x['thur'] == True]['Size'].sum()
    d['Friday'] = x[x['fri'] == True]['Size'].sum()
    s = pd.Series(d)
    return s


data.groupby(['region']).apply(f_group).reset_index()

sorted(data.start.unique())

dayOfWeek = 1

df_group = data.groupby(['region', 'start']).apply(f_group).reset_index()

df_group = df_group.drop(42)

for i in range(5):
    if (i != 0):
        temp = {'region': i+1, 'start': 6, 'Monday': 0,
                'Tuesday': 0, 'Wednesday': 0, 'Thursday': 0, 'Friday': 0}
        df_group = df_group.append(temp, ignore_index=True)
    if (i != 2):
        temp2 = {'region': i+1, 'start': 20, 'Monday': 0,
                 'Tuesday': 0, 'Wednesday': 0, 'Thursday': 0, 'Friday': 0}
        df_group = df_group.append(temp2, ignore_index=True)


df_group = df_group.sort_values(by=['start', 'region'])
df_group

print(df_group.iloc[:, [0, 1, 2]])

# df_group.iloc[:,[2]][[3]]

print(df_group.iloc[5:10, dayOfWeek+1])

print(sum(df_group.iloc[5:10, dayOfWeek+1]))

# !pip install tensorflow == 2.3.0
# !pip install gym
# !pip install keras
# !pip install keras-rl2


print(max(df_group.max()))

arrlow = np.concatenate((df_group[['region', 'start']], np.zeros(
    (len(df_group), len(df_group.columns)-2), dtype=int)), axis=1)
arrhigh = np.concatenate((df_group[['region', 'start']], np.full(
    ((len(df_group), len(df_group.columns)-2)), max(df_group.max()))), axis=1)
print(arrlow)
print("_________")
print(arrhigh)


def numberOfStops(start, stop, bus):
    counter = 0
    if not (start in bus and stop in bus):
        return 0
    if start == stop:
        return 0

    counter = 0
    for i in range(bus.index(start), len(bus)):
        if not bus[i] == stop:
            counter += 1
        else:
            return abs(5-counter)


goldbus = [2, 4, 3, 1]
redbus = [2, 4, 5, 3, 1]
bluebus = [1, 3, 5, 4, 2]
greenbus = [2, 4, 5, 6]

gold = []
red = []
blue = []
green = []

for i in range(5):
    gold.append([])
    red.append([])
    blue.append([])
    green.append([])

    for j in range(5):
        gold[i].append(numberOfStops(i+1, j+1, goldbus*2))
        red[i].append(numberOfStops(i+1, j+1, redbus*2))
        blue[i].append(numberOfStops(i+1, j+1, bluebus*2))
        green[i].append(numberOfStops(i+1, j+1, greenbus*2))

gold = np.array(gold)
red = np.array(red)
blue = np.array(blue)
green = np.array(green)

for k in range(8):
    flowss = [[0 for i in range(5)] for j in range(5)]
    for i in range(5):
        ourDelta = df_group.iloc[(5*(k+1)+i), dayOfWeek+1] - \
            df_group.iloc[(5*k+i), dayOfWeek+1]
        currSum = sum(df_group.iloc[5*(k+1):5*(k+2), dayOfWeek+1]
                      ) - df_group.iloc[(5*(k+1)+i), dayOfWeek+1]
        for j in range(5):
            if (i == j):
                flowss[i][j] = 0
            else:
                flowss[i][j] = abs((ourDelta / currSum) *
                                   df_group.iloc[5*(k+1)+j, dayOfWeek+1])

    flows = np.array(flowss)
    print("")
    print(np.sum(np.add(np.add(np.matmul(flowss, red), np.matmul(flowss, blue)),
          np.add(np.matmul(flowss, gold), np.matmul(flowss, green)))))
    print("")
    print("----------")

print("")


class CustomEnv(Env):

    def __init__(self):
        self.action_space = Discrete(7)  # [0, 1, 2, 3, 4, 5, 6]
        # +- the number of red/blue, green, and gold buses.
        # space[0] = red/blue ++, space[1] = red/blue --, space[2] = green ++, space[3] = green --, space[4] = gold ++, space[5] = gold --, space[6] = no change
        # i'm pretty sure the observation space is all the possible states the model can take -- i e the df_group is largely irrevelant in this context
        #arrlow = np.concatenate((df_group[['region', 'start']], np.zeros((len(df_group), len(df_group.columns)-2), dtype=int)), axis = 1)
        #arrhigh = np.concatenate((df_group[['region', 'start']], np.full(((len(df_group), len(df_group.columns)-2)), max(df_group.max()))), axis = 1)

        #self.observation_space = Box(low = np.array([0,0,0,0]), high = np.array([12, 12, 12, 12]))
        self.observation_space = Box(low=0, high=12, shape=(4,))
        # observation space should still preserve the first two columns as df_group (with the regions and start times) -- fixed
        # np.full_like(df_group.shape, max(df_group.max())))
        # , 0.1, dtype=np.double)max(df_group.max())(df_group.shape)) #not sure about this -- come back to it
        # red buses, blue buses, green buses, gold buses
        self.state = [3, 3, 1, 2]
        self.trials = 25

    def step(self, action):
        if (action == 0):
            self.state[0] += 1
            self.state[1] += 1
        elif (action == 1):
            self.state[0] -= 1
            self.state[1] -= 1
        elif (action == 2):
            self.state[2] += 1
        elif (action == 3):
            self.state[2] -= 1
        elif (action == 4):
            self.state[3] += 1
        elif (action == 5):
            self.state[3] -= 1
        else:
            self.state[0] += 0

        self.trials -= 1

        curr_reward = 0
        temp_reward = 0
        for k in range(8):
            flows = [[0 for i in range(5)] for j in range(5)]
            for i in range(5):
                ourDelta = df_group.iloc[(
                    5*(k+1)+i), dayOfWeek+1] - df_group.iloc[(5*k+i), dayOfWeek+1]
                currSum = sum(
                    df_group.iloc[5*(k+1):5*(k+2), dayOfWeek+1]) - df_group.iloc[(5*(k+1)+i), dayOfWeek+1]
                for j in range(5):
                    if (i == j):
                        flows[i][j] = 0
                    else:
                        flows[i][j] = abs(
                            (ourDelta / currSum) * df_group.iloc[5*(k+1)+j, dayOfWeek+1])

            flows = np.array(flows)
            curr_reward = np.sum(np.add(np.add(self.state[0]*np.matmul(red, flows), self.state[1]*np.matmul(
                blue, flows)),  self.state[2]*np.add(np.matmul(green, flows), self.state[3]*np.matmul(gold, flows))))
            # if any(n < 0 for n in self.state):
            #curr_reward = -1 * (curr_reward ** 2)

            temp_reward += curr_reward
            curr_reward = 0

        if (temp_reward <= 0):
            reward = temp_reward * (2 * (np.sum(self.state)-7.5) ** 2 + 2.5)
        else:
            reward = temp_reward * (-2 * (np.sum(self.state)-7.5) ** 2 + 2.5)

        # Calculating the reward -- need to come back to this part and actually make a reward function
        '''if sum(self.state) >= 9 and sum(self.state) <= 11: 
       reward = dayOfWeek
    else: 
       reward = -dayOfWeek'''

        if self.trials <= 0:
            done = True
        else:
            done = False

        info = {}

        return self.state, reward, done, info

    def reset(self):
        self.state = [3, 3, 1, 2]
        self.trials = 25
        return self.state


env = CustomEnv()

dayOfWeek = 1
episodes = 25
for episode in range(1, episodes+1):
    state = env.reset()
    done = False
    score = 0

    while not done:
        action = env.action_space.sample()
        n_state, reward, done, info = env.step(action)
        score += reward
    print('Episode:{}.  Score:{}.  State:{}.  ASDF:{}'.format(
        episode, score, state, np.sum(state)))


states = env.observation_space.shape
actions = env.action_space.n


def build_model(states, actions):
    model = Sequential()
    model.add(Dense(24, activation='relu', input_shape=(1, 4)))
    model.add(Dense(24, activation='relu'))
    model.add(Flatten())
    model.add(Dense(actions, activation='linear'))
    return model


model = build_model(states, actions)

model.summary()


def build_agent(model, actions):
    policy = BoltzmannQPolicy()
    memory = SequentialMemory(limit=50000, window_length=1)
    dqn = DQNAgent(model=model, memory=memory, policy=policy,
                   nb_actions=actions, nb_steps_warmup=10, target_model_update=1e-2)
    return dqn


dayOfWeek = 2
dqn = build_agent(model, actions)
dqn.compile(Adam(lr=1e-3), metrics=['mae'])
dqn.fit(env, nb_steps=10000, visualize=False, verbose=1)

dqn.recent_action
dqn.recent_observation
# dqn.get_config
#print('Episode:{}.  Score:{}.  State:{}'.format(episode, score, state))

#results = dqn.test(env, nb_episodes=150, visualize=False)
# print(np.mean(results.history['episode_reward']))

print(dqn.recent_action)
print(dqn.recent_observation)
print(dayOfWeek)

dqn.get_config
model.summary()

model.save('saved_model/Tuesday')

"""For each day, train the model, and output dqn.recent_observation

Reward func() should optimize for flow between areas, minimizing time, and penalize scenarios where there are just 12 buses each (some sort of sin function for reward with a peak around 7-8 buses) 
"""

print(dayOfWeek, dqn.recent_observation)

dayOfWeek = 1
for i in range(5):
    dqn = build_agent(model, actions)
    dqn.compile(Adam(lr=1e-3), metrics=['mae'])
    dqn.fit(env, nb_steps=1000, visualize=False, verbose=1)
    print(dayOfWeek, dqn.recent_observation)
    dayOfWeek += 1