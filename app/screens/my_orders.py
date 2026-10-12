from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame, QScrollArea
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap
from .base_page import BasePage
import config
import database

class MyOrdersPage(BasePage):

    def __init__(self, main_window):
        super().__init__(main_window, 'my_orders_page')
        self.orders = []
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        top_bar = QHBoxLayout()
        back_btn = QPushButton('←')
        back_btn.setObjectName('big_back_btn')
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.go_back)
        logo_label = QLabel()
        pixmap = QPixmap(config.DOG_IMAGE)
        if not pixmap.isNull():
            logo_label.setPixmap(pixmap.scaled(35, 35, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        title = QLabel('Мои заказы')
        title.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        title.setStyleSheet('color: white;')
        self.refresh_btn = QPushButton('🔄')
        self.refresh_btn.setFixedSize(35, 35)
        self.refresh_btn.setStyleSheet('background-color: white; color: black; border-radius: 5px; font-size: 16px;')
        self.refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_btn.clicked.connect(self.fetch_and_render)
        top_bar.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignTop)
        top_bar.addStretch()
        top_bar.addWidget(logo_label)
        top_bar.addWidget(title)
        top_bar.addStretch()
        top_bar.addWidget(self.refresh_btn, alignment=Qt.AlignmentFlag.AlignTop)
        scroll_content = QWidget()
        scroll_content.setObjectName('scroll_content')
        scroll_content.setStyleSheet('#scroll_content { background: transparent; }')
        self.scroll_layout = QVBoxLayout(scroll_content)
        self.scroll_layout.setSpacing(15)
        self.scroll_layout.setContentsMargins(0, 10, 0, 0)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.viewport().setAutoFillBackground(False)
        self.scroll.setStyleSheet('QScrollArea { border: none; background: transparent; }')
        self.scroll.setWidget(scroll_content)
        main_layout.addLayout(top_bar)
        main_layout.addSpacing(10)
        main_layout.addWidget(self.scroll)

    def go_back(self):
        if self.main_window.current_user:
            role_id = self.main_window.current_user.get('role_id')
            if role_id == 1:
                self.main_window.switch_to('order')
            elif role_id == 2:
                self.main_window.switch_to('orders_list')
            else:
                self.main_window.switch_to('welcome')
        else:
            self.main_window.switch_to('welcome')

    def update_data(self):
        self.fetch_and_render()

    def fetch_and_render(self):
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if not self.main_window.current_user:
            return
        user_id = self.main_window.current_user['id']
        role_id = self.main_window.current_user['role_id']
        if role_id == 1:
            self.orders = database.get_client_orders(user_id)
        elif role_id == 2:
            self.orders = database.get_walker_orders(user_id)
        else:
            self.orders = []
        if not self.orders:
            empty_lbl = QLabel('У вас пока нет заказов 🐕')
            empty_lbl.setStyleSheet('color: white; font-size: 16px; margin-top: 50px;')
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.scroll_layout.addWidget(empty_lbl)
        else:
            for order in self.orders:
                card = self.create_order_card(order, role_id)
                self.scroll_layout.addWidget(card)

    def create_order_card(self, order, role_id):
        card = QFrame()
        card.setStyleSheet('QFrame { background-color: rgba(248, 249, 250, 0.95); border-radius: 12px; }')
        layout = QHBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)
        avatar = QLabel()
        avatar.setFixedSize(60, 60)
        avatar.setStyleSheet('background-color: #E0E0E0; border-radius: 8px;')
        pixmap = QPixmap(config.DOG_IMAGE)
        if not pixmap.isNull():
            avatar.setPixmap(pixmap.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        title_lbl = QLabel(f"<b>Заказ №{order['id']}</b> | {order['dog_name']} ({order['breed_name']})")
        title_lbl.setStyleSheet('color: black; font-size: 15px;')
        address_lbl = QLabel(f"📍 {order['walk_address']}")
        address_lbl.setStyleSheet('color: #555; font-size: 13px;')
        date_lbl = QLabel(f"📅 {order['date_str']}")
        date_lbl.setStyleSheet('color: #555; font-size: 13px;')
        status_id = order['status_id']
        is_paid = order['pay_status'] == 'оплачен'
        status_color = '#333'
        status_text = ''
        if status_id == 1:
            if is_paid:
                status_text = 'Оплачен, поиск выгульщика'
                status_color = '#F57C00'
            else:
                status_text = 'Создан, ожидает оплаты'
                status_color = '#D32F2F'
        elif status_id == 2:
            status_text = 'Выгульщик в пути / Прогулка'
            status_color = '#1976D2'
        elif status_id == 3:
            status_text = 'Завершен'
            status_color = '#388E3C'
        status_lbl = QLabel(f'ℹ️ {status_text}')
        status_lbl.setStyleSheet(f'color: {status_color}; font-size: 12px; font-weight: bold;')
        info_layout.addWidget(title_lbl)
        info_layout.addWidget(address_lbl)
        info_layout.addWidget(date_lbl)
        info_layout.addWidget(status_lbl)
        btn_layout = QVBoxLayout()
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        action_btn = QPushButton()
        action_btn.setFixedSize(90, 35)
        action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if status_id in (1, 2):
            action_btn.setText('Открыть')
            action_btn.setStyleSheet('font-size: 13px; background-color: #4CAF50; color: white;')
            action_btn.clicked.connect(lambda _, o=order: self.open_active_order(o, role_id))
        else:
            action_btn.setText('Отчет')
            action_btn.setStyleSheet('font-size: 13px; background-color: #757575; color: white;')
            action_btn.clicked.connect(lambda _, o=order: self.view_report(o, role_id))
        btn_layout.addWidget(action_btn)
        layout.addWidget(avatar)
        layout.addLayout(info_layout)
        layout.addLayout(btn_layout)
        return card

    def open_active_order(self, order, role_id):
        if role_id == 1:
            self.main_window.active_client_order_id = order['id']
            self.main_window.switch_to('walk')
        elif role_id == 2:
            self.main_window.active_order = order
            self.main_window.switch_to('walker_walk')

    def view_report(self, order, role_id):
        if role_id == 1:
            self.main_window.active_client_order_id = order['id']
            self.main_window.switch_to('walk')
        elif role_id == 2:
            self.main_window.active_order = order
            self.main_window.switch_to('walker_walk')