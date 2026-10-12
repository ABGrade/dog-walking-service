from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame, QScrollArea, QTextEdit
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap
from .base_page import BasePage
import config
import database

class WalkPage(BasePage):

    def __init__(self, main_window):
        super().__init__(main_window, 'walk_page')
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        top_bar = QHBoxLayout()
        back_btn = QPushButton('←')
        back_btn.setObjectName('big_back_btn')
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self.go_back)
        title = QLabel('Статус заказа')
        title.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        title.setStyleSheet('color: white;')
        self.refresh_btn = QPushButton('🔄')
        self.refresh_btn.setFixedSize(35, 35)
        self.refresh_btn.setStyleSheet('background-color: white; color: black; border-radius: 5px; font-size: 16px;')
        self.refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_btn.clicked.connect(self.update_data)
        top_bar.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignTop)
        top_bar.addStretch()
        top_bar.addWidget(title)
        top_bar.addStretch()
        top_bar.addWidget(self.refresh_btn, alignment=Qt.AlignmentFlag.AlignTop)
        scroll_content = QWidget()
        scroll_content.setObjectName('scroll_content')
        scroll_content.setStyleSheet('#scroll_content { background: transparent; }')
        self.scroll_layout = QVBoxLayout(scroll_content)
        self.scroll_layout.setContentsMargins(0, 10, 0, 0)
        self.info_container = QFrame()
        self.info_container.setObjectName('form_container')
        self.info_container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.info_layout = QVBoxLayout(self.info_container)
        self.info_layout.setSpacing(15)
        self.info_layout.setContentsMargins(20, 20, 20, 20)
        self.scroll_layout.addWidget(self.info_container)
        self.scroll_layout.addStretch()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.viewport().setAutoFillBackground(False)
        scroll.setStyleSheet('QScrollArea { border: none; background: transparent; }')
        scroll.setWidget(scroll_content)
        main_layout.addLayout(top_bar)
        main_layout.addWidget(scroll)

    def update_data(self):
        order_id = getattr(self.main_window, 'active_client_order_id', None)
        if not order_id:
            self.clear_layout(self.info_layout)
            self.info_layout.addWidget(QLabel('Заказ не найден'))
            return
        if not hasattr(self, 'last_order_id') or self.last_order_id != order_id:
            self.last_order_id = order_id
            self.editing_review = False
        order_details = database.get_order_details_for_client(order_id)
        if order_details:
            self.update_ui(order_details)

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            elif item.layout() is not None:
                self.clear_layout(item.layout())

    def create_row(self, label, value, bold_value=False):
        row = QHBoxLayout()
        lbl = QLabel(label)
        lbl.setStyleSheet('color: #666; font-size: 13px;')
        val = QLabel(f'<b>{value}</b>' if bold_value else value)
        val.setAlignment(Qt.AlignmentFlag.AlignRight)
        val.setStyleSheet('font-size: 14px;')
        row.addWidget(lbl)
        row.addWidget(val)
        return row

    def update_ui(self, order):
        self.clear_layout(self.info_layout)
        header = QLabel(f"Заказ #{order['id']}")
        header.setFont(QFont('Arial', 18, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_layout.addWidget(header)
        self.info_layout.addSpacing(10)
        walker_name = f"{order['walker_name']} {order.get('walker_last', '')}".strip() if order['walker_name'] else 'Не назначен'
        if order['status_id'] == 1:
            if order['payment_status'] == 'pending':
                status_lbl = QLabel('Ожидает оплаты')
                status_lbl.setStyleSheet('color: #D32F2F; font-size: 16px; font-weight: bold;')
                status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.info_layout.addWidget(status_lbl)
                self.info_layout.addLayout(self.create_row('К оплате:', f"{order['amount']} ₽", True))
                pay_btn = QPushButton('Оплатить заказ')
                pay_btn.setStyleSheet('background-color: #4CAF50; color: white; padding: 12px; font-weight: bold; margin-top: 20px;')
                pay_btn.clicked.connect(lambda: self.main_window.switch_to('payment_confirm'))
                self.info_layout.addWidget(pay_btn)
            else:
                status_lbl = QLabel('Поиск выгульщика...')
                status_lbl.setStyleSheet('color: #F57C00; font-size: 16px; font-weight: bold;')
                status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.info_layout.addWidget(status_lbl)
                self.info_layout.addLayout(self.create_row('Статус оплаты:', 'Оплачено', True))
                self.info_layout.addWidget(QLabel('<i>Ждите, пока выгульщик примет ваш заказ</i>'))
        elif order['status_id'] == 2:
            if order['payment_status'] == 'pending':
                status_lbl = QLabel('Выгульщик найден. Ожидается оплата заказа.')
                status_lbl.setStyleSheet('color: #D32F2F; font-size: 16px; font-weight: bold;')
                status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.info_layout.addWidget(status_lbl)
                self.info_layout.addLayout(self.create_row('К оплате:', f"{order['amount']} ₽", True))
                pay_btn = QPushButton('Оплатить заказ')
                pay_btn.setStyleSheet('background-color: #4CAF50; color: white; padding: 12px;')
                pay_btn.clicked.connect(lambda: self.main_window.switch_to('payment_confirm'))
                self.info_layout.addWidget(pay_btn)
                return
            else:
                if order['start_time']:
                    status_lbl = QLabel('🐕 Прогулка в процессе!')
                    status_lbl.setStyleSheet('color: #1976D2; font-size: 18px; font-weight: bold;')
                else:
                    status_lbl = QLabel('Ожидание прогулки')
                    status_lbl.setStyleSheet('color: #F57C00; font-size: 16px; font-weight: bold;')
                status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.info_layout.addWidget(status_lbl)
                self.info_layout.addLayout(self.create_row('Выгульщик:', walker_name, True))
                if order['start_time']:
                    self.info_layout.addLayout(self.create_row('Начало:', order['start_time']))
                gif_placeholder = QLabel('<i>Отслеживание по GPS...</i>')
                gif_placeholder.setStyleSheet('color: #888; background: #eee; border-radius: 10px;')
                gif_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
                gif_placeholder.setFixedHeight(120)
                self.info_layout.addWidget(gif_placeholder)
        elif order['status_id'] == 3:
            status_lbl = QLabel('✅ Прогулка завершена')
            status_lbl.setStyleSheet('color: #388E3C; font-size: 18px; font-weight: bold;')
            status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.info_layout.addWidget(status_lbl)
            self.info_layout.addLayout(self.create_row('Выгульщик:', walker_name, True))
            self.info_layout.addLayout(self.create_row('Начало:', order['start_time']))
            self.info_layout.addLayout(self.create_row('Конец:', order['end_time']))
            self.info_layout.addSpacing(10)
            self.info_layout.addWidget(QLabel('<b>Отчет выгульщика:</b>'))
            report_text = QTextEdit()
            report_text.setReadOnly(True)
            report_text.setText(order.get('report_summary', 'Отчет отсутствует'))
            report_text.setStyleSheet('background-color: white; border: 1px solid #ccc; font-size: 13px; color: #333;')
            report_text.setFixedHeight(90)
            self.info_layout.addWidget(report_text)
            
            self.info_layout.addSpacing(15)
            self.info_layout.addWidget(QLabel('<b>Отзыв о прогулке:</b>'))
            if order.get('review_rating') and not getattr(self, 'editing_review', False):
                rating_val = int(order['review_rating'])
                stars_text = '★' * rating_val + '☆' * (5 - rating_val)
                rating_lbl = QLabel(f"Оценка: <span style='color: #FFB300; font-size: 36px;'>{stars_text}</span>")
                rating_lbl.setStyleSheet('font-size: 16px;')
                self.info_layout.addWidget(rating_lbl)
                comment_text = QTextEdit()
                comment_text.setReadOnly(True)
                comment_text.setText(order.get('review_comment', 'Без комментария'))
                comment_text.setStyleSheet('background-color: white; border: 1px solid #ccc; font-size: 13px; color: #333;')
                comment_text.setFixedHeight(60)
                self.info_layout.addWidget(comment_text)
                
                edit_btn = QPushButton('Изменить отзыв')
                edit_btn.setStyleSheet('background-color: #1976D2; color: white; font-weight: bold; margin-top: 10px;')
                edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                edit_btn.clicked.connect(lambda: self.start_editing_review(order))
                self.info_layout.addWidget(edit_btn)
            else:
                rating_layout = QHBoxLayout()
                rating_layout.addWidget(QLabel('Ваша оценка:'))
                self.rating_buttons = []
                existing_rating = int(order['review_rating']) if order.get('review_rating') else 5
                self.selected_rating = existing_rating
                for rating_i in range(1, 6):
                    star_char = '★' if rating_i <= existing_rating else '☆'
                    star_color = '#FFB300' if rating_i <= existing_rating else '#888'
                    star_btn = QPushButton(star_char)
                    star_btn.setFixedSize(50, 50)
                    star_btn.setStyleSheet(f'font-size: 38px; color: {star_color}; background: transparent; border: none;')
                    star_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    star_btn.clicked.connect(lambda _, r=rating_i: self.set_rating(r))
                    self.rating_buttons.append(star_btn)
                    rating_layout.addWidget(star_btn)
                rating_layout.addStretch()
                self.info_layout.addLayout(rating_layout)
                self.comment_input = QTextEdit()
                self.comment_input.setPlaceholderText('Напишите ваш отзыв о прогулке...')
                self.comment_input.setFixedHeight(60)
                self.comment_input.setStyleSheet('background-color: white; border: 1px solid #ccc; font-size: 13px; color: black;')
                existing_comment = order.get('review_comment', '')
                if existing_comment:
                    self.comment_input.setText(existing_comment)
                self.info_layout.addWidget(self.comment_input)
                
                actions_layout = QHBoxLayout()
                submit_text = 'Сохранить изменения' if order.get('review_rating') else 'Оставить отзыв'
                submit_review_btn = QPushButton(submit_text)
                submit_review_btn.setStyleSheet('background-color: #FFB300; color: white; font-weight: bold;')
                submit_review_btn.clicked.connect(self.submit_review)
                actions_layout.addWidget(submit_review_btn)
                
                if order.get('review_rating'):
                    cancel_btn = QPushButton('Отмена')
                    cancel_btn.setStyleSheet('background-color: #757575; color: white; font-weight: bold;')
                    cancel_btn.clicked.connect(lambda: self.cancel_editing_review(order))
                    actions_layout.addWidget(cancel_btn)
                self.info_layout.addLayout(actions_layout)

    def start_editing_review(self, order):
        self.editing_review = True
        self.update_ui(order)

    def cancel_editing_review(self, order):
        self.editing_review = False
        self.update_ui(order)

    def go_back(self):
        self.main_window.switch_to('my_orders')

    def set_rating(self, rating):
        self.selected_rating = rating
        for i, btn in enumerate(self.rating_buttons):
            if i < rating:
                btn.setText('★')
                btn.setStyleSheet('font-size: 38px; color: #FFB300; background: transparent; border: none;')
            else:
                btn.setText('☆')
                btn.setStyleSheet('font-size: 38px; color: #888; background: transparent; border: none;')

    def submit_review(self):
        order_id = self.main_window.active_client_order_id
        if not order_id or not self.main_window.current_user:
            return
        user_id = self.main_window.current_user['id']
        comment = self.comment_input.toPlainText().strip()
        success = database.add_or_update_review(user_id, order_id, self.selected_rating, comment)
        self.editing_review = False
        self.update_data()

    def process_payment(self, order_id):
        conn = database.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("UPDATE payments SET payment_status = 'оплачен', paid_at = NOW() WHERE order_id = %s", (order_id,))
            conn.commit()
        finally:
            cur.close()
            conn.close()
        self.update_data()