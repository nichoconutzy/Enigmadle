import random
import tkinter as tk
from tkinter import messagebox, ttk

from enigma_constants import ALPHABET
from enigma_machine import EnigmaMachine
from puzzle import create_puzzle
from word_bank import load_valid_words


class EnigmaWordleApp:
    BG = '#20252b'
    TILE_COLOURS = {'🟩': '#538d4e', '🟨': '#b59f3b', '⬛': '#3a3a3c'}

    def __init__(self, root):
        self.root = root
        self.words = load_valid_words()
        self.allowed_words = set(self.words)
        self.rng = random.SystemRandom()
        root.title('Enigma-Wordle Workstation')
        root.geometry('850x860')
        root.minsize(780, 820)
        root.configure(bg=self.BG)
        self._build_interface()
        self.new_game()

    def _build_interface(self):
        style = ttk.Style(self.root)
        style.theme_use('clam')
        style.configure('TFrame', background=self.BG)
        style.configure('TLabel', background=self.BG, foreground='#edf2f7')
        style.configure('TLabelframe', background=self.BG)
        style.configure('TLabelframe.Label', background=self.BG, foreground='#64dfc4')
        style.configure('TButton', padding=6)
        panel = ttk.Frame(self.root, padding=18)
        panel.pack(fill='both', expand=True)
        header = ttk.Frame(panel)
        header.pack(fill='x')
        ttk.Label(header, text='ENIGMA-WORDLE', font=('Helvetica', 18, 'bold')).pack(side='left')
        ttk.Button(header, text='New Game', command=self.new_game).pack(side='right')
        ttk.Label(panel, text='Operator training • five-letter words • six guesses').pack(anchor='w', pady=(5, 12))

        intel = ttk.LabelFrame(panel, text='Intercept and daily key', padding=10)
        intel.pack(fill='x')
        self.key_text = tk.StringVar()
        self.intercept_text = tk.StringVar()
        ttk.Label(intel, textvariable=self.key_text, font=('Courier', 10)).pack(anchor='w')
        ttk.Label(intel, textvariable=self.intercept_text, font=('Courier', 13, 'bold')).pack(anchor='w', pady=8)
        ttk.Label(intel, text='The daily key is supplied so this exercise can be solved.').pack(anchor='w')
        instructions = ('1. Copy the daily rotor order, rings and plugboard into the controls.\n'
                        '2. Decode the indicator at the open group; its output becomes the body windows.\n'
                        '3. Decrypt the five-letter body, then submit your word below.')
        ttk.Label(panel, text=instructions, justify='left').pack(anchor='w', pady=12)

        settings = ttk.LabelFrame(panel, text='Machine settings — LEFT / MIDDLE / RIGHT', padding=10)
        settings.pack(fill='x')
        settings.columnconfigure(1, weight=1)
        self.order_vars = [tk.StringVar() for _ in range(3)]
        self.ring_vars = [tk.StringVar() for _ in range(3)]
        self.window_vars = [tk.StringVar() for _ in range(3)]
        rows = [('Rotor order', self.order_vars, ('I', 'II', 'III', 'IV', 'V')),
                ('Ring settings', self.ring_vars, tuple(ALPHABET)),
                ('Body windows', self.window_vars, tuple(ALPHABET))]
        for row, (label, variables, choices) in enumerate(rows):
            ttk.Label(settings, text=label).grid(row=row, column=0, sticky='w', padx=(0, 15), pady=4)
            controls = ttk.Frame(settings)
            controls.grid(row=row, column=1, sticky='w')
            for variable in variables:
                ttk.Combobox(controls, textvariable=variable, values=choices,
                             state='readonly', width=5).pack(side='left', padx=(0, 8))
        self.plug_var = tk.StringVar()
        ttk.Label(settings, text='Plugboard pairs').grid(row=3, column=0, sticky='w', pady=4)
        ttk.Entry(settings, textvariable=self.plug_var, width=48).grid(row=3, column=1, sticky='ew')
        ttk.Label(settings, text='Example: A-B X-Y • at most 10 pairs • blank clears all cables').grid(
            row=4, column=1, sticky='w', pady=(3, 8))
        actions = ttk.Frame(settings)
        actions.grid(row=5, column=0, columnspan=2, sticky='w')
        ttk.Button(actions, text='Decode Indicator', command=self.decode_indicator).pack(side='left', padx=(0, 8))
        ttk.Button(actions, text='Decrypt Word', command=self.run_decrypt).pack(side='left')
        self.output_text = tk.StringVar()
        ttk.Label(settings, textvariable=self.output_text, font=('Courier', 11, 'bold')).grid(
            row=6, column=0, columnspan=2, sticky='w', pady=(8, 0))

        board = ttk.LabelFrame(panel, text='Wordle grid', padding=8)
        board.pack(fill='x', pady=12)
        self.grid_labels = []
        for _ in range(6):
            row_frame = ttk.Frame(board)
            row_frame.pack(pady=2)
            labels = []
            for _ in range(5):
                tile = tk.Label(row_frame, text='', width=3, font=('Courier', 17, 'bold'),
                                bg='#3a3a3c', fg='white', relief='flat', pady=3)
                tile.pack(side='left', padx=3)
                labels.append(tile)
            self.grid_labels.append(labels)
        guess_panel = ttk.Frame(panel)
        guess_panel.pack(fill='x')
        ttk.Label(guess_panel, text='Five-letter guess:').pack(side='left')
        self.guess_entry = ttk.Entry(guess_panel, width=15, font=('Courier', 13))
        self.guess_entry.pack(side='left', padx=10)
        self.guess_entry.bind('<Return>', lambda event: self.submit_guess())
        self.submit_button = ttk.Button(guess_panel, text='Submit Guess', command=self.submit_guess)
        self.submit_button.pack(side='left')
        self.status_text = tk.StringVar()
        ttk.Label(panel, textvariable=self.status_text, wraplength=740).pack(anchor='w', pady=(10, 0))

    def new_game(self):
        """Generate a new transmission and reset the entire round."""
        puzzle = create_puzzle(self.words, rng=self.rng)
        self.daily_key = puzzle.daily_key
        self.packet = puzzle.transmission
        self.game = puzzle.new_wordle_game()
        self.game_over = False
        self.key_text.set('ORDER: ' + ' '.join(self.daily_key.rotor_order)
                          + '    RINGS: ' + ' '.join(self.daily_key.ring_settings)
                          + '\nPLUG: ' + ' '.join(self.daily_key.plugboard_pairs))
        self.intercept_text.set(f'OPEN: {self.packet.open_group}   INDICATOR: {self.packet.indicator}'
                                f'   BODY: {self.packet.ciphertext}')
        for variable, value in zip(self.order_vars, ('I', 'II', 'III')):
            variable.set(value)
        for variable in self.ring_vars + self.window_vars:
            variable.set('A')
        self.plug_var.set('')
        self.output_text.set('Indicator: ???    Body output: ?????')
        self.status_text.set('0 / 6 guesses used. Configure the machine with the supplied daily key.')
        self.guess_entry.configure(state='normal')
        self.submit_button.configure(state='normal')
        self.guess_entry.delete(0, tk.END)
        for row in self.grid_labels:
            for tile in row:
                tile.configure(text='', bg='#3a3a3c')
        self.guess_entry.focus_set()

    def _configured_machine(self, windows=None):
        """Fresh state makes repeated decryption attempts reproducible."""
        return EnigmaMachine(
            rotors=windows if windows is not None else tuple(v.get() for v in self.window_vars),
            rotor_order=tuple(v.get() for v in self.order_vars),
            ring_settings=tuple(v.get() for v in self.ring_vars),
            plugboard=self.plug_var.get().strip())

    def decode_indicator(self):
        try:
            machine = self._configured_machine(windows=self.packet.open_group)
            recovered_key = machine.encrypt_string(self.packet.indicator)
        except ValueError as error:
            messagebox.showerror('Invalid machine settings', str(error), parent=self.root)
            return
        for variable, letter in zip(self.window_vars, recovered_key):
            variable.set(letter)
        self.output_text.set(f'Indicator output: {recovered_key}    Body output: ?????')
        self.status_text.set('Indicator output copied into body windows. Now select Decrypt Word. '
                             'Incorrect daily settings will produce an incorrect key.')

    def run_decrypt(self):
        try:
            decoded = self._configured_machine().encrypt_string(self.packet.ciphertext)
        except ValueError as error:
            messagebox.showerror('Invalid machine settings', str(error), parent=self.root)
            return
        windows = ''.join(v.get() for v in self.window_vars)
        self.output_text.set(f'Body starting windows: {windows}    Body output: {decoded}')

    def submit_guess(self):
        if self.game_over:
            return
        guess = self.guess_entry.get().strip().upper()
        # Validate here to remain compatible with the original wordle.py.
        if len(guess) != 5 or any(c not in ALPHABET for c in guess):
            messagebox.showerror('Invalid guess', 'Enter exactly five letters A-Z.', parent=self.root)
            return
        if guess not in self.allowed_words:
            messagebox.showerror('Invalid guess', 'That word is not in the word bank.', parent=self.root)
            return
        feedback, error = self.game.evaluate_guess(guess)
        if error:
            messagebox.showerror('Invalid guess', error, parent=self.root)
            return
        row = len(self.game.guesses)
        self.game.guesses.append((guess, feedback))
        for tile, letter, status in zip(self.grid_labels[row], guess, feedback):
            tile.configure(text=letter, bg=self.TILE_COLOURS[status])
        self.guess_entry.delete(0, tk.END)
        if guess == self.game.target_word:
            self._finish(f'Success! You decoded {guess} in {row + 1} / 6 guesses.')
        elif len(self.game.guesses) >= self.game.max_guesses:
            self._finish(f'Out of guesses. The word was {self.game.target_word}.')
        else:
            self.status_text.set(f'{len(self.game.guesses)} / 6 guesses used.')
            self.guess_entry.focus_set()

    def _finish(self, message):
        self.game_over = True
        self.guess_entry.configure(state='disabled')
        self.submit_button.configure(state='disabled')
        self.status_text.set(message + ' Select New Game to play again.')


def main():
    root = tk.Tk()
    try:
        EnigmaWordleApp(root)
    except ValueError as error:
        messagebox.showerror('Unable to start game', str(error), parent=root)
        root.destroy()
        return
    root.mainloop()


if __name__ == '__main__':
    main()
