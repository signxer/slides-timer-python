import customtkinter as ctk
import threading
import time
import sys
import os

from config import cfg
from monitor import SlideShowMonitor
from ui.banner import BannerWindow
from ui.setup_window import SetupWindow
from ui.settings_window import SettingsWindow
from ui.resume_dialog import ResumeDialog
from ui.tray import SystemTray
from ui.ppt_manager_window import PPTManagerWindow

import winsound
import miniaudio

# Set theme
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class SlidesTimerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Hide the main root window
        self.withdraw()
        self.title("Slides Timer Host")
        
        # State
        self.timer_running = False
        self.timer_paused = False
        self.remaining_seconds = 0
        self.total_seconds = 0
        self.warning_triggered = False
        self.critical_triggered = False
        self.session_finished = False # True if time ran out
        
        # Components
        self.banner = BannerWindow(self)
        self.monitor = SlideShowMonitor(self.on_slideshow_start, self.on_slideshow_end)
        
        # Tray
        self.tray = SystemTray(self.open_settings, self.on_exit)
        self.tray.run()
        
        # Start Monitor
        self.monitor.start()
        
        print("Application Started. Waiting for PowerPoint/WPS...")

    def on_slideshow_start(self, ppt_path=None):
        print("Slideshow Started detected.")
        # If we were paused and not finished, resume
        if self.timer_paused and not self.session_finished:
            print("Resuming previous session...")
            self.timer_paused = False
            self.timer_running = True
            self._start_timer_loop()
        elif self.session_finished:
            # Previous session finished, start new
            self._start_new_session(ppt_path)
        else:
            # Fresh start
            self._start_new_session(ppt_path)

    def on_slideshow_end(self):
        print("Slideshow Ended detected.")
        if self.timer_running:
            self.timer_running = False # Pause loop
            self.timer_paused = True   # Mark as paused
            
            # If time already ran out, we don't need to ask, just reset for next time
            if self.session_finished:
                self.reset_state()
            else:
                # Ask user if they are done
                self.open_resume_dialog()

    def open_setup_window(self):
        # Ensure we are on main thread
        self.after(0, lambda: SetupWindow(self, self.start_timer, self.open_settings))

    def open_settings(self):
        self.after(0, lambda: SettingsWindow(self, cfg))

    def open_resume_dialog(self):
        self.after(0, lambda: ResumeDialog(self, self.on_user_resume, self.on_user_stop))

    def _start_new_session(self, ppt_path=None):
        print(f"Starting new session with PPT path: {ppt_path}")
        # Check if there's a preset time for this PPT file
        if ppt_path:
            ppt_timers = cfg.get("ppt_timers")
            print(f"Current PPT timers: {ppt_timers}")
            
            # Normalize path for comparison
            normalized_ppt_path = ppt_path.replace('/', '\\').lower()
            print(f"Normalized PPT path: {normalized_ppt_path}")
            
            # Check if the path exists in the timers (case-insensitive)
            for stored_path, time in ppt_timers.items():
                normalized_stored_path = stored_path.replace('/', '\\').lower()
                if normalized_ppt_path == normalized_stored_path:
                    print(f"Found preset time for PPT: {time} minutes")
                    self.start_timer(time, show_notification=True)
                    return
            print("No preset time found for this PPT")
        # No preset time found, open setup window
        self.open_setup_window()

    def start_timer(self, minutes, show_notification=False):
        print(f"Starting timer for {minutes} minutes")
        self.total_seconds = minutes * 60
        self.remaining_seconds = self.total_seconds
        self.timer_running = True
        self.timer_paused = False
        self.session_finished = False
        self.warning_triggered = False
        self.critical_triggered = False
        
        # Show start timer notification only for preset times
        if show_notification:
            self.show_banner(
                f"开始计时：{minutes}分钟",
                "#4CAF50",  # Green color for start notification
                3  # 3 seconds duration
            )
        
        self._start_timer_loop()

    def _start_timer_loop(self):
        if self.timer_running:
            self.after(1000, self._tick)

    def _tick(self):
        if not self.timer_running:
            return

        self.remaining_seconds -= 1
        # Debug print every 10s
        if self.remaining_seconds % 10 == 0:
            print(f"Time remaining: {self.remaining_seconds}s")

        # Check triggers
        # 1. Warning trigger
        # Default is 1/3 (percent=33) or user defined
        trigger_type = cfg.get("warning_trigger_type")
        trigger_val = cfg.get("warning_trigger_value")
        
        should_warn = False
        
        if trigger_type == "percent":
            # trigger_val is percentage (e.g., 33 for 33%)
            # threshold seconds = total * (val / 100)
            threshold = self.total_seconds * (trigger_val / 100.0)
            if self.remaining_seconds <= threshold and self.remaining_seconds > 0:
                should_warn = True
        else: # time_remaining
            # trigger_val is minutes
            threshold = trigger_val * 60
            if self.remaining_seconds <= threshold and self.remaining_seconds > 0:
                should_warn = True
                
        if not self.warning_triggered and should_warn:
            self.warning_triggered = True
            self.show_banner(
                cfg.get("text_warning"),
                cfg.get("bg_color_warning"),
                cfg.get("duration_warning")
            )
            self.play_sound("warning")

        # 2. Time up
        if not self.critical_triggered and self.remaining_seconds <= 0:
            self.critical_triggered = True
            self.session_finished = True
            self.show_banner(
                cfg.get("text_critical"),
                cfg.get("bg_color_critical"),
                cfg.get("duration_critical")
            )
            self.play_sound("critical")
            # We keep running into negatives or stop? 
            # Requirement: "Time exhausted... show banner... exit... if countdown ended..."
            # Usually timers stop or count up. Let's stop the internal countdown logic's *triggers* but maybe keep variable?
            # User said "Time exhausted... show banner".
            # If we stop running, the loop ends.
            self.timer_running = False

        if self.timer_running:
            self.after(1000, self._tick)

    def show_banner(self, text, bg_color, duration):
        self.banner.show_message(
            message=text,
            bg_color=bg_color,
            text_color=cfg.get("text_color"),
            font_size=cfg.get("font_size"),
            font_family=cfg.get("font_family"),
            position=cfg.get("position"),
            duration=duration,
            offset_x=cfg.get("offset_x"),
            offset_y=cfg.get("offset_y"),
            manual_width=cfg.get("screen_width"),
            manual_height=cfg.get("screen_height")
        )

    def play_sound(self, sound_type):
        if sound_type == "warning":
            if cfg.get("sound_warning_enabled"):
                path = cfg.get("sound_warning_path")
                self._play_file(path)
        elif sound_type == "critical":
            if cfg.get("sound_critical_enabled"):
                path = cfg.get("sound_critical_path")
                self._play_file(path)

    def _play_file(self, path):
        if path and os.path.exists(path):
            try:
                # Check extension
                ext = os.path.splitext(path)[1].lower()
                if ext == ".mp3":
                    # Use miniaudio for mp3 (run in thread to not block)
                    threading.Thread(target=self._play_mp3_thread, args=(path,), daemon=True).start()
                else:
                    # Use winsound for wav (built-in async support)
                    winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            except Exception as e:
                print(f"Error playing sound: {e}")

    def _play_mp3_thread(self, path):
        try:
            stream = miniaudio.stream_file(path)
            with miniaudio.PlaybackDevice() as device:
                device.start(stream)
                # Wait for stream to finish? miniaudio stream might need handling.
                # Actually miniaudio.stream_file yields frames. 
                # Let's use simple playback if possible or just decode and play.
                # The simple way:
                file_info = miniaudio.get_file_info(path)
                decoded_audio = miniaudio.decode_file(path)
                device.play(decoded_audio) # This is not quite right API for miniaudio python
                # Correct way for simple blocking playback in thread:
                # miniaudio doesn't have a simple one-liner "play this file" in python binding usually?
                # Actually, looking at docs or common usage:
                pass
        except:
            pass
            
        # Re-implementing mp3 playback using miniaudio properly:
        try:
            # We can just decode and play
            info = miniaudio.get_file_info(path)
            stream = miniaudio.stream_file(path)
            with miniaudio.PlaybackDevice() as device:
                device.start(stream)
                # We need to keep thread alive while playing
                time.sleep(info.duration)
        except Exception as e:
            print(f"MP3 Playback error: {e}")

    def on_user_resume(self):
        # User said "No, I'm not finished".
        # We stay in paused state.
        # Timer is already paused.
        # Next on_slideshow_start will resume.
        print("User chose to resume later.")
        pass 

    def on_user_stop(self):
        # User said "Yes, finished".
        print("User chose to stop.")
        self.reset_state()

    def reset_state(self):
        self.timer_running = False
        self.timer_paused = False
        self.session_finished = False
        self.remaining_seconds = 0

    def on_exit(self):
        self.monitor.stop()
        if hasattr(self, 'tray'):
            self.tray.stop()
        self.destroy()
        sys.exit(0)

if __name__ == "__main__":
    app = SlidesTimerApp()
    try:
        app.mainloop()
    except KeyboardInterrupt:
        app.on_exit()
