import math
import time

from agents.agent import Agent
from oxono import Game
from heuristics.heuristic_v2 import Evaluator


# Création d'une exception personnalisée pour le chronomètre
class TimeOutException(Exception):
    pass


class IterativeDeepeningAgent(Agent):
    def __init__(self, player, max_depth=20):
        super().__init__(player)
        self.max_depth = max_depth
        self.evaluator = Evaluator(self.player)

        # On initialise les Killer Moves pour la profondeur maximale possible
        self.killer_moves = [[None, None] for _ in range(self.max_depth + 1)]

        # Variables pour la gestion du temps
        self.start_time = 0
        self.time_limit = 0

        #Variables pour forcer la profondeur 6
        self.min_guaranteed_depth = 6
        self.current_iteration_depth = 1

    def act(self, state, remaining_time):
        """
        Détermine la meilleure action en gérant intelligemment le temps
        """
        self.start_time = time.time()

        # Premier coup instantané
        # Si on a toutes nos pièces, c'est notre premier tour
        if state.pieces_x[self.player] == 8 and state.pieces_o[self.player] == 8:
            actions = Game.actions(state)
            # On utilise le tri qui valorise le centre et on joue le premier choix instantanément
            actions_triees = self.sort_action(state, actions, 1)
            return actions_triees[0]

        # Gestion du temps
        # On calcule le nombre de pièces qu'il nous reste
        remaining_pieces = state.pieces_x[self.player] + state.pieces_o[self.player]

        # On divise le temps restant par les pièces restantes +1 par sécurité pour la fin
        self.time_limit = remaining_time / (remaining_pieces + 1)

        actions = Game.actions(state)

        # Si une seule action dispo, on la joue directement
        if len(actions) == 1:
            return actions[0]

        best_action_global = actions[0]  # Action par défaut (sécurité)

        # Iterative deepning
        try:
            for target_depth in range(1, self.max_depth + 1):
                self.current_iteration_depth = target_depth

                # On lance la recherche pour que cette profondeur
                current_best_action, current_best_score = self.search_root(state, target_depth, actions)

                # Mise à jour du meilleur coup global
                best_action_global = current_best_action

                # Si on a trouvé un coup qui garantit la victoire, on arrête de chercher
                if current_best_score >= 9000000:
                    break

        except TimeOutException:
            # Dépassement du temps autorisé
            pass

        print(self.current_iteration_depth)
        return best_action_global

    def search_root(self, state, depth, actions):
        best_score = -math.inf
        best_action = actions[0]
        alpha = -math.inf
        beta = math.inf

        # Tri des actions
        actions = self.sort_action(state, actions, depth)

        for action in actions:
            # Verification du temps si depth >6
            if self.current_iteration_depth > self.min_guaranteed_depth:
                if time.time() - self.start_time > self.time_limit:
                    raise TimeOutException()

            next_state = state.copy()
            Game.apply(next_state, action)

            score = self.alphabeta(next_state, depth - 1, alpha, beta, False)

            if score > best_score:
                best_score = score
                best_action = action

            alpha = max(alpha, score)

        return best_action, best_score

    def alphabeta(self, state, depth, alpha, beta, maximize):
        """
        Alphabeta algorithme avec vérification du temps ignorée jusqu'à depth 6
        """
        # Vérification du temps si depth > 6
        if self.current_iteration_depth > self.min_guaranteed_depth:
            if time.time() - self.start_time > self.time_limit:
                raise TimeOutException()

        if depth == 0 or Game.is_terminal(state):
            return self.evaluator.evaluate(state)

        # Tour de l'agent (Maximize)
        if maximize:
            max_eval = -math.inf
            actions = Game.actions(state)
            actions = self.sort_action(state, actions, depth)

            for action in actions:
                next_state = state.copy()
                Game.apply(next_state, action)

                eval_score = self.alphabeta(next_state, depth - 1, alpha, beta, False)
                max_eval = max(eval_score, max_eval)
                alpha = max(alpha, eval_score)

                if beta <= alpha:
                    if action != self.killer_moves[depth][0]:
                        self.killer_moves[depth][1] = self.killer_moves[depth][0]
                        self.killer_moves[depth][0] = action
                    break
            return max_eval

        # Tour de l'adversaire (Minimize)
        else:
            min_eval = math.inf
            actions = Game.actions(state)
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

            neighbors = [(row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)]

            for r, c in neighbors:
                if 0 <= r < 6 and 0 <= c < 6:
                    cell = board[r][c]
                    if cell is not None:
                        neighbor_symbol, neighbor_color = cell
                        if neighbor_color == my_color:
                            score += 8
                        if neighbor_symbol == my_symbol:
                            score += 8

            # Killer move
            if action == self.killer_moves[depth][0]:
                score += 50
            elif action == self.killer_moves[depth][1]:
                score += 40

            return score

        return sorted(actions, key=get_action_score, reverse=True)