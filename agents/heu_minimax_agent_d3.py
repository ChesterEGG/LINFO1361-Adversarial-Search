import math


from agents.agent import Agent
from oxono import Game
from heuristics.heuristic_v1 import Evaluator


class MinimaxAgent(Agent):
    def __init__(self, player, depth=3):
        super().__init__(player)
        self.depth = depth
        self.evaluator = Evaluator(self.player)

    def act(self, state, remaining_time):
        """
        Détermine la meilleur action à jouer
        """
        best_score = -math.inf
        best_action = None

        actions = Game.actions(state)

        # Si que une action dispo
        if len(actions) == 1:
            return actions[0]

        for action in actions:
            next_state = state.copy()
            Game.apply(next_state, action)

            # Lancer minimax pour l'adversaire
            score = self.minimax(next_state, self.depth - 1, False)
            if score > best_score:
                best_score = score
                best_action = action

        return best_action

    def minimax(self, state, depth, maximizing):
        """
        Algorithme du minimax
        :param state: L'état du board
        :param depth: la profondeur restante de l'algo minimax
        :param maximizing: True si c'est le tour de notre agent, False sinon
        :return: Le score evaluer du noeud
        """

        # Condition d'arrêt
        if Game.is_terminal(state):
            return self.evaluator.evaluate(state)
        if depth == 0:
            return self.evaluator.evaluate(state)

        # Tour de l'agent
        if maximizing:
            max_eval = -math.inf
            actions = Game.actions(state)
            for action in actions:
                next_state = state.copy()
                Game.apply(next_state, action)
                # Tour de l'adversaire
                eval = self.minimax(next_state, depth - 1, False)
                max_eval = max(max_eval, eval)
            return max_eval

        #Tour de l'adversaire
        else:
            min_eval = math.inf
            actions = Game.actions(state)
            for action in actions:
                next_state = state.copy()
                Game.apply(next_state, action)
                # Tour de l'agent
                eval = self.minimax(next_state, depth - 1, True)
                min_eval = min(min_eval, eval)
            return min_eval




