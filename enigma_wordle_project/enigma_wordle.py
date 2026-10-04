from enigma_constants import ALPHABET, ROTOR_SPECS, REFLECTOR_B
from enigma_machine import EnigmaMachine, QUOTED_KEYSPACE, plugboard_combinations
from message_protocol import Transmission
from puzzle import DailyKey, random_daily_key, create_puzzle
from word_bank import load_valid_words as _load_words
from wordle import WordleGame


def play_game():
    puzzle = create_puzzle()
    target = puzzle.target_word
    daily_key = puzzle.daily_key
    packet = puzzle.transmission
    game = puzzle.new_wordle_game()
    machine = EnigmaMachine()
    print('\nENIGMA-WORDLE: OPERATOR TRAINING')
    print('Daily key (left to right):')
    print('  ORDER:', ' '.join(daily_key.rotor_order))
    print('  RINGS:', ' '.join(daily_key.ring_settings))
    print('  PLUG:', ' '.join(daily_key.plugboard_pairs))
    print(f'Intercept: {packet.open_group} {packet.indicator} {packet.ciphertext}')
    print('First group is open. Decode the indicator there; use its output as body windows.')
    print('The daily key is supplied for a solvable operator exercise.')
    print('Commands: ORDER I II III | RINGS A A A | PLUG A-B X-Y (PLUG alone clears)')
    print('          ROTORS A A A | INDICATOR | DECRYPT | GUESS WORD | QUIT')
    print('INDICATOR uses the open group. DECRYPT uses your entered body windows.')
    while not game.game_over:
        try:
            parts = input(f'\n[{len(game.guesses) + 1}/{game.max_guesses}] > ').upper().split()
        except (EOFError, KeyboardInterrupt):
            print('\nSession ended.')
            return
        if not parts:
            continue
        command, args = parts[0], parts[1:]
        try:
            if command == 'QUIT' and not args:
                return
            if command == 'ORDER' and len(args) == 3:
                machine.set_rotor_order(args)
            elif command == 'RINGS' and len(args) == 3:
                machine.set_ring_settings(args)
            elif command == 'ROTORS' and len(args) == 3:
                machine.set_rotors(*args)
            elif command == 'PLUG':
                machine.set_plugboard(args)
            elif command == 'INDICATOR' and not args:
                worker = machine.copy()
                worker.set_windows(packet.open_group)
                print('Recovered message key:', worker.encrypt_string(packet.indicator))
            elif command == 'DECRYPT' and not args:
                # Copy prevents repeated attempts from advancing the entered windows.
                print('Body output:', machine.copy().encrypt_string(packet.ciphertext))
            elif command == 'GUESS' and len(args) == 1:
                feedback, error = game.submit_guess(args[0])
                if error:
                    print(error)
                    continue
                for word, result in game.guesses:
                    print(word, result)
                if args[0] == target:
                    print('Success! Message decoded.')
                    return
            else:
                print('Invalid command or number of arguments.')
        except ValueError as exc:
            print('Error:', exc)
    print(f'Out of guesses. The word was {target}.')


if __name__ == '__main__':
    play_game()
