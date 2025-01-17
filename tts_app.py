import sys
from pathlib import Path
from openai import OpenAI
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QLabel, QTextEdit, QLineEdit, QPushButton,
    QFileDialog, QMessageBox, QWidget, QComboBox
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimedia import QMediaDevices, QAudioDevice
from PySide6.QtCore import QUrl
import os

import traceback

if getattr(sys, 'frozen', False):  # If running in a frozen environment
    BASE_DIR = Path(sys.executable).parent  # Get the directory of the executable
else:  # Development environment
    BASE_DIR = Path(__file__).parent

if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError("OpenAI API Key is not set!")

class TTSApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Text-to-Speech Application")
        self.setGeometry(300, 100, 600, 500)
        
        # Create OpenAI client
        self.client = OpenAI()
        
        # Main window layout
        self.layout = QVBoxLayout()
        
        # Text input section
        self.text_label = QLabel("Enter text to convert to speech:")
        self.layout.addWidget(self.text_label)
        
        self.text_input = QTextEdit()
        self.layout.addWidget(self.text_input)
        
        # File name input section
        self.file_label = QLabel("Enter the file name to save (no extension):")
        self.layout.addWidget(self.file_label)
        
        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText("Default file name: speech")
        self.layout.addWidget(self.file_input)
        
        # Voice selection section
        self.voice_label = QLabel("Select a voice:")
        self.layout.addWidget(self.voice_label)
        
        self.voice_selector = QComboBox()
        self.voice_selector.addItems(["alloy", "ash", "coral", "echo", "fable", "onyx", "nova", "sage", "shimmer"])
        self.voice_selector.setCurrentText("alloy")  # Set default value
        self.layout.addWidget(self.voice_selector)
        
        # Buttons
        self.generate_button = QPushButton("Generate Speech")
        self.generate_button.clicked.connect(self.generate_speech)
        self.layout.addWidget(self.generate_button)
        
        self.play_button = QPushButton("Play Speech")
        self.play_button.clicked.connect(self.play_speech)
        self.play_button.setEnabled(False)
        self.layout.addWidget(self.play_button)
        
        self.save_button = QPushButton("Save Speech File")
        self.save_button.clicked.connect(self.save_speech)
        self.save_button.setEnabled(False)
        self.layout.addWidget(self.save_button)
        
        # Central widget
        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)
        
        # Audio player
        audio_device = QMediaDevices.defaultAudioOutput()  # Get the default audio device
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput(audio_device)
        self.player.setAudioOutput(self.audio_output)
        
        # Directory to save generated audio files
        self.output_dir = BASE_DIR / "audio_files"
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize audio file path
        self.audio_file_path = self.output_dir / "speech.mp3"

    def generate_speech(self):
        """Call OpenAI API to generate speech"""
        text = self.text_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Warning", "Please enter text!")
            return
        
        # Get user input for file name
        file_name = self.file_input.text().strip()
        if not file_name:
            file_name = "speech"  # Use default file name
        
        # Get user-selected voice
        selected_voice = self.voice_selector.currentText()
        
        # Set file path
        self.audio_file_path = self.output_dir / f"{file_name}.mp3"
        
        try:
            # Call OpenAI API
            response = self.client.audio.speech.create(
                model="tts-1",
                voice=selected_voice,
                input=text,
            )
            response.stream_to_file(self.audio_file_path)
            
            QMessageBox.information(self, "Success", f"Speech generated successfully! File saved to: {self.audio_file_path}")
            self.play_button.setEnabled(True)
            self.save_button.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate speech: {e}")

    def play_speech(self):
        """Play the generated speech"""
        if self.audio_file_path.exists():
            self.player.setSource(QUrl.fromLocalFile(str(self.audio_file_path)))
            self.player.play()
        else:
            QMessageBox.warning(self, "Warning", "Audio file does not exist. Please generate speech first!")

    def save_speech(self):
        """Save speech file to a user-specified path"""
        if not self.audio_file_path.exists():
            QMessageBox.warning(self, "Warning", "No generated speech file to save!")
            return
        
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Speech File", str(self.audio_file_path), "Audio Files (*.mp3)")
        if save_path:
            try:
                with open(self.audio_file_path, "rb") as file:
                    data = file.read()
                with open(save_path, "wb") as file:
                    file.write(data)
                QMessageBox.information(self, "Success", f"File saved to: {save_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file: {e}")

try:
    # Main program entry point
    if __name__ == "__main__":
        app = QApplication(sys.argv)
        window = TTSApp()
        window.show()
        sys.exit(app.exec())
except Exception as e:
    # Set the log file path in the application directory
    log_path = Path(__file__).parent if not getattr(sys, 'frozen', False) else Path(sys.executable).parent.parent
    log_file = log_path / "error_log.txt"
    with open(log_file, "w") as log:
        log.write(traceback.format_exc())
    print(f"Error log saved to: {log_file}")