import sys
import os
import subprocess
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QPushButton,
    QFileDialog,
    QStackedWidget,
    QSizePolicy,
    QLineEdit,
)
from PyQt5.QtGui import QFont, QPalette, QColor
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from chatbot import load_model, generate_response
from rag_model import (
    read_pdf,
    read_word,
    read_text,
    read_csv_excel,
    get_text_chunks,
    get_vector_store,
    user_input,
)
from sysaction import SystemController


class ChatWindow(QWidget):
    def __init__(self, model, is_rag=False):
        super().__init__()
        self.model = model
        self.is_rag = is_rag
        self.history = []

        self.initUI()

    def initUI(self):
        self.setWindowTitle("AI ChatBot" if not self.is_rag else "RAG")

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Chat History
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setFont(QFont("Arial", 14))
        layout.addWidget(self.chat_history)

        # Input Box and Buttons
        input_layout = QHBoxLayout()
        layout.addLayout(input_layout)

        if self.is_rag:
            upload_button = QPushButton("📂")
            upload_button.clicked.connect(self.upload_document)
            upload_button.setMinimumSize(80, 80)
            upload_button.setMaximumSize(100, 80)
            input_layout.addWidget(upload_button)

        self.input_box = QTextEdit()
        self.input_box.setFont(QFont("Arial", 14))
        self.input_box.setMaximumSize(700, 100)
        input_layout.addWidget(self.input_box)

        enter_button = QPushButton("➤")
        enter_button.clicked.connect(self.send_message)
        enter_button.setMinimumSize(80, 80)
        enter_button.setMaximumSize(100, 80)
        input_layout.addWidget(enter_button)

        clear_button = QPushButton("🧹")
        clear_button.clicked.connect(self.clear_chat)
        clear_button.setMinimumSize(80, 80)
        clear_button.setMaximumSize(100, 80)
        input_layout.addWidget(clear_button)

        # Style
        self.setStyleSheet(
            """
            QTextEdit {
                background-color: #F2F2F2;
                border: 1px solid #CCCCCC;
                padding: 10px;
                border-radius: 20px;

            }
            QPushButton {
                background-color: #007BFF;
                color: white;
                border: none;
                padding: 10px 5px;
                border-radius: 10px;
                font-weight: bold; 
                font-size: 30px
            }
            QPushButton:hover {
                background-color: #0056b3;
                border-radius: 10px;
                font-size: 40px
            }
        """
        )

    def send_message(self):
        user_query = self.input_box.toPlainText().strip()
        self.input_box.clear()

        if not user_query:
            return

        self.display_message("You: " + user_query, "user")

        if self.is_rag:
            response = self.get_rag_response(user_query)
        else:
            response = self.get_llm_response(user_query)

        self.display_message("BarsAI: " + response, "ai")

    def get_llm_response(self, user_query):
        response = generate_response(self.model, user_query, self.history)
        self.history.extend([f"User Query: {user_query}", f"Assistant Response: {response}"])
        return response

    def get_rag_response(self, user_query):
        if hasattr(self, 'file_path'):
            response = user_input(user_query, self.file_path)
            return response['output_text']
        else:
            return "Please upload a document first."

    def display_message(self, message, message_type):
        self.chat_history.append(f'<p style="color: {"blue" if message_type == "user" else "green"};">{message}</p>')

    def clear_chat(self):
        self.chat_history.clear()
        self.history = []

    def upload_document(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Upload Document", "",
            "All Files (*);;PDF Files (*.pdf);;Word Files (*.docx);;Text Files (*.txt);;CSV Files (*.csv);;Excel Files (*.xlsx)",
            options=options
        )
        if file_path:
            self.file_path = file_path
            self.process_document(file_path)

    def process_document(self, file_path):
        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension == '.pdf':
            text = read_pdf(file_path)
        elif file_extension == '.docx':
            text = read_word(file_path)
        elif file_extension in ('.txt', '.csv', '.xlsx'):
            text = read_csv_excel(file_path) if file_extension in ('.csv', '.xlsx') else read_text(file_path)
        else:
            self.chat_history.append("<p>Unsupported file format.</p>")
            return

        chunks = get_text_chunks(text)
        get_vector_store(chunks, file_path)
        self.chat_history.append("<p>Document processed and indexed successfully!</p>")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("AI Assistant")
        self.setGeometry(100, 100, 1000, 650)

        self.llm_model = load_model()

        self.initUI()

    def initUI(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        layout = QHBoxLayout()
        central_widget.setLayout(layout)

        # Side Menu
        side_menu = QVBoxLayout()
        layout.addLayout(side_menu)
        side_menu.setAlignment(Qt.AlignTop)

        # Buttons for AI Chatbot, RAG, GC
        chatbot_button = QPushButton("📜 AI ChatBot")
        chatbot_button.clicked.connect(self.open_chatbot)
        side_menu.addWidget(chatbot_button)

        rag_button = QPushButton("🗂️ RAG")
        rag_button.clicked.connect(self.open_rag)
        side_menu.addWidget(rag_button)

        gc_button = QPushButton("🖐️ GC")
        gc_button.clicked.connect(self.open_gc)
        side_menu.addWidget(gc_button)

        self.content_area = QStackedWidget()
        layout.addWidget(self.content_area)

        self.chatbot_window = ChatWindow(self.llm_model)
        self.rag_window = ChatWindow(self.llm_model, is_rag=True)
        self.gc_window = GCWindow()

        self.content_area.addWidget(self.chatbot_window)
        self.content_area.addWidget(self.rag_window)
        self.content_area.addWidget(self.gc_window)

        self.setStyleSheet(
            """
            QPushButton {
                background-color: #FFFFFF;
                border: none;
                padding: 10px 5px;
                border-radius: 15px;
                width: 150

            }
            QPushButton:hover {
                background-color: #ADD8E6;
                border-radius: 15px;
                border: 2px solid #04AA6D;
            }
        """
        )

    def open_chatbot(self):
        self.content_area.setCurrentIndex(0)  # Index 0 for AI Chatbot

    def open_rag(self):
        self.content_area.setCurrentIndex(1)  # Index 1 for RAG

    def open_gc(self):
        self.content_area.setCurrentIndex(2)  # Index 2 for GC (gesture control)


class GCWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setWindowTitle("Gesture Control")

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.handgest_process = None
        self.volumecontrol_process = None

        # Hand Gesture Control Buttons
        handgest_layout = QHBoxLayout()
        layout.addLayout(handgest_layout)

        self.handgest_button = QPushButton("Enable Hand Gesture Control")
        self.handgest_button.clicked.connect(self.toggle_handgest)
        handgest_layout.addWidget(self.handgest_button)

        self.volumecontrol_button = QPushButton("Enable Volume Control")
        self.volumecontrol_button.clicked.connect(self.toggle_volumecontrol)
        handgest_layout.addWidget(self.volumecontrol_button)

        # System Action Input
        self.action_input = QLineEdit()
        self.action_input.setPlaceholderText("Enter system action command...")
        layout.addWidget(self.action_input)

        self.action_button = QPushButton("Execute Command")
        self.action_button.clicked.connect(self.execute_command)
        layout.addWidget(self.action_button)

        # Style
        self.setStyleSheet(
            """
            QPushButton {
                background-color: #007BFF;
                color: white;
                border: none;
                padding: 10px 5px;
                border-radius: 10px;
                font-weight: bold; 
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QLineEdit {
                padding: 10px;
                font-size: 18px;
                border-radius: 10px;
                border: 1px solid #CCCCCC;
            }
        """
        )

    def toggle_handgest(self):
        if self.handgest_process is None:
            self.handgest_process = subprocess.Popen(["python", "handgest.py"])
            self.handgest_button.setText("Disable Hand Gesture Control")
        else:
            self.handgest_process.terminate()
            self.handgest_process = None
            self.handgest_button.setText("Enable Hand Gesture Control")

    def toggle_volumecontrol(self):
        if self.volumecontrol_process is None:
            self.volumecontrol_process = subprocess.Popen(["python", "volumecontrol.py"])
            self.volumecontrol_button.setText("Disable Volume Control")
        else:
            self.volumecontrol_process.terminate()
            self.volumecontrol_process = None
            self.volumecontrol_button.setText("Enable Volume Control")

    def execute_command(self):
        command = self.action_input.text().strip()
        if command:
            controller = SystemController()
            controller.process_command(command)
            self.action_input.clear()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())