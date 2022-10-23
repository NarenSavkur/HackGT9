import numpy as np

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