import time
import random
import json
from oxono import Game, State
# Remplace par les vrais noms de tes fichiers
from agents.test_agent import IterativeDeepeningAgent


def mutate_weights(champion_weights, generation):
    """
    Mutation avec décroissance géométrique (40% -> 1%) et utilisation de floats.
    """
    # Baisse de 0.5% par génération. Le 'max' agit comme un filet de sécurité à 1%.
    mutation_rate = max(0.01, 0.40 * (0.990 ** generation))

    challenger = champion_weights.copy()

    # Plus on approche de la fin, moins on touche de variables en même temps
    nb_mutations = random.randint(2, 4) if mutation_rate > 0.10 else 1
    keys_to_mutate = random.sample(list(challenger.keys()), k=nb_mutations)

    for key in keys_to_mutate:
        variation = random.uniform(-mutation_rate, mutation_rate)

        # NOUVEAU : On garde des floats pure ! (Pas de int())
        nouveau_poids = challenger[key] * (1.0 + variation)

        # On s'assure qu'aucun poids ne descend en dessous de 1.0
        challenger[key] = max(1.0, nouveau_poids)

    return challenger


def play_match(weights_A, weights_B, games=8):
    """
    Fait jouer l'agent A (Champion) contre B (Challenger)
    Retourne le score de B.
    """
    score_B = 0

    for i in range(games):
        # Alterne qui commence (Rose ou Noir)
        player_A = 0 if i % 2 == 0 else 1
        player_B = 1 - player_A

        agent_A = IterativeDeepeningAgent(player=player_A, max_depth=10, custom_weights=weights_A)
        agent_B = IterativeDeepeningAgent(player=player_B, max_depth=10, custom_weights=weights_B)

        state = State()  # Assure-toi d'initialiser correctement l'état de ton jeu
        state.last_move = None

        # Pour aller très vite, on ne leur donne que 15 secondes globales par partie !
        # L'agent ira moins profond, mais c'est suffisant pour évaluer l'heuristique.
        time_A = 25.0
        time_B = 25.0

        while not Game.is_terminal(state):
            current_player = state.current_player

            start_time = time.time()
            if current_player == player_A:
                action = agent_A.act(state, time_A)
                time_A -= (time.time() - start_time)
            else:
                action = agent_B.act(state, time_B)
                time_B -= (time.time() - start_time)

            Game.apply(state, action)

        utility = Game.utility(state, player_B)
        if utility > 0:
            score_B += 1
        elif utility == 0:
            score_B += 0.5  # Match nul

    return score_B


if __name__ == "__main__":
    print("🚀 Début de l'entrainement Machine Learning...")

    # Les poids de base par lesquels on commence
    champion_weights = {
        'center': 2.0,
        'align_2': 10.0,
        'align_3': 8000.0,
        'intersection': 500,
        'fork': 2000,
        'teleportation': 4000,
        'kiting': 50.0,
        'totem' : 7.0,
    }

    generation = 1

    try:
        while True:
            print(f"\n--- Génération {generation} ---")

            # 1. Créer un challenger
            challenger_weights = mutate_weights(champion_weights, generation)
            print(f"Test du Challenger avec ces poids : {challenger_weights}")

            # 2. Lancer le combat (8 parties = 4 en Rose, 4 en Noir)
            score_challenger = play_match(champion_weights, challenger_weights, games=8)
            print(f"Résultat du Challenger : {score_challenger} / 8")

            # 3. Évolution (Le Challenger doit gagner strictement plus de la moitié pour remplacer le champion)
            if score_challenger > 4:
                print("🏆 NOUVEAU CHAMPION TROUVÉ ! Mise à jour des poids...")
                champion_weights = challenger_weights

                # SAUVEGARDE SUR LE DISQUE : Très important si ton PC s'éteint cette nuit !
                with open("best_weights.json", "w") as f:
                    json.dump(champion_weights, f, indent=4)
            else:
                print("❌ Le Challenger a échoué. Le Champion conserve son titre.")

            generation += 1

    except KeyboardInterrupt:
        print("\n🛑 Entraînement arrêté manuellement. Meilleurs poids trouvés :")
        print(json.dumps(champion_weights, indent=4))