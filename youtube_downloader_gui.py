import sys
import os
import subprocess
import re # yt-dlp 출력 파싱을 위해 추가

from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit,
                             QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog, QProgressBar)
from PyQt5.QtCore import QThread, pyqtSignal

class DownloaderThread(QThread):
    """
    다운로드를 처리하기 위한 별도의 스레드
    GUI가 멈추는 것을 방지합니다.
    """
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, url, save_path):
        super().__init__()
        self.url = url
        self.save_path = save_path

    def run(self):
        try:
            # yt-dlp 명령어 구성
            # -o: 출력 파일 경로 및 이름 형식 지정
            # --progress: 진행 상황을 stderr로 출력
            # --no-warnings: 경고 메시지 출력 안 함
            # --restrict-filenames: 파일 이름 제한 (안전한 파일 이름)
            # --no-playlist: 플레이리스트 다운로드 방지 (단일 영상만)
            command = [
                "yt-dlp",
                "--progress",
                "--no-warnings",
                "--restrict-filenames",
                "--no-playlist",
                "-o", os.path.join(self.save_path, "%(title)s.%(ext)s"),
                self.url
            ]

            self.finished.emit(f"다운로드를 시작합니다: {self.url}")

            # subprocess를 사용하여 yt-dlp 실행
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True, # 텍스트 모드로 설정
                bufsize=1, # 라인 버퍼링
                universal_newlines=True # 유니코드 처리
            )

            # stderr에서 진행 상황 읽기
            for line in iter(process.stderr.readline, ''):
                if "%" in line:
                    match = re.search(r"(\d+\.\d+)%", line)
                    if match:
                        percentage = float(match.group(1))
                        self.progress.emit(int(percentage))
                # print(f"yt-dlp output: {line.strip()}") # 디버깅용

            process.wait() # 프로세스 종료 대기

            if process.returncode == 0:
                self.finished.emit(f"다운로드 완료! 저장 경로: {os.path.abspath(self.save_path)}")
            else:
                error_output = process.stderr.read()
                self.error.emit(f"다운로드 실패: {error_output}")

        except FileNotFoundError:
            self.error.emit("오류: 'yt-dlp'를 찾을 수 없습니다. yt-dlp가 시스템 PATH에 추가되었는지 확인하세요.")
        except Exception as e:
            self.error.emit(f"오류 발생: {e}")


class YoutubeDownloader(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('YouTube Downloader (yt-dlp)') # 제목 변경
        self.setGeometry(300, 300, 500, 200) # 창 크기 조정

        # 레이아웃 설정
        vbox = QVBoxLayout()

        # URL 입력 필드
        url_hbox = QHBoxLayout()
        self.url_label = QLabel('영상 URL:')
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText('다운로드할 유튜브 영상의 전체 URL을 입력하세요')
        url_hbox.addWidget(self.url_label)
        url_hbox.addWidget(self.url_input)
        vbox.addLayout(url_hbox)

        # 저장 경로 선택
        path_hbox = QHBoxLayout()
        self.path_label = QLabel('저장 경로:')
        self.path_input = QLineEdit(os.path.join(os.getcwd(), 'downloads')) # 기본 경로
        self.path_button = QPushButton('찾아보기...')
        self.path_button.clicked.connect(self.select_path)
        path_hbox.addWidget(self.path_label)
        path_hbox.addWidget(self.path_input)
        path_hbox.addWidget(self.path_button)
        vbox.addLayout(path_hbox)

        # 다운로드 버튼
        self.download_button = QPushButton('다운로드')
        self.download_button.clicked.connect(self.start_download)
        vbox.addWidget(self.download_button)

        # 진행률 표시 바
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        vbox.addWidget(self.progress_bar)

        # 상태 메시지 라벨
        self.status_label = QLabel('준비')
        vbox.addWidget(self.status_label)

        self.setLayout(vbox)
        self.show()

    def select_path(self):
        path = QFileDialog.getExistingDirectory(self, '저장할 폴더를 선택하세요', self.path_input.text())
        if path:
            self.path_input.setText(path)

    def start_download(self):
        url = self.url_input.text()
        save_path = self.path_input.text()

        if not url:
            self.status_label.setText('URL을 입력해주세요.')
            return
        
        if not os.path.exists(save_path):
            try:
                os.makedirs(save_path)
            except OSError:
                self.status_label.setText('유효하지 않은 저장 경로입니다.')
                return

        self.download_button.setEnabled(False)
        self.status_label.setText('다운로드 준비 중...')
        self.progress_bar.setValue(0)

        # 다운로드 스레드 시작
        self.downloader = DownloaderThread(url, save_path)
        self.downloader.progress.connect(self.update_progress)
        self.downloader.finished.connect(self.download_finished)
        self.downloader.error.connect(self.download_error)
        self.downloader.start()

    def update_progress(self, percentage):
        self.progress_bar.setValue(percentage)
        self.status_label.setText(f"다운로드 중... {percentage}%")

    def download_finished(self, message):
        self.status_label.setText(message)
        self.download_button.setEnabled(True)
        self.progress_bar.setValue(100) # 완료 시 100%로 설정

    def download_error(self, error_message):
        self.status_label.setText(error_message)
        self.download_button.setEnabled(True)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = YoutubeDownloader()
    sys.exit(app.exec_())