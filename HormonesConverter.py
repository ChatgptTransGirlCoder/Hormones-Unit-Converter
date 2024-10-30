# Made with love by FayEstrogirl on Discord <3
import sys
from functools import partial
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QDesktopWidget, QLabel, QLineEdit, QPushButton, QComboBox, QVBoxLayout, QWidget, QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsScene, QGraphicsView
from PyQt5.QtGui import QPen, QPainter
from PyQt5.QtCore import Qt, QPointF
from PyQt5 import sip

class Converter(QWidget):

    CONVERSIONS = {
        'estradiol': {
            'pg/mL': {'pmol/L': lambda x: x*3.671341463414634},
            'pmol/L': {'pg/mL': lambda x: x/3.671341463414634}
        },
        'testosterone': {
            'ng/dL': {'nmol/L': lambda x: x/28.842, 'ng/mL': lambda x: x/100},
            'nmol/L': {'ng/dL': lambda x: x*28.842, 'ng/mL': lambda x: x/3.46716505301953},
            'ng/mL': {'nmol/L': lambda x: x/0.2884200070627729, 'ng/dL': lambda x: x*3.46716505301953}
        },
        'prolactin': {
            'mIU/L': {'ng/mL': lambda x: x / 21.27659574468085, 'µg/L': lambda x: x / 21.27659574468085},
            'ng/mL': {'mIU/L': lambda x: x * 21.27659574468085, 'µg/L': lambda x: x * 1},
            'µg/L': {'mIU/L': lambda x: x * 21.27659574468085, 'ng/mL': lambda x: x * 1}
        },
        'progesterone': {
            'nmol/L': {'ng/mL': lambda x: x * 0.314460162601626, 'pmol/L': lambda x: x * 1000, 'ng/dL': lambda x: x * 31.446},
            'ng/mL': {'nmol/L': lambda x: x / 0.314460162601626, 'pmol/L': lambda x: x * 1000 / 0.314460162601626, 'ng/dL': lambda x: x * 10},
            'pmol/L': {'nmol/L': lambda x: x / 1000, 'ng/mL': lambda x: x * 0.314460162601626 / 1000, 'ng/dL': lambda x: x * 31.446 / 1000},
            'ng/dL': {'nmol/L': lambda x: x / 31.446, 'ng/mL': lambda x: x / 10, 'pmol/L': lambda x: x * 1000 / 31.446}
        }
    }

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
       
        self.add_hormone("Estradiol", ["pmol/L", "pg/mL"], 0, 1, 100, 200)
        self.add_hormone("Testosterone", ["nmol/L", "ng/dL", "ng/mL"], 0, 1, 15, 70)
        self.add_hormone("Prolactin", ["mIU/L", "ng/mL", "µg/L"], 0, 1, 4.8, 23.3)
        self.add_hormone("Progesterone", ["nmol/L", "ng/mL", "pmol/L", "ng/dL"], 0, 1, 4, 25)
        
        self.setGeometry(300, 300, 360, 320)
        self.setWindowTitle('Hormone Unit Converter')

        # Center the window on the screen
        desktop = QApplication.desktop()
        screen_rect = desktop.screenGeometry(desktop.primaryScreen())
        center = screen_rect.center() - self.rect().center()
        self.move(center)
        self.show()

    def add_hormone(self, hormone_name, units, from_index, to_index, min_value, max_value):
        hormone_label = QLabel(hormone_name, self)
        self.layout.addWidget(hormone_label)

        input_layout = QHBoxLayout()
        self.layout.addLayout(input_layout)

        hormone_input = QLineEdit(self)
        input_layout.addWidget(hormone_input)

        from_combo = QComboBox(self)
        for unit in units:
            from_combo.addItem(unit)
        from_combo.setCurrentIndex(from_index)
        input_layout.addWidget(from_combo)

        to_combo = QComboBox(self)
        for unit in units:
            to_combo.addItem(unit)
        to_combo.setCurrentIndex(to_index)
        input_layout.addWidget(to_combo)

        button_layout = QHBoxLayout()
        self.layout.addLayout(button_layout)

        hormone_button = QPushButton('Convert', self)
        button_layout.addWidget(hormone_button)
        hormone_button.clicked.connect(lambda: self.convert(hormone_name.lower(), hormone_input.text(), from_combo.currentText(), to_combo.currentText()))

        switch_button = QPushButton('Switch', self)
        button_layout.addWidget(switch_button)
        switch_button.clicked.connect(partial(self.switch_units, from_combo, to_combo))

        result_layout = QHBoxLayout()
        self.layout.addLayout(result_layout)

        result_label = QLabel('', self)
        result_label.setWordWrap(True)
        result_label.setFixedWidth(280)
        result_label.setStyleSheet("border: 1px solid #a9a9a9; background-color: white; padding: 5px;")
        result_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        result_layout.addWidget(result_label)

        copy_button = QPushButton('Copy', self)
        copy_button.clicked.connect(lambda: self.copy_result(result_label))
        result_layout.addWidget(copy_button)

        if hormone_name.lower() == 'estradiol':
            self.estradiol_result_label = result_label
        elif hormone_name.lower() == 'testosterone':
            self.testosterone_result_label = result_label
        elif hormone_name.lower() == 'prolactin':
            self.prolactin_result_label = result_label
        elif hormone_name.lower() == 'progesterone':
            self.progesterone_result_label = result_label

        # Add recommended levels section
        recommended_levels_label = QLabel(f"Recommended Levels ({units[to_index]}):", self)
        self.layout.addWidget(recommended_levels_label)

        hormone_level_widget = HormoneLevelWidget(min_value, max_value, self)
        hormone_level_widget.setFixedWidth(350)
        self.layout.addWidget(hormone_level_widget)
        hormone_button.clicked.connect(
            lambda: self.convert_and_update_dot(
                hormone_name.lower(),
                hormone_input.text(),
                from_combo.currentText(),
                to_combo.currentText(),
                min_value,
                max_value,
                hormone_level_widget
            )
        )
    
    def convert_and_update_dot(self, hormone, value, from_unit, to_unit, min_value, max_value, widget):
        converted_value = None
        if hasattr(self, 'converted_value_label'):
            if not sip.isdeleted(self.converted_value_label):
                self.converted_value_label.deleteLater()
            self.converted_value_label = None
        try:
            value = float(value)
            converted_value = self.CONVERSIONS[hormone][from_unit][to_unit](value)
        except ValueError:
            pass

        if converted_value is not None:
            message = f'{value:.4f} {from_unit} = {converted_value:.4f} {to_unit}'
            if hormone == 'estradiol':
                self.estradiol_result_label.setText(message)
            elif hormone == 'testosterone':
                self.testosterone_result_label.setText(message)
            elif hormone == 'prolactin':
                self.prolactin_result_label.setText(message)
            elif hormone == 'progesterone':
                self.progesterone_result_label.setText(message)

            # Convert the value to the preferred unit before updating the graph
            preferred_unit = list(self.CONVERSIONS[hormone].keys())[0]
            if to_unit != preferred_unit:
                converted_value = self.CONVERSIONS[hormone][to_unit][preferred_unit](converted_value)

            in_range = min_value <= converted_value <= max_value
            widget.set_red_dot_position(converted_value, in_range)

    def get_position(self, min_value, max_value, value, total_width):
        if value < min_value:
            position = -5
        elif value > max_value:
            position = total_width - 15
        else:
            position = ((value - min_value) / (max_value - min_value)) * total_width - 10
        return position

    def copy_result(self, result_label):
        result_text = result_label.text()
        result_text = result_text.split("=")[-1].strip()
        QApplication.clipboard().setText(result_text)
        print(result_text)

    def switch_units(self, from_combo, to_combo):
        from_index = from_combo.currentIndex()
        to_index = to_combo.currentIndex()

        from_combo.setCurrentIndex(to_index)
        to_combo.setCurrentIndex(from_index)

    def convert(self, hormone, value, from_unit, to_unit):
        if from_unit == to_unit:
            message = "You can't convert from the same unit to the same unit."
            if hormone == 'estradiol':
                self.estradiol_result_label.setText(message)
            elif hormone == 'testosterone':
                self.testosterone_result_label.setText(message)
            elif hormone == 'prolactin':
                self.prolactin_result_label.setText(message)
            elif hormone == 'progesterone':
                self.progesterone_result_label.setText(message)
            return

        try:
            value = float(value)
        except ValueError:
            return

        result = self.CONVERSIONS[hormone][from_unit][to_unit](value)
        if isinstance(result, int):
            result_str = str(result)
        else:
            result_str = '{:.4f}'.format(result).rstrip('0').rstrip('.')
        message = f'{value:.4g} {from_unit} = {result_str} {to_unit}'

        if hormone == 'estradiol':
            self.estradiol_result_label.setText(message)
        elif hormone == 'testosterone':
            self.testosterone_result_label.setText(message)
        elif hormone == 'prolactin':
            self.prolactin_result_label.setText(message)
        elif hormone == 'progesterone':
            self.progesterone_result_label.setText(message)
        
    def add_recommended_levels(self, hormone_name, unit, min_value, max_value):
        recommended_levels_layout = QHBoxLayout()
        self.layout.addLayout(recommended_levels_layout)

        hormone_label = QLabel(hormone_name, self)
        recommended_levels_layout.addWidget(hormone_label)

        min_label = QLabel(f"{min_value} {unit}", self)
        recommended_levels_layout.addWidget(min_label)

        max_label = QLabel(f"{max_value} {unit}", self)
        recommended_levels_layout.addWidget(max_label)

