from PyQt6.QtWidgets import QVBoxLayout, QPushButton, QLabel, QLineEdit, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap
import config
from .base_page import BasePage
from custom_ui import PasswordLineEdit, set_field_error, clear_field_error
import database

class PaymentConfirmPage(BasePage):

    def __init__(self, main_window):
        super().__init__(main_window, 'payment_confirm_page')
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 30, 20, 30)
        back_btn = QPushButton('← Отмена')
        back_btn.setObjectName('back_btn')
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(lambda: self.main_window.switch_to('walk'))
        header_layout = QVBoxLayout()
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label = QLabel()
        pixmap = QPixmap(config.DOG_IMAGE)
        if not pixmap.isNull():
            logo_label.setPixmap(pixmap.scaled(60, 60, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(logo_label)
        form_container = QFrame()
        form_container.setObjectName('form_container')
        form_container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.form_layout = QVBoxLayout(form_container)
        self.form_layout.setSpacing(15)
        self.form_layout.setContentsMargins(25, 25, 25, 25)
        form_title = QLabel('Подтверждение оплаты')
        form_title.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        form_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        descr = QLabel('Введите данные вашего аккаунта для списания средств')
        descr.setWordWrap(True)
        descr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        descr.setStyleSheet('color: #666; font-size: 13px;')
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText('E-mail')
        self.password_input = PasswordLineEdit()
        self.submit_btn = QPushButton('Подтвердить и оплатить')
        self.submit_btn.clicked.connect(self.verify_and_pay)
        self.form_layout.addWidget(form_title)
        self.form_layout.addWidget(descr)
        self.form_layout.addSpacing(10)
        self.form_layout.addWidget(self.email_input)
        self.form_layout.addWidget(self.password_input)
        self.form_layout.addSpacing(10)
        self.form_layout.addWidget(self.submit_btn)
        main_layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        main_layout.addLayout(header_layout)
        main_layout.addSpacing(15)
        main_layout.addWidget(form_container)
        main_layout.addStretch()

    def verify_and_pay(self):
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()
        curr_user = self.main_window.current_user
        if email != curr_user['email']:
            set_field_error(self.email_input, 'E-mail (нужен ваш)')
            return
        user_valid = database.authenticate_user(email, password)
        if user_valid:
            order_id = getattr(self.main_window, 'active_client_order_id', None)
            if order_id:
                self.process_db_payment(order_id)
                self.main_window.switch_to('walk')
        else:
            set_field_error(self.password_input, 'Неверный пароль')

    def process_db_payment(self, order_id):
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("UPDATE payments SET payment_status = 'оплачен', paid_at = NOW() WHERE order_id = %s", (order_id,))
            conn.commit()
            print(f'Оплата заказа #{order_id} подтверждена пользователем.')
        finally:
            cur.close()
            conn.close()

    def update_data(self):
        self.email_input.clear()
        self.password_input.clear()
        clear_field_error(self.email_input)
        clear_field_error(self.password_input)