import json

contents = json.loads(open('team-honestpotatofarmers.json').read())

with open('team-honestpotatofarmers.json', 'w') as f:
    f.write(json.dumps(contents, indent=2))
contents = json.loads(open('team-starter-bot.json').read())

with open('team-starter-bot.json', 'w') as f:
    f.write(json.dumps(contents, indent=2))
contents = json.loads(open('game.json').read())

with open('game.json', 'w') as f:
    f.write(json.dumps(contents, indent=2))
contents = json.loads(open('engine.json').read())

with open('engine.json', 'w') as f:
    f.write(json.dumps(contents, indent=2))