class HormoneLevelWidget(QWidget):
    def __init__(self, min_value, max_value, parent=None):
        super().__init__(parent)
        self.min_value = min_value
        self.max_value = max_value
        self.red_dot_x = -10
        self.in_range = False
        self.setFixedSize(280, 70)

        self.previous_converted_value_label = None

        # Add labels for "too high" and "too low"
        self.too_high_label = QLabel("Too high", self)
        self.too_high_label.setStyleSheet("color: red;")
        self.too_high_label.hide()
        self.too_low_label = QLabel("Too low", self)
        self.too_low_label.setStyleSheet("color: red;")
        self.too_low_label.hide()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw line
        painter.setPen(QPen(Qt.black, 1))
        painter.drawLine(0, int(self.height() / 2), self.width(), int(self.height() / 2))

        # Draw min and max value labels
        painter.setPen(Qt.black)
        painter.drawText(3, int(self.height() / 2 - 3), f"{self.min_value}")
        painter.drawText(QPointF(self.width() - 30, self.height() / 2 - 3), f"{self.max_value}")

        # Draw red dot
        if self.in_range:  # Change color to green when in range
            painter.setBrush(Qt.green)
            painter.setPen(QPen(Qt.green, 5))
        else:
            painter.setBrush(Qt.red)
            painter.setPen(QPen(Qt.red, 5))

        if self.red_dot_x < 0:
            self.red_dot_x = -10
            painter.drawPoint(int(self.red_dot_x), int(self.height() / 2))
            painter.drawLine(int(self.red_dot_x), int(self.height() / 2), 0, int(self.height() / 2))
        elif self.red_dot_x > self.width():
            self.red_dot_x = self.width() - 10
            painter.drawPoint(int(self.red_dot_x), int(self.height() / 2))
            painter.drawLine(int(self.red_dot_x), int(self.height() / 2), self.width(), int(self.height() / 2))
        else:
            painter.drawPoint(int(self.red_dot_x), int(self.height() / 2))

        self.update()

    def set_red_dot_position(self, value, in_range):
        self.in_range = in_range
        if self.min_value <= value <= self.max_value:
            # Delete the previous label if it exists
            if self.previous_converted_value_label is not None:
                self.previous_converted_value_label.deleteLater()
            percentage = (value - self.min_value) / (self.max_value - self.min_value)
            self.red_dot_x = self.width() * percentage
            self.too_high_label.hide()
            self.too_low_label.hide()

            # Set dot color to green
            self.dot_color = Qt.green

            # Show converted value below the black line
            self.converted_value_label = QLabel(f"{value:.2f}", self)
            self.converted_value_label.move(int(self.red_dot_x), int(self.height() / 2 + 10))
            self.converted_value_label.show()

            self.previous_converted_value_label = self.converted_value_label

        elif value > self.max_value:
            self.red_dot_x = self.width() - 10
            self.too_high_label.move(305, int(self.height() / 2 + 5))
            self.too_high_label.show()
            self.too_low_label.hide()

            # Set dot color to red
            self.dot_color = Qt.red

            # Hide converted value label if exists
            if hasattr(self, 'converted_value_label'):
                self.converted_value_label.hide()

        elif value < self.min_value:
            self.red_dot_x = -10
            self.too_low_label.move(3, int(self.height() / 2 + 5))
            self.too_low_label.show()
            self.too_high_label.hide()

            # Set dot color to red
            self.dot_color = Qt.red

            # Hide converted value label if exists
            if hasattr(self, 'converted_value_label'):
                self.converted_value_label.hide()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    converter = Converter()
    sys.exit(app.exec_())
