from oxono import Game

class Evaluator:
    def __init__(self, player):
        self.player = player

        # poids de l'heuristique
        self.weight_center = 2 # Poids pour le controle du centre
        self.weight_align_2 = 10 # poids pour avoir 2 pions aligner
        self.weight_align_3 = 50 # Poids pour avoir 3 pions aligner
        self.weight_critical = 10000 # Poids pour une victoire imminente
        self.weight_structure = 8000 # Poids pour un alignement de 3 mais totem loin
        self.weight_totem = 2 # Poids de la flexibilité du totem
        self.weight_intersection = 500 # Poids pour une intersection d'alignements
        self.weight_fork = 2000 # Poids pour une fourchettes
        self.weight_teleportation = 4000 # Poids pour la possibilité de téléprotation du totem
        self.weight_kiting = 50 # Poids par case d'éloignement tactique
        self.extension_threshold = (self.weight_critical + self.weight_structure) / 2 # Poids qui détermine une situation critique où les extensions doivent etre appeler

    def evaluate(self, state, current_depth=0):
        """
        Fonction d'évaluation de position utilisé par Minimax ou Alpha-Beta
        """

        # Condition de victiore absolue
        if Game.is_terminal(state):
            utility = Game.utility(state, self.player)
            if utility > 0:
                # Victoire rapide
                return 9999999 + current_depth
            elif utility < 0:
                # Défaite lente
                return -9999999 - current_depth
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

        # Carte des maneces
        # {(row, col): nombre des menaces sur cette case}
        my_threats = {}
        opp_threats = {}


        # Parcourir les 6 lignes et les 6 colonnes
        for i in range(6):
            row_cells = [(state.board[i][col], i , col) for col in range(6)]
            col_cells = [(state.board[row][i], row, i) for row in range(6)]

            # Evaluer les 2 axes
            score += self.score_axis(row_cells, state, my_threats, opp_threats)
            score += self.score_axis(col_cells, state, my_threats, opp_threats)

        # Intersections
        for count in my_threats.values():
            if count >= 2:
                score += self.weight_intersection
        for count in opp_threats.values():
            if count >= 2:
                score -= self.weight_intersection

        # Fourchettes
        if len(my_threats) >= 2:
            score += self.weight_fork
        if len(opp_threats) >= 2:
            score -= self.weight_fork

        totem_O = state.totem_O
        totem_X = state.totem_X

        def manhattan_dist(row1, col1, row2, col2):
            return abs(row1 - row2) + abs(col1 - col2)

        # Attaque, On veut nos totems le plus proche possible de nos alignements
        for row, col in my_threats.keys():
            # On regarde quel totem est le plus proche de la case gagnante
            min_dist = min(manhattan_dist(row, col, totem_O[0], totem_O[1]),
                           manhattan_dist(row, col, totem_X[0], totem_X[1]))
            # Plus nos totems sont loin de la victoire, plus on perd des points
            score -= min_dist * self.weight_kiting

        # Defence, on veut les totems les plus loin possible de leurs alignements
        for row, col in opp_threats.keys():
            min_dist = min(manhattan_dist(row, col, totem_O[0], totem_O[1]),
                           manhattan_dist(row, col, totem_X[0], totem_X[1]))
            # Plus les totems de l'adeversaire sont loin de la victoire, plus on gagne des points
            score += min_dist * self.weight_kiting

        return score

    def score_axis(self, axis, state, my_threats, opp_threats):
        """
        Découpe un axe de 6 cases en 3 fenêtres de 4 case
        """
        current_player = state.current_player

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
            empty_row = -1
            empty_col = -1

            # Compter ce qu'il y'a dans la fenêtre
            for cell, row, col in window:
                if cell is None:
                    empty += 1
                    empty_row, empty_col = row, col
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
            is_reachable = False
            if empty == 1:
                is_reachable = self.can_play_at(state, empty_row, empty_col)
            total_my_pieces = state.pieces_x[self.player] + state.pieces_o[self.player]
            total_opp_pieces = state.pieces_x[1 - self.player] + state.pieces_o[1 - self.player]

            # Si la fenetre contient les 2 couleurs on lui donne un score de 0
            if my_color > 0 and opp_color > 0:
                color_score = 0

            # Opportunité pour moi
            elif my_color == 3 and empty == 1 and total_my_pieces > 0:
                # On enregistre la case comme une menace
                my_threats[(empty_row, empty_col)] = my_threats.get((empty_row, empty_col), 0) +1

                # Si c'est mon tour je vais gagner
                if current_player == self.player and is_reachable:
                    color_score = self.weight_critical
                else:
                    color_score = self.weight_structure
            elif my_color == 2 and empty == 2:
                color_score = self.weight_align_2

            # Menace pour moi
            elif opp_color == 3 and empty == 1 and total_opp_pieces > 0:
                # Enregistre la case comme une menace
                opp_threats[(empty_row, empty_col)] = opp_threats.get((empty_row, empty_col), 0) +1

                if current_player != self.player and is_reachable:
                    color_score = -self.weight_critical
                else:
                    color_score = -self.weight_structure
            elif opp_color == 2 and empty == 2:
                color_score = -self.weight_align_2

        # Logique d'évaluation par symbole

            # Si le fenetre contient les 2 symboles on lui met un score de 0
            if x_count > 0 and o_count > 0:
                symbol_score = 0

                # Cas des 'x'
            elif x_count >= 2 and empty > 0:
                # On vérifie si quelqu'un peut encore jouer des 'x'
                can_my_player_play_x = state.pieces_x[self.player] > 0
                can_opp_player_play_x = state.pieces_x[1 - self.player] > 0

                if x_count == 3 and empty == 1:
                    s_score = 0
                    if can_my_player_play_x:
                        my_threats[(empty_row, empty_col)] = my_threats.get((empty_row, empty_col), 0) + 1
                        # Menace critique si le joueur a la pièce en stock
                        if current_player == self.player and is_reachable:
                            s_score += self.weight_critical
                        else:
                            s_score += self.weight_structure

                    if can_opp_player_play_x:
                        opp_threats[(empty_row, empty_col)] = opp_threats.get((empty_row, empty_col), 0) + 1
                        if current_player != self.player and is_reachable:
                            s_score -= self.weight_critical
                        else:
                            s_score -= self.weight_structure
                    symbol_score = s_score


                elif x_count == 2 and empty == 2:
                    # Alignement de 2 : utile seulement si on a encore des pièces pour construire
                    if can_my_player_play_x or can_opp_player_play_x:
                        symbol_score = self.weight_align_2 if current_player == self.player else -self.weight_align_2

                # Cas des 'o' (Identique en vérifiant state.pieces_o)
            elif o_count >= 2 and empty > 0:
                can_my_player_play_o = state.pieces_o[self.player] > 0
                can_opp_player_play_o = state.pieces_o[1 - self.player] > 0

                if o_count == 3 and empty == 1:
                    s_score= 0
                    if can_my_player_play_o:
                        my_threats[(empty_row, empty_col)] = my_threats.get((empty_row, empty_col), 0) + 1
                        if current_player == self.player and is_reachable:
                            s_score += self.weight_critical
                        else:
                            s_score += self.weight_structure

                    if can_opp_player_play_o:
                        opp_threats[(empty_row, empty_col)] = opp_threats.get((empty_row, empty_col), 0) + 1
                        if current_player != self.player and is_reachable:
                            s_score -= self.weight_critical
                        else:
                            s_score -= self.weight_structure
                    symbol_score = s_score


                elif o_count == 2 and empty == 2:
                    if can_my_player_play_o or can_opp_player_play_o:
                        symbol_score = self.weight_align_2 if current_player == self.player else -self.weight_align_2

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

            # Détection de téléportation
            if free_space == 0:
                if state.current_player == self.player:
                    score += self.weight_teleportation
                else:
                    score -= self.weight_teleportation
            else:

                if state.current_player == self.player:
                    score += free_space * self.weight_totem
                else:
                    score -= free_space * self.weight_totem

        return score

    def can_play_at(self, state, row, col):
        """
        Vérifie si le joueur actuel possède un chemin légal avec l'un des totems
        pour poser une pièce sur la case (row, col)
        """
        board = state.board
        totem_O = state.totem_O
        totem_X = state.totem_X

        # Trouver les cases de destinations valides pour le totem
        valid_destinations = []
        for dest_row, dest_col in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            adj_row, adj_col = row + dest_row, col + dest_col
            if 0 <= adj_row < 6 and 0 <= adj_col < 6:
                if board[adj_row][adj_col] is None and (adj_row, adj_col) != totem_O and (adj_row, adj_col) != totem_X:
                    valid_destinations.append((adj_row, adj_col))

        if not(valid_destinations):
            return False

        # Verifier la teleportation
        for tp_row, tp_col in [totem_O, totem_X]:
            free = 0
            for dest_row, dest_col in [(1,0), (-1,0), (0,1), (0,-1)]:
                n_row, n_col = tp_row + dest_row, tp_col + dest_col
                if 0 <= n_row < 6 and 0 <= n_col < 6 and board[n_row][n_col] is None and (n_row, n_col) != totem_O and (n_row, n_col) != totem_X:
                    free += 1
            if free == 0:
                return True

        # Verifier les lignes droites
        for dest_row, dest_col in valid_destinations:
            for tp_row, tp_col in [totem_O, totem_X]:
                # Mouvement sur la ligne
                if tp_row == dest_row:
                    step = 1 if dest_col > tp_col else -1
                    path_clear = True
                    for c in range(tp_col+ step, dest_col + step, step):
                        if board[tp_row][c] is not None or (tp_row, c) in [totem_O, totem_X]:
                            path_clear = False
                            break
                    if path_clear:
                        return True
                # Mouvement sur la colonne
                elif tp_col == dest_col:
                    step = 1 if dest_row > tp_row else -1
                    path_clear = True
                    for r in range(tp_row +step, dest_row + step, step):
                        if board[r][tp_col] is not None or (r, tp_col) in [totem_O, totem_X]:
                            path_clear = False
                            break
                    if path_clear:
                        return True
        return False


