"""Make Cyrillic fonts available in Windows offscreen rendering as well."""
from pathlib import Path
import os
import sys
from PyQt6.QtGui import QFont, QFontDatabase

_configured=False

def configure_fonts(application):
    global _configured
    if _configured or application is None:
        return
    _configured=True
    if sys.platform=='win32':
        font_directory=Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'
        for filename in ['arial.ttf','arialbd.ttf']:
            font=font_directory/filename
            if font.exists():QFontDatabase.addApplicationFont(str(font))
        application.setFont(QFont('Arial',11))
