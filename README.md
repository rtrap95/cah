# Cards Against Humanity - Generator

Generatore di carte personalizzate per Cards Against Humanity con interfaccia grafica e CLI.

> **Note**: Questo progetto è stato creato interamente tramite *vibe coding* con [Claude Code](https://claude.ai/code).

## Requisiti

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) (package manager)
- macOS: `brew install python-tk@3.13` (per tkinter)

## Installazione

```bash
git clone <repo-url>
cd cah
uv sync
```

## Utilizzo

### GUI (predefinita)

```bash
uv run python main.py
```

### CLI

```bash
uv run python main.py --cli
```

## Funzionalità

### Gestione Mazzi
- Crea mazzi personalizzati con nome, abbreviazione e logo
- Carica e gestisci più mazzi
- Imposta un mazzo predefinito per l'avvio
- Duplica mazzi esistenti

### Gestione Carte
- Carte nere (domande) con supporto multi-pick (pesca 2-3 carte)
- Carte bianche (risposte)
- Aggiungi carte singole o in batch (più carte alla volta)
- Modifica ed elimina carte con un click
- Ricerca testuale
- Paginazione per performance ottimale

### Export
- **PDF**: Carte stampabili in formato griglia (9 per pagina)
- **Testo**: Copia negli appunti in formato Markdown per condivisione/AI

### Altre funzionalità
- Combo casuale: mostra combinazione carta nera + bianche
- Navigazione da tastiera (frecce per cambiare pagina)
- Persistenza dati con SQLite

## Struttura Progetto

```
cah/
├── gui.py      # Interfaccia grafica (customtkinter)
├── db.py       # Database SQLite
├── models.py   # Modelli dati (Card, Deck, DeckConfig)
├── export.py   # Generazione PDF
├── cli.py      # Interfaccia a riga di comando
data/
├── cah.db      # Database SQLite
exports/        # PDF generati
```

## Scorciatoie da Tastiera

| Tasto | Azione |
|-------|--------|
| ← / → | Pagina precedente/successiva |
| ↑ / ↓ | Scroll verticale |
| Page Up/Down | Scroll veloce |
| Home / End | Inizio/fine lista |

## Tecnologie

- [customtkinter](https://github.com/TomSchimansky/CustomTkinter) - GUI moderna
- [reportlab](https://www.reportlab.com/) - Generazione PDF
- [SQLite](https://sqlite.org/) - Database
- [rich](https://github.com/Textualize/rich) / [typer](https://typer.tiangolo.com/) - CLI

## License

MIT
