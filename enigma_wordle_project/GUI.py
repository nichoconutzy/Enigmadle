"""Enigma-Wordle operator training GUI. Run: python GUI.py.
Keep the separated project modules beside this file.
"""
import random
import tkinter as tk
from tkinter import messagebox, ttk

from enigma_constants import ALPHABET
from enigma_machine import EnigmaMachine
from puzzle import create_puzzle
from word_bank import load_valid_words
from wordle import WORD_LENGTH, MAX_GUESSES


class EnigmaWordleApp:
    BG = '#20252b'
    TILE_COLOURS = {'🟩': '#538d4e', '🟨': '#b59f3b', '⬛': '#3a3a3c'}

    @property
    def game_over(self):
        return self.game.game_over

    def __init__(self, root):
        self.root = root
        self.words = load_valid_words()
        self.rng = random.SystemRandom()
        root.title('Enigma-Wordle Workstation')
        root.geometry('850x720')
        root.minsize(780, 560)
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
        # Round progress and the final result stay visible while the page scrolls.
        footer = ttk.Frame(self.root, padding=(18, 10))
        footer.pack(side='bottom', fill='x')
        self.status_text = tk.StringVar()
        status_label = ttk.Label(footer, textvariable=self.status_text,
                                 wraplength=680, font=('Helvetica', 11, 'bold'))
        status_label.pack(fill='x')
        footer.bind('<Configure>', lambda event: status_label.configure(
            wraplength=max(1, event.width - 36)))
        # Keep every control reachable on smaller laptop screens.
        container = ttk.Frame(self.root)
        container.pack(fill='both', expand=True)
        canvas = tk.Canvas(container, bg=self.BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient='vertical', command=canvas.yview)
        scrollbar.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)
        canvas.configure(yscrollcommand=scrollbar.set)
        panel = ttk.Frame(canvas, padding=18)
        panel_id = canvas.create_window((0, 0), window=panel, anchor='nw')
        panel.bind('<Configure>', lambda event: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>', lambda event: canvas.itemconfigure(panel_id, width=event.width))
        self.canvas = canvas
        self.root.bind('<MouseWheel>', self._scroll, add='+')
        self.root.bind('<Button-4>', lambda event: canvas.yview_scroll(-1, 'units'), add='+')
        self.root.bind('<Button-5>', lambda event: canvas.yview_scroll(1, 'units'), add='+')
        header = ttk.Frame(panel)
        header.pack(fill='x')
        ttk.Label(header, text='ENIGMA-WORDLE', font=('Helvetica', 18, 'bold')).pack(side='left')
        ttk.Button(header, text='New Game', command=self.new_game).pack(side='right')
        ttk.Button(header, text='Help', command=self.show_help).pack(side='right', padx=8)
        ttk.Label(panel, text='Operator training • five-letter words • six guesses').pack(anchor='w', pady=(5, 12))

        intel = ttk.LabelFrame(panel, text='Intercept and daily key', padding=10)
        intel.pack(fill='x')
        self.key_text = tk.StringVar()
        self.intercept_text = tk.StringVar()
        ttk.Label(intel, textvariable=self.key_text, font=('Courier', 10), wraplength=700).pack(anchor='w')
        ttk.Label(intel, textvariable=self.intercept_text, font=('Courier', 13, 'bold'), wraplength=700).pack(anchor='w', pady=8)
        ttk.Label(intel, text='The daily key is supplied so this exercise can be solved.').pack(anchor='w')
        instructions = ('1. Copy the daily rotor order, rings and plugboard into the controls.\n'
                        '2. Decode the indicator at the open group; its output becomes the body windows.\n'
                        '3. Decrypt the five-letter body, then submit your word below.')
        ttk.Label(panel, text=instructions, justify='left', wraplength=700).pack(anchor='w', pady=12)

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
        self.indicator_button = ttk.Button(actions, text='Decode Indicator', command=self.decode_indicator)
        self.indicator_button.pack(side='left', padx=(0, 8))
        self.decrypt_button = ttk.Button(actions, text='Decrypt Word', command=self.run_decrypt)
        self.decrypt_button.pack(side='left')
        self.output_text = tk.StringVar()
        ttk.Label(settings, textvariable=self.output_text, font=('Courier', 11, 'bold'), wraplength=700).grid(
            row=6, column=0, columnspan=2, sticky='w', pady=(8, 0))

        board = ttk.LabelFrame(panel, text='Wordle grid', padding=8)
        board.pack(fill='x', pady=12)
        self.grid_labels = []
        for _ in range(MAX_GUESSES):
            row_frame = ttk.Frame(board)
            row_frame.pack(pady=2)
            labels = []
            for _ in range(WORD_LENGTH):
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

    def _scroll(self, event):
        # Leave combobox scrolling to the widget so selecting a rotor is predictable.
        if isinstance(event.widget, ttk.Combobox):
            return
        if event.delta:
            units = -int(event.delta / 120) if abs(event.delta) >= 120 else (-1 if event.delta > 0 else 1)
            self.canvas.yview_scroll(units, 'units')

    def show_help(self):
        messagebox.showinfo(
            'How to play',
            'This is an operator-training exercise: the daily key is supplied.\n\n'
            '1. Set rotor order, rings and plugboard to the daily key.\n'
            '2. Decode Indicator starts at the unencrypted OPEN group. The recovered '
            'three letters are copied to Body windows.\n'
            '3. Decrypt Word starts a fresh machine at those windows, so repeating '
            'it gives the same output.\n'
            '4. Submit a five-letter word from the word bank. You have six valid guesses.\n\n'
            'Green: correct letter and position. Yellow: letter in another position. '
            'Grey: no remaining match. Repeated letters are counted individually.\n\n'
            'You can also guess directly. Machine operations do not use guesses. '
            'Incorrect machine settings can produce incorrect output.',
            parent=self.root)

    def new_game(self):
        """Generate a new transmission and reset the entire round."""
        puzzle = create_puzzle(self.words, rng=self.rng)
        self.daily_key = puzzle.daily_key
        self.packet = puzzle.transmission
        self.game = puzzle.new_wordle_game()
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
        self.status_text.set(f'0 / {self.game.max_guesses} guesses used. '
                             'Configure the machine with the supplied daily key.')
        self.guess_entry.configure(state='normal')
        self.submit_button.configure(state='normal')
        self.indicator_button.configure(state='normal')
        self.decrypt_button.configure(state='normal')
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
        if self.game.game_over:
            return
        try:
            machine = self._configured_machine(windows=self.packet.open_group)
            recovered_key = machine.encrypt_string(self.packet.indicator)
        except ValueError as error:
            messagebox.showerror('Invalid machine settings', str(error), parent=self.root)
            return
        for variable, letter in zip(self.window_vars, recovered_key):
            variable.set(letter)
        self.output_text.set(f'Indicator output: {recovered_key}    Body output: ?????')
        self.status_text.set(f'{len(self.game.guesses)} / {self.game.max_guesses} guesses used. '
                             'Indicator output copied into body windows. Now select Decrypt Word. '
                             'Incorrect daily settings will produce an incorrect key.')

    def run_decrypt(self):
        if self.game.game_over:
            return
        try:
            decoded = self._configured_machine().encrypt_string(self.packet.ciphertext)
        except ValueError as error:
            messagebox.showerror('Invalid machine settings', str(error), parent=self.root)
            return
        windows = ''.join(v.get() for v in self.window_vars)
        self.output_text.set(f'Body starting windows: {windows}\nBody output: {decoded}')

    def submit_guess(self):
        if self.game.game_over:
            return
        row = len(self.game.guesses)
        feedback, error = self.game.submit_guess(self.guess_entry.get())
        if error:
            messagebox.showerror('Invalid guess', error, parent=self.root)
            return
        guess = self.game.guesses[-1][0]
        for tile, letter, status in zip(self.grid_labels[row], guess, feedback):
            tile.configure(text=letter, bg=self.TILE_COLOURS[status])
        self.guess_entry.delete(0, tk.END)
        if self.game.won:
            self._finish(f'Success! You found {guess} in {row + 1} / {self.game.max_guesses} guesses.')
        elif self.game.game_over:
            self._finish(f'Out of guesses. The word was {self.game.target_word}.')
        else:
            self.status_text.set(f'{len(self.game.guesses)} / {self.game.max_guesses} guesses used.')
            self.guess_entry.focus_set()

    def _finish(self, message):
        self.guess_entry.configure(state='disabled')
        self.submit_button.configure(state='disabled')
        self.indicator_button.configure(state='disabled')
        self.decrypt_button.configure(state='disabled')
        self.status_text.set(message + ' Select New Game to play again.')
        messagebox.showinfo('You won!' if self.game.won else 'Out of guesses',
                            message, parent=self.root)


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
