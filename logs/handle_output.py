import sys
import json

output = sys.argv[1]
try:
    [player1, player2] = output.split(',')
except ValueError:
    exit(0)
fail = False
if 'ERROR' in player1:
    with open('logs/team-honestpotatofarmers.json', 'r') as f:
        logs = json.loads(f.read())["Logs"]
        for row in logs:
            if len(row["Exception"]) > 0:
                print("----HONEST POTATO FARMERS HAD AN ERROR---")
                print("----Turn----")
                print(row["Turn"])
                print("----Debug----\n","\n".join(row["Debug"]))
                print("----Info----\n","\n".join(row["Info"]))
                print("----Error----\n","\n".join(row["Exception"]))
                fail = True
if 'ERROR' in player2:
    with open('logs/team-starter-bot.json', 'r') as f:
        logs = json.loads(f.read())["Logs"]
        for row in logs:
            if len(row["Exception"]) > 0:
                print("----STARTER BOT HAD AN ERROR---")
                print("----Turn----")
                print(row["Turn"])
                print("----Debug----\n","\n".join(row["Debug"]))
                print("----Info----\n","\n".join(row["Info"]))
                print("----Error----\n","\n".join(row["Exception"]))
                fail = True
if fail:
    exit(1)