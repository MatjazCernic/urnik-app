import sys
import sqlite3
import datetime
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QHBoxLayout, QWidget,
    QPushButton, QAbstractItemView, QComboBox, QStyledItemDelegate,
    QHeaderView, QSizePolicy
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QAbstractItemDelegate

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
EMPLOYEES = ["Matjaž Č.", "Edin B.", "Haris H."]

# 🔥 tvoj dropdown seznam
SHIFTS = ["", "Dop", "Pop", "Prost", "Dopust", "Bolniška"]


# ---------------- DROPDOWN DELEGATE ----------------

class ComboDelegate(QStyledItemDelegate):
    def _commit_close(self, editor):
        self.commitData.emit(editor)
        self.closeEditor.emit(editor, QAbstractItemDelegate.NoHint)

    def createEditor(self, parent, option, index):
        combo = QComboBox(parent)
        combo.addItems(SHIFTS)
        combo.activated.connect(lambda: self._commit_close(combo))
        return combo

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

    def setEditorData(self, editor, index):
        value = index.data() or ""
        i = editor.findText(value)
        editor.setCurrentIndex(i if i >= 0 else 0)

    def setModelData(self, editor, model, index):
        value = editor.currentText()
        model.setData(index, value)


# ---------------- MAIN APP ----------------

