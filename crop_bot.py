from actual_bot import Move
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
from model.tile_type import TileType
from model.item_type import ItemType
from model.crop_type import CropType
from model.upgrade_type import UpgradeType
from model.game_state import GameState
from model.player import Player
from api.constants import Constants

import random

logger = Logger()
constants = Constants()

GREEN_GROCER_LOCATION = Position(constants.BOARD_WIDTH // 2, 0)
PLANT_1 = Position(7, 48)
PLANT_2 = Position(7, 47)
phase = "BUY"

def manhatten_distance(p1: Position, p2: Position):
    return abs(p1.x - p2.x) + abs(p1.y - p2.y)

def get_grocer_move(pos: Position, to) -> MoveDecision:
    '''
    Return the move to the grocer
    '''

    if game_util.distance(pos, to) == 0:
        logger.debug(f"ALREADY THERE! {pos}")
        return MoveDecision(pos)
    else:
        logger.debug(f"BEST MOVE: {game_util.get_best_move(pos, to)}")
        logger.debug(f"pos: {pos}")
        logger.debug(f"to: {to}")
        logger.debug(f"manhatten_distance(pos, to) = {manhatten_distance(pos, to)}")
        decision = MoveDecision(game_util.get_best_move(pos, to))
        return decision


def get_move_decision(game: Game) -> MoveDecision:
    player = game.get_game_state().get_my_player()
    if phase == "BUY":
        return get_grocer_move(player.position, GREEN_GROCER_LOCATION)
    elif phase == "MOVE_1":
        return get_grocer_move(player.position, PLANT_1)
    elif phase == "MOVE_2":
        return get_grocer_move(player.position, PLANT_2)
    elif phase == "HARVEST_2":
        return get_grocer_move(player.position, PLANT_2)
    elif phase == "HARVEST_1":
        return get_grocer_move(player.position, PLANT_1)
    elif phase == "DONE":
        return get_grocer_move(player.position, GREEN_GROCER_LOCATION)
    else:
        logger.debug(f"UNEXPECTED PHASE: {phase}")
        return MoveDecision(player.position)
def get_action_decision(game: Game) -> ActionDecision:
    global phase
    player = game.get_game_state().get_my_player()
    logger.debug(f'ACTION {game.game_state.turn} {phase}')
    if phase == "BUY" and game_util.distance(player.position, GREEN_GROCER_LOCATION) == 0:
        phase = "MOVE_1"
        return BuyDecision(["potato","corn","grape","jogan_fruit", "quadrotriticale", "ducham_fruit"], [1 for _ in range(6)])
    elif phase == "MOVE_1" and game_util.distance(player.position, PLANT_1) == 0:
        phase = "MOVE_2"
        plant_offsets = [
            [0, 0],
            [-1, 0],
            [1, 0],
        ]
        actual_locations = [Position(PLANT_1.x + x, PLANT_1.y + y) for (x, y) in plant_offsets]
        return PlantDecision(["potato","corn","grape"], actual_locations)
    elif phase == "MOVE_2" and game_util.distance(player.position, PLANT_2) == 0:
        plant_offsets = [
            [0, 0],
            [-1, 0],
            [1, 0],
        ]
        actual_locations = [Position(PLANT_2.x + x, PLANT_2.y + y) for (x, y) in plant_offsets]
        phase = "HARVEST_2"
        return PlantDecision(["jogan_fruit","quadrotriticale","ducham_fruit"], actual_locations)
    elif phase == "HARVEST_2" and game.game_state.turn >= 100 and game_util.distance(player.position, PLANT_2) == 0:
        phase = "HARVEST_1"
        plant_offsets = [
            [0, 0],
            [-1, 0],
            [1, 0],
        ]
        possible_harvest_locations = [Position(PLANT_2.x + x, PLANT_2.y + y) for (x, y) in plant_offsets]
        return HarvestDecision(possible_harvest_locations)
    elif phase == "HARVEST_1" and game_util.distance(player.position, PLANT_1) == 0:
        phase = "DONE"
        plant_offsets = [
            [0, 0],
            [-1, 0],
            [1, 0],
        ]
        possible_harvest_locations = [Position(PLANT_1.x + x, PLANT_1.y + y) for (x, y) in plant_offsets]
        return HarvestDecision(possible_harvest_locations)
    else:
        return DoNothingDecision()
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
        game_state = game.game_state
        decision = get_move_decision(game)
        logger.debug(f"[Turn {game_state.turn}] Sending MoveDecision: {decision}")

        game.send_move_decision(decision)

        try:
            game.update_game()
        except IOError:
            exit(-1)
        
        decision = get_action_decision(game)
        logger.debug(f"[Turn {game_state.turn}] Sending ActionDecsion: {decision}")

        game.send_action_decision(decision)

if __name__ == "__main__":
    main()


