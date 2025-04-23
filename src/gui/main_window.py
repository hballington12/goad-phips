from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLineEdit, QPushButton
import sys
from core.subprocess_runner import SubprocessRunner

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Light Scattering App")
        self.setGeometry(100, 100, 400, 200)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.command_input = QLineEdit(self)
        self.command_input.setPlaceholderText("Enter terminal command")
        self.layout.addWidget(self.command_input)

        self.run_button = QPushButton("Run Command", self)
        self.run_button.clicked.connect(self.run_command)
        self.layout.addWidget(self.run_button)

        self.subprocess_runner = SubprocessRunner()

    def run_command(self):
        command = self.command_input.text()
        output = self.subprocess_runner.run_command(command)
        print(output)  # For now, we just print the output to the console

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())