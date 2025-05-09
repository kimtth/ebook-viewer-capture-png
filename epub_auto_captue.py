import os
from tkinter import *
from tkinter import ttk, filedialog, messagebox
import pyautogui
import mss
import mss.tools
import time
import numpy as np
import random
import string


class EbookAutoCapture:
    def __init__(self, root):
        # Coordinates for capture region
        self.x1 = self.y1 = self.x2 = self.y2 = 0

        # UI variables
        self.pos_display1 = StringVar(value="[0,0]")
        self.pos_display2 = StringVar(value="[0,0]")
        self.current_page = IntVar(value=0)

        self.total_pages = IntVar()
        self.file_name = StringVar(value="page")
        self.save_path = StringVar()

        self.capture_interval = IntVar(value=1000)  # ms
        self.auto_detect = IntVar(value=1)  # 0: off, 1: on
        self.sensitivity = IntVar(value=5)  # percent change threshold
        self.next_page_method = IntVar(value=0)  # 0: key, 1: click

        self.progress = DoubleVar(value=0.0)

        # Store current capture job reference
        self.current_capture = None

        # Window setup
        root.title("Ebook Auto Capture")
        root.resizable(False, False)

        frame = ttk.Frame(root, padding=10)
        frame.grid()

        # Program description
        ttk.Label(
            frame, text="Ebook Auto Capture: Automatically capture and save ebook pages"
        ).grid(column=0, row=0, columnspan=4, sticky=W)
        ttk.Label(
            frame, text="Click 'Set Coordinates' then press SPACE to record position"
        ).grid(column=0, row=1, columnspan=4, sticky=W)

        # Coordinate inputs
        ttk.Label(frame, text="Top-left corner:").grid(column=0, row=2, sticky=W)
        ttk.Label(frame, textvariable=self.pos_display1, width=12).grid(column=1, row=2)
        ttk.Button(frame, text="Set Coordinates", command=self.bind_left_coord).grid(
            column=2, row=2
        )

        ttk.Label(frame, text="Bottom-right corner:").grid(column=0, row=3, sticky=W)
        ttk.Label(frame, textvariable=self.pos_display2, width=12).grid(column=1, row=3)
        ttk.Button(frame, text="Set Coordinates", command=self.bind_right_coord).grid(
            column=2, row=3
        )

        # Pages, current page, and filename
        ttk.Label(frame, text="Total pages:").grid(column=0, row=4, sticky=W)
        ttk.Entry(frame, width=8, textvariable=self.total_pages).grid(column=1, row=4)
        ttk.Label(frame, text="Current page:").grid(column=2, row=4, sticky=W)
        ttk.Label(frame, textvariable=self.current_page, width=4).grid(column=3, row=4)

        ttk.Label(frame, text="File name:").grid(column=0, row=5, sticky=W)
        ttk.Entry(frame, width=12, textvariable=self.file_name).grid(
            column=1, row=5, columnspan=3, sticky=(W, E)
        )

        # Capture interval and auto-detect
        ttk.Label(frame, text="Capture interval (ms):").grid(column=0, row=6, sticky=W)
        ttk.Label(frame, textvariable=self.capture_interval, width=4).grid(
            column=1, row=6
        )
        ttk.Scale(
            frame,
            from_=1,
            to=2000,
            orient=HORIZONTAL,
            variable=self.capture_interval,
            command=lambda e: self.capture_interval.set(
                round(self.capture_interval.get())
            ),
        ).grid(column=2, row=6, columnspan=2, sticky=(W, E))

        ttk.Checkbutton(
            frame, text="Enable auto-detect", variable=self.auto_detect
        ).grid(column=0, row=7, columnspan=4, sticky=W)
        ttk.Label(frame, text="Sensitivity (% changed pixels):").grid(
            column=0, row=8, sticky=W
        )
        ttk.Scale(
            frame,
            from_=1,
            to=100,
            orient=HORIZONTAL,
            variable=self.sensitivity,
            command=lambda e: self.sensitivity.set(round(self.sensitivity.get())),
        ).grid(column=1, row=8, columnspan=2, sticky=(W, E))
        ttk.Label(frame, textvariable=self.sensitivity, width=4).grid(column=3, row=8)

        # Next page method
        ttk.Label(frame, text="Go to next page via:").grid(column=0, row=9, sticky=W)
        ttk.Radiobutton(
            frame, text="Keyboard Right Arrow", variable=self.next_page_method, value=0
        ).grid(column=1, row=9)
        ttk.Radiobutton(
            frame, text="Mouse Click", variable=self.next_page_method, value=1
        ).grid(column=2, row=9)

        # Progress bar
        ttk.Progressbar(
            frame,
            orient=HORIZONTAL,
            length=200,
            mode="determinate",
            maximum=100,
            variable=self.progress,
        ).grid(column=0, row=10, columnspan=4, pady=5)

        # Control buttons
        ttk.Button(frame, text="Set Save Path", command=self.choose_directory).grid(
            column=0, row=11, columnspan=2, sticky=(W, E)
        )
        ttk.Button(frame, text="Start Capture", command=self.start_capture).grid(
            column=2, row=11, sticky=(W, E)
        )
        ttk.Button(frame, text="Stop Capture", command=self.stop_capture).grid(
            column=3, row=11, sticky=(W, E)
        )

        for child in frame.winfo_children():
            child.grid_configure(padx=5, pady=5)

    def bind_left_coord(self, *args):
        root.bind("<Key-space>", lambda e: self.record_coord(e, True))
        root.focus_set()

    def bind_right_coord(self, *args):
        root.bind("<Key-space>", lambda e: self.record_coord(e, False))
        root.focus_set()

    def record_coord(self, event, is_left):
        x, y = pyautogui.position()
        if is_left:
            self.x1, self.y1 = x, y
            self.pos_display1.set(f"[{x},{y}]")
        else:
            self.x2, self.y2 = x, y
            self.pos_display2.set(f"[{x},{y}]")

    def choose_directory(self):
        path = filedialog.askdirectory()
        if path:
            self.save_path.set(path)

    def start_capture(self):
        if self.current_capture and self.current_capture.running:
            return  # already running
        name = self.file_name.get() or "".join(
            random.choices(string.ascii_letters + string.digits, k=4)
        )
        self.current_capture = Capture(
            region=(self.x1, self.y1, self.x2 - self.x1, self.y2 - self.y1),
            pages=self.total_pages.get(),
            name=name,
            save_dir=self.save_path.get(),
            interval_ms=self.capture_interval.get(),
            auto_detect=bool(self.auto_detect.get()),
            sensitivity=self.sensitivity.get(),
            move_method=self.next_page_method.get(),
            progress_var=self.progress,
            current_page_var=self.current_page,
        )
        self.current_capture.running = True
        root.after(1000, self.current_capture.process)

    def stop_capture(self):
        if self.current_capture:
            self.current_capture.running = False
            self.progress.set(0)
            self.current_page.set(1)
            print("Capture stopped by user.")


