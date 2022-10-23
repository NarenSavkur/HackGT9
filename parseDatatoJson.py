import json
import requests
from bs4 import BeautifulSoup
from datetime import *

r = requests.Session()


def to24hr(x):
    print(x)
    m2 = str(datetime.strptime(x, '%I:%M %p'))[11:16].split(":")
    for i in range(2):
        m2[i] = int(m2[i])
    if m2[1] > 30:
        m2[0] += 1
    if m2[0] == 24:
        m2[0] = 0
    return m2[0]


def periodToNumber(x):
    final = []
    x = x.upper().split(" - ")
    final.append(to24hr(x[0]))
    final.append(to24hr(x[1]))
    return final


alldata = r.get("https://gt-scheduler.github.io/crawler/202008.json").json()
classes = alldata["courses"]
loc = alldata["caches"]["locations"]
periods = alldata["caches"]["periods"]
data = {}

for key in classes:
    sections = classes[key][1]
    for i in sections:
        crn = sections[i][0]
        if sections[i][4] != 0:
            continue
        try:
            currData = sections[i][1][0]
            if periods[currData[0]] == "TBA" or currData[2] == "TBA" or loc[currData[3]] == None:
                continue
            data[crn] = {}
            data[crn]["section"] = i
            data[crn]["name"] = key
            period = periodToNumber(periods[currData[0]])
            data[crn]["start"] = period[0]
            data[crn]["end"] = period[1]
            data[crn]["building"] = currData[2]
            data[crn]["location"] = loc[currData[3]]
            data[crn]["days"] = currData[1]
            for i in currData[1]:
                t = {"M": False, "T": False, "W": False, "R": False, "F": False}
                for j in currData[1]:
                    t[j] = True
                data[crn]["days"] = t
        except:
            pass


y = 0
for crn in data:
    try:
        x = r.get(
            "https://gt-scheduler.azurewebsites.net/proxy/class_section?term=202208&crn=" + crn).text
        soup = BeautifulSoup(x, 'html.parser')
        tempData = []
        for x in soup.find_all("td", {"class": "dddefault"}):
            if len(str(x)) < 40:
                tempData.append(int(x.text))
        data[crn]["seats"] = {}
        data[crn]["seats"]["aCap"] = tempData[0]
        data[crn]["seats"]["aAc"] = tempData[1]
        data[crn]["seats"]["aRe"] = tempData[2]
        print(str(y) + " Completed")
        y += 1
    except:
        print("Some Error on " + str(crn))
        pass

print(data)
g = open("cleanData.json", "w")
g.write(str(data))
g.close()
