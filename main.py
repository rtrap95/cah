"""Entry point per il generatore Cards Against Humanity."""

import sys


def main():
    """Entry point principale - avvia la GUI."""
    from cah.gui import run_gui
    run_gui()


def cli():
    """Entry point CLI."""
    from cah.cli import menu
    menu()


if __name__ == "__main__":
    if "--cli" in sys.argv:
        cli()
    else:
        main()
