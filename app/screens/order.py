from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QFrame, QComboBox, QTextEdit, QScrollArea
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap
import config
import database
from datetime import datetime
from .base_page import BasePage
from custom_ui import set_field_error, clear_field_error, get_date_validator, get_time_validator
from datetime import timedelta

class OrderPage(BasePage):

    def __init__(self, main_window):
        super().__init__(main_window, 'order_page')
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        top_bar = QHBoxLayout()
        back_btn = QPushButton('←')
        back_btn.setObjectName('big_back_btn')
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(lambda: self.main_window.switch_to('welcome'))
        logo_label = QLabel()
        pixmap = QPixmap(config.DOG_IMAGE)
        if not pixmap.isNull():
            logo_label.setPixmap(pixmap.scaled(35, 35, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        title = QLabel('Оформление заказа')
        title.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        title.setStyleSheet('color: white;')
        self.history_btn = QPushButton('📋')
        self.history_btn.setFixedSize(35, 35)
        self.history_btn.setStyleSheet('background-color: white; color: black; border-radius: 5px; font-size: 16px;')
        self.history_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.history_btn.clicked.connect(lambda: self.main_window.switch_to('my_orders'))
        top_bar.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignTop)
        top_bar.addStretch()
        top_bar.addWidget(logo_label)
        top_bar.addWidget(title)
        top_bar.addStretch()
        top_bar.addWidget(self.history_btn, alignment=Qt.AlignmentFlag.AlignTop)
        scroll_content = QWidget()
        scroll_content.setObjectName('scroll_content')
        scroll_content.setStyleSheet('#scroll_content { background: transparent; }')
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 10, 0, 0)
        form_container = QFrame()
        form_container.setObjectName('form_container')
        form_container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        form_layout = QVBoxLayout(form_container)
        form_layout.setSpacing(12)
        form_layout.setContentsMargins(20, 20, 20, 20)
        lbl_dog = QLabel('Выбор собаки')
        lbl_dog.setProperty('class', 'field_label')
        self.dog_combo = QComboBox()
        self.dog_combo.addItem('Выберите собаку...', 0)
        self.dog_combo.activated.connect(self.check_new_dog)
        self.dog_combo.currentIndexChanged.connect(lambda: clear_field_error(self.dog_combo))
        lbl_service = QLabel('Выбор услуги')
        lbl_service.setProperty('class', 'field_label')
        self.service_combo = QComboBox()
        self.service_combo.addItems(['Выберите услугу...', 'Обычный выгул (30 минут)', 'Активный выгул (1 час)'])
        self.service_combo.currentIndexChanged.connect(lambda: clear_field_error(self.service_combo))
        lbl_datetime = QLabel('Дата и время начала')
        lbl_datetime.setProperty('class', 'field_label')
        datetime_layout = QHBoxLayout()
        self.date_input = QLineEdit()
        self.date_input.setPlaceholderText('ДД.ММ.ГГГГ')
        self.date_input.setValidator(get_date_validator())
        self.date_input.textChanged.connect(lambda: clear_field_error(self.date_input, 'ДД.ММ.ГГГГ'))
        self.time_input = QLineEdit()
        self.time_input.setPlaceholderText('ЧЧ:ММ')
        self.time_input.setValidator(get_time_validator())
        self.time_input.textChanged.connect(lambda: clear_field_error(self.time_input, 'ЧЧ:ММ'))
        datetime_layout.addWidget(self.date_input)
        datetime_layout.addWidget(self.time_input)
        lbl_address = QLabel('Адрес проживания (откуда забрать)')
        lbl_address.setProperty('class', 'field_label')
        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText('Например: ул. Лесная, д. 5')
        self.address_input.textChanged.connect(lambda: clear_field_error(self.address_input, 'Адрес'))
        lbl_comment = QLabel('Комментарий (необязательно)')
        lbl_comment.setProperty('class', 'field_label')
        self.comment_input = QTextEdit()
        self.comment_input.setPlaceholderText('Особенности передачи ключей и т.д.')
        self.comment_input.setFixedHeight(80)
        submit_btn = QPushButton('Оформить и перейти к статусу')
        submit_btn.clicked.connect(self.validate_and_submit)
        form_layout.addWidget(lbl_dog)
        form_layout.addWidget(self.dog_combo)
        form_layout.addSpacing(5)
        form_layout.addWidget(lbl_service)
        form_layout.addWidget(self.service_combo)
        form_layout.addSpacing(5)
        form_layout.addWidget(lbl_datetime)
        form_layout.addLayout(datetime_layout)
        form_layout.addSpacing(5)
        form_layout.addWidget(lbl_address)
        form_layout.addWidget(self.address_input)
        form_layout.addSpacing(5)
        form_layout.addWidget(lbl_comment)
        form_layout.addWidget(self.comment_input)
        form_layout.addSpacing(10)
        form_layout.addWidget(submit_btn)
        scroll_layout.addWidget(form_container)
        scroll_layout.addStretch()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.viewport().setAutoFillBackground(False)
        scroll.setStyleSheet('QScrollArea { border: none; background: transparent; }')
        scroll.setWidget(scroll_content)
        main_layout.addLayout(top_bar)
        main_layout.addWidget(scroll)

    def check_new_dog(self, index):
        if self.dog_combo.currentData() == -1:
            self.dog_combo.setCurrentIndex(0)
            self.main_window.switch_to('new_dog')
        if self.dog_combo.itemText(index) == '+ добавить новую':
            self.dog_combo.setCurrentIndex(0)
            self.main_window.switch_to('new_dog')

    def set_selected_walker(self, walker_id, name, experience):
        self.selected_walker_id = walker_id
        self.w_name.setText(f'<b>{name}</b>')
        self.w_exp.setText(experience)
        self.w_name.setStyleSheet('color: black;')

    def update_data(self):
        self.dog_combo.clear()
        self.dog_combo.addItem('Выберите собаку...', 0)
        if self.main_window.current_user:
            owner_id = self.main_window.current_user['id']
            dogs = database.get_user_dogs(owner_id)
            for d in dogs:
                self.dog_combo.addItem(f"{d['name']} ({d['breed_name']})", d['id'])
        self.dog_combo.addItem('+ добавить новую', -1)

    def validate_and_submit(self):
        if hasattr(self.main_window, 'is_debug_mode') and self.main_window.is_debug_mode:
            self.main_window.switch_to('walk')
            return
        has_error = False
        dog_id = self.dog_combo.currentData()
        if dog_id == 0 or dog_id == -1:
            set_field_error(self.dog_combo)
            has_error = True
        if self.service_combo.currentIndex() == 0:
            set_field_error(self.service_combo)
            has_error = True
        date_text = self.date_input.text()
        time_text = self.time_input.text()
        db_start_datetime = None
        try:
            dt_string = f'{date_text} {time_text}'
            db_start_datetime = datetime.strptime(dt_string, '%d.%m.%Y %H:%M')
        except ValueError:
            set_field_error(self.date_input, 'формат')
            set_field_error(self.time_input, 'формат')
            has_error = True
        address = self.address_input.text().strip()
        if not address:
            set_field_error(self.address_input, 'адрес')
            has_error = True
        if not has_error and self.main_window.current_user:
            owner_id = self.main_window.current_user['id']
            comment = self.comment_input.toPlainText().strip()
            duration_mins = 60 if '1 час' in self.service_combo.currentText() else 30
            db_end_datetime = db_start_datetime + timedelta(minutes=duration_mins)
            order_id = database.create_order(owner_id=owner_id, dog_id=dog_id, start_at=db_start_datetime, end_at=db_end_datetime, address=address, comment=comment)
            if order_id:
                print(f'Заказ #{order_id} отправлен в пул!')
                self.main_window.active_client_order_id = order_id
                self.address_input.clear()
                self.comment_input.clear()
                self.date_input.clear()
                self.time_input.clear()
                self.main_window.switch_to('walk')