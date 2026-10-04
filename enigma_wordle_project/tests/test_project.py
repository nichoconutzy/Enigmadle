"""Regression checks for the separated modules; no third-party packages needed."""
from contextlib import redirect_stdout
import io
import itertools
from pathlib import Path
import random
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from enigma_constants import ALPHABET, ROTOR_SPECS
from enigma_machine import EnigmaMachine, QUOTED_KEYSPACE
from message_protocol import send_message, receive_message
from puzzle import create_puzzle, random_daily_key, DailyKey
from word_bank import ENGLISH_WORDS, load_valid_words
from wordle import WordleGame
import enigma_wordle


class MachineTests(unittest.TestCase):
    def test_reference_ciphertexts(self):
        self.assertEqual(EnigmaMachine().encrypt_string('AAAAA'), 'BDZGO')
        self.assertEqual(EnigmaMachine().encrypt_string('HELLOWORLD'), 'ILBDAAMTAZ')

    def test_double_step(self):
        for rings in ('AAA', 'BCD', 'ZZZ'):
            machine = EnigmaMachine('ADU', ring_settings=rings)
            for expected in ('ADV', 'AEW', 'BFX'):
                machine.encrypt_char('A')
                self.assertEqual(machine.windows, expected)

    def test_all_rotor_orders_and_ring_settings(self):
        rng = random.Random(42)
        for order in itertools.permutations(ROTOR_SPECS, 3):
            for _ in range(10):
                generated = random_daily_key(randomize_rings=True, rng=rng)
                key = DailyKey(order, generated.ring_settings, generated.plugboard_pairs)
                windows = ''.join(rng.choices(ALPHABET, k=3))
                text = ''.join(rng.choices(ALPHABET, k=100))
                machine = key.machine(windows)
                ciphertext = machine.encrypt_string(text)
                self.assertTrue(all(a != b for a, b in zip(text, ciphertext)))
                machine.reset()
                self.assertEqual(machine.encrypt_string(ciphertext), text)

    def test_invalid_plugboard_and_atomic_update(self):
        machine = EnigmaMachine(plugboard='AB')
        original = machine.plugboard.copy()
        for invalid in ('AA', 'AB AC', 'AB AB', 'ABC', 'AB CD EF GH IJ KL MN OP QR ST UV'):
            with self.assertRaises(ValueError):
                machine.set_plugboard(invalid)
            self.assertEqual(machine.plugboard, original)
        machine.set_plugboard('')
        self.assertEqual(machine.plugboard, {})

    def test_keyspace(self):
        self.assertEqual(QUOTED_KEYSPACE, 158962555217826360000)


class ProtocolAndPuzzleTests(unittest.TestCase):
    def test_indicator_and_body_reset(self):
        machine = random_daily_key(rng=random.Random(9)).machine('XYZ')
        packet = send_message(machine, 'APPLE', 'VER', 'ITA')
        self.assertEqual(machine.windows, 'XYZ')
        worker = machine.copy()
        worker.set_windows('VER')
        self.assertEqual(worker.encrypt_string(packet.indicator), 'ITA')
        worker.set_windows('ITA')
        self.assertEqual(worker.encrypt_string(packet.ciphertext), 'APPLE')
        self.assertEqual(receive_message(machine, packet), 'APPLE')
        self.assertEqual(machine.receive_message(packet), 'APPLE')
        self.assertEqual(machine.send_message('APPLE', 'VER', 'ITA'), packet)
        self.assertEqual(machine.windows, 'XYZ')

    def test_shared_puzzles_and_wordle_class(self):
        first = create_puzzle(rng=random.Random(12))
        second = create_puzzle(rng=random.Random(12))
        self.assertEqual(first, second)
        self.assertEqual(len(first.target_word), 5)
        self.assertEqual(len(first.daily_key.plugboard_pairs), 10)
        self.assertEqual(first.daily_key.ring_settings, tuple('AAA'))
        self.assertEqual(receive_message(first.daily_key.machine(), first.transmission), first.target_word)
        self.assertIs(enigma_wordle.WordleGame, WordleGame)
        self.assertIsInstance(first.new_wordle_game(), WordleGame)
        self.assertIsNot(first.new_wordle_game(), first.new_wordle_game())

    def test_word_bank_and_custom_vocabulary(self):
        self.assertEqual(len(ENGLISH_WORDS), len(set(ENGLISH_WORDS)))
        self.assertTrue(all(len(w) == 5 and all(c in ALPHABET for c in w) for w in ENGLISH_WORDS))
        self.assertEqual(load_valid_words([' apple ', 'APPLE', 'NO', None]), ['APPLE'])
        puzzle = create_puzzle(['APPLE'], rng=random.Random(1))
        self.assertEqual(puzzle.target_word, 'APPLE')
        for words in ([], 'APPLE', [None, 'NO']):
            with self.assertRaises(ValueError):
                create_puzzle(words)


