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
        global FILTER, ENCRYPTOR, DESTRUCTOR, PING, EMP, SCRAMBLER
        FILTER = config["unitInformation"][0]["shorthand"]
        ENCRYPTOR = config["unitInformation"][1]["shorthand"]
        DESTRUCTOR = config["unitInformation"][2]["shorthand"]
        PING = config["unitInformation"][3]["shorthand"]
        EMP = config["unitInformation"][4]["shorthand"]
        SCRAMBLER = config["unitInformation"][5]["shorthand"]
        # This is a good place to do initial setup
        self.scored_on_locations = []
        self.front_def = [[2, 12], [3, 12], [24, 12], [25, 12], [4, 11], [5, 11], [22, 11], [23, 11]] 


        self.front_filters = [[0, 13], [1, 13], [3, 13], [24, 13], [26, 13], [27, 13], [5, 12], [22, 12]]
        self.maze_encryptors = [[8, 8], [9, 8], [10, 8], [11, 8], [12, 8], [13, 8], [14, 8], [15, 8], [16, 8], [17, 8], [18, 8], [19, 8], [7, 6], [9, 6], [10, 6], [11, 6], [12, 6], [13, 6], [14, 6], [15, 6], [16, 6], [17, 6], [18, 6], [20, 6], [10, 5], [11, 5], [12, 5], [13, 5], [14, 5], [15, 5], [16, 5], [17, 5], [10, 3], [12, 3], [13, 3], [14, 3], [15, 3], [17, 3], [13, 2], [14, 2]].reverse()
        self.mazeL = [[7, 7], [17, 4], [12, 1]]
        self.mazeR = [[20, 7], [10, 4], [15, 1]]
        self.maze_switch = False
        self.maze_on_L = True
        self.blue_destructors_points = [[6, 11], [7, 11], [8, 11], [9, 11], [18, 11], [19, 11], [20, 11], [21, 11], [8, 10], [9, 10], [10, 10], [17, 10], [18, 10], [19, 10], [10, 9], [17, 9]]
        self.blue_filters_points = [[7, 12], [9, 12], [18, 12], [20, 12], [10, 11], [17, 11], [11, 10], [16, 10]]
        self.teal_destructors_points = [[1, 12], [26, 12], [2, 11], [3, 11], [24, 11], [25, 11], [7, 10], [20, 10], [8, 9], [9, 9], [18, 9], [19, 9]]
        self.teal_filters_points = [[8, 12], [19, 12], [12, 10], [15, 10]]

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

        self.starter_strategy(game_state)

        game_state.submit_turn()


    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safely be replaced for your custom algo.
    """


    def starter_strategy(self, game_state):
        """
        For defense we will use a spread out layout and some Scramblers early on.
        We will place destructors near locations the opponent managed to score on.
        For offense we will use long range EMPs if they place stationary units near the enemy's front.
        If there are no stationary units to attack in the front, we will send Pings to try and score quickly.
        """
        # Place frontline
        self.build_frontline(game_state)
        self.build_maze(game_state)
        self.boost_def(game_state)
        self.scrambler_def(game_state)
        if game_state.turn_number % 2 == 1:
            self.ping_atk(game_state)

    def build_frontline(self, game_state):
        """
        Build basic defenses using hardcoded locations.
        Remember to defend corners and avoid placing units in the front where enemy EMPs can attack them.
        """
        # attempt_spawn will try to spawn units if we have resources, and will check if a blocking unit is already there
        game_state.attempt_spawn(FILTER, self.front_filters)
        game_state.attempt_spawn(DESTRUCTOR, self.front_def)
        
    def encryptors_in_maze(self, game_state):
        return sum([game_state.contains_stationary_unit(location) for location in self.maze_encryptors])

    def build_maze(self, game_state):
        game_state.attempt_spawn(ENCRYPTOR, self.maze_encryptors)

        if self.maze_switch: 
            if self.maze_on_L:
                game_state.attempt_spawn(ENCRYPTOR, self.mazeL)
            else:
                game_state.attempt_spawn(ENCRYPTOR, self.mazeR)
            self.maze_on_L = not self.maze_on_L 
            self.maze_switch = False
        else: 
            # Randomly decide whether or not to change maze configuration 
            self.maze_switch = bool(random.getrandbits(1))
            if self.maze_switch: 
                if self.maze_on_L:
                    game_state.attempt_remove(self.mazeR)
                else:
                    game_state.attempt_remove(self.mazeL)
            else:
                if self.maze_on_L:
                    game_state.attempt_spawn(ENCRYPTOR, self.mazeR)
                else:
                    game_state.attempt_spawn(ENCRYPTOR, self.mazeL)

    def boost_def(self, game_state):
        game_state.attempt_spawn(DESTRUCTOR, self.blue_destructors_points[:2:] + self.blue_destructors_points[-2::])
        game_state.attempt_spawn(FILTER, self.blue_filters_points)
        game_state.attempt_spawn(DESTRUCTOR, self.blue_destructors_points)

        game_state.attempt_spawn(FILTER, self.teal_filters_points)
        game_state.attempt_spawn(DESTRUCTOR, self.teal_destructors_points)
    def scrambler_def(self, game_state):
        """
        Send out Scramblers at random locations to defend our base from enemy moving units.
        """
        # Possible deploy locations
        left_scrambler_pts = [[4, 9], [6, 7]]
        right_scrambler_pts = [[23, 9], [21, 7]]

        opponent_bits = game_state.get_resource(game_state.BITS, player_index=1)
        self_bits = game_state.get_resource(game_state.BITS, player_index=0)

        # Remove locations that are blocked by our own firewalls
        # since we can't deploy units there.

        deploy_locations = []

        if (self.maze_on_L or (opponent_bits > 10 and self_bits > 7)):
            deploy_locations.extend(self.filter_blocked_locations(left_scrambler_pts, game_state))
        if (not self.maze_on_L or (opponent_bits > 10 and self_bits > 7)):
            deploy_locations.extend(self.filter_blocked_locations(right_scrambler_pts, game_state))

        # While we have remaining bits to spend lets send out scramblers randomly.
        for location in deploy_locations:
            game_state.attempt_spawn(SCRAMBLER, location)
        return

    def ping_atk(self, game_state):
        # Possible spawn locations
        left_loc = [13, 0]
        right_loc = [14, 0]

        spawn_loc = left_loc if self.maze_on_L else right_loc

        _, damage = self.least_damage_spawn_location(game_state, [spawn_loc])
        self_bits = game_state.get_resource(game_state.BITS, player_index=0)

        num_emps = round(self_bits / 21)

        game_state.attempt_spawn(EMP, spawn_loc, num_emps)
        game_state.attempt_spawn(PING, spawn_loc, 1000)
        return

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
                # Get number of enemy destructors that can attack the final location and multiply by destructor damage
                damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(DESTRUCTOR, game_state.config).damage
            damages.append(damage)

        # Now just return the location that takes the least damage
        return (location_options[damages.index(min(damages))], min(damages))

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
        Full doc on format of a game frame at: https://docs.c1games.com/json-docs.html
        """
        # Let's record at what position we get scored on
        state = json.loads(turn_string)
        events = state["events"]
        breaches = events["breach"]
        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly,
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                gamelib.debug_write("Got scored on at: {}".format(location))
                self.scored_on_locations.append(location)
                gamelib.debug_write("All locations: {}".format(self.scored_on_locations))


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
