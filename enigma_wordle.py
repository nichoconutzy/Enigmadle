import random
import sys

class EnigmaMachine:
    def __init__(self, rotors=('A', 'A', 'A'), plugboard=None):
        # Rotors start positions (indices 0-25)
        self.rotors = [ord(r.upper()) - ord('A') for r in rotors]
        # Plugboard is a dictionary mapping letters to swapped letters
        self.plugboard = plugboard if plugboard else {}

    def set_rotors(self, r1, r2, r3):
        self.rotors = [ord(r1.upper()) - ord('A'), ord(r2.upper()) - ord('A'), ord(r3.upper()) - ord('A')]

    def set_plugboard(self, pairs):
        """Pairs format: ['A-B', 'X-Y']"""
        self.plugboard.clear()
        for pair in pairs:
            if '-' in pair:
                l1, l2 = pair.upper().split('-')
                self.plugboard[l1] = l2
                self.plugboard[l2] = l1

    def encrypt_char(self, char):
        char = char.upper()
        if not char.isalpha():
            return char
        
        # 1. Plugboard swap
        char = self.plugboard.get(char, char)
        
        # 2. Simple rotor simulation (shifting based on rotor offsets)
        shift = (self.rotors[0] + self.rotors[1] + self.rotors[2]) % 26
        code = (ord(char) - ord('A') + shift) % 26
        out_char = chr(ord('A') + code)
        
        # 3. Plugboard swap back
        out_char = self.plugboard.get(out_char, out_char)
        
        # Step rotors forward slightly for next letter
        self.rotors[2] = (self.rotors[2] + 1) % 26
        
        return out_char

    def encrypt_string(self, text):
        return "".join([self.encrypt_char(c) for c in text])


class WordleGame:
    def __init__(self, target_word, ciphertext):
        self.target_word = target_word.upper()
        self.ciphertext = ciphertext.upper()
        self.guesses = []
        self.max_guesses = 6

    def evaluate_guess(self, guess):
        guess = guess.upper()
        if len(guess) != 5:
            return None, "Error: Word must be exactly 5 letters."
        
        result = []
        target_chars = list(self.target_word)
        guess_chars = list(guess)
        
        # Check greens first
        feedback = ['⬛'] * 5
        for i in range(5):
            if guess_chars[i] == target_chars[i]:
                feedback[i] = '🟩'
                target_chars[i] = None
                guess_chars[i] = None

        # Check yellows
        for i in range(5):
            if guess_chars[i] is not None:
                if guess_chars[i] in target_chars:
                    feedback[i] = '🟨'
                    target_chars[target_chars.index(guess_chars[i])] = None
                else:
                    feedback[i] = '⬛'
                    
        return "".join(feedback), None


def play_game():
    # Word bank and matching ciphers
    word_bank = [
        ("STORM", "QMPFZ"),
        ("TIDES", "XWKLP"),
        ("FLEET", "BRVVA"),
        ("OCEAN", "KLPQM")
    ]
    
    target, cipher = random.choice(word_bank)
    game = WordleGame(target, cipher)
    enigma = EnigmaMachine()

    print("==========================================")
    print("      ENIGMA-WORDLE: PYTHON EDITION       ")
    print("==========================================")
    print(f"Intercepted Ciphertext: {cipher}")
    print("Hint: Marine / Weather related theme.\n")

    while len(game.guesses) < game.max_guesses:
        print(f"\n--- Row {len(game.guesses) + 1} of {game.max_guesses} ---")
        print("Commands:")
        print("  ROTORS <R1> <R2> <R3>  (e.g., ROTORS M A R)")
        print("  PLUG <A-B> <C-D>      (e.g., PLUG A-B X-Y)")
        print("  DECRYPT                (Run ciphertext through Enigma)")
        print("  GUESS <WORD>           (Submit your Wordle guess)")
        
        user_input = input("\nCommand > ").strip().upper().split()
        if not user_input:
            continue
            
        cmd = user_input[0]
        
        if cmd == "ROTORS" and len(user_input) == 4:
            enigma.set_rotors(user_input[1], user_input[2], user_input[3])
            print(f"[Machine] Rotors updated to: {user_input[1]} {user_input[2]} {user_input[3]}")
            
        elif cmd == "PLUG":
            pairs = user_input[1:]
            enigma.set_plugboard(pairs)
            print(f"[Machine] Plugboard updated with pairs: {pairs}")
            
        elif cmd == "DECRYPT":
            # Reset rotor state for clean decryption run
            decoded = enigma.encrypt_string(game.ciphertext)
            print(f"[Machine] Ciphertext '{game.ciphertext}' decrypted to: '{decoded}'")
            
        elif cmd == "GUESS" and len(user_input) == 2:
            guess_word = user_input[1]
            feedback, err = game.evaluate_guess(guess_word)
            if err:
                print(err)
                continue
                
            game.guesses.append((guess_word, feedback))
            
            # Print board state
            print("\n--- BATTLEFIELD BOARD ---")
            for idx, (g, f) in enumerate(game.guesses):
                print(f"Row {idx+1}: {' '.join(list(g))}  ->  {f}")
                
            if guess_word == game.target_word:
                print("\n🎉 SUCCESS! You cracked the Enigma code and solved the Wordle!")
                return
        else:
            print("Invalid command syntax. Try again.")

    print(f"\nGame Over! The secret word was: {game.target_word}")

if __name__ == "__main__":
    play_game()