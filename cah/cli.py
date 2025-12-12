"""Interactive CLI for the card generator."""

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, IntPrompt
from rich import print as rprint
from pathlib import Path
import random

from .models import CardType, DeckConfig
from .database import create_default_deck, get_cards_count
from .decks import (
    list_saved_decks, save_deck, load_deck, delete_deck,
    create_empty_deck, add_card_to_deck
)
from .export import export_deck_to_pdf

app = typer.Typer(help="Cards Against Humanity generator")
console = Console()

EXPORTS_DIR = Path(__file__).parent.parent / "exports"


def ensure_exports_dir():
    """Ensure exports directory exists."""
    EXPORTS_DIR.mkdir(exist_ok=True)


@app.command()
def menu():
    """Launch the main interactive menu."""
    while True:
        console.clear()
        console.print(Panel.fit(
            "[bold white on black] CARDS AGAINST HUMANITY [/]\n"
            "[dim]Card Generator[/]",
            border_style="white"
        ))

        console.print("\n[bold]Main menu:[/]\n")
        console.print("  [cyan]1.[/] Browse default cards")
        console.print("  [cyan]2.[/] Create new custom deck")
        console.print("  [cyan]3.[/] Manage saved decks")
        console.print("  [cyan]4.[/] Export to PDF")
        console.print("  [cyan]5.[/] Generate random combo")
        console.print("  [cyan]0.[/] Exit\n")

        choice = Prompt.ask("Choose an option", choices=["0", "1", "2", "3", "4", "5"])

        if choice == "0":
            console.print("\n[dim]Goodbye![/]")
            break
        elif choice == "1":
            explore_cards()
        elif choice == "2":
            create_custom_deck()
        elif choice == "3":
            manage_decks()
        elif choice == "4":
            export_menu()
        elif choice == "5":
            random_combo()


def explore_cards():
    """Browse default cards."""
    deck = create_default_deck()
    stats = get_cards_count()

    while True:
        console.clear()
        console.print(Panel.fit(
            f"[bold]Default cards[/]\n"
            f"Black: {stats['black']} | White: {stats['white']} | Total: {stats['total']}",
            border_style="cyan"
        ))

        console.print("\n  [cyan]1.[/] Show black cards (questions)")
        console.print("  [cyan]2.[/] Show white cards (answers)")
        console.print("  [cyan]3.[/] Search card")
        console.print("  [cyan]0.[/] Back to menu\n")

        choice = Prompt.ask("Choose", choices=["0", "1", "2", "3"])

        if choice == "0":
            break
        elif choice == "1":
            show_cards_list(deck.black_cards, "Black Cards (Questions)")
        elif choice == "2":
            show_cards_list(deck.white_cards, "White Cards (Answers)")
        elif choice == "3":
            search_cards(deck)


def show_cards_list(cards: list, title: str):
    """Show a paginated card list."""
    page_size = 10
    total_pages = (len(cards) + page_size - 1) // page_size
    current_page = 0

    while True:
        console.clear()
        start = current_page * page_size
        end = min(start + page_size, len(cards))

        table = Table(title=f"{title} (Page {current_page + 1}/{total_pages})")
        table.add_column("#", style="dim", width=4)
        table.add_column("Text", style="white")
        if cards and cards[0].card_type == CardType.BLACK:
            table.add_column("Pick", style="cyan", width=6)

        for i, card in enumerate(cards[start:end], start=start + 1):
            if card.card_type == CardType.BLACK:
                table.add_row(str(i), card.text, str(card.pick) if card.pick > 1 else "")
            else:
                table.add_row(str(i), card.text)

        console.print(table)
        console.print(f"\n[dim]< Prev[/] | [dim]Next >[/] | [dim]Q to exit[/]")

        key = Prompt.ask("", choices=["<", ">", "q", "Q"], default=">")

        if key in ["q", "Q"]:
            break
        elif key == "<" and current_page > 0:
            current_page -= 1
        elif key == ">" and current_page < total_pages - 1:
            current_page += 1