class WordleTests(unittest.TestCase):
    def test_duplicate_letter_feedback(self):
        game = WordleGame('APPLE', 'ABCDE')
        self.assertEqual(game.evaluate_guess('ALLEY'), ('🟩🟨⬛🟨⬛', None))
        self.assertEqual(game.guesses, [])

    def test_invalid_guesses_and_six_attempts(self):
        game = WordleGame('APPLE', 'ABCDE')
        for invalid in ('', 'APP', '12345', 'ZZZZZ', None, 'ééééé'):
            self.assertIsNotNone(game.submit_guess(invalid)[1])
            self.assertEqual(len(game.guesses), 0)
        for _ in range(6):
            self.assertIsNone(game.submit_guess('CRANE')[1])
        self.assertEqual(len(game.guesses), 6)
        self.assertTrue(game.game_over)
        self.assertEqual(game.remaining_guesses, 0)
        self.assertIsNotNone(game.submit_guess('APPLE')[1])

    def test_winning_guess_records_once_and_ends_game(self):
        game = WordleGame('APPLE', 'ABCDE')
        self.assertIsNone(game.submit_guess(' apple ')[1])
        self.assertEqual(len(game.guesses), 1)
        self.assertTrue(game.won)
        self.assertTrue(game.game_over)
        self.assertIsNotNone(game.submit_guess('CRANE')[1])


class InterfaceTests(unittest.TestCase):
    def test_terminal_validation_decrypt_repeat_and_win(self):
        puzzle = create_puzzle(['APPLE'], rng=random.Random(7))
        key, packet = puzzle.daily_key, puzzle.transmission
        commands = [
            'ORDER ' + ' '.join(key.rotor_order),
            'RINGS ' + ' '.join(key.ring_settings),
            'PLUG ' + ' '.join(key.plugboard_pairs),
            'INDICATOR',
        ]
        worker = key.machine(packet.open_group)
        message_key = worker.encrypt_string(packet.indicator)
        commands.extend(['ROTORS ' + ' '.join(message_key), 'DECRYPT', 'DECRYPT', 'GUESS ZZZZZ', 'GUESS APPLE'])
        output = io.StringIO()
        with patch.object(enigma_wordle, 'create_puzzle', return_value=puzzle), patch('builtins.input', side_effect=commands), redirect_stdout(output):
            enigma_wordle.play_game()
        text = output.getvalue()
        self.assertEqual(text.count('Body output: APPLE'), 2)
        self.assertIn('Guess must be in the word bank.', text)
        self.assertIn('Success! Message decoded.', text)
        self.assertEqual(text.count('APPLE 🟩🟩🟩🟩🟩'), 1)

    def test_gui_callbacks_and_new_game_reset(self):
        try:
            import GUI
        except ModuleNotFoundError as error:
            if error.name == 'tkinter':
                self.skipTest('Tkinter is not installed')
            raise

        class Widget:
            def __init__(self):
                self.value = ''
                self.properties = {}
            def get(self): return self.value
            def set(self, value): self.value = value
            def configure(self, **values): self.properties.update(values)
            def delete(self, *args): self.value = ''
            def focus_set(self): pass

        app = GUI.EnigmaWordleApp.__new__(GUI.EnigmaWordleApp)
        app.root = None
        app.words = load_valid_words()
        app.allowed_words = set(app.words)
        app.rng = random.Random(5)
        for name in ('key_text', 'intercept_text', 'plug_var', 'output_text', 'status_text', 'guess_entry', 'submit_button'):
            setattr(app, name, Widget())
        for name in ('order_vars', 'ring_vars', 'window_vars'):
            setattr(app, name, [Widget() for _ in range(3)])
        app.grid_labels = [[Widget() for _ in range(5)] for _ in range(6)]
        with patch.object(GUI.messagebox, 'showerror') as errors:
            app.new_game()
            for variable, value in zip(app.order_vars, app.daily_key.rotor_order): variable.set(value)
            for variable, value in zip(app.ring_vars, app.daily_key.ring_settings): variable.set(value)
            app.plug_var.set(' '.join(app.daily_key.plugboard_pairs))
            app.decode_indicator()
            app.run_decrypt()
            output = app.output_text.get()
            app.run_decrypt()
            self.assertEqual(app.output_text.get(), output)
            self.assertTrue(output.endswith(app.game.target_word))
            app.guess_entry.set('ZZZZZ')
            app.submit_guess()
            errors.assert_called_once()
            self.assertEqual(app.game.guesses, [])
            app.guess_entry.set(app.game.target_word)
            app.submit_guess()
            self.assertTrue(app.game_over)
            self.assertEqual(len(app.game.guesses), 1)
            self.assertTrue(all(t.properties['bg'] == app.TILE_COLOURS['🟩'] for t in app.grid_labels[0]))
            app.new_game()
            self.assertFalse(app.game_over)
            self.assertEqual(app.game.guesses, [])
            self.assertEqual(app.guess_entry.properties['state'], 'normal')
            self.assertTrue(all(t.properties['text'] == '' for row in app.grid_labels for t in row))
            wrong = next(w for w in app.words if w != app.game.target_word)
            for _ in range(6):
                app.guess_entry.set(wrong)
                app.submit_guess()
            self.assertTrue(app.game_over)
            self.assertEqual(len(app.game.guesses), 6)
            self.assertEqual(app.submit_button.properties['state'], 'disabled')


if __name__ == '__main__':
    unittest.main()
