from PyQt6.QtWidgets import QLineEdit, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt, QRegularExpression
from PyQt6.QtGui import QRegularExpressionValidator
import config

class PasswordLineEdit(QLineEdit):

    def __init__(self, placeholder='Пароль', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setPlaceholderText(placeholder)
        self.setEchoMode(QLineEdit.EchoMode.Password)
        self.setStyleSheet('QLineEdit { padding-right: 35px; }')
        self.eye_btn = QPushButton(self)
        self.eye_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.eye_btn.setFixedSize(24, 24)
        self.eye_btn.setStyleSheet(f"background: transparent; border-image: url('{config.EYE_CLOSE}');")
        self.eye_btn.setCheckable(True)
        self.eye_btn.toggled.connect(self.toggle_echo)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.addWidget(self.eye_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def toggle_echo(self, checked):
        if checked:
            self.setEchoMode(QLineEdit.EchoMode.Normal)
            self.eye_btn.setStyleSheet(f"background: transparent; border-image: url('{config.EYE_OPEN}');")
        else:
            self.setEchoMode(QLineEdit.EchoMode.Password)
            self.eye_btn.setStyleSheet(f"background: transparent; border-image: url('{config.EYE_CLOSE}');")

def set_field_error(field, error_message=''):
    field.setProperty('error', True)
    field.style().unpolish(field)
    field.style().polish(field)
    if isinstance(field, QLineEdit):
        field.clear()
        if error_message:
            field.setPlaceholderText(f'Неправильный {error_message}')

def clear_field_error(field, original_placeholder=''):
    field.setProperty('error', False)
    field.style().unpolish(field)
    field.style().polish(field)
    if isinstance(field, QLineEdit) and original_placeholder:
        field.setPlaceholderText(original_placeholder)

def get_date_validator():
    regex = QRegularExpression('^[0-9.]{0,10}$')
    return QRegularExpressionValidator(regex)

def get_time_validator():
    regex = QRegularExpression('^[0-9:]{0,5}$')
    return QRegularExpressionValidator(regex)