def search_cards(deck):
    """Search cards by text."""
    console.clear()
    query = Prompt.ask("Search").lower()

    results = []
    for card in deck.black_cards + deck.white_cards:
        if query in card.text.lower():
            results.append(card)

    if not results:
        console.print(f"\n[yellow]No results for '{query}'[/]")
    else:
        console.print(f"\n[green]Found {len(results)} cards:[/]\n")
        for card in results[:20]:
            card_type = "[black on white]WHITE[/]" if card.card_type == CardType.WHITE else "[white on black]BLACK[/]"
            console.print(f"  {card_type} {card.text}")

    Prompt.ask("\n[dim]Press Enter to continue[/]")


def create_custom_deck():
    """Create a new custom deck."""
    console.clear()
    console.print(Panel.fit("[bold]Create new deck[/]", border_style="green"))

    name = Prompt.ask("\nDeck name", default="My deck")
    short_name = Prompt.ask("Short name (max 5 chars)", default="DECK")[:5].upper()

    logo_path = None
    if Confirm.ask("Add a logo?", default=False):
        logo_path = Prompt.ask("Logo path (PNG/JPG)")
        if not Path(logo_path).exists():
            console.print("[yellow]File not found, continuing without logo[/]")
            logo_path = None

    deck = create_empty_deck(name, short_name, logo_path)

    # Ask to import default cards
    if Confirm.ask("\nImport default cards?", default=True):
        default_deck = create_default_deck()
        deck.black_cards = list(default_deck.black_cards)
        deck.white_cards = list(default_deck.white_cards)
        console.print(f"[green]Imported {deck.total_cards} cards![/]")

    # Card adding menu
    while True:
        console.print(f"\n[dim]Current cards: {len(deck.black_cards)} black, {len(deck.white_cards)} white[/]")
        console.print("\n  [cyan]1.[/] Add black card")
        console.print("  [cyan]2.[/] Add white card")
        console.print("  [cyan]3.[/] Save deck")
        console.print("  [cyan]0.[/] Cancel\n")

        choice = Prompt.ask("Choose", choices=["0", "1", "2", "3"])

        if choice == "0":
            if deck.total_cards > 0 and Confirm.ask("Save before exiting?"):
                filename = save_deck(deck)
                console.print(f"[green]Saved to {filename}[/]")
            break
        elif choice == "1":
            text = Prompt.ask("Text (use _____ for blanks)")
            pick = IntPrompt.ask("How many cards to pick?", default=1)
            add_card_to_deck(deck, text, CardType.BLACK, pick)
            console.print("[green]Card added![/]")
        elif choice == "2":
            text = Prompt.ask("White card text")
            add_card_to_deck(deck, text, CardType.WHITE)
            console.print("[green]Card added![/]")
        elif choice == "3":
            filename = save_deck(deck)
            console.print(f"[green]Saved to {filename}[/]")
            break


def manage_decks():
    """Manage saved decks."""
    while True:
        console.clear()
        decks = list_saved_decks()

        console.print(Panel.fit("[bold]Saved decks[/]", border_style="magenta"))

        if not decks:
            console.print("\n[dim]No saved decks[/]")
        else:
            table = Table()
            table.add_column("#", style="dim", width=4)
            table.add_column("Name")
            table.add_column("Short", style="cyan")
            table.add_column("Black", style="white on black")
            table.add_column("White", style="black on white")

            for i, d in enumerate(decks, 1):
                table.add_row(
                    str(i), d["name"], d["short_name"],
                    str(d["black_count"]), str(d["white_count"])
                )

            console.print(table)

        console.print("\n  [cyan]V.[/] View deck")
        console.print("  [cyan]E.[/] Delete deck")
        console.print("  [cyan]0.[/] Back to menu\n")

        choice = Prompt.ask("Choose", choices=["0", "v", "V", "e", "E"])

        if choice == "0":
            break
        elif choice.lower() == "v" and decks:
            idx = IntPrompt.ask("Deck number", default=1) - 1
            if 0 <= idx < len(decks):
                view_deck(decks[idx]["filename"])
        elif choice.lower() == "e" and decks:
            idx = IntPrompt.ask("Deck number to delete", default=1) - 1
            if 0 <= idx < len(decks):
                if Confirm.ask(f"Delete '{decks[idx]['name']}'?"):
                    delete_deck(decks[idx]["filename"])
                    console.print("[green]Deleted![/]")


