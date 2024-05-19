import gamelib
import random
import math
import warnings
from sys import maxsize
import json


"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips: 

  - You can analyze action frames by modifying on_action_frame function

  - The GameState.map object can be manually manipulated to create hypothetical 
  board states. Though, we recommended making a copy of the map to preserve 
  the actual current map state.
"""

class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        """ 
        Read in config and perform any initial setup here 
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR
        global L1_WALL_HEALTH, L2_WALL_HEALTH, SUPPORT_HEALTH, TURRET_HEALTH
        WALL = config["unitInformation"][0]["shorthand"]
        L1_WALL_HEALTH = config["unitInformation"][0]["startHealth"]
        L2_WALL_HEALTH = config["unitInformation"][0]["upgrade"]["startHealth"]
        
        SUPPORT = config["unitInformation"][1]["shorthand"]
        SUPPORT_HEALTH = config["unitInformation"][1]["startHealth"]
        
        TURRET = config["unitInformation"][2]["shorthand"]
        TURRET_HEALTH = config["unitInformation"][2]["startHealth"]

        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        # This is a good place to do initial setup
        self.scored_on_locations = []
        self.unit_type_map = { 0: WALL, 1: SUPPORT, 2: TURRET }
        self.spawn_left, self.last_spawn = True, 0
        # target defence structure
        self.left_support_locations = [[11, 4], [10, 8], [12, 3], [13, 2], [12, 4], [13, 4], [13, 3]]
        self.right_support_locations = [[16, 4], [17, 8], [15, 3], [14, 2], [14, 4], [15, 4], [14, 3]]
        self.initial_turret_locations = [[0, 13], [4, 13], [5, 13], [23, 13], [24, 13], [27, 13], [1, 12], [6, 12], [22, 12], [26, 12], [2, 11], [7, 11], [21, 11], [3, 10], [9, 10], [11, 10], [13, 10], [15, 10], [17, 10], [19, 10]] 
        self.right_turret_locations = [[22, 13], [21, 12], [23, 12], [20, 11], [22, 11], [25, 11], [14, 10], [16, 10], [18, 10], [20, 10], [21, 10], [24, 10], [19, 9], [20, 9], [23, 9], [19, 8], [22, 8], [18, 7], [21, 7], [17, 6], [16, 5]]
        self.left_turret_locations = [[3, 13], [4, 12], [5, 12], [5, 11], [6, 11], [6, 10], [7, 10], [8, 10], [10, 10], [12, 10], [4, 9], [7, 9], [8, 9], [5, 8], [8, 8], [6, 7], [9, 7], [10, 6], [11, 5]]
        self.no_building_locations = list(map(tuple, [[1, 13], [2, 13], [25, 13], [26, 13], [2, 12], [3, 12], [24, 12], [25, 12], [3, 11], [4, 11], [23, 11], [24, 11], [4, 10], [5, 10], [22, 10], [23, 10], [5, 9], [6, 9], [21, 9], [22, 9], [6, 8], [7, 8], [20, 8], [21, 8], [7, 7], [8, 7], [19, 7], [20, 7], [7, 6], [8, 6], [9, 6], [19, 6], [20, 6], [8, 5], [9, 5], [18, 5], [19, 5], [9, 4], [10, 4], [17, 4], [18, 4], [10, 3], [11, 3], [16, 3], [17, 3], [11, 2], [12, 2], [15, 2], [16, 2], [12, 1], [13, 1], [14, 1], [15, 1], [13, 0], [14, 0]]))
        self.no_building_locations = set(list(map(tuple, self.left_support_locations)) + list(map(tuple, self.right_support_locations)) + self.no_building_locations)

    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  #Comment or remove this line to enable warnings.

        # Get the current building locations and health
        state = json.loads(turn_state)
        units = state["p1Units"]
        self.wall_stats, self.support_stats, self.turret_stats = units[0], units[1], units[2]
        self.upgrade_locations = units[7]
        self.destroyed_buildings, self.turret_attacks, self.support_shields, self.wall_damage = [], {}, {}, {}

        self.starter_strategy(game_state)

        game_state.submit_turn()


    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safely be replaced for your custom algo.
    """

    def starter_strategy(self, game_state):
        """
        For defense we will use a spread out layout and some interceptors early on.
        We will place turrets near locations the opponent managed to score on.
        For offense we will use long range demolishers if they place stationary units near the enemy's front.
        If there are no stationary units to attack in the front, we will send Scouts to try and score quickly.
        """
        # First, place basic defenses
        self.build_defences(game_state)

        # If it is the first turn, do not attack and wait to see enemy's base
        if game_state.turn_number != 0:
            # Let's figure out their least defended area and send Scouts there.

            # Only spawn when the opponent is not spawning, and we have waited at least 3 turns
            # Must spawn within 5 turns of last spawn
            x = game_state.turn_number - self.last_spawn
            if (game_state.get_resource(1, 1) < 10 and x >= 3) or (x > 3):
                # To simplify we will just check sending them from back left and right
                scout_spawn_location_options = [[13, 0], [14, 0]]
                best_location, min_damage = self.least_damage_spawn_location(game_state, scout_spawn_location_options)
                gamelib.debug_write("Min damage: {}".format(min_damage))
                if min_damage < 20:
                    game_state.attempt_spawn(SCOUT, best_location, 1000)
                else:
                    game_state.attempt_spawn(DEMOLISHER, best_location, 1000)

                if best_location[0] <= 13:
                    self.spawn_left = True
                    support_locations = self.left_support_locations
                else:
                    self.spawn_right = False 
                    support_locations = self.right_support_locations
                
                self.last_spawn = game_state.turn_number
                
            if self.spawn_left:
                support_locations = self.left_support_locations
            else:
                support_locations = self.right_support_locations
            for support_location in support_locations:
                num_spawned = game_state.attempt_spawn(SUPPORT, support_location)
                if num_spawned == 1:
                    break 

    def build_defences(self, game_state):
        # Useful tool for setting up your base locations: https://www.kevinbai.design/terminal-map-maker
        # More community tools available at: https://terminal.c1games.com/rules#Download

        # Place turrets that attack enemy units
        # attempt_spawn will try to spawn units if we have resources, and will check if a blocking unit is already there
        if game_state.turn_number == 0:
            # Use up all 40 points to spawn first line of defence (20 turrets)
            game_state.attempt_spawn(TURRET, self.initial_turret_locations)
        else:
            # 1st priority: repair buildings with <=30% health (except support) and replace destroyed buildings
            # destroyed[4] is a Boolean, it's true for a player removing their own structure.
            # destroyed[1] is the unit type (int) {0 for wall, 1 for support, 2 for turrets}
            for destroyed in self.destroyed_buildings:
                # replace buildings that we removed ourselves last turn
                location = destroyed[0]
                unit_type = self.unit_type_map[destroyed[1]]
                game_state.attempt_spawn(unit_type, location)
            for turret in self.turret_stats:
                hp_percent = turret[2] / TURRET_HEALTH
                location = [turret[0], turret[1]]
                if hp_percent <= 0.3:
                    game_state.attempt_remove(location)

            # 2nd priority: Build any reactive defence
            sorted_turrets_desc = sorted(self.turret_attacks.items(), key=lambda item: item[1], reverse=True)
            gamelib.debug_write("sorted_turrets: {}".format(sorted_turrets_desc))
            self.build_reactive_defense(game_state, sorted_turrets_desc[:5])

            # 3rd priority: build our ideal structure. Build at most 1 support and 5 turrets each turn
            # Support is built after we deploy mobile units (in starter_strategy)
            # build turrets on the side where the turrets attack the most
            if not sorted_turrets_desc or sorted_turrets_desc[0][0] <= 13:     
                game_state.attempt_spawn(TURRET, self.left_turret_locations)
            else:
                game_state.attempt_spawn(TURRET, self.right_turret_locations)

            # 4th priority: upgrade buildings using importance metric 
            # Importance for turret is based on attack damage, support is based on height, wall based on damage taken
            # Upgrade order: support, turrets
            sorted_supports_desc = sorted(self.support_stats, key=lambda x: x[1], reverse=True)
            for (x, y, _, _) in sorted_supports_desc:
                # location is a tuple so we convert to list type
                game_state.attempt_upgrade([x, y])
            for (location, _) in sorted_turrets_desc:
                game_state.attempt_upgrade(list(location))

            # If there's spare SP > 10, dont waste it. Add 1 turret at any random location that is not a forbidden(no building) location
            # no building locations are specified so that we don't block the path of mobile units
            if game_state.get_resource(0) > 10:  
                self.build_relevant_turrets(self, game_state, sorted_turrets_desc[5:])

    def build_relevant_turrets(self, game_state, sorted_turrets_desc):
        # Based on importance metrics, add turrets near the turrets that attack the most
        for (location, _) in sorted_turrets_desc:
                x, y = location 
                for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    spawn_loc = (x + dx, y + dy)
                    if spawn_loc not in self.no_building_locations:
                        game_state.attempt_spawn(list(spawn_loc))
                if game_state.get_resource(0) < 2:
                    return
                
    def build_reactive_defense(self, game_state, sorted_turrets_desc):
        """
        This function builds reactive defenses based on where the enemy scored on us from.
        We can track where the opponent scored by looking at events in action frames 
        as shown in the on_action_frame function
        """
        self.build_relevant_turrets(game_state, sorted_turrets_desc)

        for location in self.scored_on_locations:
            if location[0] <= 13: # left side
                build_location = [location[0] + 3, location[1]]
            else: # right side
                build_location = [location[0] - 3, location[1]]
            num_spawned = game_state.attempt_spawn(TURRET, build_location)
            if num_spawned == 0:
                game_state.attempt_upgrade(build_location)

        # spawn interceptor when the enemy MP >= 14, choose the side of the turret that attacked the most
        if game_state.get_resource(1, 1) >= 14 and game_state.turn_number > 28:
            turret_most_attack_location = sorted_turrets_desc[0][0]
            if turret_most_attack_location <= 13: 
                game_state.attempt_spawn(INTERCEPTOR, [7, 6])
            else:
                game_state.attempt_spawn(INTERCEPTOR, [20, 6])

    # To make sure the path of the interceptor is blocked so it goes up instead of to the opposite side
    # def check_interceptor_path(self, game_state, left=True):
    #     if left:
    #         path = game_state.find_path_to_edge([7, 6])

    #     else:
    #         path = game_state.find_path_to_edge([20, 6])

    def least_damage_spawn_location(self, game_state, location_options):
        """
        This function will help us guess which location is the safest to spawn moving units from.
        It gets the path the unit will take then checks locations on that path to 
        estimate the path's damage risk.
        """
        damages = []
        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0
            for path_location in path:
                # Get number of enemy turrets that can attack each location and multiply by turret damage
                damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(TURRET, game_state.config).damage_i
            damages.append(damage)
        
        # Now just return the location that takes the least damage
        return location_options[damages.index(min(damages))], min(damages)

    def detect_enemy_unit(self, game_state, unit_type=None, valid_x = None, valid_y = None):
        total_units = 0
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and (unit_type is None or unit.unit_type == unit_type) and (valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
                        total_units += 1
        return total_units
        
    def filter_blocked_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered

    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called 
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at in json-docs.html in the root of the Starterkit.
        """
        # Let's record at what position we get scored on
        state = json.loads(turn_string)
        events = state["events"]
        breaches = events["breach"]
        for breach in breaches:
            location = breach[0]
            unit_owner_self = breach[4] == 1
            # When parsing the frame data directly, 
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                gamelib.debug_write("Got scored on at: {}".format(location))
                self.scored_on_locations.append(location)
                gamelib.debug_write("All locations: {}".format(self.scored_on_locations))

        # Track if enemy destoryed our buildings
        deaths = events["death"]
        for death in deaths:
            # death[4] is a Boolean, it's true for a player removing their own structure.
            # death[3] is player id, 1 for myself
            # death[0] is the location, death[1] is the unit type (int) {0 for wall, 1 for support, 2 for turrets}
            if death[3] == 1 and death[1] < 3:
                self.destroyed_buildings.append(death)

        # Track turret attacks, support shielding and wall damage taken to calculate importance
        attacks = events["attack"]
        shields = events["shield"]
        # damage_taken = events["damage"]
        for attack in attacks:
            if attack[3] == 2:
                # turret location as key, turret damage as value
                location = tuple(attack[0])
                self.turret_attacks[location] = self.turret_attacks.get(location, 0) + attack[2]
        for shield in shields:
            # support location as key, total shield amount as value
            location = tuple(shield[0])
            self.support_shields[location] = self.support_shields.get(location, 0) + shield[2]
            gamelib.debug_write("Support at {sup} gave shield value {amt} to {id}".format(sup=location, amt=shield[2], id=shield[5]))
        # for damage in damage_taken:
        #     if damage[2] == 0:
        #         # wall location as key, total damage taken as value
        #         location = tuple(damage[0])
        #         self.wall_damage[location] = self.wall_damage.get(location, 0) + damage[1]

if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
