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

def main():
    """
    Competitor TODO: choose an item and upgrade for your bot
    """
    game = Game(ItemType.COFFEE_THERMOS, UpgradeType.LONGER_LEGS)

    while (True):
        try:
            game.update_game()
        except IOError:
            exit(-1)

        p1 = game.get_game_state().get_my_player()
        p2 = game.get_game_state().get_opponent_player()

        pos = game_util.get_best_move(p1.position, p2.position, 20)
        game.send_move_decision(MoveDecision(pos))

        try:
            game.update_game()
        except IOError:
            exit(-1)

        near = [
            [0,0],
            [0,1],
            [1,0],
            [-1,0],
            [0,-1]
        ]

        adj = [[n[0] + pos.x, n[1] + pos.y] for n in near]

        r = []
        for s in adj:
            if s[0] >= 0 and s[0] < 30 and s[1] >= 0 and s[1] < 50:
                r.append(Position(s[0], s[1]))

        if r:
            game.send_action_decision(HarvestDecision(r))
        else:
            game.send_action_decision(DoNothingDecision())


if __name__ == "__main__":
    main()
