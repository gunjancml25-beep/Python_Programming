import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import re
import os
import base64

DB_NAME = "recruitment_hr.db"
REPORT_DIR = "reports"
os.makedirs(REPORT_DIR, exist_ok=True)

def get_conn():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_conn()
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
        )""")
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
        )""")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER NOT NULL,
            job_id INTEGER NOT NULL,
            application_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Applied',
            FOREIGN KEY(candidate_id) REFERENCES candidates(id) ON DELETE CASCADE,
            FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE
        )""")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS interviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id INTEGER NOT NULL,
            interview_date TEXT NOT NULL,
            interview_time TEXT NOT NULL,
            interviewer TEXT NOT NULL,
            result TEXT NOT NULL DEFAULT 'Pending',
            FOREIGN KEY(application_id) REFERENCES applications(id) ON DELETE CASCADE
        )""")
    conn.commit()
    conn.close()

def validate_email(email):
    return re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email) is not None

def validate_date(date_str):
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def validate_time(time_str):
    try:
        datetime.strptime(time_str, "%H:%M")
        return True
    except ValueError:
        return False

def load_df(query, params=()):
    conn = get_conn()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def execute_query(query, params=()):
    conn = get_conn()
    conn.execute(query, params)
    conn.commit()
    conn.close()

def fetch_one(query, params=()):
    conn = get_conn()
    row = conn.execute(query, params).fetchone()
    conn.close()
    return row

