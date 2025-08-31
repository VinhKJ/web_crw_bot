"""
Main window for the Web Scraper & Automation Bot.

This module defines the top-level QMainWindow which holds the controls
for selecting between static and dynamic scraping modes, entering the
target URL, and displaying logs/results. It orchestrates the
interaction between the static and dynamic panels and delegates
scraping and automation tasks to the appropriate back-end classes.
"""

from __future__ import annotations

from typing import List, Dict, Any

from PyQt6.QtCore import Qt, pyqtSignal, QThread, QObject
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QRadioButton,
    QButtonGroup,
    QStackedWidget,
    QTextEdit,
    QMessageBox,
)

from gui.static_panel import StaticPanel
from gui.dynamic_panel import DynamicPanel
from core.static_scraper import StaticScraper, ScrapedItem
from core.data_exporter import to_dataframe
from core.scenario_runner import ScenarioRunner


class ScenarioThread(QThread):
    """Runs a ScenarioRunner in a separate thread."""

    log_signal = pyqtSignal(str)
    result_signal = pyqtSignal(list)
    finished_signal = pyqtSignal()

    def __init__(self, actions: List[Dict[str, Any]], headless: bool = True) -> None:
        super().__init__()
        self.actions = actions
        self.headless = headless
        self.runner: ScenarioRunner | None = None

    def run(self) -> None:
        try:
            self.runner = ScenarioRunner(headless=self.headless)
        except Exception as exc:
            self.log_signal.emit(str(exc))
            self.finished_signal.emit()
            return

        def log_callback(msg: str) -> None:
            self.log_signal.emit(msg)

        def result_callback(data: List[Dict[str, str]]) -> None:
            self.result_signal.emit(data)

        try:
            self.runner.run(
                self.actions, log_callback=log_callback, result_callback=result_callback
            )
        finally:
            if self.runner:
                self.runner.close()
            self.finished_signal.emit()

    def stop(self) -> None:
        if self.runner:
            self.runner.stop()


class MainWindow(QMainWindow):
    """
    The main application window. Provides controls for entering a URL,
    switching between static and dynamic modes, and viewing logs and
    results. Delegates work to StaticPanel or DynamicPanel depending
    on the selected mode.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Web Scraper & Automation Bot")
        self.resize(900, 600)

        # Top-level layout
        central_widget = QWidget()
        central_layout = QVBoxLayout()
        central_widget.setLayout(central_layout)
        self.setCentralWidget(central_widget)

        # URL input
        url_layout = QHBoxLayout()
        url_label = QLabel("URL:")
        self.url_edit = QLineEdit()
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_edit)

        # Mode selection
        mode_layout = QHBoxLayout()
        mode_label = QLabel("Chế độ:")
        self.static_radio = QRadioButton("Web Tĩnh")
        self.dynamic_radio = QRadioButton("Web Động")
        self.static_radio.setChecked(True)
        self.mode_group = QButtonGroup(self)
        self.mode_group.addButton(self.static_radio)
        self.mode_group.addButton(self.dynamic_radio)
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.static_radio)
        mode_layout.addWidget(self.dynamic_radio)
        mode_layout.addStretch()

        # Stacked panels
        self.static_panel = StaticPanel()
        self.dynamic_panel = DynamicPanel()
        self.stack = QStackedWidget()
        self.stack.addWidget(self.static_panel)
        self.stack.addWidget(self.dynamic_panel)

        # Logs/Results area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFixedHeight(150)
        self.log_text.setPlaceholderText("Log sẽ hiển thị ở đây...")

        # Assemble layout
        central_layout.addLayout(url_layout)
        central_layout.addLayout(mode_layout)
        central_layout.addWidget(self.stack)
        central_layout.addWidget(QLabel("Nhật ký:"))
        central_layout.addWidget(self.log_text)

        # Connections
        self.static_radio.toggled.connect(self.switch_mode)
        self.static_panel.run_requested.connect(self.handle_static_run)
        self.static_panel.log_signal.connect(self.append_log)
        self.static_panel.result_signal.connect(self.handle_static_result)

        self.dynamic_panel.run_requested.connect(self.handle_dynamic_run)
        self.dynamic_panel.stop_requested.connect(self.stop_dynamic_run)
        self.dynamic_panel.log_signal.connect(self.append_log)

        # Placeholder for running thread
        self.scenario_thread: ScenarioThread | None = None

    def switch_mode(self, checked: bool) -> None:
        """Switch the visible panel based on the selected radio button."""
        if self.static_radio.isChecked():
            self.stack.setCurrentWidget(self.static_panel)
        else:
            self.stack.setCurrentWidget(self.dynamic_panel)

    def append_log(self, message: str) -> None:
        """Append a message to the log area."""
        self.log_text.append(message)

    # ===== Static Mode Handling =====
    def handle_static_run(self, selector: str) -> None:
        """Callback when the static panel requests a scrape."""
        url = self.url_edit.text().strip()
        if not url:
            QMessageBox.warning(self, "Thiếu URL", "Vui lòng nhập URL để cào dữ liệu.")
            return
        self.append_log(f"Bắt đầu cào web tĩnh: {url} với selector '{selector}'")
        # Run scraping in worker thread to avoid blocking UI
        thread = QThread()

        class Worker(QObject):
            finished = pyqtSignal()
            result = pyqtSignal(list)
            log = pyqtSignal(str)

            def run(self_inner: Worker) -> None:
                try:
                    items = StaticScraper.scrape(url, selector)
                    self_inner.result.emit([{'text': item.text, **item.attrs} for item in items])
                except Exception as exc:
                    self_inner.log.emit(f"Lỗi khi cào trang tĩnh: {exc}")
                finally:
                    self_inner.finished.emit()

        worker = Worker()
        worker.moveToThread(thread)
        # Connect signals
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        worker.result.connect(self.static_panel.display_results)
        worker.log.connect(self.append_log)
        thread.started.connect(worker.run)
        thread.start()

    def handle_static_result(self, data: List[Dict[str, str]]) -> None:
        """No-op: results are displayed by static panel itself."""
        pass

    # ===== Dynamic Mode Handling =====
    def handle_dynamic_run(self, actions: List[Dict[str, Any]]) -> None:
        """Start executing a dynamic scenario in a separate thread."""
        if not actions:
            QMessageBox.information(self, "Kịch bản trống", "Vui lòng thêm hành động vào kịch bản.")
            return
        # Ask for headless mode maybe: for now always headless
        # disable UI controls to prevent multiple runs
        self.dynamic_panel.set_running(True)
        self.append_log("Bắt đầu chạy kịch bản động...")
        # Create and start scenario thread
        self.scenario_thread = ScenarioThread(actions, headless=True)
        self.scenario_thread.log_signal.connect(self.append_log)
        self.scenario_thread.result_signal.connect(self.handle_dynamic_result)
        self.scenario_thread.finished_signal.connect(self.dynamic_run_finished)
        self.scenario_thread.start()

    def stop_dynamic_run(self) -> None:
        """Stop an ongoing dynamic scenario, if any."""
        if self.scenario_thread:
            self.scenario_thread.stop()
            self.append_log("Đã gửi tín hiệu dừng kịch bản.")

    def dynamic_run_finished(self) -> None:
        """Called when the scenario thread has finished."""
        self.append_log("Kịch bản động đã kết thúc.")
        self.dynamic_panel.set_running(False)
        self.scenario_thread = None

    def handle_dynamic_result(self, data: List[Dict[str, str]]) -> None:
        """Pass extracted data to the dynamic panel for display."""
        self.dynamic_panel.display_results(data)