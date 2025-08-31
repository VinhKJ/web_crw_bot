"""
dynamic_panel.py
----------------

Defines the widget used for building and executing dynamic web
automation scenarios. Users can add, remove and reorder actions
representing typical user interactions (navigate, click, type,
keypress, scroll, wait, extract) and then run the scenario using
Selenium. Results from extraction steps are displayed in a table.
"""

from __future__ import annotations

import json
from typing import List, Dict, Any

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QFileDialog,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLabel,
    QDialog,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QComboBox,
    QDialogButtonBox,
)


class DynamicPanel(QWidget):
    """
    Panel for building and executing scenarios on dynamic web pages. It
    contains a list of actions that can be manipulated and executed via
    Selenium. The panel emits signals to run or stop a scenario and
    displays extraction results.
    """

    run_requested = pyqtSignal(list)
    stop_requested = pyqtSignal()
    log_signal = pyqtSignal(str)
    result_signal = pyqtSignal(list)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.actions: List[Dict[str, Any]] = []
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Action list and controls
        list_layout = QHBoxLayout()
        self.action_list = QListWidget()
        list_controls = QVBoxLayout()
        add_buttons = QVBoxLayout()
        # Buttons for adding different actions
        btn_open = QPushButton("Mở URL")
        btn_open.clicked.connect(self.add_open_url)
        btn_click = QPushButton("Nhấp chuột")
        btn_click.clicked.connect(self.add_click)
        btn_type = QPushButton("Gõ văn bản")
        btn_type.clicked.connect(self.add_type)
        btn_key = QPushButton("Nhấn phím")
        btn_key.clicked.connect(self.add_keypress)
        btn_scroll = QPushButton("Cuộn trang")
        btn_scroll.clicked.connect(self.add_scroll)
        btn_wait = QPushButton("Chờ")
        btn_wait.clicked.connect(self.add_wait)
        btn_extract = QPushButton("Trích xuất")
        btn_extract.clicked.connect(self.add_extract)

        for b in [btn_open, btn_click, btn_type, btn_key, btn_scroll, btn_wait, btn_extract]:
            b.setMinimumWidth(100)
            add_buttons.addWidget(b)
        add_buttons.addStretch()

        # Up/Down/Remove controls
        move_up_btn = QPushButton("↑")
        move_up_btn.clicked.connect(self.move_up)
        move_down_btn = QPushButton("↓")
        move_down_btn.clicked.connect(self.move_down)
        remove_btn = QPushButton("Xóa")
        remove_btn.clicked.connect(self.remove_action)

        list_controls.addLayout(add_buttons)
        list_controls.addWidget(move_up_btn)
        list_controls.addWidget(move_down_btn)
        list_controls.addWidget(remove_btn)
        list_controls.addStretch()

        list_layout.addWidget(self.action_list)
        list_layout.addLayout(list_controls)

        # Run controls
        run_layout = QHBoxLayout()
        self.run_btn = QPushButton("▶ Chạy kịch bản")
        self.run_btn.clicked.connect(self.run_scenario)
        self.stop_btn = QPushButton("■ Dừng")
        self.stop_btn.clicked.connect(lambda: self.stop_requested.emit())
        self.stop_btn.setEnabled(False)
        save_btn = QPushButton("💾 Lưu")
        save_btn.clicked.connect(self.save_scenario)
        open_btn = QPushButton("📂 Mở")
        open_btn.clicked.connect(self.load_scenario)
        run_layout.addWidget(self.run_btn)
        run_layout.addWidget(self.stop_btn)
        run_layout.addStretch()
        run_layout.addWidget(save_btn)
        run_layout.addWidget(open_btn)

        # Results table
        self.table = QTableWidget()
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        layout.addLayout(list_layout)
        layout.addLayout(run_layout)
        layout.addWidget(QLabel("Kết quả (từ hành động Trích xuất):"))
        layout.addWidget(self.table)

    # ============== Action Formatting ==============
    @staticmethod
    def format_action(action: Dict[str, Any]) -> str:
        t = action.get("type")
        if t == "open_url":
            return f"Mở URL: {action.get('url', '')}"
        if t == "click":
            return f"Nhấp vào: {action.get('selector', '')}"
        if t == "type":
            return f"Gõ '{action.get('text', '')}' vào: {action.get('selector', '')}"
        if t == "keypress":
            return f"Nhấn phím: {action.get('key', '')}"
        if t == "scroll":
            direction = action.get('direction', 'down')
            amount = action.get('amount', 0)
            dir_vn = 'Xuống' if direction == 'down' else 'Lên'
            return f"Cuộn {dir_vn} {amount}px"
        if t == "wait":
            return f"Chờ {action.get('seconds', 0)} giây"
        if t == "extract":
            return f"Trích xuất: {action.get('selector', '')}"
        return str(action)

    def refresh_list(self) -> None:
        self.action_list.clear()
        for act in self.actions:
            item = QListWidgetItem(self.format_action(act))
            self.action_list.addItem(item)

    # ============== Add Action Dialogs ==============
    def add_open_url(self) -> None:
        dlg = _OpenUrlDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            url = dlg.url_edit.text().strip()
            if url:
                act = {"type": "open_url", "url": url, "description": f"Mở URL {url}"}
                self.actions.append(act)
                self.refresh_list()

    def add_click(self) -> None:
        dlg = _SelectorDialog(self, title="Nhấp chuột", selector_label="CSS Selector")
        if dlg.exec() == QDialog.DialogCode.Accepted:
            selector = dlg.selector_edit.text().strip()
            if selector:
                act = {"type": "click", "selector": selector, "description": f"Nhấp {selector}"}
                self.actions.append(act)
                self.refresh_list()

    def add_type(self) -> None:
        dlg = _TypeDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            selector = dlg.selector_edit.text().strip()
            text = dlg.text_edit.text()
            if selector:
                act = {
                    "type": "type",
                    "selector": selector,
                    "text": text,
                    "description": f"Gõ '{text}' vào {selector}",
                }
                self.actions.append(act)
                self.refresh_list()

    def add_keypress(self) -> None:
        dlg = _KeyPressDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            key = dlg.key_combo.currentText().strip()
            if key:
                act = {
                    "type": "keypress",
                    "key": key,
                    "description": f"Nhấn phím {key}",
                }
                self.actions.append(act)
                self.refresh_list()

    def add_scroll(self) -> None:
        dlg = _ScrollDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            direction = dlg.direction_combo.currentText()
            amount = dlg.amount_spin.value()
            act = {
                "type": "scroll",
                "direction": "down" if direction == "Xuống" else "up",
                "amount": amount,
                "description": f"Cuộn {direction.lower()} {amount} px",
            }
            self.actions.append(act)
            self.refresh_list()

    def add_wait(self) -> None:
        dlg = _WaitDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            seconds = dlg.seconds_spin.value()
            act = {
                "type": "wait",
                "seconds": seconds,
                "description": f"Chờ {seconds} giây",
            }
            self.actions.append(act)
            self.refresh_list()

    def add_extract(self) -> None:
        dlg = _SelectorDialog(self, title="Trích xuất", selector_label="CSS Selector")
        if dlg.exec() == QDialog.DialogCode.Accepted:
            selector = dlg.selector_edit.text().strip()
            if selector:
                act = {
                    "type": "extract",
                    "selector": selector,
                    "all": True,
                    "description": f"Trích xuất {selector}",
                }
                self.actions.append(act)
                self.refresh_list()

    # ============== List Manipulation ==============
    def move_up(self) -> None:
        row = self.action_list.currentRow()
        if row > 0:
            self.actions[row - 1], self.actions[row] = self.actions[row], self.actions[row - 1]
            self.refresh_list()
            self.action_list.setCurrentRow(row - 1)

    def move_down(self) -> None:
        row = self.action_list.currentRow()
        if 0 <= row < len(self.actions) - 1:
            self.actions[row + 1], self.actions[row] = self.actions[row], self.actions[row + 1]
            self.refresh_list()
            self.action_list.setCurrentRow(row + 1)

    def remove_action(self) -> None:
        row = self.action_list.currentRow()
        if 0 <= row < len(self.actions):
            del self.actions[row]
            self.refresh_list()

    # ============== Scenario I/O ==============
    def save_scenario(self) -> None:
        if not self.actions:
            self.log_signal.emit("Không có hành động nào để lưu.")
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Lưu kịch bản", "", "JSON Files (*.json)"
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(self.actions, f, ensure_ascii=False, indent=2)
                self.log_signal.emit(f"Đã lưu kịch bản vào {file_path}")
            except Exception as exc:
                self.log_signal.emit(f"Lỗi khi lưu kịch bản: {exc}")

    def load_scenario(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Mở kịch bản", "", "JSON Files (*.json)"
        )
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    self.actions = data
                    self.refresh_list()
                    self.log_signal.emit(f"Đã tải kịch bản từ {file_path}")
                else:
                    self.log_signal.emit("File kịch bản không hợp lệ.")
            except Exception as exc:
                self.log_signal.emit(f"Lỗi khi mở kịch bản: {exc}")

    # ============== Run Scenario ==============
    def run_scenario(self) -> None:
        if not self.actions:
            self.log_signal.emit("Vui lòng thêm hành động vào kịch bản trước khi chạy.")
            return
        # Emit run request with a deep copy to avoid modification during run
        self.run_requested.emit([dict(a) for a in self.actions])

    def set_running(self, running: bool) -> None:
        """Enable/disable run and stop buttons based on running state."""
        self.run_btn.setEnabled(not running)
        self.stop_btn.setEnabled(running)

    # ============== Display Results ==============
    def display_results(self, data: List[Dict[str, str]]) -> None:
        """Show extracted data in the result table."""
        if not data:
            return
        columns = set()
        for item in data:
            columns.update(item.keys())
        cols = list(columns)
        self.table.setColumnCount(len(cols))
        self.table.setRowCount(len(data))
        self.table.setHorizontalHeaderLabels(cols)
        for row, item in enumerate(data):
            for col, key in enumerate(cols):
                value = item.get(key, "")
                self.table.setItem(row, col, QTableWidgetItem(str(value)))


