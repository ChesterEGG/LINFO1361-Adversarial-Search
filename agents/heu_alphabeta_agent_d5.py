import math


from agents.agent import Agent
from oxono import Game
from heuristics.heuristic_v1 import Evaluator

class AlphaBetaAgent(Agent):
    def __init__(self, player, depth=5):
        super().__init__(player)
        self.depth = depth
        self.evaluator = Evaluator(self.player)

    def act(self, state, remaining_time):
        """
        Détermine la meilleur action en utilisant l'algorithme Alpha-Beta
        """
        best_score = -math.inf
        best_action = None

        # Initialisation de alpha et beta
        alpha = -math.inf
        beta = math.inf

        actions = Game.actions(state)

        # Si il y a qu'une action dispo on le joue directement
        if len(actions) == 1:
            return actions[0]

        for action in actions:
            next_state = state.copy()
            Game.apply(next_state, action)

            # Lancer alpha-beta pour l'adversaire
            score = self.alphabeta(next_state, self.depth - 1,alpha, beta, False)

            if score > best_score:
                best_score = score
                best_action = action

            alpha = max(alpha, score)

        return best_action

    def alphabeta(self, state, depth, alpha, beta, maximize):
        """
        Alpha-Beta algorithme
        """
        if depth == 0:
            return self.evaluator.evaluate(state)
        if Game.is_terminal(state):
            return self.evaluator.evaluate(state)

        # Tour de l'agent (Maximize)
        if maximize:
            max_eval = -math.inf
            actions = Game.actions(state)
            for action in actions:
                next_state = state.copy()
                Game.apply(next_state, action)

                eval_score = self.alphabeta(next_state, depth - 1, alpha, beta, False)
                max_eval = max(eval_score, max_eval)

                alpha = max(alpha, eval_score)

                if beta <= alpha:
                    break

            return max_eval

        # Tour de l'adversaire (Minimize)
        else:
            min_eval = math.inf
            actions = Game.actions(state)
            for action in actions:
                next_state = state.copy()
                Game.apply(next_state, action)

                eval_score = self.alphabeta(next_state, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval_score)

                beta = min(beta, eval_score)

                if beta <= alpha:
                    break

            return min_eval

        
