"""Human Perception & Performance Tester desktop application."""

import csv
import random
import time
import tkinter as tk
import uuid
from tkinter import messagebox, ttk

from data_logger import CSV_COLUMNS, DataLogger
from main_settings import CONTRAST_PALETTES, SIZE_FONTS, shade_color
from screens.identification import IDENTIFICATION_RESPONSES, draw_ambiguous_figure
from screens.target_hitting import TARGET_DIAMETERS, TARGET_DISTANCES, make_target_schedule


WINDOW_TITLE = "Human Perception & Performance Tester"
CANVAS_WIDTH = 1000
CANVAS_HEIGHT = 600
START_CENTER = (150, CANVAS_HEIGHT // 2)
START_RADIUS = 18
START_TOLERANCE = 28
TARGET_TIMEOUT_SECONDS = 30

RATINGS = (
    ("1 - Very difficult", 1),
    ("2 - Difficult", 2),
    ("3 - Neutral", 3),
    ("4 - Easy", 4),
    ("5 - Very easy", 5),
)


class ExperimentApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(WINDOW_TITLE)
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        initial_width = min(1120, max(760, screen_width - 80))
        initial_height = min(900, max(560, screen_height - 120))
        self.geometry("{}x{}".format(initial_width, initial_height))
        self.minsize(min(760, initial_width), min(560, initial_height))
        self.protocol("WM_DELETE_WINDOW", self.close_application)
        self.style = ttk.Style(self)
        self.apply_interface_size("Medium")

        try:
            self.logger = DataLogger()
        except (OSError, ValueError) as error:
            messagebox.showerror("Results file problem", str(error), parent=self)
            self.destroy()
            raise

        self.participant_id = ""
        self.session_id = ""
        self.session_seed = 0
        self.trial_order = 0
        self.current_page = None
        self.active_trial = None
        self.target_rating_row = None
        self.pending_rows = []
        self.last_settings = {"contrast": "High", "size": "Medium", "brightness": 100}

        header = ttk.Frame(self, padding=(16, 10))
        header.pack(fill="x")
        ttk.Label(header, text=WINDOW_TITLE, font=("Segoe UI", 16, "bold")).pack(
            side="left"
        )
        self.retry_button = ttk.Button(
            header, text="Retry unsaved results", command=self.retry_pending
        )
        self.retry_button.pack(side="right")
        self.retry_button.pack_forget()
        page_area = ttk.Frame(self)
        page_area.pack(fill="both", expand=True)
        page_area.grid_rowconfigure(0, weight=1)
        page_area.grid_columnconfigure(0, weight=1)

        self.scroll_canvas = tk.Canvas(
            page_area, borderwidth=0, highlightthickness=0
        )
        vertical_scrollbar = ttk.Scrollbar(
            page_area, orient="vertical", command=self.scroll_canvas.yview
        )
        horizontal_scrollbar = ttk.Scrollbar(
            page_area, orient="horizontal", command=self.scroll_canvas.xview
        )
        self.scroll_canvas.configure(
            yscrollcommand=vertical_scrollbar.set,
            xscrollcommand=horizontal_scrollbar.set,
        )
        self.scroll_canvas.grid(row=0, column=0, sticky="nsew")
        vertical_scrollbar.grid(row=0, column=1, sticky="ns")
        horizontal_scrollbar.grid(row=1, column=0, sticky="ew")
        ttk.Frame(page_area).grid(row=1, column=1)

        self.body = ttk.Frame(self.scroll_canvas, padding=18)
        self.body_window = self.scroll_canvas.create_window(
            (0, 0), window=self.body, anchor="nw"
        )
        self.body.bind("<Configure>", self.update_scroll_region)
        self.scroll_canvas.bind("<Configure>", self.fit_scroll_content)
        self.bind_all("<MouseWheel>", self.scroll_with_mousewheel)
        self.bind_all("<Shift-MouseWheel>", self.scroll_horizontally)
        self.bind_all("<Button-4>", lambda _event: self.scroll_canvas.yview_scroll(-1, "units"))
        self.bind_all("<Button-5>", lambda _event: self.scroll_canvas.yview_scroll(1, "units"))
        self.show_welcome()

    def update_scroll_region(self, _event=None):
        self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))

    def fit_scroll_content(self, event):
        requested_width = self.body.winfo_reqwidth()
        self.scroll_canvas.itemconfigure(
            self.body_window, width=max(event.width, requested_width)
        )
        self.update_scroll_region()

    def scroll_with_mousewheel(self, event):
        if event.delta:
            units = int(-event.delta / 120)
            if units == 0:
                units = -1 if event.delta > 0 else 1
            self.scroll_canvas.yview_scroll(units, "units")
        return "break"

    def scroll_horizontally(self, event):
        if event.delta:
            units = int(-event.delta / 120)
            if units == 0:
                units = -1 if event.delta > 0 else 1
            self.scroll_canvas.xview_scroll(units, "units")
        return "break"

    def clear(self):
        if self.active_trial and self.active_trial.get("timeout_id"):
            self.after_cancel(self.active_trial["timeout_id"])
        self.active_trial = None
        for child in self.body.winfo_children():
            child.destroy()
        self.scroll_canvas.xview_moveto(0)
        self.scroll_canvas.yview_moveto(0)

    def show_welcome(self):
        self.clear()
        self.current_page = "welcome"
        ttk.Label(self.body, text="Explore perception and pointing performance.",
                  font=("Segoe UI", 14)).pack(pady=(90, 12))
        ttk.Label(
            self.body,
            text="Complete an ambiguous-figure task and a target-hitting activity.\n"
                 "Only an anonymous participant ID is collected. Participation is "
                 "voluntary; you may stop at any time.",
            justify="center",
        ).pack(pady=12)
        ttk.Button(self.body, text="Start experiment", command=self.show_participant,
                   width=28).pack(pady=10)
        ttk.Button(self.body, text="Instructions", command=self.show_instructions,
                   width=28).pack(pady=10)
        ttk.Button(self.body, text="Exit", command=self.close_application,
                   width=28).pack(pady=10)

    def show_instructions(self):
        self.clear()
        self.current_page = "instructions"
        ttk.Label(self.body, text="Experiment instructions",
                  font=("Segoe UI", 18, "bold")).pack(anchor="w", pady=(10, 20))
        text = (
            "Identification: view the figure and select what you see. Response "
            "time starts when the figure appears and stops when you submit.\n\n"
            "Target hitting: place the pointer in the start circle and press Space. "
            "Click the target as quickly as you can. Misses count but do not stop "
            "the timer. Each target trial has a 30-second limit.\n\n"
            "After a completed trial, rate its ease from 1 (very difficult) to 5 "
            "(very easy). Press Escape to stop an active trial. Stopped and timed-out "
            "attempts are logged separately and are not counted as completed trials.\n\n"
            "Visual settings may be adjusted between trials. They do not change "
            "physical monitor brightness. All results are stored locally in "
            "data/performance_results.csv."
        )
        ttk.Label(self.body, text=text, wraplength=800, justify="left").pack(
            anchor="w", pady=12
        )
        ttk.Button(self.body, text="Back", command=self.show_welcome).pack(
            anchor="w", pady=18
        )

    def show_participant(self):
        self.clear()
        self.current_page = "participant"
        ttk.Label(self.body, text="Participant identification",
                  font=("Segoe UI", 18, "bold")).pack(anchor="w", pady=12)
        ttk.Label(self.body, text="Enter an anonymous participant ID (for example P001)."
                  ).pack(anchor="w", pady=(8, 4))
        self.id_var = tk.StringVar()
        entry = ttk.Entry(self.body, textvariable=self.id_var, width=32)
        entry.pack(anchor="w", pady=8)
        entry.focus_set()
        entry.bind("<Return>", lambda _event: self.start_session())
        ttk.Button(self.body, text="Continue", command=self.start_session).pack(
            anchor="w", pady=10
        )
        ttk.Button(self.body, text="Back", command=self.show_welcome).pack(
            anchor="w", pady=4
        )

    def start_session(self):
        participant_id = self.id_var.get().strip()
        if not participant_id:
            messagebox.showwarning("Participant ID required",
                                   "Please enter an anonymous participant ID.",
                                   parent=self)
            return
        try:
            with self.logger.path.open("r", newline="", encoding="utf-8-sig") as file:
                existing = any(
                    row.get("participant_id", "").casefold() == participant_id.casefold()
                    for row in csv.DictReader(file)
                )
        except OSError as error:
            messagebox.showerror("Unable to check participant ID", str(error), parent=self)
            return
        if existing and not messagebox.askyesno(
            "Participant ID already exists",
            "This ID has previous records. Start a separate new session?",
            parent=self,
        ):
            return

        self.participant_id = participant_id
        self.session_id = str(uuid.uuid4())
        self.session_seed = random.SystemRandom().randrange(0, 2**32)
        self.trial_order = 0
        self.show_task_menu()

    def show_task_menu(self):
        self.clear()
        self.current_page = "menu"
        ttk.Label(self.body, text="Choose an activity",
                  font=("Segoe UI", 18, "bold")).pack(anchor="w", pady=10)
        ttk.Label(
            self.body,
            text="Participant: {}    Session: {}".format(
                self.participant_id, self.session_id[:8]
            ),
        ).pack(anchor="w", pady=(0, 20))
        ttk.Button(self.body, text="Identification task",
                   command=self.show_identification, width=32).pack(anchor="w", pady=8)
        ttk.Button(self.body, text="Target-hitting task (1 practice + 27 trials)",
                   command=self.begin_target_task, width=42).pack(anchor="w", pady=8)
        ttk.Button(self.body, text="Session results",
                   command=self.show_results, width=32).pack(anchor="w", pady=8)
        ttk.Button(self.body, text="End session / main menu",
                   command=self.show_welcome, width=32).pack(anchor="w", pady=8)

    def settings_panel(self, parent):
        panel = ttk.LabelFrame(parent, text="Visual condition (applies between trials)")
        panel.pack(fill="x", pady=(0, 12))
        controls = []
        vars_ = {
            "contrast": tk.StringVar(value=self.last_settings["contrast"]),
            "size": tk.StringVar(value=self.last_settings["size"]),
            "brightness": tk.IntVar(value=self.last_settings["brightness"]),
        }
        for title, key, values in (
            ("Contrast", "contrast", ("High", "Medium", "Low")),
            ("Interface size", "size", ("Small", "Medium", "Large")),
        ):
            group = ttk.Frame(panel)
            group.pack(side="left", padx=12, pady=6)
            ttk.Label(group, text=title).pack(anchor="w")
            for value in values:
                size_command = (
                    lambda variable=vars_["size"]: self.apply_interface_size(
                        variable.get()
                    )
                ) if key == "size" else None
                control = ttk.Radiobutton(group, text=value, value=value,
                                          variable=vars_[key],
                                          command=size_command)
                control.pack(anchor="w")
                controls.append(control)
        bright = ttk.Frame(panel)
        bright.pack(side="left", padx=16, pady=6)
        ttk.Label(bright, text="Simulated brightness:").pack(anchor="w")
        brightness_scale = ttk.Scale(bright, from_=0, to=100, orient="horizontal",
                                     variable=vars_["brightness"])
        brightness_scale.pack(fill="x")
        controls.append(brightness_scale)
        brightness_label = ttk.Label(bright, text="100%")
        brightness_label.pack(anchor="w")
        vars_["brightness"].trace_add(
            "write", lambda *_: brightness_label.config(
                text="{}%".format(vars_["brightness"].get())
            )
        )
        self.apply_interface_size(vars_["size"].get())
        self.current_visual_controls = controls
        return vars_

    def apply_interface_size(self, size):
        font = ("Segoe UI", SIZE_FONTS[size])
        self.style.configure("TLabel", font=font)
        self.style.configure("TButton", font=font)
        self.style.configure("TRadiobutton", font=font)

    def set_visual_controls_enabled(self, enabled):
        state = "normal" if enabled else "disabled"
        for control in getattr(self, "current_visual_controls", []):
            control.configure(state=state)

    def settings_snapshot(self, vars_):
        values = {
            "contrast": vars_["contrast"].get(),
            "size": vars_["size"].get(),
            "brightness": int(round(vars_["brightness"].get())),
        }
        self.last_settings = values.copy()
        return values

    def make_row(self, task_type, settings, practice=False, **fields):
        self.trial_order += 1
        row = {column: "" for column in CSV_COLUMNS}
        row.update({
            "session_id": self.session_id,
            "random_seed": self.session_seed,
            "trial_id": str(uuid.uuid4()),
            "participant_id": self.participant_id,
            "timestamp_utc": "",
            "trial_order": self.trial_order,
            "is_practice": str(bool(practice)).lower(),
            "outcome": "completed",
            "task_type": task_type,
            "contrast_level": settings["contrast"].lower(),
            "interface_size": settings["size"].lower(),
            "brightness": settings["brightness"],
            "incorrect_clicks": 0 if task_type == "target_hitting" else "",
        })
        row.update(fields)
        return row

    def save_row(self, row):
        if not row["timestamp_utc"]:
            row["timestamp_utc"] = self.logger.timestamp_utc()
        try:
            inserted = self.logger.append(row)
        except (OSError, ValueError) as error:
            self.pending_rows.append(row)
            self.retry_button.pack(side="right")
            messagebox.showerror(
                "Results not saved",
                "{}\n\nThe row is retained in this session. Close the CSV if it is "
                "open, then select 'Retry unsaved results'.".format(error),
                parent=self,
            )
            return False
        self.pending_rows = [
            pending for pending in self.pending_rows
            if pending["trial_id"] != row["trial_id"]
        ]
        if inserted and row["outcome"] == "completed":
            self.session_rows.append(row)
        if not self.pending_rows:
            self.retry_button.pack_forget()
        return True

    def retry_pending(self):
        remaining = []
        for row in self.pending_rows:
            try:
                self.logger.append(row)
                if row["outcome"] == "completed":
                    self.session_rows.append(row)
            except (OSError, ValueError):
                remaining.append(row)
        self.pending_rows = remaining
        if remaining:
            messagebox.showerror(
                "Retry failed",
                "Some records are still unsaved. Close the CSV if it is open and retry.",
                parent=self,
            )
        else:
            self.retry_button.pack_forget()
            messagebox.showinfo("Results saved", "All pending records were saved.",
                                parent=self)

    def show_identification(self):
        self.clear()
        self.current_page = "identification"
        self.session_rows = self.logger.rows_for_session(self.session_id)
        ttk.Label(self.body, text="Identification task",
                  font=("Segoe UI", 18, "bold")).pack(anchor="w", pady=(0, 8))
        settings = self.settings_panel(self.body)
        ttk.Label(
            self.body,
            text="Start the trial to reveal the figure, then select what you see.",
                  font=("Segoe UI", 14)).pack(pady=(0, 8))
        self.figure = tk.Canvas(self.body, width=700, height=330,
                                highlightthickness=1, highlightbackground="#777")
        self.figure.pack(pady=8)
        answer_frame = ttk.Frame(self.body)
        answer_frame.pack(pady=8)
        self.answer_var = tk.StringVar(value="")
        self.answer_controls = []
        for answer in IDENTIFICATION_RESPONSES:
            control = ttk.Radiobutton(
                answer_frame,
                text=answer,
                variable=self.answer_var,
                value=answer,
                command=self.toggle_other,
                state="disabled",
            )
            control.pack(side="left", padx=8)
            self.answer_controls.append(control)
        self.other_var = tk.StringVar()
        self.other_entry = ttk.Entry(self.body, textvariable=self.other_var, width=48)
        self.other_entry.configure(state="disabled")
        self.other_entry.pack(pady=4)
        self.other_entry.pack_forget()
        button_row = ttk.Frame(self.body)
        button_row.pack(pady=10)
        self.submit_answer_button = ttk.Button(
            button_row, text="Show figure and start trial",
            command=lambda: self.start_identification(settings)
        )
        self.submit_answer_button.pack(side="left", padx=5)
        self.ident_back_button = ttk.Button(
            button_row, text="Back to activities", command=self.show_task_menu
        )
        self.ident_back_button.pack(side="left", padx=5)
        self.ident_timer = None
        self.ident_row = None
        self.rating_frame = ttk.Frame(self.body)

    def toggle_other(self):
        if self.answer_var.get() == "Something else":
            self.other_entry.configure(state="normal")
            self.other_entry.pack(pady=4)
        else:
            self.other_entry.pack_forget()

    def start_identification(self, vars_):
        if self.ident_timer is not None:
            return
        self.answer_var.set("")
        self.other_var.set("")
        self.other_entry.configure(state="disabled")
        self.other_entry.pack_forget()
        for control in self.answer_controls:
            control.configure(state="normal")
        settings = self.settings_snapshot(vars_)
        self.set_visual_controls_enabled(False)
        self.ident_back_button.config(state="disabled")
        self.ident_row = self.make_row("identification", settings)
        self.ident_timer = time.perf_counter()
        draw_ambiguous_figure(self.figure, settings)
        self.figure.update_idletasks()
        self.submit_answer_button.config(
            text="Submit answer", command=self.submit_identification
        )
        self.bind("<Escape>", self.abort_active_trial)

    def submit_identification(self):
        answer = self.answer_var.get()
        if not answer:
            messagebox.showwarning("Response required", "Please select an answer.",
                                   parent=self)
            return
        detail = self.other_var.get().strip() if answer == "Something else" else ""
        if answer == "Something else" and not detail:
            messagebox.showwarning("Description required",
                                   "Please describe what you see.", parent=self)
            return
        elapsed = time.perf_counter() - self.ident_timer
        self.ident_row["response"] = answer
        self.ident_row["response_detail"] = detail
        self.ident_row["response_time_seconds"] = "{:.6f}".format(elapsed)
        self.ident_timer = None
        self.submit_answer_button.config(state="disabled")
        self.show_rating(self.ident_row, on_submit=self.finish_identification)

    def finish_identification(self, row, rating):
        row["ease_rating"] = rating
        if not self.save_row(row):
            return
        self.unbind("<Escape>")
        self.show_task_menu()

    def show_rating(self, row, on_submit):
        self.rating_frame.pack(pady=12)
        for child in self.rating_frame.winfo_children():
            child.destroy()
        ttk.Label(self.rating_frame, text="How easy was this task to complete?"
                  ).pack(pady=4)
        rating_var = tk.IntVar(value=0)
        for label, rating in RATINGS:
            ttk.Radiobutton(self.rating_frame, text=label, value=rating,
                            variable=rating_var).pack(side="left", padx=5)

        def submit():
            if rating_var.get() not in range(1, 6):
                messagebox.showwarning("Rating required",
                                       "Please select an ease-of-use rating.",
                                       parent=self)
                return
            on_submit(row, rating_var.get())

        ttk.Button(self.rating_frame, text="Save completed trial",
                   command=submit).pack(pady=8)

    def begin_target_task(self):
        self.target_schedule = make_target_schedule(self.session_seed)
        self.target_index = 0
        self.show_target_trial()

    def show_target_trial(self):
        self.clear()
        self.current_page = "target"
        self.session_rows = self.logger.rows_for_session(self.session_id)
        practice = self.target_schedule[self.target_index][2]
        title = "Target-hitting task - Practice" if practice else (
            "Target-hitting task - Trial {} of 27".format(self.target_index)
        )
        ttk.Label(self.body, text=title, font=("Segoe UI", 18, "bold")).pack(
            anchor="w", pady=(0, 6)
        )
        size, distance, self.is_practice = self.target_schedule[self.target_index]
        ttk.Label(
            self.body,
            text="Move the pointer into the start circle, then press Space. "
                 "Click the target. Escape stops the attempt.",
        ).pack(anchor="w", pady=(0, 8))
        settings = self.settings_panel(self.body)
        ttk.Label(self.body, text="Target: {}    Distance: {}".format(size, distance)
                  ).pack(anchor="w", pady=(0, 6))
        self.target_canvas = tk.Canvas(
            self.body, width=CANVAS_WIDTH, height=CANVAS_HEIGHT,
            background="#f7f7f7", highlightthickness=1, highlightbackground="#777",
        )
        self.target_canvas.pack()
        self.target_canvas.bind("<Button-1>", self.target_click)
        self.target_canvas.focus_set()
        self.target_state = ttk.Label(self.body, text="Place pointer on start circle.")
        self.target_state.pack(anchor="w", pady=6)
        controls = ttk.Frame(self.body)
        controls.pack(anchor="w", pady=4)
        ttk.Button(controls, text="Back to activities",
                   command=self.show_task_menu).pack(side="left", padx=4)
        self.draw_target_work_area(settings)
        for key in ("contrast", "brightness"):
            settings[key].trace_add(
                "write",
                lambda *_args, values=settings: self.draw_target_work_area(values),
            )
        self.active_trial = None
        self.target_rating_row = None
        self.rating_frame = ttk.Frame(self.body)
        self.bind("<space>", self.start_target_from_keyboard)
        self.bind("<Escape>", self.abort_active_trial)
        self.target_back_button = controls.winfo_children()[0]
        self.current_target_settings = settings
        self.current_target_size = size
        self.current_target_distance = distance

    def draw_target_work_area(self, vars_):
        contrast = vars_["contrast"].get()
        bg, fg = CONTRAST_PALETTES[contrast]
        brightness = int(round(vars_["brightness"].get()))
        bg, fg = shade_color(bg, brightness), shade_color(fg, brightness)
        self.target_canvas.configure(background=bg)
        x, y = START_CENTER
        if self.target_canvas.find_withtag("start"):
            self.target_canvas.itemconfigure("start", fill=fg, outline=fg)
            self.target_canvas.itemconfigure("start-label", fill=fg)
        else:
            self.target_canvas.create_oval(
                x - START_RADIUS, y - START_RADIUS,
                x + START_RADIUS, y + START_RADIUS,
                fill=fg, outline=fg, tags="start"
            )
            self.target_canvas.create_text(
                x, y + 34, text="START", fill=fg,
                font=("Segoe UI", 10), tags="start-label"
            )

    def start_target_from_keyboard(self, _event):
        if self.current_page != "target":
            return
        self.begin_target_attempt()
        return "break"

    def begin_target_attempt(self):
        if self.active_trial:
            return
        pointer_x = self.target_canvas.winfo_pointerx() - self.target_canvas.winfo_rootx()
        pointer_y = self.target_canvas.winfo_pointery() - self.target_canvas.winfo_rooty()
        start_x, start_y = START_CENTER
        if ((pointer_x - start_x) ** 2 + (pointer_y - start_y) ** 2
                > START_TOLERANCE ** 2):
            self.target_state.config(
                text="Pointer is not on the start circle. Place it there, then press Space."
            )
            self.target_canvas.focus_set()
            return

        settings = self.settings_snapshot(self.current_target_settings)
        self.set_visual_controls_enabled(False)
        bg, fg = CONTRAST_PALETTES[settings["contrast"]]
        bg = shade_color(bg, settings["brightness"])
        fg = shade_color(fg, settings["brightness"])
        self.target_canvas.configure(background=bg)
        self.target_canvas.itemconfigure("start", fill=fg, outline=fg)
        self.target_canvas.itemconfigure("start-label", fill=fg)
        self.target_back_button.config(state="disabled")
        size, distance = self.current_target_size, self.current_target_distance
        diameter = TARGET_DIAMETERS[size]
        distance_px = TARGET_DISTANCES[distance]
        target_x, target_y = start_x + distance_px, start_y
        started = time.perf_counter()
        self.target_canvas.create_oval(
            target_x - diameter / 2, target_y - diameter / 2,
            target_x + diameter / 2, target_y + diameter / 2,
            fill=shade_color(CONTRAST_PALETTES[settings["contrast"]][1],
                             settings["brightness"]),
            outline=shade_color(CONTRAST_PALETTES[settings["contrast"]][1],
                                settings["brightness"]),
            tags="target",
        )
        self.target_canvas.update_idletasks()
        row = self.make_row(
            "target_hitting", settings, practice=self.is_practice,
            target_size=size.lower(),
            target_diameter_pixels=diameter,
            target_distance=distance.lower(),
            target_distance_pixels=distance_px,
            target_direction="right",
            canvas_width_pixels=CANVAS_WIDTH,
            canvas_height_pixels=CANVAS_HEIGHT,
            incorrect_clicks=0,
        )
        self.active_trial = {
            "row": row,
            "started": started,
            "timeout_id": self.after(TARGET_TIMEOUT_SECONDS * 1000, self.timeout_target),
        }
        self.target_state.config(text="Target visible. Click it as quickly as you can.")
        self.target_canvas.focus_set()

    def target_click(self, event):
        if not self.active_trial:
            return
        target = self.target_canvas.find_withtag("target")
        if not target:
            return
        x1, y1, x2, y2 = self.target_canvas.coords(target[0])
        if x1 <= event.x <= x2 and y1 <= event.y <= y2:
            elapsed = time.perf_counter() - self.active_trial["started"]
            self.after_cancel(self.active_trial["timeout_id"])
            row = self.active_trial["row"]
            row["click_time_seconds"] = "{:.6f}".format(elapsed)
            self.active_trial = None
            self.target_rating_row = row
            self.target_state.config(text="Target acquired. Please rate the task.")
            self.show_rating(row, on_submit=self.finish_target_trial)
        else:
            self.active_trial["row"]["incorrect_clicks"] += 1
            self.target_state.config(
                text="Missed target. Incorrect clicks: {}".format(
                    self.active_trial["row"]["incorrect_clicks"]
                )
            )

    def finish_target_trial(self, row, rating):
        row["ease_rating"] = rating
        if not self.save_row(row):
            return
        self.target_rating_row = None
        self.unbind("<space>")
        self.unbind("<Escape>")
        self.target_index += 1
        if self.target_index == len(self.target_schedule):
            self.show_results()
        else:
            self.show_target_trial()

    def timeout_target(self):
        if not self.active_trial:
            return
        row = self.active_trial["row"]
        row["outcome"] = "timed_out"
        row["attempt_elapsed_seconds"] = "{:.6f}".format(TARGET_TIMEOUT_SECONDS)
        self.active_trial = None
        self.save_row(row)
        self.unbind("<space>")
        self.unbind("<Escape>")
        messagebox.showinfo("Time limit reached",
                            "This attempt timed out and is not counted as completed.",
                            parent=self)
        self.target_index += 1
        if self.target_index >= len(self.target_schedule):
            self.show_results()
        else:
            self.show_target_trial()

    def abort_active_trial(self, _event=None):
        if self.current_page == "identification" and self.ident_timer is not None:
            row = self.ident_row
            row["outcome"] = "aborted"
            row["attempt_elapsed_seconds"] = "{:.6f}".format(
                time.perf_counter() - self.ident_timer
            )
            self.ident_timer = None
            self.save_row(row)
            self.unbind("<Escape>")
            self.show_task_menu()
            return "break"
        if (self.current_page == "identification" and self.ident_row is not None
                and self.ident_timer is None):
            self.ident_row["outcome"] = "aborted"
            self.ident_row["attempt_elapsed_seconds"] = (
                self.ident_row["response_time_seconds"]
            )
            self.save_row(self.ident_row)
            self.ident_row = None
            self.unbind("<Escape>")
            self.show_task_menu()
            return "break"
        if self.current_page == "target" and self.active_trial:
            row = self.active_trial["row"]
            row["outcome"] = "aborted"
            row["attempt_elapsed_seconds"] = "{:.6f}".format(
                time.perf_counter() - self.active_trial["started"]
            )
            self.after_cancel(self.active_trial["timeout_id"])
            self.active_trial = None
            self.save_row(row)
            self.unbind("<space>")
            self.unbind("<Escape>")
            self.target_index += 1
            if self.target_index >= len(self.target_schedule):
                self.show_results()
            else:
                self.show_target_trial()
            return "break"
        if self.current_page == "target" and self.target_rating_row is not None:
            row = self.target_rating_row
            if not row["ease_rating"]:
                row["outcome"] = "aborted"
                row["attempt_elapsed_seconds"] = row["click_time_seconds"]
                self.save_row(row)
                self.target_rating_row = None
                self.target_index += 1
                if self.target_index >= len(self.target_schedule):
                    self.show_results()
                else:
                    self.show_target_trial()
            return "break"

    def show_results(self):
        self.clear()
        self.current_page = "results"
        rows = self.logger.rows_for_session(self.session_id)
        persisted_trial_ids = {row["trial_id"] for row in rows}
        rows.extend(
            row for row in self.pending_rows
            if row["session_id"] == self.session_id
            and row["trial_id"] not in persisted_trial_ids
        )
        complete = [
            row for row in rows
            if row["outcome"] == "completed" and row["is_practice"] != "true"
        ]
        ident = [r for r in complete if r["task_type"] == "identification"]
        target = [r for r in complete if r["task_type"] == "target_hitting"]

        def average(items, column):
            values = [float(row[column]) for row in items if row[column]]
            return "{:.3f}s".format(sum(values) / len(values)) if values else "N/A"

        ratings = [int(row["ease_rating"]) for row in complete if row["ease_rating"]]
        rating_average = "{:.2f} / 5".format(sum(ratings) / len(ratings)) if ratings else "N/A"
        ttk.Label(self.body, text="Session results",
                  font=("Segoe UI", 18, "bold")).pack(anchor="w", pady=8)
        summary = (
            "Participant: {}\nSession: {}\nCompleted identification trials: {}\n"
            "Completed target-hitting trials: {}\nAverage identification response time: {}\n"
            "Average target acquisition time: {}\nAverage ease rating: {}\n\n"
            "Timed-out and aborted attempts are excluded. Results are stored in "
            "data/performance_results.csv.{}"
        ).format(
            self.participant_id, self.session_id[:8], len(ident), len(target),
            average(ident, "response_time_seconds"),
            average(target, "click_time_seconds"), rating_average,
            "\nSome records are not yet saved. Use 'Retry unsaved results' before exiting."
            if any(row["session_id"] == self.session_id for row in self.pending_rows)
            else "",
        )
        ttk.Label(self.body, text=summary, justify="left").pack(anchor="w", pady=14)
        ttk.Button(self.body, text="Repeat an activity",
                   command=self.show_task_menu).pack(anchor="w", pady=6)
        ttk.Button(self.body, text="End session",
                   command=self.show_welcome).pack(anchor="w", pady=6)

    def close_application(self):
        if not messagebox.askyesno(
            "Exit application",
            "Are you sure you want to exit?",
            parent=self,
        ):
            return
        if self.active_trial and self.active_trial.get("timeout_id"):
            row = self.active_trial["row"]
            row["outcome"] = "aborted"
            row["attempt_elapsed_seconds"] = "{:.6f}".format(
                time.perf_counter() - self.active_trial["started"]
            )
            self.after_cancel(self.active_trial["timeout_id"])
            self.active_trial = None
            self.save_row(row)
        if self.current_page == "target" and self.target_rating_row is not None:
            row = self.target_rating_row
            if not row["ease_rating"]:
                row["outcome"] = "aborted"
                row["attempt_elapsed_seconds"] = row["click_time_seconds"]
                self.save_row(row)
            self.target_rating_row = None
        if self.current_page == "identification" and self.ident_row is not None:
            row = self.ident_row
            if self.ident_timer is not None:
                row["outcome"] = "aborted"
                row["attempt_elapsed_seconds"] = "{:.6f}".format(
                    time.perf_counter() - self.ident_timer
                )
                self.ident_timer = None
                self.save_row(row)
            elif row.get("ease_rating", "") == "":
                row["outcome"] = "aborted"
                row["attempt_elapsed_seconds"] = row["response_time_seconds"]
                self.save_row(row)
            self.ident_row = None
        if self.pending_rows and not messagebox.askyesno(
            "Unsaved results",
            "Some results are still unsaved. Exit anyway?",
            parent=self,
        ):
            if self.session_id:
                self.show_task_menu()
            return
        self.destroy()


def main():
    app = ExperimentApp()
    app.mainloop()


if __name__ == "__main__":
    main()
