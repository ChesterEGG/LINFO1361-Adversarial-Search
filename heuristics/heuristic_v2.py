from oxono import Game

class Evaluator:
    def __init__(self, player):
        self.player = player

        # poids de l'heuristique
        self.weight_center = 2 # Poids pour le controle du centre
        self.weight_align_2 = 10 # poids pour avoir 2 pions aligner
        self.weight_align_3 = 50 # Poids pour avoir 3 pions aligner
        self.weight_critical = 10000 # Poids pour une victoire imminente
        self.weight_totem = 2 # Poids de la flexibilité du totem

    def evaluate(self, state):
        """
        Fonction d'évaluation de position utilisé par Minimax ou Alpha-Beta
        """

        # Condition de victiore absolue
        if Game.is_terminal(state):
            utility = Game.utility(state, self.player)
            if utility > 0:
                return 9999999
            elif utility < 0:
                return -9999999
            else:
                return 0

        # Si le jeu peut continuer, on calcule le score positionnel
        score = 0
        score += self.evaluate_center(state) * self.weight_center
        score += self.evaluate_alignements(state)
        score += self.evaluate_totem(state)

        return score

    def evaluate_center(self, state):
        """
        Evalue la présence de nos pièces ou ceux de l'adversaire au centre du plateau

        """
        score = 0

        center = [(2, 2), (2, 3), (3, 2), (3, 3)]

        external_center = [
            (1, 1), (1, 2), (1, 3), (1, 4),
            (2, 1), (2, 4), (3, 1), (3, 4),
            (4, 1), (4, 2), (4, 3), (4, 4)
        ]

        # Evaluation du centre centre
        for row, col in center:

            cell = state.board[row][col]
            if cell is not None:
                _, player = cell
                if player == self.player:
                    score += 4
                else:
                    score -= 4

        # Evaluation du centre externe
        for row, col in external_center:
            cell = state.board[row][col]
            if cell is not None:
                _, player = cell
                if player == self.player:
                    score += 2
                else:
                    score -= 2


        return score

    def evaluate_alignements(self, state):
        """
        Evalue les alignements de 2 ou 3 pièce
        """

        score = 0

        # Parcourir les 6 lignes et les 6 colonnes
        for i in range(6):
            full_row = state.board[i]

            full_col = [state.board[r][i] for r in range(6)]

            # Evaluer les 2 axes
            score += self.score_axis(full_row, state.current_player)
            score += self.score_axis(full_col, state.current_player)

        return score

    def score_axis(self, axis, current_player):
        """
        Découpe un axe de 6 cases en 3 fenêtres de 4 case
        """

        def score_window(window):
            """
            Donne un score à la window
            """
            color_score = 0
            symbol_score = 0

            my_color = 0
            opp_color = 0
            x_count = 0
            o_count = 0
            empty = 0

            # Compter ce qu'il y'a dans la fenêtre
            for cell in window:
                if cell is None:
                    empty += 1
                else:
                    symbol, player = cell

                    # Compter les couleurs
                    if player == self.player:
                        my_color += 1
                    else:
                        opp_color += 1

                    # Compter les symbole
                    if symbol == "x":
                        x_count += 1
                    elif symbol == "o":
                        o_count += 1

            # Logique d'évaluation par couleur

            # Si la fenetre contient les 2 couleurs on lui donne un score de 0
            if my_color > 0 and opp_color > 0:
                color_score = 0

            # Opportunité pour moi
            elif my_color == 3 and empty == 1:
                # Si c'est mon tour je vais gagner
                if current_player == self.player:
                    color_score = self.weight_critical
                else:
                    color_score = self.weight_align_3
            elif my_color == 2 and empty == 2:
                color_score = self.weight_align_2

            # Menace pour moi
            elif opp_color == 3 and empty == 1:
                if current_player != self.player:
                    color_score = -self.weight_critical
                else:
                    color_score = -self.weight_align_3
            elif opp_color == 2 and empty == 2:
                color_score = -self.weight_align_2

        # Logique d'évaluation par symbole

            # Si le fenetre contient les 2 symboles on lui met un score de 0
            if x_count > 0 and o_count > 0:
                symbol_score = 0

            # Si 3 symbole dans la fenêtre, on verifie qui a l'initiative
            elif (x_count == 3 or o_count == 3) and empty == 1:
                if current_player == self.player:
                    symbol_score = self.weight_critical
                else:
                    symbol_score = -self.weight_critical
            # Meme chose pour 2 symbole
            elif (x_count == 2 or o_count == 2) and empty == 2:
                if current_player == self.player:
                    symbol_score = self.weight_align_2
                else:
                    symbol_score = -self.weight_align_2

            return color_score + symbol_score

        axis_score = 0
        for i in range(3):
            window = axis[i : i+4]
            axis_score += score_window(window)
        return axis_score

    def evaluate_totem(self, state):
        """
        Evalue la flexibilité du totem (liberté de mouvement)
        """
        score = 0
        totems = [state.totem_O, state.totem_X]
        board = state.board

        for row, col in totems:
            free_space = 0
            # Regarder les 4 cases adjacent
            for d_row, d_col in [(1,0), (0, 1), (-1, 0), (0, -1)]:
                n_row, n_col = row + d_row, col + d_col
                if 0 <= n_row < 6 and 0 <= n_col < 6:
                    if board[n_row][n_col] is None and (n_row, n_col) not in totems:
                        free_space += 1

            if state.current_player == self.player:
                score += free_space * self.weight_totem
            else:
                score -= free_space * self.weight_totem

        return score

