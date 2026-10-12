from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / 'app'))

def main():
    import database
    try:
        database.get_connection().close()
    except Exception:
        print('PostgreSQL is unavailable. Start the demo database, check .env, then run python initialize_demo.py.')
        return 1
    from PyQt6.QtWidgets import QApplication
    from main import DogWalkingApp
    application = QApplication(sys.argv)
    window = DogWalkingApp()
    window.show()
    return application.exec()

if __name__ == '__main__':
    raise SystemExit(main())