# ====== Helper Dialog Classes ======

class _OpenUrlDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Mở URL")
        layout = QFormLayout(self)
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("https://example.com")
        layout.addRow("URL:", self.url_edit)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class _SelectorDialog(QDialog):
    def __init__(self, parent: QWidget | None = None, title: str = "Chọn", selector_label: str = "Selector") -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        layout = QFormLayout(self)
        self.selector_edit = QLineEdit()
        self.selector_edit.setPlaceholderText("CSS selector hoặc XPath")
        layout.addRow(f"{selector_label}:", self.selector_edit)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class _TypeDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Gõ văn bản")
        layout = QFormLayout(self)
        self.selector_edit = QLineEdit()
        self.selector_edit.setPlaceholderText("input#search")
        self.text_edit = QLineEdit()
        self.text_edit.setPlaceholderText("Nội dung cần gõ")
        layout.addRow("Selector:", self.selector_edit)
        layout.addRow("Văn bản:", self.text_edit)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class _KeyPressDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Nhấn phím")
        layout = QFormLayout(self)
        self.key_combo = QComboBox()
        self.key_combo.addItems(["Enter", "Tab", "Escape", "Backspace"])
        layout.addRow("Phím:", self.key_combo)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class _ScrollDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Cuộn trang")
        layout = QFormLayout(self)
        self.direction_combo = QComboBox()
        self.direction_combo.addItems(["Xuống", "Lên"])
        self.amount_spin = QSpinBox()
        self.amount_spin.setRange(10, 5000)
        self.amount_spin.setSingleStep(100)
        self.amount_spin.setValue(500)
        layout.addRow("Hướng:", self.direction_combo)
        layout.addRow("Pixel:", self.amount_spin)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class _WaitDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Chờ")
        layout = QFormLayout(self)
        self.seconds_spin = QSpinBox()
        self.seconds_spin.setRange(1, 120)
        self.seconds_spin.setValue(5)
        layout.addRow("Giây:", self.seconds_spin)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)