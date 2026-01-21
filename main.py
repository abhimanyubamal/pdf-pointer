import sys
import os
from PyQt5.QtWidgets import QApplication
from pdf_parser import extract_characters
from viewer import PDFViewer
from controls import KeyboardController

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_PATH = os.path.join(BASE_DIR, "sample.pdf")


class App(PDFViewer):
    def __init__(self):
        characters = extract_characters(PDF_PATH)
        super().__init__(PDF_PATH, characters)
        self.controller = KeyboardController(self)

    def keyPressEvent(self, event):
        self.controller.handle_key(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = App()
    viewer.show()
    sys.exit(app.exec_())