def view_deck(filename: str):
    """View deck details."""
    deck = load_deck(filename)

    console.clear()
    console.print(Panel.fit(
        f"[bold]{deck.config.name}[/] ({deck.config.short_name})\n"
        f"Black: {len(deck.black_cards)} | White: {len(deck.white_cards)}",
        border_style="cyan"
    ))

    console.print("\n  [cyan]1.[/] Show black cards")
    console.print("  [cyan]2.[/] Show white cards")
    console.print("  [cyan]0.[/] Go back\n")

    choice = Prompt.ask("Choose", choices=["0", "1", "2"])

    if choice == "1":
        show_cards_list(deck.black_cards, "Black Cards")
    elif choice == "2":
        show_cards_list(deck.white_cards, "White Cards")


def export_menu():
    """PDF export menu."""
    console.clear()
    console.print(Panel.fit("[bold]Export to PDF[/]", border_style="yellow"))

    console.print("\n  [cyan]1.[/] Export default cards")
    console.print("  [cyan]2.[/] Export saved deck")
    console.print("  [cyan]0.[/] Back to menu\n")

    choice = Prompt.ask("Choose", choices=["0", "1", "2"])

    if choice == "0":
        return

    if choice == "1":
        # Custom configuration
        console.print("\n[bold]Customization:[/]")
        name = Prompt.ask("Game name", default="Cards Against Humanity")
        short_name = Prompt.ask("Short name", default="CAH")[:5].upper()

        logo_path = None
        if Confirm.ask("Add a logo?", default=False):
            logo_path = Prompt.ask("Logo path")
            if not Path(logo_path).exists():
                console.print("[yellow]File not found[/]")
                logo_path = None

        config = DeckConfig(name=name, short_name=short_name, logo_path=logo_path)
        deck = create_default_deck(config)
    else:
        decks = list_saved_decks()
        if not decks:
            console.print("[yellow]No saved decks[/]")
            Prompt.ask("[dim]Press Enter[/]")
            return

        for i, d in enumerate(decks, 1):
            console.print(f"  {i}. {d['name']}")

        idx = IntPrompt.ask("Deck number", default=1) - 1
        if not (0 <= idx < len(decks)):
            return

        deck = load_deck(decks[idx]["filename"])

    # Card type to export
    console.print("\n[bold]Which cards to export?[/]")
    console.print("  [cyan]1.[/] All")
    console.print("  [cyan]2.[/] Black only")
    console.print("  [cyan]3.[/] White only\n")

    cards_choice = Prompt.ask("Choose", choices=["1", "2", "3"])
    cards_type = {"1": "all", "2": "black", "3": "white"}[cards_choice]

    # Export
    ensure_exports_dir()
    filename = f"{deck.config.short_name.lower()}_{cards_type}.pdf"
    output_path = EXPORTS_DIR / filename

    with console.status("[bold green]Generating PDF..."):
        export_deck_to_pdf(deck, output_path, cards_type)

    console.print(f"\n[green]PDF created: {output_path}[/]")
    Prompt.ask("[dim]Press Enter to continue[/]")


def random_combo():
    """Generate a random card combination."""
    deck = create_default_deck()

    console.clear()
    console.print(Panel.fit("[bold]Random combination[/]", border_style="red"))

    black_card = random.choice(deck.black_cards)
    white_cards = random.sample(deck.white_cards, min(black_card.pick, len(deck.white_cards)))

    console.print("\n[white on black] QUESTION [/]")
    console.print(f"\n  {black_card.text}\n")

    console.print("[black on white] ANSWER [/]")
    for card in white_cards:
        console.print(f"\n  {card.text}")

    # Show combined result
    result = black_card.text
    for wc in white_cards:
        result = result.replace("_____", f"[bold red]{wc.text}[/]", 1)

    console.print("\n" + "─" * 40)
    console.print(f"\n[italic]{result}[/]")

    console.print("\n")
    if Confirm.ask("Another combination?", default=True):
        random_combo()


def main():
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
