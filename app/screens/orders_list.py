from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame, QScrollArea, QLineEdit, QComboBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap
from .base_page import BasePage
import config
import database

class OrdersListPage(BasePage):

    def __init__(self, main_window):
        super().__init__(main_window, 'orders_list_page')
        self.all_orders = []
        self.current_index = 0
        self.chunk_size = 20
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
        title = QLabel('Биржа заказов')
        title.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        title.setStyleSheet('color: white;')
        self.my_orders_btn = QPushButton('📋')
        self.my_orders_btn.setFixedSize(35, 35)
        self.my_orders_btn.setStyleSheet('background-color: white; color: black; border-radius: 5px; font-size: 16px;')
        self.my_orders_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.my_orders_btn.clicked.connect(lambda: self.main_window.switch_to('my_orders'))
        self.refresh_btn = QPushButton('🔄')
        self.refresh_btn.setFixedSize(35, 35)
        self.refresh_btn.setStyleSheet('background-color: white; color: black; border-radius: 5px; font-size: 16px;')
        self.refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_btn.clicked.connect(self.fetch_and_render_orders)
        top_bar.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignTop)
        top_bar.addStretch()
        top_bar.addWidget(logo_label)
        top_bar.addWidget(title)
        top_bar.addStretch()
        top_bar.addWidget(self.my_orders_btn, alignment=Qt.AlignmentFlag.AlignTop)
        top_bar.addWidget(self.refresh_btn, alignment=Qt.AlignmentFlag.AlignTop)
        filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('🔍 Поиск по номеру телефона...')
        self.search_input.setStyleSheet('background-color: rgba(255, 255, 255, 0.9); border-radius: 5px; padding: 8px;')
        self.search_input.textChanged.connect(self.fetch_and_render_orders)
        self.status_filter = QComboBox()
        self.status_filter.addItems(['Все заказы', 'Оплачено', 'Не оплачено'])
        self.status_filter.setStyleSheet('background-color: rgba(255, 255, 255, 0.9); border-radius: 5px; padding: 8px;')
        self.status_filter.currentIndexChanged.connect(self.fetch_and_render_orders)
        filter_layout.addWidget(self.search_input)
        filter_layout.addWidget(self.status_filter)
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
        self.scroll.verticalScrollBar().valueChanged.connect(self.check_scroll)
        main_layout.addLayout(top_bar)
        main_layout.addLayout(filter_layout)
        main_layout.addSpacing(10)
        main_layout.addWidget(self.scroll)

    def update_data(self):
        self.fetch_and_render_orders()

    def check_scroll(self, value):
        scrollbar = self.scroll.verticalScrollBar()
        if value >= scrollbar.maximum() - 50 and self.current_index < len(self.all_orders):
            self.render_next_chunk()

    def fetch_and_render_orders(self):
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        search_query = self.search_input.text().strip()
        payment_filter = self.status_filter.currentText()
        if payment_filter == 'Все заказы':
            payment_filter = 'Все'
        self.all_orders = database.get_available_orders(search_query, payment_filter)
        self.current_index = 0
        if not self.all_orders:
            empty_lbl = QLabel('По этим фильтрам ничего не найдено 😴')
            empty_lbl.setStyleSheet('color: white; font-size: 16px; margin-top: 50px;')
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.scroll_layout.addWidget(empty_lbl)
        else:
            self.render_next_chunk()

    def render_next_chunk(self):
        end_index = min(self.current_index + self.chunk_size, len(self.all_orders))
        chunk = self.all_orders[self.current_index:end_index]
        for order in chunk:
            card = self.create_order_card(order)
            self.scroll_layout.addWidget(card)
        self.current_index = end_index

    def create_order_card(self, order_data):
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
        title_lbl = QLabel(f"<b>Заказ №{order_data['id']}</b> | {order_data['dog_name']} ({order_data['breed_name']})")
        title_lbl.setStyleSheet('color: black; font-size: 15px;')
        region_lbl = QLabel(f"📍 {order_data['walk_address']}")
        region_lbl.setStyleSheet('color: #555; font-size: 13px;')
        date_lbl = QLabel(f"📅 {order_data['date_str']}")
        date_lbl.setStyleSheet('color: #555; font-size: 13px;')
        is_paid = order_data['pay_status'] == 'оплачен'
        status_color = '#388E3C' if is_paid else '#D32F2F'
        status_text = 'Оплачено' if is_paid else 'Не оплачено'
        status_lbl = QLabel(f"💰 {status_text} ({order_data['total_cost']} ₽)")
        status_lbl.setStyleSheet(f'color: {status_color}; font-size: 12px; font-weight: bold;')
        info_layout.addWidget(title_lbl)
        info_layout.addWidget(region_lbl)
        info_layout.addWidget(date_lbl)
        info_layout.addWidget(status_lbl)
        btn_layout = QVBoxLayout()
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        accept_btn = QPushButton('Принять')
        accept_btn.setFixedSize(80, 35)
        accept_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        accept_btn.setStyleSheet('font-size: 13px; background-color: #4CAF50; color: white;')
        accept_btn.clicked.connect(lambda _, c=card, o=order_data: self.accept_order(c, o))
        btn_layout.addWidget(accept_btn)
        layout.addWidget(avatar)
        layout.addLayout(info_layout)
        layout.addLayout(btn_layout)
        return card

    def accept_order(self, card_widget, order_data):
        if hasattr(self.main_window, 'is_debug_mode') and self.main_window.is_debug_mode:
            self.main_window.active_order = order_data
            self.main_window.switch_to('walker_walk')
            return
        walker_id = self.main_window.current_user['id']
        success = database.accept_order(order_data['id'], walker_id)
        if success:
            self.main_window.active_order = order_data
            self.main_window.switch_to('walker_walk')
        else:
            print('Ошибка: не удалось принять заказ (возможно, его уже забрали).')
            self.fetch_and_render_orders()