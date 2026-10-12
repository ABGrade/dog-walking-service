from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt
import config

class BasePage(QWidget):

    def __init__(self, main_window, object_name):
        super().__init__()
        self.main_window = main_window
        self.setObjectName(object_name)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(f'\n            #{object_name} {{\n                background-image: url("{config.BACKGROUND_IMAGE}");\n                background-position: center;\n                background-repeat: no-repeat;\n            }}\n        ')