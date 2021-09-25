from networking.io import Logger
from game import Game
from api import game_util
from model.position import Position
from model.decisions.move_decision import MoveDecision
from model.decisions.action_decision import ActionDecision
from model.decisions.buy_decision import BuyDecision
from model.decisions.harvest_decision import HarvestDecision
from model.decisions.plant_decision import PlantDecision
from model.decisions.do_nothing_decision import DoNothingDecision
from model.decisions.use_item_decision import UseItemDecision
from model.item_type import ItemType
from model.crop_type import CropType
from model.upgrade_type import UpgradeType
from model.game_state import GameState
from model.player import Player
from api.constants import Constants
from enum import Enum
from dataclasses import dataclass
from model.crop_type import CropType
import random
import sys
import json

logger = Logger()
constants = Constants()
GREEN_GROCER_LOCATION = Position(constants.BOARD_WIDTH // 2, 0)
SCARECROW_START_LOCATION = Position(constants.BOARD_WIDTH // 2, GREEN_GROCER_LOCATION.y + 20 + 20 - 2)
SCARECROW_LEFT_PLANT = Position(SCARECROW_START_LOCATION.x - 1, SCARECROW_START_LOCATION.y)
SCARECROW_DECOY_PLANT = Position(SCARECROW_START_LOCATION.x, SCARECROW_START_LOCATION.y - 2)
SCARECROW_DECOY_HARVEST_FROM = Position(SCARECROW_START_LOCATION.x, SCARECROW_START_LOCATION.y - 3)
SCARECROW_RIGHT_PLANT = Position(SCARECROW_START_LOCATION.x + 1, SCARECROW_START_LOCATION.y)
SCARECROW_RUN_LOCATION = Position(SCARECROW_START_LOCATION.x, SCARECROW_START_LOCATION.y - 18)
last_plant: Position = None
scarecrow_seed_limit = 9

class TOP_LEVEL_ACTION(Enum):
    DETERMINE_STALKER = 'Determine if the other bot is a stalker'
    SCARECROW_START = 'Anti-follow scarecrow strat'
    BUY_SEEDS = 'Buying Seeds'
    PLANT_CROPS = 'Planting Crops'
    WAIT_FOR_CROPS = 'Waiting for crops to finish growing'
    HARVEST_CROPS = 'Harvesting crops'
    DODGE_OTHER_PLAYER = 'Move Away From Player'

DETERMINE_STALKER = TOP_LEVEL_ACTION.DETERMINE_STALKER
SCARECROW_START = TOP_LEVEL_ACTION.SCARECROW_START
BUY_SEEDS = TOP_LEVEL_ACTION.BUY_SEEDS
PLANT_CROPS = TOP_LEVEL_ACTION.PLANT_CROPS
WAIT_FOR_CROPS = TOP_LEVEL_ACTION.WAIT_FOR_CROPS
HARVEST_CROPS = TOP_LEVEL_ACTION.HARVEST_CROPS
DODGE_OTHER_PLAYER = TOP_LEVEL_ACTION.DODGE_OTHER_PLAYER


def get_decision_move_maker(phase: TOP_LEVEL_ACTION):
    return phase_to_move_decision[phase]


def get_decision_action_maker(phase: TOP_LEVEL_ACTION):
    return phase_to_action_decision[phase]


current_phase: TOP_LEVEL_ACTION = DETERMINE_STALKER
scarecrow_phase = "BUY_POTATO"

@dataclass
class Move:
    move: MoveDecision
    next_phase: TOP_LEVEL_ACTION


@dataclass
class Action:
    action: ActionDecision
    next_phase: TOP_LEVEL_ACTION


def get_grocer_move(pos: Position) -> MoveDecision:
    '''
    Return the move to the grocer
    '''

    if game_util.distance(pos, GREEN_GROCER_LOCATION) == 0:
        return MoveDecision(pos)
    else:
        decision = MoveDecision(game_util.get_best_move(pos, GREEN_GROCER_LOCATION))
        return decision

def move_towards(pos: Position, to: Position, limit: int = 20) -> MoveDecision:
    '''
    Return the move to the grocer
    '''

    if game_util.distance(pos, to) == 0:
        return MoveDecision(pos)
    else:
        decision = MoveDecision(game_util.get_best_move(pos, to, limit=limit))
        return decision

def buy_seeds_move_decision(game: Game) -> Move:
    global last_plant
    player = game.get_game_state().get_my_player()
    if sum(player.seed_inventory.values()) >= 5:
        last_plant = None
        return Move(MoveDecision(player.position), PLANT_CROPS)
    return Move(get_grocer_move(player.position), BUY_SEEDS)


def plant_crops_move_decision(game: Game) -> Move:
    crop_planting_location = Position(constants.BOARD_WIDTH // 2 + 3,
                                      game_util.center_fertility_row(game.game_state) + 1)

    global last_plant
    player = game.get_game_state().get_my_player()
    if game_util.distance(player.position, crop_planting_location) == 0:
        last_plant = crop_planting_location
        return Move(MoveDecision(player.position), PLANT_CROPS)
    else:
        last_plant = None
        decision = MoveDecision(game_util.get_best_move(player.position, crop_planting_location))
        return Move(decision, PLANT_CROPS)


def wait_for_crops_move_decision(game: Game) -> Move:
    player = game.get_game_state().get_my_player()

    return Move(MoveDecision(player.position), WAIT_FOR_CROPS)


def harvest_crops_move_decision(game: Game) -> Move:
    player = game.get_game_state().get_my_player()
    crop_planting_location = last_plant
    if game_util.distance(player.position, crop_planting_location) == 0:
        return Move(MoveDecision(player.position), HARVEST_CROPS)
    else:
        decision = MoveDecision(game_util.get_best_move(player.position, crop_planting_location))
        return Move(decision, HARVEST_CROPS)

def scarecrow_move_decision(game: Game) -> Move:
    player = game.get_game_state().get_my_player()
    logger.info(f"SCARECROW MOVE PHASE on turn {game.game_state.turn}: {scarecrow_phase}")
    if scarecrow_phase == "BUY_POTATO":
        return Move(move_towards(player.position, GREEN_GROCER_LOCATION), SCARECROW_START)
    elif scarecrow_phase == "PLACE_SCARECROW":
        return Move(move_towards(player.position, SCARECROW_START_LOCATION), SCARECROW_START)
    elif scarecrow_phase == "RUN":
        return Move(move_towards(player.position, SCARECROW_RUN_LOCATION), SCARECROW_START)
    
    elif scarecrow_phase == "DECOY_PLANT":
        return Move(move_towards(player.position, SCARECROW_DECOY_PLANT), SCARECROW_START)
    
    elif scarecrow_phase == "LEFT_PLANT":
        return Move(move_towards(player.position, SCARECROW_LEFT_PLANT), SCARECROW_START)
    elif scarecrow_phase == "RIGHT_PLANT":
        return Move(move_towards(player.position, SCARECROW_RIGHT_PLANT), SCARECROW_START)
    elif scarecrow_phase == "RUN_2":
        return Move(move_towards(player.position, SCARECROW_RUN_LOCATION, limit=7), SCARECROW_START)
    elif scarecrow_phase == "DECOY_HARVEST":
        return Move(move_towards(player.position, SCARECROW_DECOY_HARVEST_FROM), SCARECROW_START)
    elif scarecrow_phase == "LEFT_HARVEST":
        return Move(move_towards(player.position, SCARECROW_LEFT_PLANT), SCARECROW_START)
    elif scarecrow_phase == "RIGHT_HARVEST":
        return Move(move_towards(player.position, SCARECROW_RIGHT_PLANT), SCARECROW_START)
    else:
        logger.debug(f"Unknown phase {scarecrow_phase} in scarecrow")

turn_arrived = None
enemy_is_stalker_bot = False
def determine_stalker_move_decision(game: Game) -> Action:
    global turn_arrived
    global enemy_is_stalker_bot
    # if game.game_state.get_opponent_player().name in ['chairs', 'venkat', 'the_patriots', 'team-starter-bot']:
    #     enemy_is_stalker_bot = True
    #     return Move(move_toward(player.position, GREEN_GROCER_LOCATION), SCARECROW_START)
    player = game.game_state.get_my_player()
    turn = game.game_state.turn
    stalker_location = Position(constants.BOARD_WIDTH // 2 - 5, 5)
    if game_util.distance(player.position, stalker_location) == 0 and turn_arrived is None:
        turn_arrived = turn
    elif turn_arrived is not None and turn - turn_arrived >= 3:
        opp_pos = game.get_game_state().get_opponent_player().position
        if game_util.distance(player.position, opp_pos) <= 2:
            enemy_is_stalker_bot = True
            return Move(move_toward(player.position, GREEN_GROCER_LOCATION), SCARECROW_START)
        else:
            enemy_is_stalker_bot = False
            return Move(move_toward(player.position, GREEN_GROCER_LOCATION), BUY_SEEDS)
    else:
        return Move(move_towards(player.position, stalker_location), SCARECROW_START)
    
    return Action(DoNothingDecision(), DETERMINE_STALKER)
phase_to_move_decision = {
    DETERMINE_STALKER: determine_stalker_move_decision,
    SCARECROW_START: scarecrow_move_decision,
    BUY_SEEDS: buy_seeds_move_decision,
    PLANT_CROPS: plant_crops_move_decision,
    WAIT_FOR_CROPS: wait_for_crops_move_decision,
    HARVEST_CROPS: harvest_crops_move_decision
}


def buy_seeds_action_decision(game: Game) -> Action:
    player = game.get_game_state().get_my_player()
    if game.game_state.turn > 150:
        return Action(DoNothingDecision(), BUY_SEEDS)
    elif game_util.distance(player.position, GREEN_GROCER_LOCATION) == 0:
        if player.money > 1000:
            return Action(BuyDecision(["golden_corn"], [player.money // 1000]), PLANT_CROPS)
        if game.game_state.turn > 139:
            return Action(BuyDecision(["ducham_fruit"], [5]), PLANT_CROPS)
        else:
            return Action(BuyDecision(["ducham_fruit"], [player.money // 100]), PLANT_CROPS)
    else:
        return Action(DoNothingDecision(), BUY_SEEDS)


def manhatten_distance(p1: Position, p2: Position):
    return abs(p1.x - p2.x) + abs(p1.y - p2.y)

def generate_plant_locations(offsets, plant_center: Position):
    return [Position(plant_center.x + x, plant_center.y + y) for (x, y) in offsets]
def plant_crops_action_decision(game: Game) -> Action:
    pos1 = game.get_game_state().get_my_player().position
    pos2 = game.get_game_state().get_opponent_player().position

    if manhatten_distance(pos1, pos2) < 4:
        return Action(DoNothingDecision(), PLANT_CROPS)


    crop_planting_location = last_plant  # Position(Constants.BOARD_WIDTH, game_util.center_fertility_row(game.game_state)+1)

    if crop_planting_location is None or game.game_state.turn < 25:
        return Action(DoNothingDecision(), PLANT_CROPS)

    player = game.get_game_state().get_my_player()

    plant_offsets = [
        [0, 0],
        [1, 0],
        [-1, 0],
        [0, 1],
        [0, -1]
    ]

    actual_locations = generate_plant_locations(plant_offsets, crop_planting_location)
    player = game.get_game_state().get_my_player()
    if game_util.distance(player.position, crop_planting_location) == 0:
        if player.seed_inventory[CropType.GOLDEN_CORN] > 0:
            plant_str = "golden_corn"
            plant_enum = CropType.GOLDEN_CORN
        else:
            if player.seed_inventory[CropType.DUCHAM_FRUIT] == 0:
                return Action(DoNothingDecision(), BUY_SEEDS)
            plant_str = "ducham_fruit"
            plant_enum = CropType.DUCHAM_FRUIT

        plants_in_inventory = player.seed_inventory[plant_enum]

        if plants_in_inventory < 5:
            return Action(PlantDecision([plant_str] * plants_in_inventory, actual_locations[:plants_in_inventory]),
                          WAIT_FOR_CROPS)
        else:
            return Action(PlantDecision([plant_str] * 5, actual_locations), WAIT_FOR_CROPS)
    else:
        return Action(DoNothingDecision(), PLANT_CROPS)


def wait_for_crops_action_decision(game: Game) -> Action:
    # bug checking wrong cell
    crop_planting_location = last_plant

    logger.debug(
        f'growth timer: {game.game_state.tile_map.get_tile(crop_planting_location.x, crop_planting_location.y).crop.growth_timer}')
    logger.debug(
        f'turns left to grow: {game.game_state.tile_map.get_tile(crop_planting_location.x, crop_planting_location.y).turns_left_to_grow}')
    logger.debug(f'crop: {game.game_state.tile_map.get_tile(crop_planting_location.x, crop_planting_location.y).crop}')
    if (game.game_state.tile_map.get_tile(crop_planting_location.x, crop_planting_location.y).crop.growth_timer == 0):
        return Action(DoNothingDecision(), HARVEST_CROPS)
    else:
        return Action(DoNothingDecision(), WAIT_FOR_CROPS)

potatos_harvested = 0
def scarecrow_start_action_decision(game: Game) -> Action:
    global potatos_harvested
    global scarecrow_phase
    logger.info(f"SCARECROW ACTION PHASE on turn {game.game_state.turn}: {scarecrow_phase}")
    player = game.get_game_state().get_my_player()
    my_pos = player.position
    if scarecrow_phase == "BUY_POTATO" and game_util.distance(my_pos, GREEN_GROCER_LOCATION) > 0:
        # Determine amount of harvested seeds
        potatos_harvested = sum(player.harvested_inventory.values())
    if scarecrow_phase == "BUY_POTATO" and game_util.distance(my_pos, GREEN_GROCER_LOCATION) == 0:
        if game.game_state.turn > 130:
            # FEAT: switch to follow bot?
            return Action(DoNothingDecision(), SCARECROW_START)
        else:
            scarecrow_phase = "PLACE_SCARECROW"
            if game.game_state.turn < 10:
                # We need 1 more for the decoy strat
                return Action(BuyDecision(["potato"],[9]), SCARECROW_START)
                # Set new seed limit
            return Action(BuyDecision(["potato"],[potatos_harvested]), SCARECROW_START)
    elif scarecrow_phase == "PLACE_SCARECROW" and game_util.distance(my_pos, SCARECROW_START_LOCATION) == 0:
        scarecrow_phase = "RUN"
        if game.game_state.turn > 5:
            # get_tile(SCARECROW_START).item == Scarecrow:
            plant_offsets = [
                [1, 0],
                [-1, 0],
            ]
            actual_locations = generate_plant_locations(plant_offsets, SCARECROW_START_LOCATION)
            return Action(HarvestDecision(actual_locations), BUY_SEEDS)
        else:
            return Action(UseItemDecision(), SCARECROW_START)
    elif scarecrow_phase == "RUN" and game_util.distance(my_pos, SCARECROW_RUN_LOCATION) == 0:
        if game.game_state.turn > 10:
            scarecrow_phase = "LEFT_PLANT"
        else:
            scarecrow_phase = "DECOY_PLANT"
        return Action(DoNothingDecision(), SCARECROW_START)
    elif scarecrow_phase == "DECOY_PLANT" and game_util.distance(my_pos, SCARECROW_DECOY_PLANT) == 0:

        scarecrow_phase = "LEFT_PLANT"
        return Action(PlantDecision(["potato"], [SCARECROW_DECOY_PLANT]), SCARECROW_START)
    elif scarecrow_phase == "LEFT_PLANT" and game_util.distance(my_pos, SCARECROW_LEFT_PLANT) == 0:
        plant_offsets = [
            [-1, 0],
            [0, 1],
            [0, 0],
            [0, -1]
        ]
        actual_locations = generate_plant_locations(plant_offsets, SCARECROW_LEFT_PLANT)
        scarecrow_phase = "RIGHT_PLANT"
        return Action(PlantDecision(["potato" for _ in range(len(actual_locations))], actual_locations), SCARECROW_START)
    elif scarecrow_phase == "RIGHT_PLANT" and game_util.distance(my_pos, SCARECROW_RIGHT_PLANT) == 0:
        plant_offsets = [
            [1, 0],
            [0, 1],
            [0, -1],
            [0, 0]
        ]
        actual_locations = generate_plant_locations(plant_offsets, SCARECROW_RIGHT_PLANT)
        scarecrow_phase = "RUN_2"
        return Action(PlantDecision(["potato" for _ in range(len(actual_locations))], actual_locations), SCARECROW_START)

    elif scarecrow_phase == "RUN_2" and game_util.distance(my_pos, SCARECROW_RUN_LOCATION) == 0:
        pos2 = game.get_game_state().get_opponent_player().position

        if game_util.distance(SCARECROW_DECOY_PLANT, pos2) > 2:
            scarecrow_phase = "DECOY_HARVEST"
        else:
            scarecrow_phase = "LEFT_HARVEST"
        return Action(DoNothingDecision(), SCARECROW_START)
    elif scarecrow_phase == "DECOY_HARVEST" and game_util.distance(my_pos, SCARECROW_DECOY_HARVEST_FROM) == 0:
        scarecrow_phase = "LEFT_HARVEST"
        return Action(HarvestDecision([SCARECROW_DECOY_PLANT]), SCARECROW_START)

    elif scarecrow_phase == "LEFT_HARVEST" and game_util.distance(my_pos, SCARECROW_LEFT_PLANT) == 0:
        plant_offsets = [
            [-1, 0],
            [0, 1],
            [0, 0],
            [0, -1]
        ]
        actual_locations = generate_plant_locations(plant_offsets, SCARECROW_LEFT_PLANT)
        scarecrow_phase = "RIGHT_HARVEST"
        return Action(HarvestDecision(actual_locations), SCARECROW_START)
    elif scarecrow_phase == "RIGHT_HARVEST" and game_util.distance(my_pos, SCARECROW_RIGHT_PLANT) == 0:
        plant_offsets = [
            [1, 0],
            [0, 1],
            [0, -1],
            [0, 0]
        ]
        actual_locations = generate_plant_locations(plant_offsets, SCARECROW_RIGHT_PLANT)
        return Action(HarvestDecision(actual_locations), BUY_SEEDS)
    else:
        logger.debug("No actions required, doing nothing.")
        return Action(DoNothingDecision(), SCARECROW_START)
def harvest_crops_action_decision(game: Game) -> Action:
    pos1 = game.get_game_state().get_my_player().position
    pos2 = game.get_game_state().get_opponent_player().position

    if manhatten_distance(pos1, pos2) < 4:
        return Action(DoNothingDecision(), HARVEST_CROPS)

    crop_planting_location = last_plant

    possible_harvest_locations = []
    player = game.get_game_state().get_my_player()
    harvest_radius = player.harvest_radius
    for harvest_pos in game_util.within_harvest_range(game.game_state, player.name):
        if game.game_state.tile_map.get_tile(harvest_pos.x, harvest_pos.y).crop.value > 0:
            possible_harvest_locations.append(harvest_pos)

    logger.debug(f"Possible harvest locations={possible_harvest_locations}")

    # If we can harvest something, try to harvest it
    if len(possible_harvest_locations) > 0:
        return Action(HarvestDecision(possible_harvest_locations), BUY_SEEDS)
    else:
        return Action(DoNothingDecision(), HARVEST_CROPS)

def determine_stalker_action_decision(game: Game) -> Action:
    return Action(DoNothingDecision(), DETERMINE_STALKER)
phase_to_action_decision = {
    DETERMINE_STALKER: determine_stalker_action_decision,
    SCARECROW_START: scarecrow_start_action_decision,
    BUY_SEEDS: buy_seeds_action_decision,
    PLANT_CROPS: plant_crops_action_decision,
    WAIT_FOR_CROPS: wait_for_crops_action_decision,
    HARVEST_CROPS: harvest_crops_action_decision
}


def get_move_decision(game: Game) -> Move:
    global current_phase
    """
    Returns a move decision for the turn given the current game state.
    This is part 1 of 2 of the turn.

    Remember, you can only sell crops once you get to a Green Grocer tile,
    and you can only harvest or plant within your harvest or plant radius.

    After moving (and submitting the move decision), you will be given a new
    game state with both players in their updated positions.

    :param: game The object that contains the game state and other related information
    :returns: MoveDecision A location for the bot to move to this turn
    """
    game_state: GameState = game.get_game_state()
    logger.debug(
        f"[Turn {game_state.turn}] Feedback received from engine: {game_state.feedback}")

    # Select your decision here!

    my_player: Player = game_state.get_my_player()
    logger.info(f"Currently at {my_player.position}")
    move = get_decision_move_maker(current_phase)(game)
    logger.info(f'current phase: [{current_phase}]')

    logger.debug(f"[Turn {game_state.turn}] Sending MoveDecision: {move.move}")

    return move


def get_action_decision(game: Game) -> Action:
    global current_phase
    """
    Returns an action decision for the turn given the current game state.
    This is part 2 of 2 of the turn.

    There are multiple action decisions that you can return here: BuyDecision,
    HarvestDecision, PlantDecision, or UseItemDecision.

    After this action, the next turn will begin.

    :param: game The object that contains the game state and other related information
    :returns: ActionDecision A decision for the bot to make this turn
    """

    # elif my_player.money >= crop.get_seed_price() and \
    #         game_state.tile_map.get_tile(pos.x, pos.y).type == TileType.GREEN_GROCER:
    # decision = DoNothingDecision()

    game_state: GameState = game.get_game_state()
    logger.debug(
        f"[Turn {game_state.turn}] Feedback received from engine: {game_state.feedback}")

    # Select your decision here!
    my_player: Player = game_state.get_my_player()
    pos: Position = my_player.position
    logger.info(f"Currently at {my_player.position}")
    action = get_decision_action_maker(current_phase)(game)
    # sum(my_player.seed_inventory.values()) == 0 or
    #          len(my_player.harvested_inventory)):
    logger.debug(f"[Turn {game_state.turn}] Sending ActionDecision: {action.action}")

    return action


def main():
    """
    Competitor TODO: choose an item and upgrade for your bot
    """
    game = Game(ItemType.SCARECROW, UpgradeType.LONGER_LEGS)

    while (True):
        try:
            game.update_game()
        except IOError:
            exit(-1)

        move = get_move_decision(game)
        game.send_move_decision(move.move)
        global current_phase
        current_phase = move.next_phase


        try:
            game.update_game()
        except IOError:
            exit(-1)

        action = get_action_decision(game)
        game.send_action_decision(action.action)
        current_phase = action.next_phase
        if enemy_is_stalker_bot and current_phase == BUY_SEEDS:
            global scarecrow_phase
            current_phase = SCARECROW_START
            scarecrow_phase = "BUY_POTATO"

def fake_main(json):
    game = Game(ItemType.SCARECROW, UpgradeType.LONGER_LEGS)
    i = 0
    while (True):
        try:
            state = json[i]
        except IndexError:
            exit(-1)
        try:
            game.game_state = GameState(state)
        except IOError:
            exit(-1)

        move = get_move_decision(game)
        game.send_move_decision(move.move)
        global current_phase
        current_phase = move.next_phase

        try:
            game.game_state = GameState(state)
        except IOError:
            exit(-1)

        action = get_action_decision(game)
        game.send_action_decision(action.action)
        current_phase = action.next_phase
        i += 1


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        print("Running with fake game")
        json_payload = json.loads(open(sys.argv[1]).read())
        fake_main(json_payload['states'])
    else:
        main()

"""

start -> buy seeds

buy seeds -> plant seeds

plant seeds
- move to specific row
- plant 3x3 grid of Q fruit

wait 15 turns

then harvest seeds (1 turn)
then move back to grocer and sell

buy seeds again

repeat
"""
