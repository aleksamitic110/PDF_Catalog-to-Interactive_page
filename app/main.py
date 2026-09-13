"""Application entry point."""

from __future__ import annotations


def main() -> None:
    """Launch the GUI application."""
    from app.ui.main_window import run_app

    run_app()


if __name__ == "__main__":
    main()