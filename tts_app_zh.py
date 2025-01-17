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

    
if getattr(sys, 'frozen', False):  # 如果是打包后的环境
    BASE_DIR = Path(sys.executable).parent  # 获取可执行文件所在目录
else:  # 开发环境
    BASE_DIR = Path(__file__).parent

if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError("OpenAI API Key is not set!")

class TTSApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Text-to-Speech Application")
        self.setGeometry(300, 100, 600, 500)
        
        # 创建 OpenAI 客户端
        self.client = OpenAI()
        
        # 主窗口布局
        self.layout = QVBoxLayout()
        
        # 文本输入部分
        self.text_label = QLabel("请输入要转换为语音的文本：")
        self.layout.addWidget(self.text_label)
        
        self.text_input = QTextEdit()
        self.layout.addWidget(self.text_input)
        
        # 文件名输入部分
        self.file_label = QLabel("请输入保存的文件名（无需扩展名）：")
        self.layout.addWidget(self.file_label)
        
        self.file_input = QLineEdit()
        self.file_input.setPlaceholderText("默认文件名：speech")
        self.layout.addWidget(self.file_input)
        
        # 音色选择部分
        self.voice_label = QLabel("请选择音色：")
        self.layout.addWidget(self.voice_label)
        
        self.voice_selector = QComboBox()
        self.voice_selector.addItems(["alloy", "ash", "coral", "echo", "fable", "onyx", "nova", "sage", "shimmer"])
        self.voice_selector.setCurrentText("alloy")  # 设置默认值
        self.layout.addWidget(self.voice_selector)
        
        # 按钮
        self.generate_button = QPushButton("生成语音")
        self.generate_button.clicked.connect(self.generate_speech)
        self.layout.addWidget(self.generate_button)
        
        self.play_button = QPushButton("播放语音")
        self.play_button.clicked.connect(self.play_speech)
        self.play_button.setEnabled(False)
        self.layout.addWidget(self.play_button)
        
        self.save_button = QPushButton("保存语音文件")
        self.save_button.clicked.connect(self.save_speech)
        self.save_button.setEnabled(False)
        self.layout.addWidget(self.save_button)
        
        # 中心窗口
        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)
        
        # 音频播放器
        audio_device = QMediaDevices.defaultAudioOutput()  # 获取默认音频设备
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput(audio_device)
        self.player.setAudioOutput(self.audio_output)
        
        # 生成音频文件的保存目录
        self.output_dir = BASE_DIR / "audio_files"
        self.output_dir.mkdir(exist_ok=True)
        
        # 初始化音频文件路径
        self.audio_file_path = self.output_dir / "speech.mp3"

    def generate_speech(self):
        """调用 OpenAI API 生成语音"""
        text = self.text_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "警告", "请输入文本内容！")
            return
        
        # 获取用户输入的文件名
        file_name = self.file_input.text().strip()
        if not file_name:
            file_name = "speech"  # 使用默认文件名
        
        # 获取用户选择的音色
        selected_voice = self.voice_selector.currentText()
        
        # 设置文件路径
        self.audio_file_path = self.output_dir / f"{file_name}.mp3"
        
        try:
            # 调用 OpenAI API
            response = self.client.audio.speech.create(
                model="tts-1",
                voice=selected_voice,
                input=text,
            )
            response.stream_to_file(self.audio_file_path)
            
            QMessageBox.information(self, "成功", f"语音生成成功！文件保存至：{self.audio_file_path}")
            self.play_button.setEnabled(True)
            self.save_button.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"生成语音失败：{e}")

    def play_speech(self):
        """播放生成的语音"""
        if self.audio_file_path.exists():
            self.player.setSource(QUrl.fromLocalFile(str(self.audio_file_path)))
            self.player.play()
        else:
            QMessageBox.warning(self, "警告", "音频文件不存在，请先生成语音！")

    def save_speech(self):
        """保存语音文件到用户指定路径"""
        if not self.audio_file_path.exists():
            QMessageBox.warning(self, "警告", "没有生成的语音文件可保存！")
            return
        
        save_path, _ = QFileDialog.getSaveFileName(self, "保存语音文件", str(self.audio_file_path), "音频文件 (*.mp3)")
        if save_path:
            try:
                with open(self.audio_file_path, "rb") as file:
                    data = file.read()
                with open(save_path, "wb") as file:
                    file.write(data)
                QMessageBox.information(self, "成功", f"文件已保存至：{save_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存文件失败：{e}")

try:
    # 主程序入口
    if __name__ == "__main__":
        app = QApplication(sys.argv)
        window = TTSApp()
        window.show()
        sys.exit(app.exec())
except Exception as e:
    # 设置日志文件保存路径为应用程序目录下
    log_path = Path(__file__).parent if not getattr(sys, 'frozen', False) else Path(sys.executable).parent.parent
    log_file = log_path / "error_log.txt"
    with open(log_file, "w") as log:
        log.write(traceback.format_exc())
    print(f"错误日志已保存至：{log_file}")

    