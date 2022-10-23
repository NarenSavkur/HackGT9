import csv
import json

f = json.load(open('./cleanData.json','r'))
g = open('./data.csv','w')
header = ['CRN','Class Name','Building','long','lat','Size','start','end','mon','tues','wed','thur','fri']

writer = csv.writer(g)
writer.writerow(header)

for i in f:
    try:
        curr = i
        i = f[i]
        bro = [curr,
        i["name"] + " " + i ["section"],
        i["building"],i["location"]["lat"],
        i["location"]["long"],
        i["seats"]["aAc"],
        i["start"],
        i["end"],
        i["days"]["M"],
        i["days"]["T"],
        i["days"]["W"],
        i["days"]["R"],
        i["days"]["F"]
        ]
        writer.writerow(bro)
    except:
        pass