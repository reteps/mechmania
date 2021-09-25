
echo "[status] Simulating Game"
output=$(java -jar engine/mm27-engine.jar -n "team-honestpotatofarmers" -N "team-starter-bot" -e "python3 -u bot.py" -E "python3 -u starter_bot.py")

echo $output;

mv team*.json logs/
mv game.json logs/
mv engine.json logs/

python3 logs/handle_output.py "$output"
cd logs; python3 format.py; cd ..