def fetch_all(query, params=()):
    conn = get_conn()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background: #0f172a; color: #e2e8f0; }
    .stApp { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); }
    .stSidebar { background: #020617 !important; border-right: 1px solid #1e293b; }
    .stSidebar [data-testid="stSidebarNav"] { background: transparent; }
    .stSidebar .css-1d391kg { padding-top: 2rem; }
    .stMetric { background: rgba(30, 41, 59, 0.7); border-radius: 16px; padding: 1.2rem; border: 1px solid #334155; box-shadow: 0 8px 32px rgba(0,0,0,0.3); backdrop-filter: blur(10px); }
    .stMetric label { color: #94a3b8 !important; font-weight: 500; font-size: 0.85rem; }
    .stMetric [data-testid="stMetricValue"] { color: #f8fafc !important; font-size: 2rem; font-weight: 700; }
    .stDataFrame { border-radius: 12px; overflow: hidden; border: 1px solid #334155; }
    .stButton button { background: linear-gradient(135deg, #3b82f6, #2563eb); color: white; border: none; border-radius: 10px; padding: 0.6rem 1.5rem; font-weight: 600; transition: all 0.3s ease; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4); }
    .stButton button:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(37, 99, 235, 0.6); }
    .stForm { background: rgba(30, 41, 59, 0.6); border-radius: 16px; padding: 1.5rem; border: 1px solid #334155; backdrop-filter: blur(8px); }
    .stTextInput input, .stSelectbox select, .stDateInput input, .stTimeInput input { background: #0f172a !important; color: #e2e8f0 !important; border: 1px solid #334155 !important; border-radius: 8px !important; }
    .stTextInput input:focus, .stSelectbox select:focus { border-color: #3b82f6 !important; box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.3) !important; }
    .stAlert { border-radius: 10px; border: none; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; background: rgba(15, 23, 42, 0.5); padding: 6px; border-radius: 12px; }
    .stTabs [data-baseweb="tab"] { background: transparent; border-radius: 8px; color: #94a3b8; font-weight: 500; }
    .stTabs [aria-selected="true"] { background: #1e293b; color: #f8fafc; }
    .plotly-chart { border-radius: 16px; overflow: hidden; border: 1px solid #334155; background: rgba(30, 41, 59, 0.5); }
    .header-banner { background: linear-gradient(90deg, #1e3a8a, #3b82f6); padding: 2rem; border-radius: 16px; margin-bottom: 2rem; box-shadow: 0 10px 40px rgba(37, 99, 235, 0.3); }
    .header-banner h1 { color: white; font-size: 2.2rem; font-weight: 700; margin: 0; }
    .header-banner p { color: #bfdbfe; font-size: 1rem; margin-top: 0.5rem; }
    .status-badge { padding: 4px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; }
    .status-Applied { background: #1e3a8a; color: #93c5fd; }
    .status-Shortlisted { background: #713f12; color: #fde047; }
    .status-Interview { background: #581c87; color: #d8b4fe; }
    .status-Selected { background: #14532d; color: #86efac; }
    .status-Rejected { background: #7f1d1d; color: #fca5a5; }
    </style>
    """, unsafe_allow_html=True)

def render_header():
    st.markdown('<div class="header-banner"><h1>🚀 Recruitment & HR Analytics Portal</h1><p>Manage hiring • Track candidates • Analyze recruitment pipelines</p></div>', unsafe_allow_html=True)

def render_dashboard():
    st.header("📊 Executive Dashboard")
    jobs_count = fetch_one("SELECT COUNT(*) as c FROM jobs")["c"]
    open_jobs = fetch_one("SELECT COUNT(*) as c FROM jobs WHERE status='Open'")["c"]
    candidates_count = fetch_one("SELECT COUNT(*) as c FROM candidates")["c"]
    apps_count = fetch_one("SELECT COUNT(*) as c FROM applications")["c"]
    selected_count = fetch_one("SELECT COUNT(*) as c FROM applications WHERE status='Selected'")["c"]
    
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Jobs", jobs_count)
    c2.metric("Open Positions", open_jobs)
    c3.metric("Candidates", candidates_count)
    c4.metric("Applications", apps_count)
    c5.metric("Selected", selected_count)
    
    st.subheader("🔄 Recruitment Pipeline")
    df = load_df("""
        SELECT status, COUNT(*) as count FROM applications 
        GROUP BY status ORDER BY CASE status 
        WHEN 'Applied' THEN 1 WHEN 'Shortlisted' THEN 2 WHEN 'Interview' THEN 3 
        WHEN 'Selected' THEN 4 WHEN 'Rejected' THEN 5 END
    """)
    if not df.empty:
        fig = px.funnel(df, x="count", y="status", color="status", 
                        color_discrete_map={"Applied":"#3b82f6","Shortlisted":"#eab308","Interview":"#a855f7","Selected":"#22c55e","Rejected":"#ef4444"},
                        title="Candidate Pipeline Flow")
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='#e2e8f0', margin=dict(l=20,r=20,t=40,b=20))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No applications yet. Start by adding jobs and candidates.")

def render_jobs():
    st.header("💼 Job Management")
    with st.form("job_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        title = c1.text_input("Job Title")
        dept = c2.text_input("Department")
        c3, c4 = st.columns(2)
        skills = c3.text_input("Required Skills")
        exp = c4.text_input("Experience Level")
        vac = st.number_input("Vacancies", min_value=1, step=1)
        submitted = st.form_submit_button("➕ Create Job")
        if submitted:
            if not title or not dept:
                st.error("Title and Department are required.")
            else:
                execute_query("INSERT INTO jobs (title, department, skills, experience, vacancies, created_date) VALUES (?,?,?,?,?,?)",
                              (title, dept, skills, exp, vac, datetime.now().strftime("%Y-%m-%d")))
                st.success("Job created successfully!")
                st.rerun()
    
    st.subheader("📋 Active Jobs")
    df = load_df("SELECT id, title, department, skills, experience, vacancies, status, created_date FROM jobs ORDER BY id DESC")
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No jobs posted yet.")

def render_candidates():
    st.header("👥 Candidate Management")
    with st.form("candidate_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        name = c1.text_input("Full Name")
        email = c2.text_input("Email Address")
        c3, c4 = st.columns(2)
        phone = c3.text_input("Phone Number")
        qual = c4.text_input("Qualification")
        c5, c6 = st.columns(2)
        skills = c5.text_input("Skills")
        exp = c6.text_input("Experience")
        submitted = st.form_submit_button("➕ Add Candidate")
        if submitted:
            if not name or not email:
                st.error("Name and Email are required.")
            elif not validate_email(email):
                st.error("Invalid email format.")
            else:
                execute_query("INSERT INTO candidates (name, email, phone, qualification, skills, experience, created_date) VALUES (?,?,?,?,?,?,?)",
                              (name, email, phone, qual, skills, exp, datetime.now().strftime("%Y-%m-%d")))
                st.success("Candidate added successfully!")
                st.rerun()
    
    st.subheader("📇 Candidate Database")
    df = load_df("SELECT id, name, email, phone, qualification, skills, experience, created_date FROM candidates ORDER BY id DESC")
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No candidates registered yet.")

def render_applications():
    st.header("📝 Application Tracking")
    candidates = fetch_all("SELECT id, name FROM candidates ORDER BY name")
    jobs = fetch_all("SELECT id, title FROM jobs WHERE status='Open' ORDER BY title")
    
    if not candidates or not jobs:
        st.warning("Add candidates and open jobs first to create applications.")
        return
    
    cand_options = {f"{c['id']} - {c['name']}": c['id'] for c in candidates}
    job_options = {f"{j['id']} - {j['title']}": j['id'] for j in jobs}
    
    with st.form("app_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        sel_cand = c1.selectbox("Select Candidate", list(cand_options.keys()))
        sel_job = c2.selectbox("Select Job", list(job_options.keys()))
        submitted = st.form_submit_button("🚀 Submit Application")
        if submitted:
            cid, jid = cand_options[sel_cand], job_options[sel_job]
            exists = fetch_one("SELECT id FROM applications WHERE candidate_id=? AND job_id=?", (cid, jid))
            if exists:
                st.error("Duplicate application detected.")
            else:
                execute_query("INSERT INTO applications (candidate_id, job_id, application_date, status) VALUES (?,?,?,'Applied')",
                              (cid, jid, datetime.now().strftime("%Y-%m-%d")))
                st.success("Application submitted!")
                st.rerun()
    
    st.subheader("📊 Application Pipeline")
    df = load_df("""
        SELECT a.id, c.name as candidate, j.title as job, j.department, a.application_date, a.status
        FROM applications a
        JOIN candidates c ON a.candidate_id = c.id
        JOIN jobs j ON a.job_id = j.id
        ORDER BY a.id DESC
    """)
    if not df.empty:
        edit_df = st.data_editor(df, use_container_width=True, hide_index=True, 
                                 column_config={"status": st.column_config.SelectColumn("Status", options=["Applied","Shortlisted","Interview","Selected","Rejected"])})
        if not df.equals(edit_df):
            for idx, row in edit_df.iterrows():
                orig_status = df.iloc[idx]["status"]
                if row["status"] != orig_status:
                    execute_query("UPDATE applications SET status=? WHERE id=?", (row["status"], row["id"]))
            st.success("Status updated!")
            st.rerun()
    else:
        st.info("No applications to display.")

def render_interviews():
    st.header("📅 Interview Scheduler")
    apps = fetch_all("""
        SELECT a.id, c.name, j.title FROM applications a
        JOIN candidates c ON a.candidate_id = c.id
        JOIN jobs j ON a.job_id = j.id
        WHERE a.status IN ('Applied','Shortlisted','Interview')
        ORDER BY a.id DESC
    """)
    
    if not apps:
        st.warning("No eligible applications for interviews.")
        return
    
    app_options = {f"{a['id']} | {a['name']} → {a['title']}": a['id'] for a in apps}
    
    with st.form("interview_form", clear_on_submit=True):
        sel_app = st.selectbox("Select Application", list(app_options.keys()))
        c1, c2 = st.columns(2)
        int_date = c1.date_input("Interview Date")
        int_time = c2.time_input("Interview Time")
        interviewer = st.text_input("Interviewer Name")
        submitted = st.form_submit_button("📅 Schedule Interview")
        if submitted:
            if not interviewer:
                st.error("Interviewer name is required.")
            else:
                aid = app_options[sel_app]
                d_str, t_str = str(int_date), str(int_time)[:5]
                execute_query("INSERT INTO interviews (application_id, interview_date, interview_time, interviewer) VALUES (?,?,?,?)",
                              (aid, d_str, t_str, interviewer))
                execute_query("UPDATE applications SET status='Interview' WHERE id=?", (aid,))
                st.success("Interview scheduled!")
                st.rerun()
    
    st.subheader("📋 Upcoming Interviews")
    df = load_df("""
        SELECT i.id, c.name as candidate, j.title as job, i.interview_date, i.interview_time, i.interviewer, i.result
        FROM interviews i
        JOIN applications a ON i.application_id = a.id
        JOIN candidates c ON a.candidate_id = c.id
        JOIN jobs j ON a.job_id = j.id
        ORDER BY i.interview_date, i.interview_time
    """)
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No interviews scheduled.")

def render_analytics():
    st.header("📈 HR Analytics & Insights")
    df = load_df("""
        SELECT a.id, c.name, c.qualification, c.experience, j.title as job, j.department, a.application_date, a.status
        FROM applications a
        JOIN candidates c ON a.candidate_id = c.id
        JOIN jobs j ON a.job_id = j.id
    """)
    
    if df.empty:
        st.info("Generate applications to view analytics.")
        return
    
    total = len(df)
    selected = len(df[df["status"]=="Selected"])
    rate = (selected/total)*100 if total else 0
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Applications", total)
    c2.metric("Selected Candidates", selected)
    c3.metric("Selection Rate", f"{rate:.1f}%")
    
    t1, t2 = st.tabs(["📊 Department Distribution", "🏆 Top Jobs"])
    with t1:
        dept_df = df["department"].value_counts().reset_index()
        dept_df.columns = ["Department", "Count"]
        fig1 = px.pie(dept_df, values="Count", names="Department", hole=0.4, title="Applications by Department")
        fig1.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='#e2e8f0')
        st.plotly_chart(fig1, use_container_width=True)
    
    with t2:
        job_df = df["job"].value_counts().head(8).reset_index()
        job_df.columns = ["Job", "Count"]
        fig2 = px.bar(job_df, x="Count", y="Job", orientation="h", title="Top Jobs by Applications", color="Count", color_continuous_scale="Blues")
        fig2.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='#e2e8f0', yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig2, use_container_width=True)
    
    st.subheader("💾 Export Data")
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="recruitment_report.csv" style="background:linear-gradient(135deg,#10b981,#059669);color:white;padding:12px 24px;border-radius:10px;text-decoration:none;font-weight:600;display:inline-block;">📥 Download CSV Report</a>'
    st.markdown(href, unsafe_allow_html=True)

def main():
    st.set_page_config(page_title="HR Analytics Portal", page_icon="🚀", layout="wide")
    inject_css()
    init_db()
    render_header()
    
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=60)
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Dashboard", "Jobs", "Candidates", "Applications", "Interviews", "Analytics"])
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("**PROJECT**")
    st.sidebar.markdown("USN: CM25078")
    st.sidebar.markdown("Serial No: 43")
    
    if page == "Dashboard": render_dashboard()
    elif page == "Jobs": render_jobs()
    elif page == "Candidates": render_candidates()
    elif page == "Applications": render_applications()
    elif page == "Interviews": render_interviews()
    elif page == "Analytics": render_analytics()

if __name__ == "__main__":
    main()

  

  
 
