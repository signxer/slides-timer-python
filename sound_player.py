import sys
import subprocess
import threading
import os


class SoundPlayer:
    """跨平台声音播放模块"""

    @staticmethod
    def play(file_path: str):
        """播放声音文件（异步）"""
        if not file_path or not os.path.exists(file_path):
            return
        threading.Thread(target=SoundPlayer._play_sync, args=(file_path,), daemon=True).start()

    @staticmethod
    def _play_sync(file_path: str):
        try:
            if sys.platform == "win32":
                import winsound
                winsound.PlaySound(file_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            elif sys.platform == "darwin":
                subprocess.run(["afplay", file_path], check=False)
            else:
                # Linux: 尝试多种播放器
                ext = os.path.splitext(file_path)[1].lower()
                players = []
                if ext == ".wav":
                    players = [
                        ["aplay", file_path],
                        ["paplay", file_path],
                        ["play", file_path],
                    ]
                else:
                    players = [
                        ["paplay", file_path],
                        ["ffplay", "-nodisp", "-autoexit", file_path],
                        ["aplay", file_path],
                    ]
                for cmd in players:
                    try:
                        subprocess.run(cmd, check=True, capture_output=True)
                        return
                    except (FileNotFoundError, subprocess.CalledProcessError):
                        continue
        except Exception as e:
            print(f"Sound playback error: {e}")
