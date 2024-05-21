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
### Initial version
At first, many teams use a V shape defensive structure with mainly walls on 1 side, and turrets on the other side forming a narrow pathway in.
Example: <br>
![image](https://github.com/wowthecoder/citadel-terminal-ai/assets/82577844/ee318694-b6fe-493a-a3d2-665c6fbc4296) <br>
No matter where you place your mobile units, the walls in the middle will redirect them to the kill zone on the right. \
Here is the replay of my initial algorithm against 2 such opponents: \
[Replay 1](https://terminal.c1games.com/watchLive/13587475) \
[Replay 2](https://terminal.c1games.com/watchLive/13587429)

### Final version
I decided that my defensive structure is too weak and I scrapped it completely, adopting a V-shape structure with 0 walls because walls at level 1 are too weak, and at level 2 I might as well use the 2 points to build a turret instead.
![image](https://github.com/wowthecoder/citadel-terminal-ai/assets/82577844/bc9d1dad-70a4-45de-8c1a-1e5b64b66f7c) <br>
 - I also realised that supports are super important for endgame because the additional health it gives my Mobile units enable them to breach regions with high turret density. As such, I made it a high priority in my code to build/upgrade my supports. <br>
 - For defence, I aim to build out my ideal structure as fast as possible, and repair any buildings with <= 30% health. I also tracked the turrets which deals the most damage to enemy Mobile units, which serves as an indication of how often a region is targeted by the enemy. I then use this information to prioritise upgrading turrets in those highly targeted regions. <br>
 - As for offense, I wrote a function to calculate the path with least damage, and use this least damage to choose between 2 options: if the damage is low, rush their base with fast Scouts; else mow down their defence with Demolishers. <br>
Full details of my logic are well documented in the code file. <br>
**Note**: I did not manage to fully test out version 2.2 (the version in this repo) due to lack of time. I submitted a slightly weaker 2.1 version for the competition.

# Results
The competition first pits my bot against 4 preset bosses, of which I won all 4. Subsequently my algo played against other people's algos in a round robin group format. 
I won 2/4 matches and didn't progress far, winding up at 15th position out of 27 teams in the final leaderboard.
However, I am satisfied with my results due to the following limitations I faced:
1. I only had 2 days to complete my algo, since I just finished my exams on the same week. In contrast, the participants were given the entire week from Monday onwards to work on it.
2. My 2 teammates dropped out due to personal reasons, and I am essentially competing as an individual against other 3 men teams.
3. This is my first time participating.

# Replays
[Leaderboard and all replays](https://terminal.c1games.com/competitions/311)
Specifically, replays of my algo (MY-ALGO2-1):
1. \[WON] https://terminal.c1games.com/watch/13605788
2. \[WON] https://terminal.c1games.com/watch/13605795
3. \[LOST] https://terminal.c1games.com/watch/13605797
4. \[LOST] https://terminal.c1games.com/watch/13605794

# Ideas for future improvements
1. Instead of using turret attacks to identify regions where enemy likes to attack (works for low to mid rating), we should use the `least_damage_spawn_location()` function from the opponent’s perspective to identify weak points in our structure, and reinforce accordingly.
2. Save up MP a few more rounds for a bigger push
3. Refind the `build_reactive_defence()` function, to not just build 1 turret but multiple turrets around the region that we lost points in. Also instead of just building at x+3/x-3, check if we can directly build on the edge instead.
4. Perhaps try RL?

