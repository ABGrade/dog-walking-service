from PyQt6.QtWidgets import QVBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap
import config
from .base_page import BasePage

class WelcomePage(BasePage):

    def __init__(self, main_window):
        super().__init__(main_window, 'welcome_page')
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        logo_label = QLabel()
        pixmap = QPixmap(config.DOG_IMAGE)
        if not pixmap.isNull():
            logo_label.setPixmap(pixmap.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title = QLabel('Сервис Выгула Собак')
        title.setFont(QFont('Arial', 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet('color: white;')
        login_btn = QPushButton('Войти')
        login_btn.clicked.connect(lambda: self.main_window.switch_to('login'))
        register_btn = QPushButton('Зарегистрироваться')
        register_btn.setObjectName('outline_btn')
        register_btn.clicked.connect(lambda: self.main_window.switch_to('register'))
        layout.addStretch()
        layout.addWidget(logo_label)
        layout.addWidget(title)
        layout.addSpacing(40)
        layout.addWidget(login_btn)
        layout.addWidget(register_btn)
        layout.addStretch()