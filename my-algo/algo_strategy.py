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
        # target defence structure
        self.target_support_locations = [[6, 10], [21, 10], [13, 3], [14, 3], [13, 2], [14, 2]]
        self.target_turret_locations = [[1, 12], [2, 12], [6, 12], [7, 12], [12, 12], [13, 12], [14, 12], [19, 12], [20, 12], [21, 12], [25, 12], [26, 12], [4, 10], [9, 10], [10, 10], [16, 10], [17, 10], [23, 10]]
        self.target_wall_locations = [[0, 13], [1, 13], [2, 13], [6, 13], [7, 13], [12, 13], [13, 13], [14, 13], [19, 13], [20, 13], [21, 13], [25, 13], [26, 13], [27, 13], [3, 13], [24, 13], [9, 11], [10, 11], [16, 11], [17, 11]]

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

            # Only spawn Scouts every other turn
            # Sending more at once is better since attacks can only hit a single scout at a time
            if game_state.turn_number % 2 == 1:
                # To simplify we will just check sending them from back left and right
                scout_spawn_location_options = [[13, 0], [14, 0]]
                best_location = self.least_damage_spawn_location(game_state, scout_spawn_location_options)
                game_state.attempt_spawn(SCOUT, best_location, 1000)

    def build_defences(self, game_state):
        # Useful tool for setting up your base locations: https://www.kevinbai.design/terminal-map-maker
        # More community tools available at: https://terminal.c1games.com/rules#Download

        # Place turrets that attack enemy units
        # attempt_spawn will try to spawn units if we have resources, and will check if a blocking unit is already there
        if game_state.turn_number == 0:
            # Use up all 40 points to spawn first line of defence (13 turrets and 14 walls)
            game_state.attempt_spawn(TURRET, self.target_turret_locations[13:])
            game_state.attempt_spawn(WALL, self.target_wall_locations[14:])
        else:
            # 1st priority: repair buildings with <=30% health (except support) and replace destroyed buildings
            # destroyed[4] is a Boolean, it's true for a player removing their own structure.
            # destroyed[1] is the unit type (int) {0 for wall, 1 for support, 2 for turrets}
            for destroyed in self.destroyed_buildings:
                # replace buildings that we removed ourselves last turn
                location = destroyed[0]
                unit_type = self.unit_type_map[destroyed[1]]
                if destroyed[4] and unit_type == WALL:
                    game_state.attempt_spawn(TURRET, location)
                else:
                    game_state.attempt_spawn(unit_type, location)
            for wall in self.wall_stats:
                hp_percent = wall[2] / L1_WALL_HEALTH
                location = [wall[0], wall[1]]
                if location in self.upgrade_locations:
                    hp_percent = wall[2] / L2_WALL_HEALTH
                if hp_percent <= 0.3:
                    game_state.attempt_remove(location)
            for turret in self.turret_stats:
                hp_percent = turret[2] / TURRET_HEALTH
                location = [turret[0], turret[1]]
                if hp_percent <= 0.3:
                    game_state.attempt_remove(location)

            # 2nd priority: Build any reactive defence
            self.build_reactive_defense(game_state)

            # 3rd priority: build our ideal structure. Take care to not replace turrets by walls 
            game_state.attempt_spawn(SUPPORT, self.target_support_locations[:2])
            game_state.attempt_spawn(TURRET, self.target_turret_locations)
            game_state.attempt_spawn(SUPPORT, self.target_support_locations[2:])
            game_state.attempt_spawn(WALL, self.target_wall_locations)

            # 4th priority: upgrade buildings using importance metric 
            # Importance for turret is based on attack damage, support is based on shield, wall based on damage taken
            # Upgrade order: 2 supports, walls, 4 supports, turrets
            sorted_supports_desc = sorted(self.support_shields.items(), key=lambda item: item[1], reverse=True)
            sorted_turrets_desc = sorted(self.turret_attacks.items(), key=lambda item: item[1], reverse=True)
            sorted_walls_desc = sorted(self.wall_damage.items(), key=lambda item: item[1], reverse=True)
            for (location, _) in sorted_supports_desc[:2]:
                # location is a tuple so we convert to list type
                game_state.attempt_upgrade(list(location))
            for (location, _) in sorted_walls_desc:
                game_state.attempt_upgrade(list(location))
            for (location, _) in sorted_supports_desc[2:]:
                game_state.attempt_upgrade(list(location))
            for (location, _) in sorted_turrets_desc:
                game_state.attempt_upgrade(list(location))

            # If there's spare SP > 10, dont waste it. Replace walls by turrets 1 at a time
            if game_state.get_resource(0) > 10:  
                # remove wall with lowest health, will be replaced by a turret next turn
                w = min(self.wall_stats, key=lambda x: x[2])
                game_state.attempt_remove([w[0], w[1]])

    def build_reactive_defense(self, game_state):
        """
        This function builds reactive defenses based on where the enemy scored on us from.
        We can track where the opponent scored by looking at events in action frames 
        as shown in the on_action_frame function
        """
        # starting from round 30, spawn interceptors
        for location in self.scored_on_locations:
            # Build turret 2 spaces from the side so that it doesn't block our own edge spawn locations
            if location == [2, 11] or location == [25, 11]:
                build_location = location
            elif location[0] <= 13: # left side
                build_location = [location[0] + 2, location[1]]
                if game_state.turn_number > 28:
                    game_state.attempt_spawn(INTERCEPTOR, [16, 2])
            else: # right side
                build_location = [location[0] - 2, location[1]]
                if game_state.turn_number > 28:
                    game_state.attempt_spawn(INTERCEPTOR, [11, 2])
            game_state.attempt_spawn(TURRET, build_location)

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
        return location_options[damages.index(min(damages))]

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
        damage_taken = events["damage"]
        for attack in attacks:
            if attack[3] == 2:
                # turret location as key, turret damage as value
                location = tuple(attack[0])
                self.turret_attacks[location] = self.turret_attacks.get(location, 0) + attack[2]
        for shield in shields:
            # support location as key, total shield amount as value
            location = tuple(shield[0])
            self.support_shields[location] = self.support_shields.get(location, 0) + shield[2]
        for damage in damage_taken:
            if damage[2] == 0:
                # wall location as key, total damage taken as value
                location = tuple(damage[0])
                self.wall_damage[location] = self.wall_damage.get(location, 0) + damage[1]

if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
