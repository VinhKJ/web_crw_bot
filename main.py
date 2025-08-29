"""
Entry point for the Web Scraper & Automation Bot application.

This script initialises the PyQt6 application, creates the main window
and starts the event loop. The main window exposes functionality for
scraping static web pages using Requests/BeautifulSoup and running
automated scenarios against dynamic sites via Selenium. Refer to the
README or accompanying documentation for usage instructions.
"""

from PyQt6.QtWidgets import QApplication
import sys

from gui.main_window import MainWindow


def main() -> None:
    """Launch the application."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()