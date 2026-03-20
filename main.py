import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy
from PySide6.QtCore import Qt


class BotPanel(QFrame):
    def __init__(self, text: str = "untitled"):
        super().__init__()
        self.setFrameShape(QFrame.Box)
        self.setLineWidth(1)
        self.setStyleSheet("background-color: #f0f0f0; border: 1px solid #999;")
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout(self)
        layout.addWidget(label)
        layout.addStretch(1)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ProjectTimeSaver - AI Bot UI")
        self.resize(1000, 700)

        central = QWidget()
        central.setStyleSheet("background-color: #b0b0b0;")

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)

        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(20, 20, 20, 20)
        left_layout.setSpacing(15)

        left_layout.addWidget(BotPanel("untitled"))
        left_layout.addWidget(BotPanel("untitled"))
        left_layout.addWidget(BotPanel("untitled"))
        left_layout.addStretch(1)

        left_container.setFixedWidth(320)

        right_spacer = QWidget()
        right_spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        main_layout.addWidget(left_container)
        main_layout.addWidget(right_spacer)

        self.setCentralWidget(central)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
