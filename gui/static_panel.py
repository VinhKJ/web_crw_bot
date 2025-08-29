"""
static_panel.py
----------------

Defines the widget used for scraping static web pages. Users can
input a CSS selector to specify which elements to extract from the
page referenced by the URL in the main window. Results are displayed
in a simple table and can be exported if desired.
"""

from __future__ import annotations

from typing import List, Dict

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)


class StaticPanel(QWidget):
    """
    Panel for configuring and executing static web scraping. Provides
    an input for CSS selectors and displays results in a table.
    """

    run_requested = pyqtSignal(str)
    log_signal = pyqtSignal(str)
    result_signal = pyqtSignal(list)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Selector input
        selector_layout = QHBoxLayout()
        selector_label = QLabel("Selector (CSS):")
        self.selector_edit = QLineEdit()
        self.selector_edit.setPlaceholderText("Ví dụ: div.article-content p")
        selector_layout.addWidget(selector_label)
        selector_layout.addWidget(self.selector_edit)

        # Buttons
        run_button = QPushButton("Cào dữ liệu")
        run_button.clicked.connect(self.on_run_clicked)

        # Results table
        self.table = QTableWidget(0, 0)
        self.table.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        layout.addLayout(selector_layout)
        layout.addWidget(run_button)
        layout.addWidget(QLabel("Kết quả:"))
        layout.addWidget(self.table)

    def on_run_clicked(self) -> None:
        selector = self.selector_edit.text().strip()
        if not selector:
            self.log_signal.emit("Vui lòng nhập selector để cào dữ liệu.")
            return
        self.run_requested.emit(selector)

    def display_results(self, data: List[Dict[str, str]]) -> None:
        """Populate the table with scraped data."""
        # Determine columns from keys present in data
        keys = set()
        for item in data:
            keys.update(item.keys())
        columns = list(keys)
        self.table.setColumnCount(len(columns))
        self.table.setRowCount(len(data))
        self.table.setHorizontalHeaderLabels(columns)
        for row, item in enumerate(data):
            for col, key in enumerate(columns):
                value = item.get(key, "")
                self.table.setItem(row, col, QTableWidgetItem(str(value)))
        self.result_signal.emit(data)