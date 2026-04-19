from oxono import Game


class Evaluator:
    def __init__(self, player, custom_weights=None):
        self.player = player

        # Poids de base (Version 4 stable)
        self.weight_center = 2.0
        self.weight_align_2 = 10.0
        self.weight_align_3 = 8000
        self.weight_critical = 10000.0  # Reste gelé (Ancrage absolu)
        self.weight_totem = 2.0
        self.weight_intersection = 500.0
        self.weight_fork = 2000.0
        self.weight_teleportation = 4000.0
        self.weight_kiting = 50.0

        # Injection des poids génétiques si on est en phase d'entraînement
        if custom_weights:
            self.weight_center = custom_weights.get('center', self.weight_center)
            self.weight_align_2 = custom_weights.get('align_2', self.weight_align_2)
            self.weight_align_3 = custom_weights.get('align_3', self.weight_align_3)
            self.weight_totem = custom_weights.get('totem', self.weight_totem)
            self.weight_intersection = custom_weights.get('intersection', self.weight_intersection)
            self.weight_fork = custom_weights.get('fork', self.weight_fork)
            self.weight_teleportation = custom_weights.get('teleportation', self.weight_teleportation)
            self.weight_kiting = custom_weights.get('kiting', self.weight_kiting)

        self.extension_threshold = (self.weight_critical + self.weight_align_3) / 2

    def evaluate(self, state, current_depth=0):
        # Condition de victoire absolue
        if Game.is_terminal(state):
            utility = Game.utility(state, self.player)
            if utility > 0:
                return 9999999 + current_depth
            elif utility < 0:
                return -9999999 - current_depth
            else:
                return 0

        # Calcul du score positionnel (Sans mobilité ni famine)
        score = 0
        score += self.evaluate_center(state) * self.weight_center
        score += self.evaluate_alignements(state)
        score += self.evaluate_totem(state)

        return score

    def evaluate_center(self, state):
        score = 0
        center = [(2, 2), (2, 3), (3, 2), (3, 3)]
        external_center = [
            (1, 1), (1, 2), (1, 3), (1, 4),
            (2, 1), (2, 4), (3, 1), (3, 4),
            (4, 1), (4, 2), (4, 3), (4, 4)
        ]

        for row, col in center:
            cell = state.board[row][col]
            if cell is not None:
                _, player = cell
                if player == self.player:
                    score += 4
                else:
                    score -= 4

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
        score = 0
        my_threats = {}
        opp_threats = {}

        for i in range(6):
            row_cells = [(state.board[i][col], i, col) for col in range(6)]
            col_cells = [(state.board[row][i], row, i) for row in range(6)]
            score += self.score_axis(row_cells, state, my_threats, opp_threats)
            score += self.score_axis(col_cells, state, my_threats, opp_threats)

        for count in my_threats.values():
            if count >= 2:
                score += self.weight_intersection
        for count in opp_threats.values():
            if count >= 2:
                score -= self.weight_intersection

        if len(my_threats) >= 2:
            score += self.weight_fork
        if len(opp_threats) >= 2:
            score -= self.weight_fork

        totem_O = state.totem_O
        totem_X = state.totem_X

        def manhattan_dist(row1, col1, row2, col2):
            return abs(row1 - row2) + abs(col1 - col2)

        for row, col in my_threats.keys():
            min_dist = min(manhattan_dist(row, col, totem_O[0], totem_O[1]),
                           manhattan_dist(row, col, totem_X[0], totem_X[1]))
            score -= min_dist * self.weight_kiting

        for row, col in opp_threats.keys():
            min_dist = min(manhattan_dist(row, col, totem_O[0], totem_O[1]),
                           manhattan_dist(row, col, totem_X[0], totem_X[1]))
            score += min_dist * self.weight_kiting

        return score

    def score_axis(self, axis, state, my_threats, opp_threats):
        current_player = state.current_player

        def score_window(window):
            color_score = 0
            symbol_score = 0
            my_color = 0
            opp_color = 0
            x_count = 0
            o_count = 0
            empty = 0
            empty_row = -1
            empty_col = -1

            for cell, row, col in window:
                if cell is None:
                    empty += 1
                    empty_row, empty_col = row, col
                else:
                    symbol, player = cell
                    if player == self.player:
                        my_color += 1
                    else:
                        opp_color += 1
                    if symbol == "x":
                        x_count += 1
                    elif symbol == "o":
                        o_count += 1

            is_reachable = False
            if empty == 1:
                is_reachable = self.can_play_at(state, empty_row, empty_col)

            total_my_pieces = state.pieces_x[self.player] + state.pieces_o[self.player]
            total_opp_pieces = state.pieces_x[1 - self.player] + state.pieces_o[1 - self.player]

            if my_color > 0 and opp_color > 0:
                color_score = 0
            elif my_color == 3 and empty == 1 and total_my_pieces > 0:
                my_threats[(empty_row, empty_col)] = my_threats.get((empty_row, empty_col), 0) + 1
                if current_player == self.player and is_reachable:
                    color_score = self.weight_critical
                else:
                    color_score = self.weight_align_3
            elif my_color == 2 and empty == 2:
                color_score = self.weight_align_2
            elif opp_color == 3 and empty == 1 and total_opp_pieces > 0:
                opp_threats[(empty_row, empty_col)] = opp_threats.get((empty_row, empty_col), 0) + 1
                if current_player != self.player and is_reachable:
                    color_score = -self.weight_critical
                else:
                    color_score = -self.weight_align_3
            elif opp_color == 2 and empty == 2:
                color_score = -self.weight_align_2

            if x_count > 0 and o_count > 0:
                symbol_score = 0
            elif x_count >= 2 and empty > 0:
                can_my_player_play_x = state.pieces_x[self.player] > 0
                can_opp_player_play_x = state.pieces_x[1 - self.player] > 0
                if x_count == 3 and empty == 1:
                    s_score = 0
                    if can_my_player_play_x:
                        my_threats[(empty_row, empty_col)] = my_threats.get((empty_row, empty_col), 0) + 1
                        if current_player == self.player and is_reachable:
                            s_score += self.weight_critical
                        else:
                            s_score += self.weight_align_3
                    if can_opp_player_play_x:
                        opp_threats[(empty_row, empty_col)] = opp_threats.get((empty_row, empty_col), 0) + 1
                        if current_player != self.player and is_reachable:
                            s_score -= self.weight_critical
                        else:
                            s_score -= self.weight_align_3
                    symbol_score = s_score
                elif x_count == 2 and empty == 2:
                    if can_my_player_play_x or can_opp_player_play_x:
                        symbol_score = self.weight_align_2 if current_player == self.player else -self.weight_align_2
            elif o_count >= 2 and empty > 0:
                can_my_player_play_o = state.pieces_o[self.player] > 0
                can_opp_player_play_o = state.pieces_o[1 - self.player] > 0
                if o_count == 3 and empty == 1:
                    s_score = 0
                    if can_my_player_play_o:
                        my_threats[(empty_row, empty_col)] = my_threats.get((empty_row, empty_col), 0) + 1
                        if current_player == self.player and is_reachable:
                            s_score += self.weight_critical
                        else:
                            s_score += self.weight_align_3
                    if can_opp_player_play_o:
                        opp_threats[(empty_row, empty_col)] = opp_threats.get((empty_row, empty_col), 0) + 1
                        if current_player != self.player and is_reachable:
                            s_score -= self.weight_critical
                        else:
                            s_score -= self.weight_align_3
                    symbol_score = s_score
                elif o_count == 2 and empty == 2:
                    if can_my_player_play_o or can_opp_player_play_o:
                        symbol_score = self.weight_align_2 if current_player == self.player else -self.weight_align_2

            return color_score + symbol_score

        axis_score = 0
        for i in range(3):
            window = axis[i: i + 4]
            axis_score += score_window(window)
        return axis_score

    def evaluate_totem(self, state):
        score = 0
        totems = [state.totem_O, state.totem_X]
        board = state.board

        for row, col in totems:
            free_space = 0
            for d_row, d_col in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
                n_row, n_col = row + d_row, col + d_col
                if 0 <= n_row < 6 and 0 <= n_col < 6:
                    if board[n_row][n_col] is None and (n_row, n_col) not in totems:
                        free_space += 1

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
        board = state.board
        totem_O = state.totem_O
        totem_X = state.totem_X

        valid_destinations = []
        for dest_row, dest_col in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            adj_row, adj_col = row + dest_row, col + dest_col
            if 0 <= adj_row < 6 and 0 <= adj_col < 6:
                if board[adj_row][adj_col] is None and (adj_row, adj_col) != totem_O and (adj_row, adj_col) != totem_X:
                    valid_destinations.append((adj_row, adj_col))

        if not (valid_destinations):
            return False

        for tp_row, tp_col in [totem_O, totem_X]:
            free = 0
            for dest_row, dest_col in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                n_row, n_col = tp_row + dest_row, tp_col + dest_col
                if 0 <= n_row < 6 and 0 <= n_col < 6 and board[n_row][n_col] is None and (n_row, n_col) != totem_O and (
                        n_row, n_col) != totem_X:
                    free += 1
            if free == 0:
                return True

        for dest_row, dest_col in valid_destinations:
            for tp_row, tp_col in [totem_O, totem_X]:
                if tp_row == dest_row:
                    step = 1 if dest_col > tp_col else -1
                    path_clear = True
                    for c in range(tp_col + step, dest_col + step, step):
                        if board[tp_row][c] is not None or (tp_row, c) in [totem_O, totem_X]:
                            path_clear = False
                            break
                    if path_clear:
                        return True
                elif tp_col == dest_col:
                    step = 1 if dest_row > tp_row else -1
                    path_clear = True
                    for r in range(tp_row + step, dest_row + step, step):
                        if board[r][tp_col] is not None or (r, tp_col) in [totem_O, totem_X]:
                            path_clear = False
                            break
                    if path_clear:
                        return True
        return False