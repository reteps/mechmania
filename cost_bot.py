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

import random

logger = Logger()
constants = Constants()


def in_bounds(pos: Position):
    return 0 <= pos.x < 30 and 0 <= pos.y < 50


def add_pos(p1: Position, p2: Position):
    ret = Position(p1.x, p1.y)
    ret.x += p2.x
    ret.y += p2.y
    return ret


def all_moves(game: Game) -> list[Position]:
    pos = game.get_game_state().get_my_player().position

    moves = []

    for dx in range(-20, 20):
        for dy in range(-20, 20):
            dP = Position(dx, dy)
            if game_util.distance(dP, Position(0,0)) < 20 and in_bounds(add_pos(dP, pos)):
                moves.append(add_pos(dP, pos))

    return moves


def best_buy_action(game: Game):
#   plant array, count array, cost, score
    player = game.get_game_state().get_my_player()
    turn = game.get_game_state().turn

    if turn > 150:
        return [], [], 0, 0

    if player.money > 100:
        count = player.money // 100
        return [CropType.DUCHAM_FRUIT], [count], count * 100, count * 2 / 3

    return [], [], 0, 0


def best_harvest_action(game: Game) -> (list[Position], float):
    near_tiles = [
        [0,0],
        [0,1],
        [1,0],
        [-1,0],
        [0,-1]
    ]

    state = game.get_game_state()

    player = state.get_my_player()
    other = state.get_opponent_player()

    if game_util.distance(player.position, other.position) < 3:
        return [], 0

    score = 0
    tiles = []
    for tile in near_tiles:
        pos = add_pos(player.position, Position(tile[0], tile[1]))
        if in_bounds(pos):
            tile = state.tile_map.get_tile(pos.x, pos.y)
            if tile.crop.type != CropType.NONE and tile.scarecrow_effect == 0:
                if tile.turns_left_to_grow == 0:
                    score += tile.crop.value
                    tiles.append(pos)

    return tiles, score


tile_type_multiply = {
    TileType.GREEN_GROCER: 0,
    TileType.F_BAND_OUTER: 2/3,
    TileType.F_BAND_INNER: 1,
    TileType.F_BAND_MID: 5/6,
    TileType.ARID: 0,
    TileType.GRASS: 0,
    TileType.SOIL: 0.5
}


def best_plant_action(game: Game) -> (list[str], list[Position], float):
    near_tiles = [
        [0, 0],
        [-1, 0],
        [1, 0],
        [0, 1],
        [0, -1]
    ]

    state = game.get_game_state()

    player = state.get_my_player()
    other = state.get_opponent_player()

    if game_util.distance(player.position, other.position) < 3:
        return [], [], 0

    score = 0
    tiles = []
    fruit_count = player.seed_inventory[CropType.DUCHAM_FRUIT]

    if fruit_count < 5:
        near_tiles = near_tiles[:fruit_count]

    for tile in near_tiles:
        pos = add_pos(player.position, Position(tile[0], tile[1]))
        if in_bounds(pos):
            tile = state.tile_map.get_tile(pos.x, pos.y)
            if tile.crop.type == "NONE":
                # logger.info(f"{tile.type} {tile_type_multiply[tile.type]}")
                score += tile_type_multiply[tile.type] * 100 * 5/6
                tiles.append(pos)

    # logger.info(f"{tiles}, {score}")

    return ["ducham_fruit"] * len(tiles), tiles, score


def best_action(game: Game) -> (ActionDecision, float):
    state = game.get_game_state()
    player = state.get_my_player()

    if game.get_game_state().tile_map.get_tile(player.position.x, player.position.y).type == TileType.GREEN_GROCER:
        (plant_arr, count_arr, cost, score) = best_buy_action(game)
        if sum(count_arr) == 0:
            return DoNothingDecision(), 0
        return BuyDecision(plant_arr, count_arr), score
    else:
        (harvest, harvest_score) = best_harvest_action(game)
        (crop_types, coords, plant_score) = best_plant_action(game)

        if plant_score > harvest_score:
            if not harvest:
                return DoNothingDecision(), 0

            return HarvestDecision(harvest), harvest_score
        else:
            if not crop_types:
                return DoNothingDecision(), 0

            return PlantDecision(crop_types, coords), plant_score


def score_move(game: Game, move: Position) -> float:
    player = game.get_game_state().get_my_player()
    pos = player.position
    player.position = move
    action, score = best_action(game)
    player.position = pos

    return score


def get_move_decision(game: Game) -> MoveDecision:
    moves = all_moves(game)

    best_score = -10000
    best_move = Position(0, 0)

    for m in moves:
        score = score_move(game, m)

        if score > best_score:
            best_move = m
            best_score = score

    return MoveDecision(best_move)


def get_action_decision(game: Game):
    action, score = best_action(game)
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

        board = game.get_game_state().tile_map

        for row in board.tiles:
            logger.info(f"{[(t.type, t.crop.type) for t in row]}")
        game.send_move_decision(get_move_decision(game))

        try:
            game.update_game()
        except IOError:
            exit(-1)
        game.send_action_decision(get_action_decision(game))


if __name__ == "__main__":
    main()
