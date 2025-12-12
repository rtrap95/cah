"""Entry point for the Cards Against Humanity generator."""

import sys


def main():
    """Main entry point - launches the GUI."""
    from cah.gui import run_gui
    run_gui()


def cli():
    """CLI entry point."""
    from cah.cli import menu
    menu()


if __name__ == "__main__":
    if "--cli" in sys.argv:
        cli()
    else:
        main()
