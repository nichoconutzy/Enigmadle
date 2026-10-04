"""Launch the GUI by default, or use --cli for the terminal interface."""
import argparse


def main():
    parser = argparse.ArgumentParser(description='Enigma-Wordle operator training')
    parser.add_argument('--cli', action='store_true', help='play in the terminal')
    args = parser.parse_args()
    if args.cli:
        from enigma_wordle import play_game
        play_game()
    else:
        from GUI import main as launch_gui
        launch_gui()


if __name__ == '__main__':
    main()
