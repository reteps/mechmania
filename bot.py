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
from model.tile_type import TileType
from model.item_type import ItemType
from model.crop_type import CropType
from model.upgrade_type import UpgradeType
from model.game_state import GameState
from model.player import Player
from api.constants import Constants
from enum import Enum
from dataclasses import dataclass
import random
import sys
import json

logger = Logger()
constants = Constants()
GREEN_GROCER_LOCATION = Position(constants.BOARD_WIDTH // 2, 0)

last_plant = None
    
class TOP_LEVEL_ACTION(Enum):
    BUY_SEEDS = 'Buying Seeds'
    PLANT_CROPS = 'Planting Crops'
    WAIT_FOR_CROPS = 'Waiting for crops to finish growing'
    HARVEST_CROPS = 'Harvesting crops'

BUY_SEEDS = TOP_LEVEL_ACTION.BUY_SEEDS
PLANT_CROPS = TOP_LEVEL_ACTION.PLANT_CROPS
WAIT_FOR_CROPS = TOP_LEVEL_ACTION.WAIT_FOR_CROPS
HARVEST_CROPS = TOP_LEVEL_ACTION.HARVEST_CROPS


phase_transitions = {
    BUY_SEEDS: PLANT_CROPS,
    PLANT_CROPS: WAIT_FOR_CROPS,
    WAIT_FOR_CROPS: HARVEST_CROPS,
    HARVEST_CROPS: BUY_SEEDS
}


def get_decision_move_maker(phase: TOP_LEVEL_ACTION):
    return phase_to_move_decision[phase]

def get_decision_action_maker(phase: TOP_LEVEL_ACTION):
    return phase_to_action_decision[phase]

def get_next_phase(phase: TOP_LEVEL_ACTION):
    return phase_transitions[phase]

current_phase: TOP_LEVEL_ACTION = BUY_SEEDS

@dataclass
class Move:
    move: MoveDecision
    will_complete: bool 

@dataclass
class Action:
    action: ActionDecision
    will_complete: bool

def get_grocer_move(pos: Position) -> Move:
    '''
    Return the move to the grocer
    '''
    
    if game_util.distance(pos, GREEN_GROCER_LOCATION) == 0:
        return Move(MoveDecision(pos), False)
    else:
        decision = MoveDecision(game_util.get_best_move(pos, GREEN_GROCER_LOCATION))
        return Move(decision, False)

def buy_seeds_move_decision(game: Game) -> Move:
    global last_plant
    player = game.get_game_state().get_my_player()
    if sum(player.seed_inventory.values()) >= 3:
        last_plant = None
        return Move(MoveDecision(player.position), True)
    return get_grocer_move(player.position)       

def plant_crops_move_decision(game: Game) -> Move:
    
    crop_planting_location = Position(constants.BOARD_WIDTH // 2 + 3, game_util.center_fertility_row(game.game_state)+1)
    
    global last_plant
    player = game.get_game_state().get_my_player()
    if game_util.distance(player.position, crop_planting_location) == 0:
        last_plant = crop_planting_location
        return Move(MoveDecision(player.position), False)
    else:
        last_plant = None
        decision = MoveDecision(game_util.get_best_move(player.position, crop_planting_location))
        return Move(decision, False)

def wait_for_crops_move_decision(game: Game) -> Move:
    player = game.get_game_state().get_my_player()

    return Move(MoveDecision(player.position), False)

def harvest_crops_move_decision(game: Game) -> Move:
    player = game.get_game_state().get_my_player()
    crop_planting_location = last_plant
    if game_util.distance(player.position, crop_planting_location) == 0:
        return Move(MoveDecision(player.position), False)
    else:
        decision = MoveDecision(game_util.get_best_move(player.position, crop_planting_location))
        return Move(decision, False)
    
phase_to_move_decision = {
    BUY_SEEDS: buy_seeds_move_decision,
    PLANT_CROPS: plant_crops_move_decision,
    WAIT_FOR_CROPS: wait_for_crops_move_decision,
    HARVEST_CROPS: harvest_crops_move_decision
}


def buy_seeds_action_decision(game: Game) -> Action:
    player = game.get_game_state().get_my_player()
    if game.game_state.turn > 150:
        return Action(DoNothingDecision(), False)
    elif game_util.distance(player.position, GREEN_GROCER_LOCATION) == 0:
        if game.game_state.turn > 139:
            return Action(BuyDecision(["ducham_fruit"], [5]), True)
        else:
            return Action(BuyDecision(["ducham_fruit"], [player.money // 100]), True)
    else:
        return Action(DoNothingDecision(), False)

def plant_crops_action_decision(game: Game) -> Action:
    crop_planting_location = last_plant #Position(Constants.BOARD_WIDTH, game_util.center_fertility_row(game.game_state)+1)

    if crop_planting_location is None or game.game_state.turn < 25:
        return Action(DoNothingDecision(), False)

    player = game.get_game_state().get_my_player()

    plant_offsets = [
        # [-1, 0],
        [1, 0],
        [-1, 0],
        # [0, -1],
        [0, 0],
    ]
    #global last_plant
    #last_plant = crop_planting_location
    
    actual_locations = [Position(crop_planting_location.x + x, crop_planting_location.y + y) for (x, y) in plant_offsets]
    if game_util.distance(player.position, crop_planting_location) == 0:
        return Action(PlantDecision(["ducham_fruit"]*3, actual_locations), True)
    else:
        return Action(DoNothingDecision(), False)

def wait_for_crops_action_decision(game: Game) -> Action:
    # bug checking wrong cell
    crop_planting_location = last_plant

    logger.debug(f'growth timer: {game.game_state.tile_map.get_tile(crop_planting_location.x, crop_planting_location.y).crop.growth_timer}')
    logger.debug(f'turns left to grow: {game.game_state.tile_map.get_tile(crop_planting_location.x, crop_planting_location.y).turns_left_to_grow}')
    logger.debug(f'crop: {game.game_state.tile_map.get_tile(crop_planting_location.x, crop_planting_location.y).crop}')
    if (game.game_state.tile_map.get_tile(crop_planting_location.x, crop_planting_location.y).crop.growth_timer == 0):
        return Action(DoNothingDecision(), True)
    else:
        return Action(DoNothingDecision(), False)

def harvest_crops_action_decision(game: Game) -> Action:
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
        return Action(HarvestDecision(possible_harvest_locations), True)
    else:
        return Action(DoNothingDecision(), False)
    
phase_to_action_decision = {
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
    pos: Position = my_player.position
    logger.info(f"Currently at {my_player.position}")
    move = get_decision_move_maker(current_phase)(game)
    # sum(my_player.seed_inventory.values()) == 0 or
    #          len(my_player.harvested_inventory)):
    logger.info(f'current phase: [{current_phase}]')
    if move.will_complete:
        current_phase = get_next_phase(current_phase)
        logger.info('moved on to next phase')

    logger.debug(f"[Turn {game_state.turn}] Sending MoveDecision: {move.move}")
    
    return move.move


def get_action_decision(game: Game) -> ActionDecision:
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
    logger.info(f'current phase: [{current_phase}]')
    if action.will_complete:
        current_phase = get_next_phase(current_phase)
        logger.info('moved on to next phase')

    logger.debug(f"[Turn {game_state.turn}] Sending ActionDecision: {action.action}")
    
    return action.action
    


def main():
    """
    Competitor TODO: choose an item and upgrade for your bot
    """
    game = Game(ItemType.COFFEE_THERMOS, UpgradeType.SCYTHE)
    
    while (True):
        try:
            game.update_game()
        except IOError:
            exit(-1)
        game.send_move_decision(get_move_decision(game))

        try:
            game.update_game()
        except IOError:
            exit(-1)
        game.send_action_decision(get_action_decision(game))



def fake_main(json):
    game = Game(ItemType.COFFEE_THERMOS, UpgradeType.SCYTHE)
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
        game.send_move_decision(get_move_decision(game))

        try:
            game.game_state = GameState(state)
        except IOError:
            exit(-1)
        game.send_action_decision(get_action_decision(game))
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