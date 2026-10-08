"""Mode selection and returning to the menu without changing Practice Mode."""
import tkinter as tk
from tkinter import messagebox, ttk


class ModeMenu:
    def __init__(self, root):
        self.root = root
        self.app = None
        self.show_menu()

    def _clear(self):
        if self.app is not None and hasattr(self.app, 'close'):
            self.app.close()
        # Remove handlers referencing a canvas that is about to be destroyed.
        for event in ('<MouseWheel>', '<Button-4>', '<Button-5>'):
            self.root.unbind(event)
        for child in self.root.winfo_children():
            child.destroy()
        self.app = None

    def show_menu(self):
        self._clear()
        self.root.title('Enigmadle — Choose a mode')
        self.root.geometry('650x440')
        self.root.minsize(600, 400)
        self.root.configure(bg='#20252b')
        style = ttk.Style(self.root)
        style.theme_use('clam')
        style.configure('TFrame', background='#20252b')
        style.configure('TLabel', background='#20252b', foreground='#edf2f7')
        style.configure('TButton', padding=10)
        panel = ttk.Frame(self.root, padding=30)
        panel.pack(fill='both', expand=True)
        ttk.Label(panel, text='ENIGMADLE', font=('Helvetica', 22, 'bold')).pack(anchor='w')
        ttk.Label(panel, text='Choose your workstation', font=('Helvetica', 12)).pack(anchor='w', pady=(5, 25))
        ttk.Button(panel, text='Practice Mode', command=lambda: self.start_mode('practice')).pack(fill='x')
        ttk.Label(panel, text='Your original five-letter Wordle game. Three guesses.', wraplength=560).pack(
            anchor='w', pady=(5, 25))
        ttk.Button(panel, text='Sentence Investigation', command=lambda: self.start_mode('sentence')).pack(fill='x')
        ttk.Label(panel, text='Investigate intercepted messages with partial plugboard clues.\n'
                  'Recover missing words; six submissions. Correct answers stay locked.',
                  wraplength=560).pack(anchor='w', pady=5)

    def start_mode(self, mode):
        if mode not in ('practice', 'sentence'):
            raise ValueError('Choose Practice or Sentence Mode.')
        self._clear()
        try:
            if mode == 'practice':
                from ui.gui import EnigmaWordleApp
                self.app = EnigmaWordleApp(self.root)
            else:
                from ui.sentence_gui import SentenceApp
                self.app = SentenceApp(self.root)
        except ValueError as error:
            messagebox.showerror('Unable to start round', str(error), parent=self.root)
            self.show_menu()
            return
        # Add navigation outside the existing Practice interface.
        toolbar = ttk.Frame(self.root, padding=(18, 4))
        toolbar.pack(side='top', fill='x', before=self.root.winfo_children()[0])
        ttk.Button(toolbar, text='Choose Mode', command=self.confirm_menu).pack(side='left')

    def confirm_menu(self):
        if self.app is not None and not self.app.game_over:
            if not messagebox.askyesno('Leave this round?', 'Return to mode selection? This round will be discarded.',
                                      parent=self.root):
                return
        self.show_menu()


def launch_gui():
    root = tk.Tk()
    ModeMenu(root)
    root.mainloop()


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Enigmadle operator training and sentence investigation')
    parser.add_argument('--cli', action='store_true', help='play practice mode in the terminal')
    args = parser.parse_args()
    if args.cli:
        from ui.cli import play_game
        play_game()
    else:
        launch_gui()


if __name__ == '__main__':
    main()
