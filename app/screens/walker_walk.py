from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame, QTextEdit, QScrollArea
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap
from .base_page import BasePage
from custom_ui import set_field_error, clear_field_error
import config
from datetime import datetime
import database

class WalkerWalkPage(BasePage):

    def __init__(self, main_window):
        super().__init__(main_window, 'walker_walk_page')
        self.current_state = 0
        self.active_walk_id = None
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
        title = QLabel('Управление прогулкой')
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
        self.scroll_layout = QVBoxLayout(scroll_content)
        self.scroll_layout.setContentsMargins(0, 10, 0, 0)
        self.dog_card = QFrame()
        self.dog_card.setStyleSheet('QFrame { background-color: rgba(248, 249, 250, 0.95); border-radius: 12px; }')
        self.dog_layout = QHBoxLayout(self.dog_card)
        self.dog_layout.setContentsMargins(15, 15, 15, 15)
        self.scroll_layout.addWidget(self.dog_card)
        self.scroll_layout.addSpacing(10)
        self.action_container = QFrame()
        self.action_container.setStyleSheet('QFrame { background-color: rgba(248, 249, 250, 0.95); border-radius: 12px; }')
        self.action_layout = QVBoxLayout(self.action_container)
        self.action_layout.setContentsMargins(20, 20, 20, 20)
        self.action_layout.setSpacing(15)
        self.scroll_layout.addWidget(self.action_container)
        self.scroll_layout.addStretch()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.viewport().setAutoFillBackground(False)
        scroll.setStyleSheet('QScrollArea { border: none; background: transparent; }')
        scroll.setWidget(scroll_content)
        main_layout.addLayout(top_bar)
        main_layout.addWidget(scroll)

    def update_data(self):
        self.clear_layout(self.dog_layout)
        order = getattr(self.main_window, 'active_order', None)
        if not order:
            self.dog_layout.addWidget(QLabel('Заказ не выбран'))
            return
        if not (hasattr(self.main_window, 'is_debug_mode') and self.main_window.is_debug_mode):
            walk_status, walk_id = database.get_order_walk_status(order['id'])
            if walk_status == 'in_progress':
                self.current_state = 1
                self.active_walk_id = walk_id
                self.existing_report_summary = ''
            elif walk_status == 'completed' or order.get('status_id') == 3:
                self.current_state = 2
                self.active_walk_id = walk_id
                details = database.get_order_details_for_client(order['id'])
                self.existing_report_summary = details.get('report_summary', '') if details else ''
            else:
                self.current_state = 0
                self.active_walk_id = None
                self.existing_report_summary = ''
        avatar = QLabel()
        avatar.setFixedSize(60, 60)
        avatar.setStyleSheet('background-color: #E0E0E0; border-radius: 8px;')
        pixmap = QPixmap(config.DOG_IMAGE)
        if not pixmap.isNull():
            avatar.setPixmap(pixmap.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_layout = QVBoxLayout()
        info_layout.addWidget(QLabel(f"<b>{order['dog_name']} ({order['breed_name']})</b>"))
        lbl_loc = QLabel(f"📍 {order['walk_address']}")
        lbl_loc.setStyleSheet('color: #555; font-size: 13px;')
        info_layout.addWidget(lbl_loc)
        self.dog_layout.addWidget(avatar, alignment=Qt.AlignmentFlag.AlignTop)
        self.dog_layout.addLayout(info_layout)
        self.dog_layout.addStretch()
        self.update_ui()

    def reset_state(self):
        self.current_state = 0
        self.active_walk_id = None
        self.update_ui()

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            elif item.layout() is not None:
                self.clear_layout(item.layout())

    def update_ui(self):
        self.clear_layout(self.action_layout)
        order = getattr(self.main_window, 'active_order', None)
        if self.current_state == 0:
            status_lbl = QLabel('Ожидание начала')
            status_lbl.setFont(QFont('Arial', 16, QFont.Weight.Bold))
            status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            time_lbl = QLabel(f"Запланировано на: <b>{(order['date_str'] if order else '...')}</b>")
            time_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            is_paid = order.get('pay_status') == 'оплачен' if order else False
            is_debug = hasattr(self.main_window, 'is_debug_mode') and self.main_window.is_debug_mode
            self.action_layout.addWidget(status_lbl)
            self.action_layout.addWidget(time_lbl)
            self.action_layout.addSpacing(20)
            start_btn = QPushButton('▶ Начать прогулку')
            if is_paid or is_debug:
                start_btn.setStyleSheet('background-color: #4CAF50; font-size: 18px; padding: 15px; color: white;')
                start_btn.clicked.connect(self.start_walk)
            else:
                start_btn.setEnabled(False)
                start_btn.setStyleSheet('background-color: #ccc; color: #888; font-size: 18px; padding: 15px;')
                warning_lbl = QLabel('⚠️ Ожидается оплата от клиента. Начать нельзя.')
                warning_lbl.setStyleSheet('color: #D32F2F; font-size: 13px; font-weight: bold;')
                warning_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.action_layout.addWidget(warning_lbl)
                refresh_btn = QPushButton('🔄 Обновить статус оплаты')
                refresh_btn.setStyleSheet('background-color: #1976D2; color: white; font-size: 14px; padding: 10px; margin-top: 5px;')
                refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                refresh_btn.clicked.connect(self.refresh_payment_status)
                self.action_layout.addWidget(refresh_btn)
            self.action_layout.addWidget(start_btn)
        elif self.current_state == 1:
            status_lbl = QLabel('🐕 Прогулка идет')
            status_lbl.setStyleSheet('color: #1976D2; font-size: 18px; font-weight: bold;')
            status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            current_time = datetime.now().strftime('%H:%M')
            time_lbl = QLabel(f'Начата в: <b>{current_time}</b>')
            time_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            end_btn = QPushButton('⏹ Завершить прогулку')
            end_btn.setStyleSheet('background-color: #D32F2F; color: white; font-size: 18px; padding: 15px;')
            end_btn.clicked.connect(self.end_walk)
            call_btn = QPushButton('📞 Позвонить хозяину')
            call_btn.setObjectName('outline_btn')
            phone = order.get('owner_phone', 'Номер скрыт') if order else 'Номер скрыт'
            call_btn.clicked.connect(lambda _, btn=call_btn, p=phone: (btn.setText(f'📞 {p}'), btn.setStyleSheet('background: transparent; color: black; border: none; font-size: 16px; font-weight: bold;'), btn.setEnabled(False)))
            self.action_layout.addWidget(status_lbl)
            self.action_layout.addWidget(time_lbl)
            self.action_layout.addSpacing(20)
            self.action_layout.addWidget(end_btn)
            self.action_layout.addWidget(call_btn)
        elif self.current_state == 2:
            status_lbl = QLabel('✅ Прогулка завершена')
            status_lbl.setStyleSheet('color: #388E3C; font-size: 16px; font-weight: bold;')
            status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.action_layout.addWidget(status_lbl)
            details = database.get_order_details_for_client(order['id']) if order else None
            if details and details.get('review_rating'):
                rating_val = int(details['review_rating'])
                stars_text = '★' * rating_val + '☆' * (5 - rating_val)
                rating_lbl = QLabel(f"Оценка клиента: <span style='color: #FFB300; font-size: 36px;'>{stars_text}</span>")
                rating_lbl.setStyleSheet('font-size: 13px; font-weight: bold; margin-top: 5px;')
                self.action_layout.addWidget(rating_lbl)
                comment_text = QTextEdit()
                comment_text.setReadOnly(True)
                comment_text.setText(details.get('review_comment', 'Без комментария'))
                comment_text.setStyleSheet('background-color: #f5f5f5; border: 1px solid #ccc; font-size: 12px; color: #555;')
                comment_text.setFixedHeight(50)
                self.action_layout.addWidget(comment_text)
                self.action_layout.addSpacing(10)
            lbl_report = QLabel('Отчет о прогулке')
            lbl_report.setProperty('class', 'field_label')
            self.report_input = QTextEdit()
            self.report_input.setPlaceholderText('Опишите, как прошла прогулка. Сходил ли питомец в туалет? Были ли проблемы?')
            self.report_input.setFixedHeight(120)
            self.report_input.textChanged.connect(lambda: clear_field_error(self.report_input, 'Опишите, как прошла прогулка...'))
            self.report_input.setText(getattr(self, 'existing_report_summary', ''))
            btn_text = 'Сохранить изменения' if order and order.get('status_id') == 3 else 'Отправить отчет и закрыть заказ'
            submit_btn = QPushButton(btn_text)
            submit_btn.clicked.connect(self.submit_report)
            self.action_layout.addWidget(lbl_report)
            self.action_layout.addWidget(self.report_input)
            self.action_layout.addSpacing(10)
            self.action_layout.addWidget(submit_btn)

    def refresh_payment_status(self):
        order = getattr(self.main_window, 'active_order', None)
        if order:
            status = database.get_order_payment_status(order['id'])
            if status == 'оплачен':
                order['pay_status'] = 'оплачен'
                self.main_window.active_order = order
                self.update_ui()

    def start_walk(self):
        if hasattr(self.main_window, 'is_debug_mode') and self.main_window.is_debug_mode:
            self.current_state = 1
            self.update_ui()
            return
        order = getattr(self.main_window, 'active_order', None)
        if order:
            walk_id = database.start_walk(order['id'])
            if walk_id:
                self.active_walk_id = walk_id
                self.current_state = 1
                self.update_ui()

    def end_walk(self):
        order = getattr(self.main_window, 'active_order', None)
        if order and self.active_walk_id:
            success = database.finish_walk(order['id'], self.active_walk_id)
            if success:
                self.current_state = 2
                self.update_ui()

    def go_back(self):
        order = getattr(self.main_window, 'active_order', None)
        if order and order.get('status_id') == 3:
            self.main_window.switch_to('my_orders')
        else:
            self.main_window.switch_to('orders_list')

    def submit_report(self):
        if hasattr(self.main_window, 'is_debug_mode') and self.main_window.is_debug_mode:
            self.main_window.switch_to('orders_list')
            return
        report_text = self.report_input.toPlainText().strip()
        if not report_text:
            set_field_error(self.report_input, 'отчет пуст')
            return
        order = getattr(self.main_window, 'active_order', None)
        if order and self.active_walk_id:
            success = database.update_report(self.active_walk_id, report_text)
            if success:
                is_already_completed = order.get('status_id') == 3
                self.main_window.active_order = None
                if is_already_completed:
                    self.main_window.switch_to('my_orders')
                else:
                    self.main_window.switch_to('orders_list')