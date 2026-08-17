import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import pandas as pd
import webbrowser
from datetime import datetime
from pathlib import Path

# Plotly is used for attractive interactive HR charts.
# Install with: pip install pandas plotly

try:
    import plotly.express as px
except ImportError:
    px = None


DB_NAME = "recruitment_hr.db"
REPORT_DIR = Path("reports")
REPORT_DIR.mkdir(exist_ok=True)


# ============================================================
# DATABASE
# ============================================================

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_database():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            department TEXT NOT NULL,
            skills TEXT,
            experience TEXT,
            vacancies INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'Open',
            created_date TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            qualification TEXT,
            skills TEXT,
            experience TEXT,
            created_date TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER NOT NULL,
            job_id INTEGER NOT NULL,
            application_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Applied',
            FOREIGN KEY(candidate_id) REFERENCES candidates(id) ON DELETE CASCADE,
            FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS interviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id INTEGER NOT NULL,
            interview_date TEXT NOT NULL,
            interview_time TEXT NOT NULL,
            interviewer TEXT NOT NULL,
            result TEXT NOT NULL DEFAULT 'Pending',
            FOREIGN KEY(application_id) REFERENCES applications(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()


# ============================================================
# MAIN APPLICATION
# ============================================================

class RecruitmentPortal:
    NAVY = "#172554"
    BLUE = "#2563eb"
    LIGHT_BLUE = "#eff6ff"
    BG = "#f5f7fb"
    WHITE = "#ffffff"
    TEXT = "#111827"
    MUTED = "#6b7280"
    GREEN = "#16a34a"
    ORANGE = "#ea580c"
    RED = "#dc2626"
    PURPLE = "#7c3aed"
    BORDER = "#e5e7eb"

    def __init__(self, root):
        self.root = root
        self.root.title("Recruitment & HR Analytics Portal")
        self.root.geometry("1400x820")
        self.root.minsize(1150, 700)
        self.root.configure(bg=self.BG)

        self.setup_styles()
        self.build_layout()
        self.refresh_everything()

    # ========================================================
    # STYLES
    # ========================================================

    def setup_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Treeview",
            background=self.WHITE,
            foreground=self.TEXT,
            rowheight=34,
            fieldbackground=self.WHITE,
            borderwidth=0,
            font=("Segoe UI", 10)
        )
        style.configure(
            "Treeview.Heading",
            background=self.NAVY,
            foreground=self.WHITE,
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            padding=8
        )
        style.map(
            "Treeview",
            background=[("selected", "#dbeafe")],
            foreground=[("selected", self.TEXT)]
        )
        style.configure(
            "TNotebook",
            background=self.BG,
            borderwidth=0
        )
        style.configure(
            "TNotebook.Tab",
            padding=(18, 10),
            font=("Segoe UI", 10, "bold")
        )
        style.configure(
            "TCombobox",
            padding=7
        )

    # ========================================================
    # LAYOUT
    # ========================================================

    def build_layout(self):
        self.sidebar = tk.Frame(self.root, bg=self.NAVY, width=235)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.main = tk.Frame(self.root, bg=self.BG)
        self.main.pack(side="right", fill="both", expand=True)

        self.build_sidebar()
        self.build_topbar()
        self.build_notebook()

    def build_sidebar(self):
        logo = tk.Frame(self.sidebar, bg=self.NAVY)
        logo.pack(fill="x", padx=20, pady=(25, 30))

        tk.Label(
            logo,
            text="HR",
            bg=self.BLUE,
            fg=self.WHITE,
            font=("Segoe UI", 22, "bold"),
            width=3,
            height=1
        ).pack(side="left")

        text = tk.Frame(logo, bg=self.NAVY)
        text.pack(side="left", padx=10)

        tk.Label(
            text,
            text="Recruitment",
            bg=self.NAVY,
            fg=self.WHITE,
            font=("Segoe UI", 12, "bold")
        ).pack(anchor="w")

        tk.Label(
            text,
            text="Analytics Portal",
            bg=self.NAVY,
            fg="#bfdbfe",
            font=("Segoe UI", 9)
        ).pack(anchor="w")

        nav_items = [
            ("Dashboard", 0),
            ("Jobs", 1),
            ("Candidates", 2),
            ("Applications", 3),
            ("Interviews", 4),
            ("HR Analytics", 5),
        ]

        for label, index in nav_items:
            btn = tk.Button(
                self.sidebar,
                text="  " + label,
                anchor="w",
                bg=self.NAVY,
                fg="#dbeafe",
                activebackground="#1e3a8a",
                activeforeground=self.WHITE,
                bd=0,
                relief="flat",
                font=("Segoe UI", 10, "bold"),
                padx=18,
                pady=12,
                cursor="hand2",
                command=lambda i=index: self.notebook.select(i)
            )
            btn.pack(fill="x", padx=10, pady=2)

        footer = tk.Frame(self.sidebar, bg=self.NAVY)
        footer.pack(side="bottom", fill="x", padx=20, pady=25)

        tk.Label(
            footer,
            text="PROJECT",
            bg=self.NAVY,
            fg="#93c5fd",
            font=("Segoe UI", 8, "bold")
        ).pack(anchor="w")

        tk.Label(
            footer,
            text="USN: CM25078",
            bg=self.NAVY,
            fg=self.WHITE,
            font=("Segoe UI", 9)
        ).pack(anchor="w", pady=(3, 0))

        tk.Label(
            footer,
            text="Serial No: 43",
            bg=self.NAVY,
            fg="#bfdbfe",
            font=("Segoe UI", 9)
        ).pack(anchor="w")

    def build_topbar(self):
        top = tk.Frame(self.main, bg=self.WHITE, height=72)
        top.pack(fill="x")
        top.pack_propagate(False)

        left = tk.Frame(top, bg=self.WHITE)
        left.pack(side="left", padx=28)

        tk.Label(
            left,
            text="Recruitment & HR Analytics Portal",
            bg=self.WHITE,
            fg=self.TEXT,
            font=("Segoe UI", 16, "bold")
        ).pack(anchor="w", pady=(14, 0))

        tk.Label(
            left,
            text="Manage hiring • track candidates • analyze recruitment",
            bg=self.WHITE,
            fg=self.MUTED,
            font=("Segoe UI", 9)
        ).pack(anchor="w")

        right = tk.Frame(top, bg=self.WHITE)
        right.pack(side="right", padx=25)

        tk.Label(
            right,
            text=datetime.now().strftime("%d %b %Y"),
            bg=self.WHITE,
            fg=self.MUTED,
            font=("Segoe UI", 9)
        ).pack(pady=25)

    def build_notebook(self):
        self.notebook = ttk.Notebook(self.main)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=20)

        self.tabs = [
            tk.Frame(self.notebook, bg=self.BG),
            tk.Frame(self.notebook, bg=self.BG),
            tk.Frame(self.notebook, bg=self.BG),
            tk.Frame(self.notebook, bg=self.BG),
            tk.Frame(self.notebook, bg=self.BG),
            tk.Frame(self.notebook, bg=self.BG),
        ]

        names = [
            "Dashboard",
            "Jobs",
            "Candidates",
            "Applications",
            "Interviews",
            "HR Analytics"
        ]

        for tab, name in zip(self.tabs, names):
            self.notebook.add(tab, text=name)

        self.build_dashboard()
        self.build_jobs()
        self.build_candidates()
        self.build_applications()
        self.build_interviews()
        self.build_analytics()

    # ========================================================
    # COMMON UI HELPERS
    # ========================================================

    def section_title(self, parent, title, subtitle=""):
        frame = tk.Frame(parent, bg=self.BG)
        frame.pack(fill="x", pady=(5, 15))

        tk.Label(
            frame,
            text=title,
            bg=self.BG,
            fg=self.TEXT,
            font=("Segoe UI", 20, "bold")
        ).pack(anchor="w")

        if subtitle:
            tk.Label(
                frame,
                text=subtitle,
                bg=self.BG,
                fg=self.MUTED,
                font=("Segoe UI", 9)
            ).pack(anchor="w", pady=(2, 0))

    def card(self, parent, title, value, color):
        frame = tk.Frame(
            parent,
            bg=self.WHITE,
            highlightbackground=self.BORDER,
            highlightthickness=1
        )
        frame.pack(side="left", fill="both", expand=True, padx=6)

        tk.Frame(frame, bg=color, width=5).pack(side="left", fill="y")

        body = tk.Frame(frame, bg=self.WHITE)
        body.pack(fill="both", expand=True, padx=16, pady=14)

        tk.Label(
            body,
            text=title,
            bg=self.WHITE,
            fg=self.MUTED,
            font=("Segoe UI", 9, "bold")
        ).pack(anchor="w")

        value_label = tk.Label(
            body,
            text=str(value),
            bg=self.WHITE,
            fg=self.TEXT,
            font=("Segoe UI", 23, "bold")
        )
        value_label.pack(anchor="w", pady=(5, 0))

        return value_label

    def labeled_entry(self, parent, label, row, column, width=27):
        box = tk.Frame(parent, bg=self.WHITE)
        box.grid(row=row, column=column, padx=12, pady=8, sticky="ew")

        tk.Label(
            box,
            text=label,
            bg=self.WHITE,
            fg=self.MUTED,
            font=("Segoe UI", 9, "bold")
        ).pack(anchor="w")

        entry = tk.Entry(
            box,
            width=width,
            bg="#f9fafb",
            fg=self.TEXT,
            relief="solid",
            bd=1,
            highlightthickness=0,
            font=("Segoe UI", 10)
        )
        entry.pack(fill="x", pady=(4, 0), ipady=6)

        return entry

    def create_tree(self, parent, columns, widths=None):
        wrapper = tk.Frame(parent, bg=self.WHITE)
        wrapper.pack(fill="both", expand=True, pady=(10, 0))

        tree = ttk.Treeview(
            wrapper,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        for i, col in enumerate(columns):
            width = widths[i] if widths else 130
            tree.heading(col, text=col)
            tree.column(col, width=width, anchor="center")

        yscroll = ttk.Scrollbar(
            wrapper,
            orient="vertical",
            command=tree.yview
        )
        xscroll = ttk.Scrollbar(
            wrapper,
            orient="horizontal",
            command=tree.xview
        )

        tree.configure(
            yscrollcommand=yscroll.set,
            xscrollcommand=xscroll.set
        )

        tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")

        wrapper.grid_rowconfigure(0, weight=1)
        wrapper.grid_columnconfigure(0, weight=1)

        return tree

    def primary_button(self, parent, text, command):
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=self.BLUE,
            fg=self.WHITE,
            activebackground="#1d4ed8",
            activeforeground=self.WHITE,
            relief="flat",
            bd=0,
            padx=18,
            pady=9,
            font=("Segoe UI", 9, "bold"),
            cursor="hand2"
        )

    def clear(self, *widgets):
        for widget in widgets:
            if isinstance(widget, ttk.Combobox):
                widget.set("")
            else:
                widget.delete(0, tk.END)

    # ========================================================
    # DASHBOARD
    # ========================================================

    def build_dashboard(self):
        tab = self.tabs[0]

        self.section_title(
            tab,
            "Dashboard",
            "A quick overview of your recruitment pipeline"
        )

        cards = tk.Frame(tab, bg=self.BG)
        cards.pack(fill="x")

        self.stat_jobs = self.card(cards, "TOTAL JOBS", 0, self.BLUE)
        self.stat_open = self.card(cards, "OPEN JOBS", 0, self.GREEN)
        self.stat_candidates = self.card(cards, "CANDIDATES", 0, self.PURPLE)
        self.stat_applications = self.card(cards, "APPLICATIONS", 0, self.ORANGE)
        self.stat_selected = self.card(cards, "SELECTED", 0, self.GREEN)

        lower = tk.Frame(tab, bg=self.BG)
        lower.pack(fill="both", expand=True, pady=20)

        left = tk.Frame(
            lower,
            bg=self.WHITE,
            highlightbackground=self.BORDER,
            highlightthickness=1
        )
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))

        tk.Label(
            left,
            text="Recruitment Pipeline",
            bg=self.WHITE,
            fg=self.TEXT,
            font=("Segoe UI", 13, "bold")
        ).pack(anchor="w", padx=20, pady=(20, 5))

        tk.Label(
            left,
            text="Track candidates from application to final decision.",
            bg=self.WHITE,
            fg=self.MUTED,
            font=("Segoe UI", 9)
        ).pack(anchor="w", padx=20)

        self.pipeline_text = tk.Text(
            left,
            height=10,
            bg=self.WHITE,
            fg=self.TEXT,
            relief="flat",
            font=("Segoe UI", 11),
            padx=20,
            pady=20
        )
        self.pipeline_text.pack(fill="both", expand=True)

        right = tk.Frame(
            lower,
            bg=self.WHITE,
            highlightbackground=self.BORDER,
            highlightthickness=1
        )
        right.pack(side="right", fill="both", expand=True, padx=(8, 0))

        tk.Label(
            right,
            text="Project Workflow",
            bg=self.WHITE,
            fg=self.TEXT,
            font=("Segoe UI", 13, "bold")
        ).pack(anchor="w", padx=20, pady=(20, 10))

        steps = [
            ("01", "Create Job", "Add company vacancies and requirements."),
            ("02", "Add Candidate", "Store candidate profile and skills."),
            ("03", "Track Application", "Move candidates through recruitment stages."),
            ("04", "Schedule Interview", "Maintain interview dates and interviewers."),
            ("05", "Analyze", "Use Pandas + Plotly to generate HR insights.")
        ]

        for num, title, desc in steps:
            row = tk.Frame(right, bg=self.WHITE)
            row.pack(fill="x", padx=20, pady=7)

            tk.Label(
                row,
                text=num,
                bg=self.LIGHT_BLUE,
                fg=self.BLUE,
                font=("Segoe UI", 9, "bold"),
                width=4
            ).pack(side="left", padx=(0, 10), ipady=5)

            info = tk.Frame(row, bg=self.WHITE)
            info.pack(side="left", fill="x", expand=True)

            tk.Label(
                info,
                text=title,
                bg=self.WHITE,
                fg=self.TEXT,
                font=("Segoe UI", 10, "bold")
            ).pack(anchor="w")

            tk.Label(
                info,
                text=desc,
                bg=self.WHITE,
                fg=self.MUTED,
                font=("Segoe UI", 8)
            ).pack(anchor="w")

    # ========================================================
    # JOBS
    # ========================================================

    def build_jobs(self):
        tab = self.tabs[1]

        self.section_title(
            tab,
            "Job Management",
            "Create and monitor open positions"
        )

        form = tk.Frame(
            tab,
            bg=self.WHITE,
            highlightbackground=self.BORDER,
            highlightthickness=1
        )
        form.pack(fill="x", pady=(0, 10))

        self.job_title = self.labeled_entry(form, "Job Title", 0, 0)
        self.job_department = self.labeled_entry(form, "Department", 0, 1)
        self.job_skills = self.labeled_entry(form, "Required Skills", 0, 2)
        self.job_experience = self.labeled_entry(form, "Experience", 1, 0)
        self.job_vacancies = self.labeled_entry(form, "Vacancies", 1, 1)

        button_box = tk.Frame(form, bg=self.WHITE)
        button_box.grid(row=1, column=2, padx=12, pady=15, sticky="e")

        self.primary_button(
            button_box,
            "＋  Add Job",
            self.add_job
        ).pack(side="left")

        self.job_tree = self.create_tree(
            tab,
            ("ID", "Job Title", "Department", "Skills", "Experience", "Vacancies", "Status"),
            [60, 180, 130, 230, 120, 90, 90]
        )

    # ========================================================
    # CANDIDATES
    # ========================================================

    def build_candidates(self):
        tab = self.tabs[2]

        self.section_title(
            tab,
            "Candidate Management",
            "Maintain candidate profiles and skills"
        )

        form = tk.Frame(
            tab,
            bg=self.WHITE,
            highlightbackground=self.BORDER,
            highlightthickness=1
        )
        form.pack(fill="x", pady=(0, 10))

        self.candidate_name = self.labeled_entry(form, "Full Name", 0, 0)
        self.candidate_email = self.labeled_entry(form, "Email", 0, 1)
        self.candidate_phone = self.labeled_entry(form, "Phone", 0, 2)
        self.candidate_qualification = self.labeled_entry(form, "Qualification", 1, 0)
        self.candidate_skills = self.labeled_entry(form, "Skills", 1, 1)
        self.candidate_experience = self.labeled_entry(form, "Experience", 1, 2)

        self.primary_button(
            form,
            "＋  Add Candidate",
            self.add_candidate
        ).grid(row=2, column=2, padx=12, pady=15, sticky="e")

        self.candidate_tree = self.create_tree(
            tab,
            ("ID", "Name", "Email", "Phone", "Qualification", "Skills", "Experience"),
            [55, 160, 200, 120, 130, 220, 120]
        )

    # ========================================================
    # APPLICATIONS
    # ========================================================

    def build_applications(self):
        tab = self.tabs[3]

        self.section_title(
            tab,
            "Application Tracking",
            "Track each candidate through the recruitment pipeline"
        )

        form = tk.Frame(
            tab,
            bg=self.WHITE,
            highlightbackground=self.BORDER,
            highlightthickness=1
        )
        form.pack(fill="x", pady=(0, 10))

        tk.Label(
            form,
            text="Candidate",
            bg=self.WHITE,
            fg=self.MUTED,
            font=("Segoe UI", 9, "bold")
        ).grid(row=0, column=0, padx=12, pady=(12, 2), sticky="w")

        self.application_candidate = ttk.Combobox(
            form,
            state="readonly",
            width=28
        )
        self.application_candidate.grid(row=1, column=0, padx=12, pady=(0, 12))

        tk.Label(
            form,
            text="Job",
            bg=self.WHITE,
            fg=self.MUTED,
            font=("Segoe UI", 9, "bold")
        ).grid(row=0, column=1, padx=12, pady=(12, 2), sticky="w")

        self.application_job = ttk.Combobox(
            form,
            state="readonly",
            width=28
        )
        self.application_job.grid(row=1, column=1, padx=12, pady=(0, 12))

        self.primary_button(
            form,
            "＋  Create Application",
            self.add_application
        ).grid(row=1, column=2, padx=12, pady=(0, 12))

        tk.Label(
            form,
            text="Application ID",
            bg=self.WHITE,
            fg=self.MUTED,
            font=("Segoe UI", 9, "bold")
        ).grid(row=0, column=3, padx=12, pady=(12, 2), sticky="w")

        self.application_id_entry = tk.Entry(
            form,
            width=14,
            bg="#f9fafb",
            relief="solid",
            bd=1
        )
        self.application_id_entry.grid(row=1, column=3, padx=12, pady=(0, 12), ipady=6)

        tk.Label(
            form,
            text="New Status",
            bg=self.WHITE,
            fg=self.MUTED,
            font=("Segoe UI", 9, "bold")
        ).grid(row=0, column=4, padx=12, pady=(12, 2), sticky="w")

        self.application_status = ttk.Combobox(
            form,
            values=["Applied", "Shortlisted", "Interview", "Selected", "Rejected"],
            state="readonly",
            width=17
        )
        self.application_status.set("Shortlisted")
        self.application_status.grid(row=1, column=4, padx=12, pady=(0, 12))

        tk.Button(
            form,
            text="Update Status",
            command=self.update_application,
            bg=self.GREEN,
            fg=self.WHITE,
            activebackground="#15803d",
            activeforeground=self.WHITE,
            relief="flat",
            bd=0,
            padx=15,
            pady=8,
            font=("Segoe UI", 9, "bold"),
            cursor="hand2"
        ).grid(row=1, column=5, padx=12, pady=(0, 12))

        self.application_tree = self.create_tree(
            tab,
            ("ID", "Candidate", "Job", "Department", "Date", "Status"),
            [55, 170, 180, 130, 110, 110]
        )

        self.application_tree.bind(
            "<<TreeviewSelect>>",
            self.on_application_select
        )

    # ========================================================
    # INTERVIEWS
    # ========================================================

    def build_interviews(self):
        tab = self.tabs[4]

        self.section_title(
            tab,
            "Interview Management",
            "Schedule and monitor candidate interviews"
        )

        form = tk.Frame(
            tab,
            bg=self.WHITE,
            highlightbackground=self.BORDER,
            highlightthickness=1
        )
        form.pack(fill="x", pady=(0, 10))

        self.interview_application = self.labeled_entry(
            form, "Application ID", 0, 0, 15
        )
        self.interview_date = self.labeled_entry(
            form, "Date (YYYY-MM-DD)", 0, 1, 18
        )
        self.interview_time = self.labeled_entry(
            form, "Time", 0, 2, 15
        )
        self.interviewer = self.labeled_entry(
            form, "Interviewer", 1, 0, 22
        )

        self.primary_button(
            form,
            "＋  Schedule Interview",
            self.add_interview
        ).grid(row=1, column=2, padx=12, pady=15, sticky="e")

        self.interview_tree = self.create_tree(
            tab,
            ("ID", "Candidate", "Job", "Date", "Time", "Interviewer", "Result"),
            [55, 170, 180, 110, 90, 150, 100]
        )

    # ========================================================
    # ANALYTICS
    # ========================================================

    def build_analytics(self):
        tab = self.tabs[5]

        self.section_title(
            tab,
            "HR Analytics",
            "Interactive recruitment insights powered by Pandas and Plotly"
        )

        controls = tk.Frame(tab, bg=self.BG)
        controls.pack(fill="x", pady=(0, 10))

        self.primary_button(
            controls,
            "📊  Open Interactive Analytics",
            self.open_plotly_dashboard
        ).pack(side="left")

        tk.Button(
            controls,
            text="Export Recruitment CSV",
            command=self.export_csv,
            bg=self.WHITE,
            fg=self.TEXT,
            activebackground="#e5e7eb",
            relief="solid",
            bd=1,
            padx=15,
            pady=8,
            font=("Segoe UI", 9, "bold"),
            cursor="hand2"
        ).pack(side="left", padx=8)

        self.analytics_summary = tk.Frame(tab, bg=self.BG)
        self.analytics_summary.pack(fill="x", pady=10)

        self.analytics_text = tk.Text(
            tab,
            bg=self.WHITE,
            fg=self.TEXT,
            relief="solid",
            bd=1,
            font=("Consolas", 11),
            padx=18,
            pady=18
        )
        self.analytics_text.pack(fill="both", expand=True)

    # ========================================================
    # DATABASE ACTIONS
    # ========================================================

    def add_job(self):
        title = self.job_title.get().strip()
        department = self.job_department.get().strip()
        skills = self.job_skills.get().strip()
        experience = self.job_experience.get().strip()
        vacancies = self.job_vacancies.get().strip()

        if not title or not department or not vacancies:
            messagebox.showwarning(
                "Missing Information",
                "Job title, department and vacancies are required."
            )
            return

        try:
            vacancies = int(vacancies)
            if vacancies <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Invalid Vacancies",
                "Vacancies must be a positive whole number."
            )
            return

        conn = get_connection()
        conn.execute("""
            INSERT INTO jobs
            (title, department, skills, experience, vacancies, created_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            title, department, skills, experience,
            vacancies, datetime.now().strftime("%Y-%m-%d")
        ))
        conn.commit()
        conn.close()

        self.clear(
            self.job_title,
            self.job_department,
            self.job_skills,
            self.job_experience,
            self.job_vacancies
        )

        self.refresh_everything()

        messagebox.showinfo(
            "Success",
            "Job vacancy added successfully."
        )

    def add_candidate(self):
        name = self.candidate_name.get().strip()
        email = self.candidate_email.get().strip()
        phone = self.candidate_phone.get().strip()
        qualification = self.candidate_qualification.get().strip()
        skills = self.candidate_skills.get().strip()
        experience = self.candidate_experience.get().strip()

        if not name or not email:
            messagebox.showwarning(
                "Missing Information",
                "Candidate name and email are required."
            )
            return

        conn = get_connection()
        conn.execute("""
            INSERT INTO candidates
            (name, email, phone, qualification, skills, experience, created_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            name, email, phone, qualification,
            skills, experience,
            datetime.now().strftime("%Y-%m-%d")
        ))
        conn.commit()
        conn.close()

        self.clear(
            self.candidate_name,
            self.candidate_email,
            self.candidate_phone,
            self.candidate_qualification,
            self.candidate_skills,
            self.candidate_experience
        )

        self.refresh_everything()

        messagebox.showinfo(
            "Success",
            "Candidate added successfully."
        )

    def add_application(self):
        candidate_value = self.application_candidate.get()
        job_value = self.application_job.get()

        if not candidate_value or not job_value:
            messagebox.showwarning(
                "Missing Information",
                "Please select both a candidate and a job."
            )
            return

        candidate_id = int(candidate_value.split(" - ")[0])
        job_id = int(job_value.split(" - ")[0])

        conn = get_connection()

        existing = conn.execute("""
            SELECT id FROM applications
            WHERE candidate_id = ? AND job_id = ?
        """, (candidate_id, job_id)).fetchone()

        if existing:
            conn.close()
            messagebox.showwarning(
                "Duplicate Application",
                "This candidate has already applied for this job."
            )
            return

        conn.execute("""
            INSERT INTO applications
            (candidate_id, job_id, application_date, status)
            VALUES (?, ?, ?, 'Applied')
        """, (
            candidate_id,
            job_id,
            datetime.now().strftime("%Y-%m-%d")
        ))

        conn.commit()
        conn.close()

        self.refresh_everything()

        messagebox.showinfo(
            "Success",
            "Application created successfully."
        )

    def update_application(self):
        application_id = self.application_id_entry.get().strip()
        status = self.application_status.get()

        if not application_id:
            messagebox.showwarning(
                "Missing ID",
                "Enter or select an Application ID."
            )
            return

        conn = get_connection()

        exists = conn.execute(
            "SELECT id FROM applications WHERE id = ?",
            (application_id,)
        ).fetchone()

        if not exists:
            conn.close()
            messagebox.showerror(
                "Not Found",
                "Application ID does not exist."
            )
            return

        conn.execute("""
            UPDATE applications
            SET status = ?
            WHERE id = ?
        """, (status, application_id))

        conn.commit()
        conn.close()

        self.refresh_everything()

        messagebox.showinfo(
            "Updated",
            f"Application #{application_id} is now {status}."
        )

    def on_application_select(self, event=None):
        selection = self.application_tree.selection()
        if not selection:
            return

        values = self.application_tree.item(selection[0], "values")
        if values:
            self.application_id_entry.delete(0, tk.END)
            self.application_id_entry.insert(0, values[0])
            self.application_status.set(values[-1])

    def add_interview(self):
        application_id = self.interview_application.get().strip()
        date = self.interview_date.get().strip()
        time = self.interview_time.get().strip()
        interviewer = self.interviewer.get().strip()

        if not application_id or not date or not time or not interviewer:
            messagebox.showwarning(
                "Missing Information",
                "Please fill all interview details."
            )
            return

        conn = get_connection()

        exists = conn.execute(
            "SELECT id FROM applications WHERE id = ?",
            (application_id,)
        ).fetchone()

        if not exists:
            conn.close()
            messagebox.showerror(
                "Invalid Application",
                "Application ID does not exist."
            )
            return

        conn.execute("""
            INSERT INTO interviews
            (application_id, interview_date, interview_time, interviewer)
            VALUES (?, ?, ?, ?)
        """, (application_id, date, time, interviewer))

        conn.execute("""
            UPDATE applications
            SET status = 'Interview'
            WHERE id = ?
        """, (application_id,))

        conn.commit()
        conn.close()

        self.clear(
            self.interview_application,
            self.interview_date,
            self.interview_time,
            self.interviewer
        )

        self.refresh_everything()

        messagebox.showinfo(
            "Success",
            "Interview scheduled successfully."
        )

    # ========================================================
    # REFRESH / LOAD
    # ========================================================

    def refresh_everything(self):
        self.load_jobs()
        self.load_candidates()
        self.load_applications()
        self.load_interviews()
        self.load_application_options()
        self.update_dashboard()
        self.update_analytics_summary()

    def load_jobs(self):
        for item in self.job_tree.get_children():
            self.job_tree.delete(item)

        conn = get_connection()
        rows = conn.execute("""
            SELECT id, title, department, skills,
                   experience, vacancies, status
            FROM jobs
            ORDER BY id DESC
        """).fetchall()
        conn.close()

        for row in rows:
            self.job_tree.insert("", "end", values=tuple(row))

    def load_candidates(self):
        for item in self.candidate_tree.get_children():
            self.candidate_tree.delete(item)

        conn = get_connection()
        rows = conn.execute("""
            SELECT id, name, email, phone,
                   qualification, skills, experience
            FROM candidates
            ORDER BY id DESC
        """).fetchall()
        conn.close()

        for row in rows:
            self.candidate_tree.insert("", "end", values=tuple(row))

    def load_applications(self):
        for item in self.application_tree.get_children():
            self.application_tree.delete(item)

        conn = get_connection()
        rows = conn.execute("""
            SELECT
                applications.id,
                candidates.name,
                jobs.title,
                jobs.department,
                applications.application_date,
                applications.status
            FROM applications
            JOIN candidates
                ON applications.candidate_id = candidates.id
            JOIN jobs
                ON applications.job_id = jobs.id
            ORDER BY applications.id DESC
        """).fetchall()
        conn.close()

        for row in rows:
            self.application_tree.insert("", "end", values=tuple(row))

    def load_interviews(self):
        for item in self.interview_tree.get_children():
            self.interview_tree.delete(item)

        conn = get_connection()
        rows = conn.execute("""
            SELECT
                interviews.id,
                candidates.name,
                jobs.title,
                interviews.interview_date,
                interviews.interview_time,
                interviews.interviewer,
                interviews.result
            FROM interviews
            JOIN applications
                ON interviews.application_id = applications.id
            JOIN candidates
                ON applications.candidate_id = candidates.id
            JOIN jobs
                ON applications.job_id = jobs.id
            ORDER BY interviews.interview_date, interviews.interview_time
        """).fetchall()
        conn.close()

        for row in rows:
            self.interview_tree.insert("", "end", values=tuple(row))

    def load_application_options(self):
        conn = get_connection()

        candidates = conn.execute("""
            SELECT id, name FROM candidates ORDER BY name
        """).fetchall()

        jobs = conn.execute("""
            SELECT id, title FROM jobs
            WHERE status = 'Open'
            ORDER BY title
        """).fetchall()

        conn.close()

        self.application_candidate["values"] = [
            f"{row['id']} - {row['name']}"
            for row in candidates
        ]

        self.application_job["values"] = [
            f"{row['id']} - {row['title']}"
            for row in jobs
        ]

    # ========================================================
    # DASHBOARD / ANALYTICS
    # ========================================================

    def get_application_df(self):
        conn = get_connection()

        query = """
            SELECT
                applications.id AS application_id,
                candidates.name AS candidate,
                candidates.qualification,
                candidates.experience,
                jobs.title AS job,
                jobs.department,
                applications.application_date,
                applications.status
            FROM applications
            JOIN candidates
                ON applications.candidate_id = candidates.id
            JOIN jobs
                ON applications.job_id = jobs.id
        """

        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    def update_dashboard(self):
        conn = get_connection()

        jobs = conn.execute(
            "SELECT COUNT(*) FROM jobs"
        ).fetchone()[0]

        open_jobs = conn.execute(
            "SELECT COUNT(*) FROM jobs WHERE status='Open'"
        ).fetchone()[0]

        candidates = conn.execute(
            "SELECT COUNT(*) FROM candidates"
        ).fetchone()[0]

        applications = conn.execute(
            "SELECT COUNT(*) FROM applications"
        ).fetchone()[0]

        selected = conn.execute(
            "SELECT COUNT(*) FROM applications WHERE status='Selected'"
        ).fetchone()[0]

        conn.close()

        self.stat_jobs.config(text=str(jobs))
        self.stat_open.config(text=str(open_jobs))
        self.stat_candidates.config(text=str(candidates))
        self.stat_applications.config(text=str(applications))
        self.stat_selected.config(text=str(selected))

        df = self.get_application_df()

        self.pipeline_text.delete("1.0", tk.END)

        stages = ["Applied", "Shortlisted", "Interview", "Selected", "Rejected"]

        if df.empty:
            self.pipeline_text.insert(
                tk.END,
                "\n  No applications yet.\n\n"
                "  Start by adding a job and a candidate."
            )
            return

        self.pipeline_text.insert(
            tk.END,
            "\n"
        )

        for stage in stages:
            count = int((df["status"] == stage).sum())
            bar = "●" * min(count, 35)
            self.pipeline_text.insert(
                tk.END,
                f"  {stage:<13} {count:>4}   {bar}\n\n"
            )

    def update_analytics_summary(self):
        for child in self.analytics_summary.winfo_children():
            child.destroy()

        df = self.get_application_df()

        if df.empty:
            return

        total = len(df)
        selected = int((df["status"] == "Selected").sum())
        rejected = int((df["status"] == "Rejected").sum())
        interview = int((df["status"] == "Interview").sum())

        rate = selected / total * 100 if total else 0

        self.card(
            self.analytics_summary,
            "TOTAL APPLICATIONS",
            total,
            self.BLUE
        )

        self.card(
            self.analytics_summary,
            "IN INTERVIEW",
            interview,
            self.ORANGE
        )

        self.card(
            self.analytics_summary,
            "SELECTED",
            selected,
            self.GREEN
        )

        self.card(
            self.analytics_summary,
            "REJECTED",
            rejected,
            self.RED
        )

        self.card(
            self.analytics_summary,
            "SELECTION RATE",
            f"{rate:.1f}%",
            self.PURPLE
        )

        self.analytics_text.delete("1.0", tk.END)

        status_counts = (
            df["status"]
            .value_counts()
            .reindex(
                ["Applied", "Shortlisted", "Interview", "Selected", "Rejected"],
                fill_value=0
            )
        )

        dept_counts = (
            df.groupby("department")
            .size()
            .sort_values(ascending=False)
        )

        text = "\n"
        text += "  RECRUITMENT ANALYTICS SUMMARY\n"
        text += "  " + "=" * 70 + "\n\n"
        text += f"  Total Applications : {total}\n"
        text += f"  Selected           : {selected}\n"
        text += f"  Rejected           : {rejected}\n"
        text += f"  Selection Rate     : {rate:.2f}%\n\n"

        text += "  APPLICATION STATUS\n"
        text += "  " + "-" * 70 + "\n"

        for status, count in status_counts.items():
            text += f"  {status:<18} : {count}\n"

        text += "\n  APPLICATIONS BY DEPARTMENT\n"
        text += "  " + "-" * 70 + "\n"

        for department, count in dept_counts.items():
            text += f"  {department:<25} : {count}\n"

        text += "\n  Pandas is used for data grouping, counting and selection-rate analysis.\n"
        text += "  Plotly is used to generate interactive charts.\n"

        self.analytics_text.insert("1.0", text)

    # ========================================================
    # PLOTLY INTERACTIVE DASHBOARD
    # ========================================================

    def open_plotly_dashboard(self):
        if px is None:
            messagebox.showerror(
                "Plotly Not Installed",
                "Install Plotly first:\n\npip install plotly"
            )
            return

        df = self.get_application_df()

        if df.empty:
            messagebox.showwarning(
                "No Data",
                "Add at least one application before opening analytics."
            )
            return

        status_order = [
            "Applied",
            "Shortlisted",
            "Interview",
            "Selected",
            "Rejected"
        ]

        status_df = (
            df["status"]
            .value_counts()
            .reindex(status_order, fill_value=0)
            .reset_index()
        )
        status_df.columns = ["Status", "Candidates"]

        fig_status = px.bar(
            status_df,
            x="Status",
            y="Candidates",
            title="Recruitment Pipeline",
            text="Candidates"
        )

        fig_status.update_layout(
            template="plotly_white",
            title_font_size=22,
            height=430
        )

        dept_df = (
            df.groupby("department")
            .size()
            .reset_index(name="Applications")
            .sort_values("Applications", ascending=False)
        )

        fig_dept = px.pie(
            dept_df,
            names="department",
            values="Applications",
            hole=0.45,
            title="Applications by Department"
        )

        fig_dept.update_layout(
            template="plotly_white",
            title_font_size=22,
            height=430
        )

        job_df = (
            df.groupby("job")
            .size()
            .reset_index(name="Applications")
            .sort_values("Applications", ascending=False)
            .head(10)
        )

        fig_jobs = px.bar(
            job_df,
            x="Applications",
            y="job",
            orientation="h",
            title="Top Jobs by Applications",
            text="Applications"
        )

        fig_jobs.update_layout(
            template="plotly_white",
            title_font_size=22,
            height=430
        )

        selected_df = df.copy()
        selected_df["Selected"] = (
            selected_df["status"] == "Selected"
        ).astype(int)

        selection_by_dept = (
            selected_df.groupby("department")["Selected"]
            .sum()
            .reset_index()
            .sort_values("Selected", ascending=False)
        )

        fig_selected = px.bar(
            selection_by_dept,
            x="department",
            y="Selected",
            title="Selected Candidates by Department",
            text="Selected"
        )

        fig_selected.update_layout(
            template="plotly_white",
            title_font_size=22,
            height=430
        )

        total = len(df)
        selected = int((df["status"] == "Selected").sum())
        rate = selected / total * 100 if total else 0

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>HR Analytics Dashboard</title>
    <style>
        body {{
            margin: 0;
            background: #f5f7fb;
            font-family: Arial, sans-serif;
            color: #111827;
        }}
        .header {{
            background: #172554;
            color: white;
            padding: 28px 45px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 30px;
        }}
        .header p {{
            margin: 7px 0 0;
            color: #bfdbfe;
        }}
        .cards {{
            display: flex;
            gap: 18px;
            padding: 25px 45px 10px;
            flex-wrap: wrap;
        }}
        .card {{
            background: white;
            border-radius: 14px;
            padding: 22px;
            min-width: 190px;
            flex: 1;
            box-shadow: 0 4px 16px rgba(0,0,0,.07);
        }}
        .label {{
            color: #6b7280;
            font-size: 13px;
            font-weight: bold;
        }}
        .value {{
            font-size: 32px;
            font-weight: bold;
            margin-top: 8px;
            color: #172554;
        }}
        .grid {{
            padding: 10px 45px 45px;
        }}
        .chart {{
            background: white;
            margin: 15px 0;
            padding: 10px;
            border-radius: 14px;
            box-shadow: 0 4px 16px rgba(0,0,0,.06);
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Recruitment & HR Analytics Dashboard</h1>
        <p>USN: CM25078 &nbsp; | &nbsp; Serial No: 43</p>
    </div>

    <div class="cards">
        <div class="card">
            <div class="label">TOTAL APPLICATIONS</div>
            <div class="value">{total}</div>
        </div>
        <div class="card">
            <div class="label">SELECTED</div>
            <div class="value">{selected}</div>
        </div>
        <div class="card">
            <div class="label">SELECTION RATE</div>
            <div class="value">{rate:.1f}%</div>
        </div>
    </div>

    <div class="grid">
        <div class="chart">
            {fig_status.to_html(full_html=False, include_plotlyjs="cdn")}
        </div>
        <div class="chart">
            {fig_dept.to_html(full_html=False, include_plotlyjs=False)}
        </div>
        <div class="chart">
            {fig_jobs.to_html(full_html=False, include_plotlyjs=False)}
        </div>
        <div class="chart">
            {fig_selected.to_html(full_html=False, include_plotlyjs=False)}
        </div>
    </div>
</body>
</html>
"""

        path = REPORT_DIR / "hr_analytics_dashboard.html"
        path.write_text(html, encoding="utf-8")

        webbrowser.open(path.resolve().as_uri())

    # ========================================================
    # EXPORT
    # ========================================================

    def export_csv(self):
        df = self.get_application_df()

        if df.empty:
            messagebox.showwarning(
                "No Data",
                "There is no application data to export."
            )
            return

        filename = filedialog.asksaveasfilename(
            title="Export Recruitment Report",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")]
        )

        if not filename:
            return

        df.to_csv(filename, index=False)

        messagebox.showinfo(
            "Export Complete",
            "Recruitment report exported successfully."
        )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    init_database()

    root = tk.Tk()
    app = RecruitmentPortal(root)
    root.mainloop()