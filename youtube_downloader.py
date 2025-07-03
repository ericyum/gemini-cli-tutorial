from pytube import YouTube
import os

def download_video(url, path='.'):
    """
    유튜브 URL을 받아 영상을 지정된 경로에 다운로드하는 함수
    """
    try:
        # YouTube 객체 생성
        yt = YouTube(url)

        print(f"'{yt.title}' 다운로드를 시작합니다...")

        # 가장 높은 해상도의 스트림 선택
        stream = yt.streams.get_highest_resolution()

        # 동영상 다운로드
        stream.download(output_path=path)

        print(f"다운로드 완료! 저장 경로: {os.path.abspath(path)}")

    except Exception as e:
        print(f"오류가 발생했습니다: {e}")

if __name__ == "__main__":
    # 사용자로부터 유튜브 링크 입력받기
    video_url = input("다운로드할 유튜브 영상 URL을 입력하세요: ")

    # 다운로드 받을 폴더 지정 (예: 'downloads' 폴더)
    # 이 폴더가 없으면 자동으로 생성됩니다.
    download_path = 'downloads'

    if video_url:
        download_video(video_url, download_path)
    else:
        print("URL이 입력되지 않았습니다.")
