import random
import tkinter as tk
from tkinter import messagebox
from enigma_wordle import EnigmaMachine
from wordle import WordleGame
from word_bank import ENGLISH_WORDS # Assuming you have a separate module for the word bank
class EnigmaWordleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Enigma-Wordle Workstation")
        self.root.geometry("650x750")
        self.root.config(bg="#2b2b2b")

        # 1. Randomly pick a secret target word
        target = random.choice(ENGLISH_WORDS)
        
        # 2. Instantiate the Enigma machine and auto-generate the ciphertext
        self.enigma = EnigmaMachine(rotors=('A', 'A', 'A'))
        cipher = self.enigma.encrypt_string(target)

        # Pass target and dynamic ciphertext to the Wordle game logic
        self.game = WordleGame(target, cipher)


        # --- TITLE & INTEL ---
        title_label = tk.Label(root, text="BCH. PARK ENIGMA-WORDLE TERMINAL", fg="#00ffcc", bg="#2b2b2b", font=("Helvetica", 14, "bold"))
        title_label.pack(pady=10)

        intel_frame = tk.Frame(root, bg="#3c3f41", bd=2, relief="groove")
        intel_frame.pack(fill="x", padx=20, pady=5)
        
        tk.Label(intel_frame, text=f"Intercepted Ciphertext: {self.game.ciphertext}", fg="yellow", bg="#3c3f41", font=("Courier", 12, "bold")).pack(anchor="w", padx=10, pady=5)
        tk.Label(intel_frame, text="Hint: Marine / Weather related theme.", fg="white", bg="#3c3f41", font=("Helvetica", 10)).pack(anchor="w", padx=10, pady=5)

        # --- ENIGMA WORKSTATION PANEL ---
        enigma_frame = tk.LabelFrame(root, text=" Enigma Machine Settings ", fg="#00ffcc", bg="#2b2b2b", font=("Helvetica", 10, "bold"))
        enigma_frame.pack(fill="x", padx=20, pady=10)

        # Rotors configuration
        rotor_sub = tk.Frame(enigma_frame, bg="#2b2b2b")
        rotor_sub.pack(fill="x", padx=10, pady=5)
        tk.Label(rotor_sub, text="Rotors (R1 R2 R3):", fg="white", bg="#2b2b2b").pack(side="left")
        self.rotor_entry = tk.Entry(rotor_sub, width=10, font=("Courier", 11))
        self.rotor_entry.insert(0, "A A A")
        self.rotor_entry.pack(side="left", padx=5)

        # Plugboard configuration
        plug_sub = tk.Frame(enigma_frame, bg="#2b2b2b")
        plug_sub.pack(fill="x", padx=10, pady=5)
        tk.Label(plug_sub, text="Plugboard Pairs (e.g., A-B X-Y):", fg="white", bg="#2b2b2b").pack(side="left")
        self.plug_entry = tk.Entry(plug_sub, width=20, font=("Courier", 11))
        self.plug_entry.pack(side="left", padx=5)

        # Decrypt Button & Output
        action_sub = tk.Frame(enigma_frame, bg="#2b2b2b")
        action_sub.pack(fill="x", padx=10, pady=5)
        decrypt_btn = tk.Button(action_sub, text="Run Enigma Decrypt", command=self.run_decrypt, bg="#008577", fg="white", font=("Helvetica", 9, "bold"))
        decrypt_btn.pack(side="left")
        
        self.decrypt_output_lbl = tk.Label(action_sub, text="Output: [ ? ? ? ? ? ]", fg="#00ffcc", bg="#2b2b2b", font=("Courier", 11, "bold"))
        self.decrypt_output_lbl.pack(side="left", padx=15)

        # --- WORDLE GRID PANEL ---
        board_frame = tk.LabelFrame(root, text=" Wordle Decoding Grid ", fg="#00ffcc", bg="#2b2b2b", font=("Helvetica", 10, "bold"))
        board_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Create 6 rows x 5 columns grid widgets
        self.grid_labels = []
        for r in range(6):
            row_list = []
            row_f = tk.Frame(board_frame, bg="#2b2b2b")
            row_f.pack(pady=3)
            for c in range(5):
                lbl = tk.Label(row_f, text="_", width=3, height=1, font=("Courier", 14, "bold"), bg="#4f5254", fg="white", relief="ridge")
                lbl.pack(side="left", padx=3)
                row_list.append(lbl)
            self.grid_labels.append(row_list)

        # Guess Input Control
        input_frame = tk.Frame(root, bg="#2b2b2b")
        input_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Label(input_frame, text="5-Letter Guess:", fg="white", bg="#2b2b2b", font=("Helvetica", 10, "bold")).pack(side="left")
        self.guess_entry = tk.Entry(input_frame, width=15, font=("Courier", 12))
        self.guess_entry.pack(side="left", padx=10)
        self.guess_entry.bind("<Return>", lambda event: self.submit_guess())

        submit_btn = tk.Button(input_frame, text="Submit Guess", command=self.submit_guess, bg="#4CAF50", fg="white", font=("Helvetica", 9, "bold"))
        submit_btn.pack(side="left", padx=5)

    def run_decrypt(self):
        # Read rotor values
        r_text = self.rotor_entry.get().strip().split()
        if len(r_text) == 3:
            self.enigma.set_rotors(r_text[0], r_text[1], r_text[2])
            
        # Read plugboard values
        p_text = self.plug_entry.get().strip()
        if p_text:
            self.enigma.set_plugboard(p_text)
            
        # Run decryption simulation
        decoded = self.enigma.encrypt_string(self.game.ciphertext)
        self.decrypt_output_lbl.config(text=f"Output: {decoded}")

    def submit_guess(self):
        current_row = len(self.game.guesses)
        if current_row >= self.game.max_guesses:
            return

        guess = self.guess_entry.get().strip().upper()
        feedback, err = self.game.evaluate_guess(guess)
        
        if err:
            messagebox.showerror("Error", err)
            return

        self.game.guesses.append((guess, feedback))
        self.guess_entry.delete(0, tk.END)

        # Update the visual grid colors
        for c in range(5):
            letter = guess[c]
            status = feedback[c]
            
            # Map status to color
            if status == 'GREEN':
                bg_color = "#538d4e" # Wordle green
            elif status == 'YELLOW':
                bg_color = "#b59f3b" # Wordle yellow
            else:
                bg_color = "#3a3a3c" # Wordle gray
                
            self.grid_labels[current_row][c].config(text=letter, bg=bg_color, fg="white")

        # Check win/loss conditions
        if guess == self.game.target_word:
            messagebox.showinfo("Victory!", "Success! You cracked the Enigma code and solved the Wordle!")
            self.root.destroy()
        elif len(self.game.guesses) >= self.game.max_guesses:
            messagebox.showerror("Game Over", f"Out of guesses! The secret word was: {self.game.target_word}")
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = EnigmaWordleApp(root)
    root.mainloop()