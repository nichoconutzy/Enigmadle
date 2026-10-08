"""Sentence investigation screen; practice remains in gui.py."""
import tkinter as tk
from tkinter import ttk, messagebox
from core.enigma_constants import ALPHABET
from game.sentence_game import create_sentence_puzzle, SentenceRound
from ui.gui import EnigmaWordleApp


class SentenceApp(EnigmaWordleApp):
    def __init__(self, root):
        self.root = root
        root.title('Enigmadle — Sentence investigation')
        root.geometry('900x780')
        root.minsize(780, 560)
        root.configure(bg=self.BG)
        self._build_interface()
        self.new_game()

    def _var(self, value=''):
        return tk.StringVar(self.root, value=value)

    def _label(self, parent, variable=None, text='', mono=False):
        options = dict(wraplength=690, justify='left')
        if mono:
            options['font'] = ('Courier', 11)
        if variable is not None:
            options['textvariable'] = variable
        else:
            options['text'] = text
        label = ttk.Label(parent, **options)
        label.pack(anchor='w', fill='x', pady=4)
        parent.bind('<Configure>', lambda event: label.configure(
            wraplength=max(1, event.width - 32)), add='+')
        return label

    def _section(self, parent, title):
        section = ttk.LabelFrame(parent, text=title, padding=12)
        section.pack(fill='x', pady=(0, 12))
        return section

    def _build_interface(self):
        style = ttk.Style(self.root)
        style.theme_use('clam')
        for name in ('TFrame', 'TLabelframe'):
            style.configure(name, background=self.BG)
        style.configure('TLabel', background=self.BG, foreground='#edf2f7')
        style.configure('TLabelframe.Label', background=self.BG, foreground='#64dfc4')
        style.configure('TButton', padding=6)
        for name in ('TEntry', 'TCombobox'):
            style.configure(name, insertcolor='#00796b', insertwidth=3)
        footer = ttk.Frame(self.root, padding=(18, 8))
        footer.pack(side='bottom', fill='x')
        self.status_text = self._var()
        self._label(footer, self.status_text)
        container = ttk.Frame(self.root)
        container.pack(fill='both', expand=True)
        self.canvas = tk.Canvas(container, bg=self.BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient='vertical', command=self.canvas.yview)
        scrollbar.pack(side='right', fill='y')
        self.canvas.pack(side='left', fill='both', expand=True)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        panel = ttk.Frame(self.canvas, padding=18)
        panel_id = self.canvas.create_window((0, 0), window=panel, anchor='nw')
        panel.bind('<Configure>', lambda event: self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.bind('<Configure>', lambda event: self.canvas.itemconfigure(panel_id, width=event.width))
        self.root.bind('<MouseWheel>', self._scroll, add='+')
        self.root.bind('<Button-4>', lambda event: self.canvas.yview_scroll(-1, 'units'), add='+')
        self.root.bind('<Button-5>', lambda event: self.canvas.yview_scroll(1, 'units'), add='+')
        header = ttk.Frame(panel)
        header.pack(fill='x', pady=(0, 10))
        ttk.Label(header, text='SENTENCE INVESTIGATION', font=('Helvetica', 18, 'bold')).pack(side='left')
        ttk.Button(header, text='New Investigation', command=self.new_game).pack(side='right')
        ttk.Button(header, text='Help', command=self.show_help).pack(side='right', padx=8)
        self.brief = self._var()
        self._label(panel, self.brief)
        mission = self._section(panel, 'Sentence to reconstruct — missing words')
        self.mask = self._var()
        self._label(mission, self.mask, mono=True)
        self._label(mission, text='Recover the numbered blanks. Visible words help you recognise correct decryption.')
        intel = self._section(panel, 'Intercepted transmission')
        self.intercept_text = self._var()
        self._label(intel, self.intercept_text, mono=True)
        self._label(intel, text='1. Use the clues to configure the daily settings.\n'
                    '2. Decode Indicator to recover the body windows.\n'
                    '3. Decrypt Body, then submit the missing words.')
        evidence = self._section(panel, 'Evidence notebook — daily key clues')
        self.key_text = self._var()
        self._label(evidence, self.key_text, mono=True)
        settings = self._section(panel, 'Machine settings — LEFT / MIDDLE / RIGHT')
        settings.columnconfigure(1, weight=1)
        self.order_vars = [self._var() for _ in range(3)]
        self.ring_vars = [self._var() for _ in range(3)]
        self.window_vars = [self._var() for _ in range(3)]
        for row, (label, variables, choices) in enumerate([
                ('Rotor order', self.order_vars, ('I', 'II', 'III', 'IV', 'V')),
                ('Ring settings', self.ring_vars, tuple(ALPHABET)),
                ('Body windows', self.window_vars, tuple(ALPHABET))]):
            ttk.Label(settings, text=label).grid(row=row, column=0, sticky='w', padx=(0, 15), pady=4)
            controls = ttk.Frame(settings)
            controls.grid(row=row, column=1, sticky='w')
            for variable in variables:
                editable = variables is not self.order_vars
                field = ttk.Combobox(controls, textvariable=variable, values=choices,
                                     state='normal' if editable else 'readonly', width=5)
                field.pack(side='left', padx=(0, 8))
                if editable:
                    field.bind('<KeyRelease>', self._uppercase_setting)
                    field.bind('<FocusOut>', self._uppercase_setting)
                    field.bind('<FocusIn>', lambda event: event.widget.selection_range(0, tk.END))
        self.plug_var = self._var()
        ttk.Label(settings, text='Plugboard pairs').grid(row=3, column=0, sticky='w', pady=4)
        ttk.Entry(settings, textvariable=self.plug_var, width=48).grid(row=3, column=1, sticky='ew')
        ttk.Label(settings, text='Keep the known pairs and add the last cable. Example: AB CD EF GH.').grid(
            row=4, column=1, sticky='w', pady=(3, 8))
        actions = ttk.Frame(settings)
        actions.grid(row=5, column=0, columnspan=2, sticky='w')
        self.indicator_button = ttk.Button(actions, text='Decode Indicator', command=self.decode_indicator)
        self.indicator_button.pack(side='left', padx=(0, 8))
        self.decrypt_button = ttk.Button(actions, text='Decrypt Body', command=self.run_decrypt)
        self.decrypt_button.pack(side='left')
        self.output_text = self._var()
        output = ttk.Label(settings, textvariable=self.output_text, font=('Courier', 11, 'bold'),
                           wraplength=700, justify='left')
        output.grid(row=6, column=0, columnspan=2, sticky='w', pady=(8, 0))
        settings.bind('<Configure>', lambda event: output.configure(wraplength=max(1, event.width - 32)))
        answers = self._section(panel, 'Submit the missing words')
        self.answer_panel = ttk.Frame(answers)
        self.answer_panel.pack(fill='x', pady=4)
        self.submit_button = ttk.Button(answers, text='Submit Answers', command=self.submit_guess)
        self.submit_button.pack(anchor='w', pady=8)
        self._label(answers, text='Six valid submissions. Correct answers stay locked; machine attempts are unlimited.')

    def new_game(self):
        self.puzzle = create_sentence_puzzle()
        self.game = SentenceRound(self.puzzle)
        self.packet = self.puzzle.transmission
        spec, key = self.puzzle.spec, self.puzzle.daily_key
        self.brief.set(spec.title + ' • ' + spec.briefing)
        grouped = ' '.join(self.packet.ciphertext[i:i+5] for i in range(0, len(self.packet.ciphertext), 5))
        self.intercept_text.set(f'OPEN: {self.packet.open_group}     INDICATOR: {self.packet.indicator}\nBODY: {grouped}')
        self.key_text.set('ORDER: ' + ' '.join(key.rotor_order) + '    RINGS: ' + ''.join(key.ring_settings)
                          + '\nKNOWN PAIRS: ' + ' '.join(self.puzzle.known_pairs)
                          + f'\nOne more cable connects {self.puzzle.missing_pair_letter} to an unused letter. Four cables total.')
        for variables, values in [(self.order_vars, ('I', 'II', 'III')),
                                   (self.ring_vars, 'AAA'), (self.window_vars, 'AAA')]:
            for var, value in zip(variables, values):
                var.set(value)
        self.plug_var.set(' '.join(self.puzzle.known_pairs))
        self.output_text.set('Decode the indicator first, then decrypt the message.')
        self.mask.set(spec.masked_sentence)
        for child in self.answer_panel.winfo_children():
            child.destroy()
        self.answer_entries, self.answer_feedback = [], []
        for i, answer in enumerate(spec.answers):
            line = ttk.Frame(self.answer_panel)
            line.pack(fill='x', pady=4)
            ttk.Label(line, text=f'Word {i + 1} ({len(answer)} letters)', width=20).pack(side='left')
            entry = ttk.Entry(line, width=20)
            entry.pack(side='left', padx=8)
            entry.bind('<Return>', lambda e: self.submit_guess())
            feedback = ttk.Label(line, text='Unsolved')
            feedback.pack(side='left')
            self.answer_entries.append(entry)
            self.answer_feedback.append(feedback)
        for button in (self.submit_button, self.indicator_button, self.decrypt_button):
            button.configure(state='normal')
        self.status_text.set('0 / 6 submissions used. Machine attempts are unlimited.')
        self.canvas.yview_moveto(0)

    def decode_indicator(self):
        if self.game.game_over:
            return
        try:
            recovered = self._configured_machine(windows=self.packet.open_group).encrypt_string(self.packet.indicator)
            for var, letter in zip(self.window_vars, recovered):
                var.set(letter)
            self.output_text.set(f'Indicator output: {recovered}. Copied to body windows. Now decrypt the message.')
        except ValueError as error:
            messagebox.showerror('Invalid settings', str(error), parent=self.root)

    def run_decrypt(self):
        if self.game.game_over:
            return
        try:
            decoded = self._configured_machine().encrypt_string(self.packet.ciphertext)
            # Word boundaries are supplied by the intercepted sentence template.
            lengths = [len(w) for w in self.puzzle.spec.sentence.split()]
            parts, start = [], 0
            for length in lengths:
                parts.append(decoded[start:start + length])
                start += length
            self.output_text.set('Body output: ' + ' '.join(parts))
        except ValueError as error:
            messagebox.showerror('Invalid settings', str(error), parent=self.root)

    def submit_guess(self):
        if self.game.game_over:
            return
        try:
            solved = self.game.submit([e.get() for e in self.answer_entries])
        except ValueError as error:
            messagebox.showerror('Invalid answers', str(error), parent=self.root)
            return
        for entry, label, correct in zip(self.answer_entries, self.answer_feedback, solved):
            label.configure(text='Recovered' if correct else 'Try again')
            if correct:
                entry.configure(state='disabled')
        self.status_text.set(f'{self.game.attempts} / 6 submissions used. {sum(solved)} / {len(solved)} words recovered.')
        if self.game.game_over:
            text = ('Intercept solved! ' if self.game.won else 'Out of submissions. ') + self.puzzle.spec.sentence
            self.status_text.set(text + ' Select New intercept to play again.')
            for widget in self.answer_entries + [self.submit_button, self.indicator_button, self.decrypt_button]:
                widget.configure(state='disabled')
            messagebox.showinfo('Success' if self.game.won else 'Round ended', text, parent=self.root)

    def show_help(self):
        messagebox.showinfo('Sentence investigation',
            'Copy the supplied rotor order and rings. Three of four plugboard pairs are supplied. '
            'For the last pair, try connecting the named letter to an unused letter.\n\n'
            'After EVERY settings change, decode the indicator again, then decrypt the message. '
            'Use the known words in the template to recognise a readable result. '
            'Open group is the starting position for the indicator; its decoded output is the starting position for the body.\n\n'
            'Submit all missing words. Correct answers stay locked. Invalid inputs cost no attempt; '
            'you have six valid submissions. Machine attempts are unlimited. '
            'Spaces and word lengths are supplied as gameplay assistance.', parent=self.root)
