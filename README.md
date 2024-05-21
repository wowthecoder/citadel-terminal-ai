# Citadel Europe Spring Terminal
This is the repository containing my algorithm for playing the Terminal game. This repo is cloned from the [starter kit](https://github.com/correlation-one/AIGamesStarterKit/tree/master/python-algo), and my code is in `my-algo2-2/algo-strategy.py`. The identically named file in the folder `my-algo1/` is my older version. 

# Introduction and Rules
[Quick start](https://terminal.c1games.com/quickstart)
[Base rules](https://terminal.c1games.com/rules)

Note that in the base rules, the demolisher has a range of 4.5 units, which is longer than the range of turrets (2.5 units, 3.5 when upgraded). So 1 possible strategy would have been to spawn demolisher(s), build a row of walls to keep the demolisher from advancing into the range of enemy turrets, and take out the turrets from far. <br>
However, for this Europe Spring competition, we have slightly different rules. Here are some of the important changes (I can't remember all):
| Units | Before | After | 
| ----- | ------ | ------|
| Demolisher | Cost: 3 MP <br> Damage: 8 | Cost 2 MP <br> Damage: 6 |
| Wall | Level 1 health: 60 | Level 1 health: 40 |
| Turrets | Level 1 range: 2.5 units | Level 1 range: 4.5 units | 

# My strategy

# Results
The competition first pits my bot against 4 preset bosses, of which I won all 4. Subsequently my algo played against other people's algos in a round robin group format. 
I won 2/4 matches and didn't progress far, winding up at 15th position out of 27 teams in the final leaderboard.
However, I am satisfied with my results due to the following limitations I faced:
1. I only had 2 days to complete my algo, since I just finished my exams on the same week. In contrast, the participants were given the entire week from Monday onwards to work on it.
2. My 2 teammates dropped out due to personal reasons, and I am essentially competing as an individual against other 3 men teams.
3. This is also my first time participating.

# Replays
https://terminal.c1games.com/competitions/311
Specifically, replays of my algo (MY-ALGO2-1):

# Ideas for future improvements

