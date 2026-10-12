import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QPushButton, QFrame, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
import config
from ui_fonts import configure_fonts
from screens.welcome import WelcomePage
from screens.auth import AuthPage
from screens.order import OrderPage
from screens.new_dog import DogRegistrationPage
from screens.walk import WalkPage
from screens.orders_list import OrdersListPage
from screens.walker_walk import WalkerWalkPage
from screens.payment_confirm import PaymentConfirmPage
from screens.my_orders import MyOrdersPage

class DogWalkingApp(QMainWindow):

    def __init__(self):
        super().__init__()
        configure_fonts(QApplication.instance())
        self.setWindowTitle('Сервис Выгула Собак')
        self.win_width = 550
        self.win_height = 900
        self.setFixedSize(self.win_width, self.win_height)
        self.setStyleSheet(config.GLOBAL_STYLES)
        self.is_debug_mode = False
        self.current_user = None
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        self.pages = {'welcome': WelcomePage(self), 'login': AuthPage(self, 'Вход', is_login=True), 'register': AuthPage(self, 'Регистрация', is_login=False), 'order': OrderPage(self), 'new_dog': DogRegistrationPage(self), 'walk': WalkPage(self), 'orders_list': OrdersListPage(self), 'walker_walk': WalkerWalkPage(self), 'payment_confirm': PaymentConfirmPage(self), 'my_orders': MyOrdersPage(self)}
        for page in self.pages.values():
            self.stacked_widget.addWidget(page)
        self.debug_menu = QFrame(self)
        self.debug_menu.setGeometry(self.win_width - 220, self.win_height - 470, 200, 400)
        self.debug_menu.setStyleSheet('QFrame { background-color: rgba(0, 0, 0, 0.85); border-radius: 10px; }')
        debug_layout = QVBoxLayout(self.debug_menu)
        debug_layout.setContentsMargins(10, 10, 10, 10)
        lbl = QLabel('Debug: Переход')
        lbl.setStyleSheet('color: white; font-weight: bold; background: transparent;')
        debug_layout.addWidget(lbl)
        for page_name in self.pages.keys():
            btn = QPushButton(page_name)
            btn.setStyleSheet('background-color: #444; color: white; padding: 5px; font-size: 12px; border: none; border-radius: 4px;')
            btn.clicked.connect(lambda checked, p=page_name: self.switch_to(p))
            debug_layout.addWidget(btn)
        exit_debug_btn = QPushButton('Выход')
        exit_debug_btn.setStyleSheet('background-color: #D32F2F; color: white; padding: 5px; font-size: 12px; border: none; border-radius: 4px; margin-top: 10px;')
        exit_debug_btn.clicked.connect(self.exit_debug_mode)
        debug_layout.addWidget(exit_debug_btn)
        self.debug_menu.hide()
        self.debug_btn = QPushButton(self)
        self.debug_btn.hide()
        self.debug_btn.setGeometry(self.win_width - 55, self.win_height - 55, 40, 40)
        self.debug_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_debug_btn_style()
        self.debug_btn.clicked.connect(self.toggle_debug_menu)
        self.switch_to('welcome')

    def update_debug_btn_style(self):
        color = 'red' if self.is_debug_mode else 'orange'
        self.debug_btn.setStyleSheet(f"\n            QPushButton {{\n                background-color: {color};\n                border-radius: 20px;\n                image: url('{config.AUTOFILL_IMAGE}');\n                padding: 10px; \n            }}\n        ")

    def toggle_debug_menu(self):
        if not self.is_debug_mode:
            self.is_debug_mode = True
            self.update_debug_btn_style()
        if self.debug_menu.isHidden():
            self.debug_menu.show()
            self.debug_menu.raise_()
            self.debug_btn.raise_()
        else:
            self.debug_menu.hide()

    def exit_debug_mode(self):
        self.is_debug_mode = False
        self.update_debug_btn_style()
        self.debug_menu.hide()
        self.switch_to('welcome')

    def switch_to(self, page_name):
        if page_name in self.pages:
            if self.current_user and self.current_user.get('role_id') == 3:
                self.debug_btn.show()
            else:
                self.debug_btn.hide()
                self.debug_menu.hide()
            page = self.pages[page_name]
            if hasattr(page, 'update_data'):
                page.update_data()
            self.stacked_widget.setCurrentWidget(page)
            if not self.debug_btn.isHidden():
                self.debug_menu.raise_()
                self.debug_btn.raise_()
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DogWalkingApp()
    window.show()
    sys.exit(app.exec())