class Capture:
    def __init__(
        self,
        region,
        pages,
        name,
        save_dir,
        interval_ms,
        auto_detect,
        sensitivity,
        move_method,
        progress_var,
        current_page_var,
    ):
        self.region = region
        self.pages = pages
        self.name = name
        self.save_dir = save_dir.replace("/", "\\")
        self.interval = interval_ms / 1000.0
        self.auto_detect = auto_detect
        self.sensitivity = sensitivity / 100.0
        self.move_method = move_method
        self.progress = progress_var
        self.current_page = current_page_var
        self.count = 1
        self.last_snapshot = None
        self.running = False

    def process(self):
        if not self.running:
            return
        if self.count == 1:
            self.current_page.set(1)
            self.capture()

        if self.count < self.pages and self.running:
            self.progress.set((self.count / self.pages) * 100)
            self.go_to_next_page()

            if self.auto_detect:
                self.wait_for_screen_change()

            time.sleep(self.interval)
            self.count += 1
            self.current_page.set(self.count)
            self.capture()
            root.after(100, self.process)
        else:
            self.progress.set(100)
            self.running = False
            print("All tasks completed.")
            messagebox.showinfo("Done", "All pages have been captured successfully!")

    def capture(self):
        if not self.running:
            return
        filename = f"{self.name}_{self.count}.png"
        # Ensure save path is valid
        if not os.path.isdir(self.save_dir):
            print(f"Invalid save directory: {self.save_dir}")
            return

        full_path = os.path.join(self.save_dir, filename)
        with mss.mss() as sct:
            monitor = {
                "top": self.region[1],
                "left": self.region[0],
                "width": self.region[2],
                "height": self.region[3],
            }
            shot = sct.grab(monitor)
            mss.tools.to_png(shot.rgb, shot.size, output=full_path)
            self.last_snapshot = np.frombuffer(shot.rgb, dtype=np.uint8)
        print(f"Captured: {full_path}")

    def go_to_next_page(self):
        if not self.running:
            return
        if self.move_method == 0:
            pyautogui.press("right")
        else:
            pyautogui.click()
        print("Moved to next page.")

    def wait_for_screen_change(self, timeout=10):
        start = time.time()
        with mss.mss() as sct:
            while time.time() - start < timeout and self.running:
                shot = sct.grab(
                    {
                        "top": self.region[1],
                        "left": self.region[0],
                        "width": self.region[2],
                        "height": self.region[3],
                    }
                )
                current = np.frombuffer(shot.rgb, dtype=np.uint8)
                diff = np.abs(current.astype(int) - self.last_snapshot.astype(int))
                changed = np.count_nonzero(diff > 0)
                total = self.region[2] * self.region[3] * 3
                if changed / total >= self.sensitivity:
                    print("Detected screen change.")
                    break
                time.sleep(0.2)


if __name__ == "__main__":
    root = Tk()
    app = EbookAutoCapture(root)
    root.mainloop()
