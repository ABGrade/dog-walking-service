from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QFrame, QComboBox, QTextEdit, QScrollArea, QFileDialog
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap
from .base_page import BasePage
from custom_ui import set_field_error, clear_field_error, get_date_validator
from datetime import datetime
import config
import database

class DogRegistrationPage(BasePage):

    def __init__(self, main_window):
        super().__init__(main_window, 'dog_reg_page')
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        top_bar = QHBoxLayout()
        back_btn = QPushButton('←')
        back_btn.setObjectName('big_back_btn')
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(lambda: self.main_window.switch_to('order'))
        logo_label = QLabel()
        pixmap = QPixmap(config.DOG_IMAGE)
        if not pixmap.isNull():
            logo_label.setPixmap(pixmap.scaled(35, 35, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        title = QLabel('Новая собака')
        title.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        title.setStyleSheet('color: white;')
        top_bar.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignTop)
        top_bar.addStretch()
        top_bar.addWidget(logo_label)
        top_bar.addWidget(title)
        top_bar.addStretch()
        scroll_content = QWidget()
        scroll_content.setObjectName('scroll_content')
        scroll_content.setStyleSheet('#scroll_content { background: transparent; }')
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 10, 0, 0)
        form_container = QFrame()
        form_container.setObjectName('form_container')
        form_container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        form_layout = QVBoxLayout(form_container)
        form_layout.setSpacing(10)
        form_layout.setContentsMargins(25, 25, 25, 25)
        self.photo_path = None
        self.photo_preview = QLabel()
        self.photo_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.photo_preview.hide()
        self.photo_btn = QPushButton('📷 Загрузить фото питомца')
        self.photo_btn.setObjectName('outline_btn')
        self.photo_btn.setFixedHeight(50)
        self.photo_btn.clicked.connect(self.upload_photo)
        self.d_name = QLineEdit()
        self.d_name.setPlaceholderText('Кличка')
        self.d_name.textChanged.connect(lambda: clear_field_error(self.d_name, 'Кличка'))
        self.d_breed = QComboBox()
        self.d_breed.addItem('Выберите породу...', 0)
        self.d_breed.currentIndexChanged.connect(lambda: clear_field_error(self.d_breed))
        self.d_sex = QComboBox()
        self.d_sex.addItems(['Укажите пол...', 'М', 'Ж'])
        self.d_sex.currentIndexChanged.connect(lambda: clear_field_error(self.d_sex))
        self.d_birth = QLineEdit()
        self.d_birth.setPlaceholderText('Дата рождения (ДД.ММ.ГГГГ)')
        self.d_birth.setValidator(get_date_validator())
        self.d_birth.textChanged.connect(lambda: clear_field_error(self.d_birth, 'Дата рождения (ДД.ММ.ГГГГ)'))
        self.d_behavior = QTextEdit()
        self.d_behavior.setPlaceholderText('Особенности поведения (необязательно)')
        self.d_behavior.setFixedHeight(60)
        self.d_health = QTextEdit()
        self.d_health.setPlaceholderText('Ограничения по здоровью (необязательно)')
        self.d_health.setFixedHeight(60)
        submit_btn = QPushButton('Сохранить собаку')
        submit_btn.clicked.connect(self.validate_and_save)
        form_layout.addWidget(self.photo_preview)
        form_layout.addWidget(self.photo_btn)
        form_layout.addSpacing(10)
        form_layout.addWidget(self.d_name)
        form_layout.addWidget(self.d_breed)
        form_layout.addWidget(self.d_sex)
        form_layout.addWidget(self.d_birth)
        form_layout.addWidget(self.d_behavior)
        form_layout.addWidget(self.d_health)
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

    def upload_photo(self):
        file_name, _ = QFileDialog.getOpenFileName(self, 'Выберите фото', '', 'Images (*.png *.jpg *.jpeg)')
        if file_name:
            self.photo_path = file_name
            pixmap = QPixmap(file_name)
            scaled_pixmap = pixmap.scaled(250, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.photo_preview.setPixmap(scaled_pixmap)
            self.photo_preview.show()
            self.photo_btn.setText('🔄 Изменить фото')
            self.photo_btn.setStyleSheet('color: #1976D2;')

    def update_data(self):
        self.d_breed.clear()
        self.d_breed.addItem('Выберите породу...', 0)
        breeds = database.get_breeds()
        for b in breeds:
            self.d_breed.addItem(b['name'], b['id'])

    def validate_and_save(self):
        if hasattr(self.main_window, 'is_debug_mode') and self.main_window.is_debug_mode:
            self.main_window.switch_to('order')
            return
        has_error = False
        name = self.d_name.text().strip()
        breed_id = self.d_breed.currentData()
        sex = self.d_sex.currentText()
        birth = self.d_birth.text().strip()
        behavior = self.d_behavior.toPlainText().strip()
        health = self.d_health.toPlainText().strip()
        if not name:
            set_field_error(self.d_name, 'имя')
            has_error = True
        if breed_id == 0:
            set_field_error(self.d_breed)
            has_error = True
        if self.d_sex.currentIndex() == 0:
            set_field_error(self.d_sex)
            has_error = True
        if len(birth.replace('.', '').strip()) < 8:
            set_field_error(self.d_birth, 'дата')
            has_error = True
        if not has_error:
            try:
                db_birth_date = datetime.strptime(birth, '%d.%m.%Y').strftime('%Y-%m-%d')
            except ValueError:
                set_field_error(self.d_birth, 'формат')
                return
            owner_id = self.main_window.current_user['id']
            success = database.add_dog(owner_id, name, breed_id, sex, db_birth_date, behavior, health)
            if success:
                self.photo_preview.hide()
                self.photo_btn.setText('📷 Загрузить фото питомца')
                self.d_name.clear()
                self.d_birth.clear()
                self.main_window.switch_to('order')