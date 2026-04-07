import math

from agents.agent import Agent
from oxono import Game
from heuristics.heuristic_v1 import Evaluator


class AlphaBetaAgent(Agent):
    def __init__(self, player, depth=6):
        super().__init__(player)
        self.depth = depth
        self.evaluator = Evaluator(self.player)
        self.killer_moves = [[None, None] for _ in range(self.depth + 1)]

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

        # Triage des actions
        actions = self.sort_action(state, actions, self.depth)

        for action in actions:
            next_state = state.copy()
            Game.apply(next_state, action)

            # Lancer alpha-beta pour l'adversaire
            score = self.alphabeta(next_state, self.depth - 1, alpha, beta, False)

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

            # Triage des actions
            actions = self.sort_action(state, actions, depth)

            for action in actions:
                next_state = state.copy()
                Game.apply(next_state, action)

                eval_score = self.alphabeta(next_state, depth - 1, alpha, beta, False)
                max_eval = max(eval_score, max_eval)

                alpha = max(alpha, eval_score)

                if beta <= alpha:
                    # Enregistrement du killer move
                    if action != self.killer_moves[depth][0]:
                        self.killer_moves[depth][1] = self.killer_moves[depth][0]
                        self.killer_moves[depth][0] = action
                    break

            return max_eval

        # Tour de l'adversaire (Minimize)
        else:
            min_eval = math.inf
            actions = Game.actions(state)

            # Triage des actions
            actions = self.sort_action(state, actions, depth)

            for action in actions:
                next_state = state.copy()
                Game.apply(next_state, action)

                eval_score = self.alphabeta(next_state, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval_score)

                beta = min(beta, eval_score)

                if beta <= alpha:
                    if action != self.killer_moves[depth][0]:
                        self.killer_moves[depth][1] = self.killer_moves[depth][0]
                        self.killer_moves[depth][0] = action
                    break

            return min_eval

    def sort_action(self, state, actions, depth):
        """
        Trie les actions les plus prometteuses à la moins prometteuse en utilisant
        une heuristique rapide O(1)
        """
        board = state.board
        current_player = state.current_player

        def get_action_score(action):
            totem, totem_pos, piece_pos = action
            score = 0
            row, col = piece_pos

            # valoriser les pièce au centre
            if 2 <= row <= 3 and 2 <= col <= 3:
                score += 10
            elif 1 <= row <= 4 and 1 <= col <= 4:
                score += 5

            # Valoriser les alignements
            my_symbol = 'o' if totem == "O" else 'x'
            my_color = current_player

            neighbors = [
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ]

            for r, c in neighbors:
                if 0 <= r < 6 and 0 <= c < 6:
                    cell = board[r][c]
                    if cell is not None:
                        neighbor_symbol, neighbor_color = cell

                        # Si le voisin a la même couleur, c'est prometteur
                        if neighbor_color == my_color:
                            score += 8

                        # Idem pour les symboles
                        if neighbor_symbol == my_symbol:
                            score += 8

            # KIller move
            if action == self.killer_moves[depth][0]:
                score += 50
            elif action == self.killer_moves[depth][1]:
                score += 40

            return score

        return sorted(actions, key= get_action_score, reverse=True)


