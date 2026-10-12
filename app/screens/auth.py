from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QFrame, QCheckBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap
import config
from .base_page import BasePage
from custom_ui import PasswordLineEdit, set_field_error, clear_field_error
import database

class AuthPage(BasePage):

    def __init__(self, main_window, title_text, is_login=False):
        super().__init__(main_window, 'auth_page')
        self.is_login = is_login
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 30, 20, 30)
        back_btn = QPushButton('← Назад')
        back_btn.setObjectName('back_btn')
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(lambda: self.main_window.switch_to('welcome'))
        header_layout = QVBoxLayout()
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label = QLabel()
        pixmap = QPixmap(config.DOG_IMAGE)
        if not pixmap.isNull():
            logo_label.setPixmap(pixmap.scaled(60, 60, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        app_title = QLabel('Сервис Выгула Собак')
        app_title.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        app_title.setStyleSheet('color: white;')
        app_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(logo_label)
        header_layout.addWidget(app_title)
        form_container = QFrame()
        form_container.setObjectName('form_container')
        form_container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.form_layout = QVBoxLayout(form_container)
        self.form_layout.setSpacing(15)
        self.form_layout.setContentsMargins(25, 25, 25, 25)
        form_title = QLabel(title_text)
        form_title.setFont(QFont('Arial', 18, QFont.Weight.Bold))
        form_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.form_layout.addWidget(form_title)
        self.form_layout.addSpacing(10)
        self.build_form()
        main_layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        main_layout.addLayout(header_layout)
        main_layout.addSpacing(15)
        main_layout.addWidget(form_container)
        main_layout.addStretch()

    def build_form(self):
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText('E-mail')
        self.email_input.textChanged.connect(lambda: clear_field_error(self.email_input, 'E-mail'))
        self.password_input = PasswordLineEdit()
        self.password_input.textChanged.connect(lambda: clear_field_error(self.password_input, 'Пароль'))
        if not self.is_login:
            self.name_input = QLineEdit()
            self.name_input.setPlaceholderText('Ваше имя')
            self.name_input.textChanged.connect(lambda: clear_field_error(self.name_input, 'Ваше имя'))
            self.phone_input = QLineEdit()
            self.phone_input.setPlaceholderText('+7 (___) ___-__-__')
            self.phone_input.textChanged.connect(lambda: clear_field_error(self.phone_input, '+7 (___) ___-__-__'))
            self.form_layout.addWidget(self.name_input)
            self.form_layout.addWidget(self.phone_input)
            self.walker_checkbox = QCheckBox('Я хочу стать выгульщиком')
            self.walker_checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
            self.form_layout.addWidget(self.walker_checkbox)
        self.form_layout.addWidget(self.email_input)
        self.form_layout.addWidget(self.password_input)
        submit_btn = QPushButton('Войти' if self.is_login else 'Зарегистрироваться')
        submit_btn.clicked.connect(self.validate_and_submit)
        self.form_layout.addSpacing(10)
        self.form_layout.addWidget(submit_btn)
        link_text = '<a href="#nav" style="color: #1976D2; text-decoration: none;">Нет аккаунта? Регистрация</a>' if self.is_login else '<a href="#nav" style="color: #1976D2; text-decoration: none;">Уже есть аккаунт? Войти</a>'
        link = QLabel(link_text)
        link.setAlignment(Qt.AlignmentFlag.AlignCenter)
        link.linkActivated.connect(lambda: self.main_window.switch_to('register' if self.is_login else 'login'))
        self.form_layout.addWidget(link)

    def validate_and_submit(self):
        if hasattr(self.main_window, 'is_debug_mode') and self.main_window.is_debug_mode:
            self.main_window.current_user = {'id': 1, 'role_id': 3, 'role_name': 'администратор'}
            if not self.is_login and self.walker_checkbox.isChecked():
                self.main_window.switch_to('orders_list')
            else:
                self.main_window.switch_to('order')
            return
        has_error = False
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()
        if not email or '@' not in email:
            set_field_error(self.email_input, 'E-mail')
            has_error = True
        if not password:
            set_field_error(self.password_input, 'Пароль')
            has_error = True
        if not self.is_login:
            name = self.name_input.text().strip()
            phone = self.phone_input.text().strip()
            if not name:
                set_field_error(self.name_input, 'Имя')
                has_error = True
            if not phone:
                set_field_error(self.phone_input, 'Телефон')
                has_error = True
        if has_error:
            return
        if self.is_login:
            user = database.authenticate_user(email, password)
            if user:
                self.main_window.current_user = user
                print(f"Успешный вход: {user['first_name']} (Роль: {user['role_name']})")
                if user['role_id'] == 3:
                    print(f"Админ вошел: {user['first_name']}. Включаем Debug-переходы.")
                    self.main_window.switch_to('welcome')
                    return
                if user['role_id'] == 2:
                    self.main_window.switch_to('orders_list')
                else:
                    self.main_window.switch_to('order')
            else:
                self.email_input.setProperty('error', True)
                self.email_input.style().unpolish(self.email_input)
                self.email_input.style().polish(self.email_input)
                set_field_error(self.password_input, 'Неверный логин или пароль')
        else:
            is_walker = self.walker_checkbox.isChecked()
            user = database.register_user(name, phone, email, password, is_walker)
            if user == 'EMAIL_EXISTS':
                set_field_error(self.email_input, 'Этот Email уже занят')
            elif user:
                self.main_window.current_user = user
                print(f"Успешная регистрация: {user['first_name']} (Роль: {user['role_name']})")
                if is_walker:
                    self.main_window.switch_to('orders_list')
                else:
                    self.main_window.switch_to('order')
            else:
                set_field_error(self.email_input, 'Внутренняя ошибка БД')