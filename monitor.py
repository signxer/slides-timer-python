import time
import threading
import pythoncom
import win32com.client

class SlideShowMonitor:
    def __init__(self, on_start_callback, on_end_callback):
        self.on_start = on_start_callback
        self.on_end = on_end_callback
        self.running = False
        self.is_slideshow_active = False
        self.current_ppt_path = None
        self.thread = None
        self._stop_event = threading.Event()

    def start(self):
        if not self.running:
            self.running = True
            self._stop_event.clear()
            self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.thread.start()

    def stop(self):
        self.running = False
        self._stop_event.set()
        if self.thread:
            self.thread.join()

    def _check_app(self, app_name):
        try:
            # try GetActiveObject first to avoid launching the app if it's not running
            app = win32com.client.GetActiveObject(app_name)
            # Check if there are any slideshow windows
            if app.SlideShowWindows.Count > 0:
                # Get the current presentation path
                try:
                    # For PowerPoint, try to get the active presentation
                    if app_name == "PowerPoint.Application" and hasattr(app, 'ActivePresentation'):
                        active_presentation = app.ActivePresentation
                        if active_presentation and hasattr(active_presentation, 'FullName'):
                            return True, active_presentation.FullName
                    # For WPS, try to get the presentation associated with the active slideshow window
                    elif app.SlideShowWindows.Count > 0:
                        slideshow_window = app.SlideShowWindows(1)
                        if hasattr(slideshow_window, 'Presentation'):
                            presentation = slideshow_window.Presentation
                            if hasattr(presentation, 'FullName'):
                                return True, presentation.FullName
                    # Fallback: get the first presentation
                    elif app.Presentations.Count > 0:
                        presentation = app.Presentations(1)
                        if hasattr(presentation, 'FullName'):
                            return True, presentation.FullName
                except Exception as e:
                    print(f"Error getting presentation path: {e}")
                return True, None
        except Exception as e:
            # App not running or COM error
            print(f"Error checking app {app_name}: {e}")
            pass
        return False, None

    def _monitor_loop(self):
        pythoncom.CoInitialize()
        try:
            while not self._stop_event.is_set():
                active = False
                ppt_path = None
                
                # Check Microsoft PowerPoint
                powerpoint_active, powerpoint_path = self._check_app("PowerPoint.Application")
                if powerpoint_active:
                    active = True
                    ppt_path = powerpoint_path
                # Check WPS Presentation (Kwpp usually refers to WPS Presentation)
                elif self._check_app("Kwpp.Application")[0]:
                    active = True
                    # Try to get WPS presentation path
                    try:
                        app = win32com.client.GetActiveObject("Kwpp.Application")
                        if app.Presentations.Count > 0:
                            presentation = app.Presentations(1)
                            if hasattr(presentation, 'FullName'):
                                ppt_path = presentation.FullName
                    except Exception:
                        pass
                # Fallback for some WPS versions
                elif self._check_app("WPS.Application")[0]:
                    active = True
                    # Try to get WPS presentation path
                    try:
                        app = win32com.client.GetActiveObject("WPS.Application")
                        if app.Presentations.Count > 0:
                            presentation = app.Presentations(1)
                            if hasattr(presentation, 'FullName'):
                                ppt_path = presentation.FullName
                    except Exception:
                        pass

                # Check if PPT path has changed
                ppt_path_changed = ppt_path != self.current_ppt_path
                
                if active and not self.is_slideshow_active:
                    self.is_slideshow_active = True
                    self.current_ppt_path = ppt_path
                    if self.on_start:
                        self.on_start(ppt_path)
                elif not active and self.is_slideshow_active:
                    self.is_slideshow_active = False
                    self.current_ppt_path = None
                    if self.on_end:
                        self.on_end()
                elif active and self.is_slideshow_active and ppt_path_changed:
                    # PPT file changed while slideshow is active
                    self.current_ppt_path = ppt_path
                    if self.on_start:
                        self.on_start(ppt_path)

                time.sleep(1) 
        finally:
            pythoncom.CoUninitialize()

if __name__ == "__main__":
    def start(): print("SlideShow Started")
    def end(): print("SlideShow Ended")
    
    mon = SlideShowMonitor(start, end)
    mon.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        mon.stop()
