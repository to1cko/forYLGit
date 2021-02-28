import sqlite3
from typing import List, Tuple
from PyQt5 import uic, QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QWidget
from PyQt5.Qt import QAbstractItemModel
import sys
from pathlib import Path


MAIN_UI_FILENAME = Path('./main.ui')
DIALOG_UI_FILENAME = Path('./addEditCoffeeForm.ui')
DB_FILENAME = Path('./coffee.sqlite')


class SqliteStorage:
    def __init__(self, filename: Path):
        self._connection = sqlite3.connect(filename)
        self._cursor = self._connection.cursor()

    def get_coffee_info(self) -> List[Tuple]:
        sql = 'select * from coffee'
        data = self._cursor.execute(sql).fetchall()
        return data

    def save_new_coffee_info(self, data) -> int:
        sql = 'insert into coffee(roasting, flavor, price,' +\
            ' size, type) values (?, ?, ?, ?, ?)'
        self._cursor.execute(sql, data)
        self._connection.commit()
        return self._cursor.lastrowid

    def update_coffee_info(self, data):
        sql = 'update coffee set roasting = ?, flavor = ?,' +\
            ' price = ?, size = ?, type = ? where id = ?'
        self._cursor.execute(sql, (*data[1:], data[0]))
        self._connection.commit()


class MainWindow(QMainWindow):
    def __init__(self, storage: SqliteStorage):
        super().__init__()
        uic.loadUi(MAIN_UI_FILENAME, self)
        self.storage = storage
        self.fill_table()
        self.edit_button.clicked.connect(self.handle_edit)
        self.create_button.clicked.connect(self.handle_create)

    def handle_edit(self):
        row = self.table.currentRow()
        if row == -1:
            return
        data = [self.table.item(row, index).text()
                for index in range(6)]

        def callback(callback_data):
            self.storage.update_coffee_info(callback_data)
            self.fill_row(row, callback_data)

        self.dialog = AddEditDialog(callback, data)
        self.dialog.show()

    def handle_create(self):
        def callback(data):
            id_ = self.storage.save_new_coffee_info(data)
            rows = self.table.rowCount()
            self.table.setRowCount(rows + 1)
            self.fill_row(rows, (id_, *data))

        self.dialog = AddEditDialog(callback)
        self.dialog.show()

    def fill_row(self, row, data):
        for index, elem in enumerate(data):
            item = QTableWidgetItem(str(elem))
            item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
            self.table.setItem(row, index, item)

    def fill_table(self):
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ['ID', 'прожарка', "вкус", "цена", "объем", "тип"])

        data = self.storage.get_coffee_info()
        for i, coffee_info in enumerate(data):
            rows = self.table.rowCount()
            self.table.setRowCount(rows + 1)
            self.fill_row(i, coffee_info)


class AddEditDialog(QWidget):
    def __init__(self, on_save_callback, data=None):
        super().__init__()
        uic.loadUi(DIALOG_UI_FILENAME, self)
        self.id_ = None
        self.type_edit.addItems(['зерна', 'молотый'])
        if data:
            self.fill_data(data)
        self.on_save_callback = on_save_callback
        self.save_button.clicked.connect(self.handle_save)

    def fill_data(self, data):
        id_, roast, flavor, price, volume, type_ = data
        self.id_ = int(id_)
        self.roast_edit.setText(roast)
        self.flavor_edit.setText(flavor)
        self.price_edit.setValue(float(price))
        self.volume_edit.setValue(float(volume))
        self.type_edit.setCurrentText(type_)

    def handle_save(self):
        data = (self.roast_edit.text(),
                self.flavor_edit.text(),
                self.price_edit.value(),
                self.volume_edit.value(),
                self.type_edit.currentText())
        if self.id_:
            data = (self.id_, *data)
        self.on_save_callback(data)
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    storage = SqliteStorage(DB_FILENAME)
    window = MainWindow(storage)
    window.show()
    sys.exit(app.exec_())