class MainWindow(QMainWindow):
    def is_week_locked(self):
        current_iso_week = datetime.date.today().isocalendar().week
        week = self.base_week + self.current_week
        return week < current_iso_week

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Urnik App MVP")
        self.setGeometry(200, 200, 900, 400)

        # ---------------- DB ----------------
        self.conn = sqlite3.connect("urnik.db")
        self.current_week = 0
        self.base_week = datetime.date.today().isocalendar().week
        self.create_table()

        # ---------------- TABLE ----------------
        self.table = QTableWidget()
        self.table.setRowCount(len(EMPLOYEES))
        self.table.setColumnCount(len(DAYS))

        self.table.setHorizontalHeaderLabels(DAYS)
        self.table.setVerticalHeaderLabels(EMPLOYEES)

        # 🔥 dropdown v tabeli
        self.table.setItemDelegate(ComboDelegate())
        self.table.itemChanged.connect(self.on_item_changed)

        # ---------------- TABLE POLISH (UI IMPROVEMENT) ----------------
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)

        self.table.verticalHeader().setDefaultSectionSize(30)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)

        # ---------------- SAVE BUTTON ----------------
        self.save_button = QPushButton("SAVE")
        self.save_button.clicked.connect(self.save_all)

        # ---------------- CLEAR BUTTON ----------------
        self.clear_button = QPushButton("CLEAR")
        self.clear_button.clicked.connect(self.clear_all)

        # ---------------- WEEK NAVIGATION ----------------
        self.week_label = QPushButton(
            f"Week: {self.base_week + self.current_week} ({self.get_week_range()})"
        )
        self.week_label.setEnabled(False)

        self.prev_week_btn = QPushButton("← Prev Week")
        self.next_week_btn = QPushButton("Next Week →")

        self.prev_week_btn.clicked.connect(self.prev_week)
        self.next_week_btn.clicked.connect(self.next_week)

        self.load_data()

        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)

        # ---------------- TOP ACTION BAR ----------------
        top_bar = QHBoxLayout()
        top_bar.addWidget(self.save_button)
        top_bar.addWidget(self.clear_button)
        top_bar.addStretch()

        # ---------------- WEEK BAR ----------------
        week_bar = QHBoxLayout()
        week_bar.addWidget(self.week_label)
        week_bar.addWidget(self.prev_week_btn)
        week_bar.addWidget(self.next_week_btn)
        week_bar.addStretch()

        layout.addLayout(top_bar)
        layout.addLayout(week_bar)
        layout.addWidget(self.table)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        # ---------------- BUTTON SIZE FIX ----------------
        for btn in [
            self.save_button,
            self.clear_button,
            self.prev_week_btn,
            self.next_week_btn,
            self.week_label
        ]:
            btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        # ---------------- UI STYLING ----------------
        self.setStyleSheet("""
QPushButton {
    padding: 6px;
    border-radius: 6px;
    background-color: #2d2d2d;
    color: white;
    font-size: 12px;
}

QPushButton:hover {
    background-color: #444444;
}

QPushButton:disabled {
    background-color: #666666;
    color: #cccccc;
}
""")

    def get_week_range(self):
        year = datetime.date.today().year
        week = self.base_week + self.current_week

        # safety clamp to valid ISO range
        week = max(1, min(week, 53))

        start = datetime.date.fromisocalendar(year, week, 1)
        end = datetime.date.fromisocalendar(year, week, 7)

        return f"{start.day}.{start.month}. - {end.day}.{end.month}."

    def color_item(self, item):
        if not item:
            return

        value = item.text()

        def bg(r, g, b):
            # very transparent colors
            return QColor(r, g, b, 20)

        # Set background color based on the value
        if value == "Dop":
            item.setBackground(bg(0, 255, 0))
        elif value == "Pop":
            item.setBackground(bg(255, 165, 0))
        elif value == "Prost":
            item.setBackground(bg(200, 200, 200))
        elif value == "Dopust":
            item.setBackground(bg(0, 120, 255))
        elif value == "Bolniška":
            item.setBackground(bg(255, 0, 0))
        else:
            item.setBackground(QColor(255, 255, 255, 0))
    def _safe_color(self, item):
        if not item:
            return

        # Check if the table is in editing state
    def on_item_changed(self, item):
        if not item:
            return
    
        # Use QTimer to delay the execution and ensure the item is updated
        QTimer.singleShot(0, lambda: self._safe_color(item))
    
    def color_item(self, item):
        if not item:
            return
    
        value = item.text()
    
        def bg(r, g, b):
            # very transparent colors
            return QColor(r, g, b, 20)
    
        # Set background color based on the value
        if value == "Dop":
            item.setBackground(bg(0, 255, 0))
        elif value == "Pop":
            item.setBackground(bg(255, 165, 0))
        elif value == "Prost":
            item.setBackground(bg(200, 200, 200))
        elif value == "Dopust":
            item.setBackground(bg(0, 120, 255))
        elif value == "Bolniška":
            item.setBackground(bg(255, 0, 0))
        else:
            item.setBackground(QColor(255, 255, 255, 0))
    
    def _safe_color(self, item):
        if not item:
            return
    
        # Check if the table is in editing state
        if self.table.state() == QAbstractItemView.EditingState:
            return
    
        # Apply color to the item
        self.color_item(item)
    
    def on_item_edit_finished(self, editor):
        # Get the current item after editing is finished
        item = self.table.currentItem()
        if not item:
            return
    
        # Apply color after editing is finished
        self.color_item(item)
        self.color_item(item)

    def _safe_color(self, item):
        if not item:
            return

        # Check if the table is in editing state
        if self.table.state() == QAbstractItemView.EditingState:
            return

        # Apply color to the item
        self.color_item(item)

    def on_item_changed(self, item):
        if not item:
            return

        # Debugging output to check when this method is called
        print(f"Item changed: {item.text()}")

        # Use QTimer to delay the execution and ensure the item is updated
        QTimer.singleShot(0, lambda: self._safe_color(item))

    # ---------------- DB ----------------

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shifts (
                employee TEXT,
                day TEXT,
                week INTEGER,
                shift TEXT,
                PRIMARY KEY (employee, day, week)
            )
        """)
        self.conn.commit()

    def save_shift(self, employee, day, shift):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO shifts (employee, day, week, shift)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(employee, day, week)
            DO UPDATE SET shift=excluded.shift
        """, (employee, day, self.current_week, shift))
        self.conn.commit()

    def load_shift(self, employee, day):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT shift FROM shifts
            WHERE employee=? AND day=? AND week=?
        """, (employee, day, self.current_week))
        row = cursor.fetchone()
        return row[0] if row else ""

    def debug_db(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM shifts")
        print("DB CONTENT:", cursor.fetchall())

    # ---------------- LOAD ----------------

    def load_data(self):
        self.table.blockSignals(True)
        locked = self.is_week_locked()
        for row, emp in enumerate(EMPLOYEES):
            for col, day in enumerate(DAYS):
                value = self.load_shift(emp, day)

                item = QTableWidgetItem(value)
                self.table.setItem(row, col, item)
                if locked:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                else:
                    item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)

                # apply color immediately
                self.color_item(item)
        self.table.setEditTriggers(
            QAbstractItemView.NoEditTriggers if locked
            else (QAbstractItemView.DoubleClicked | QAbstractItemView.SelectedClicked)
        )
        self.table.blockSignals(False)
        self.debug_db()

    # ---------------- SAVE ----------------

    def save_all(self):
        item = self.table.currentItem()
        if item:
            self.table.closePersistentEditor(item)
        self.table.clearFocus()

        cursor = self.conn.cursor()

        for r in range(len(EMPLOYEES)):
            for c in range(len(DAYS)):

                item = self.table.item(r, c)

                if item:
                    self.table.closePersistentEditor(item)

                value = item.text() if item else ""

                employee = EMPLOYEES[r]
                day = DAYS[c]

                cursor.execute("""
                    INSERT INTO shifts (employee, day, week, shift)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(employee, day, week)
                    DO UPDATE SET shift=excluded.shift
                """, (employee, day, self.current_week, value))

        self.conn.commit()
        print("SAVED CURRENT WEEK:", self.base_week + self.current_week)

    def clear_all(self):
        # clear UI
        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                self.table.setItem(row, col, QTableWidgetItem(""))

        # clear DB
        cursor = self.conn.cursor()
        real_week = self.base_week + self.current_week
        cursor.execute("DELETE FROM shifts WHERE week=?", (real_week,))
        self.conn.commit()

        print("CLEARED ALL DATA")

    def copy_week(self):
        cursor = self.conn.cursor()

        target_week = self.base_week + self.current_week + 1

        for row in range(len(EMPLOYEES)):
            for col in range(len(DAYS)):
                item = self.table.item(row, col)

                if not item:
                    continue

                value = item.text().strip()
                if value == "":
                    continue

                employee = EMPLOYEES[row]
                day = DAYS[col]

                cursor.execute("""
                    INSERT INTO shifts (employee, day, week, shift)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(employee, day, week)
                    DO UPDATE SET shift=excluded.shift
                """, (employee, day, target_week, value))

        self.conn.commit()

        print("WEEK COPIED to week", target_week)

    def prev_week(self):
        self.save_all()

        if self.current_week > 0:
            self.current_week -= 1

        self.load_data()
        self.week_label.setText(
            f"Week: {self.base_week + self.current_week} ({self.get_week_range()})"
        )

    def next_week(self):
        self.save_all()

        self.current_week += 1

        self.load_data()
        self.week_label.setText(
            f"Week: {self.base_week + self.current_week} ({self.get_week_range()})"
        )



# ---------------- RUN ----------------

app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())

# ---------------- COLORING FUNCTIONS ----------------

def color_item(self, item):
    if not item:
        return

    value = item.text()

    def bg(r, g, b):
        # very transparent colors
        return QColor(r, g, b, 20)

    # Set background color based on the value
    if value == "Dop":
        item.setBackground(bg(0, 255, 0))
    elif value == "Pop":
        item.setBackground(bg(255, 165, 0))
    elif value == "Prost":
        item.setBackground(bg(200, 200, 200))
    elif value == "Dopust":
        item.setBackground(bg(0, 120, 255))
    elif value == "Bolniška":
        item.setBackground(bg(255, 0, 0))
    else:
        item.setBackground(QColor(255, 255, 255, 0))

def _safe_color(self, item):
    if not item:
        return

    # Check if the table is in editing state
    if self.table.state() == QAbstractItemView.EditingState:
        return

    # Apply color to the item
    self.color_item(item)

def on_item_changed(self, item):
    if not item:
        return

    # Use QTimer to delay the execution and ensure the item is updated
    QTimer.singleShot(0, lambda: self._safe_color(item))

def on_item_edit_finished(self, editor):
    # Get the current item after editing is finished
    item = self.table.currentItem()
    if not item:
        return

    # Apply color after editing is finished
    self.color_item(item)