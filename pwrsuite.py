import streamlit as st
import sqlite3
import hashlib
import pandas as pd

# Database connection
conn = sqlite3.connect('employee_management.db')
c = conn.cursor()

# Create tables if not exist
c.execute('''CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                name TEXT, 
                role TEXT, 
                department TEXT)''')

c.execute('''CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                project_name TEXT, 
                assigned_to INTEGER, 
                deadline DATE,
                FOREIGN KEY (assigned_to) REFERENCES employees (id))''')

c.execute('''
CREATE TABLE IF NOT EXISTS timesheets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER,
    project_id INTEGER,
    date DATE,
    hours_worked FLOAT,
    description TEXT,
    FOREIGN KEY (employee_id) REFERENCES employees (id),
    FOREIGN KEY (project_id) REFERENCES projects (id)
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT
)
''')
conn.commit()

# Sample data for testing
c.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('admin', 'admin123', 'admin')")
c.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('employee1', 'password123', 'employee')")
conn.commit()



# Utility Functions
def hash_password(password):
    """Hash a password for secure storage."""
    return hashlib.sha256(password.encode()).hexdigest()


def authenticate_user(username, password):
    """Authenticate user credentials."""
    hashed_password = hash_password(password)
    user = c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password)).fetchone()
    return user


def get_user_role(username):
    """Get the role of a user."""
    user = c.execute("SELECT role FROM users WHERE username = ?", (username,)).fetchone()
    return user[0] if user else None


# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["username"] = None
    st.session_state["role"] = None


# Login Page
def login():
    """Display the login page."""
    st.title("Login")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

        if submitted:
            user = authenticate_user(username, password)
            if user:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.session_state["role"] = get_user_role(username)
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid username or password.")


# Function Definitions
def add_employee(name, role, department):
    c.execute("INSERT INTO employees (name, role, department) VALUES (?, ?, ?)", (name, role, department))
    conn.commit()

def update_employee(emp_id, name, role, department):
    c.execute("UPDATE employees SET name = ?, role = ?, department = ? WHERE id = ?", (name, role, department, emp_id))
    conn.commit()

def delete_employee(emp_id):
    c.execute("DELETE FROM employees WHERE id = ?", (emp_id,))
    conn.commit()

def add_project(project_name, assigned_to, deadline):
    c.execute("INSERT INTO projects (project_name, assigned_to, deadline) VALUES (?, ?, ?)", (project_name, assigned_to, deadline))
    conn.commit()

def fetch_employees():
    return pd.read_sql_query("SELECT * FROM employees", conn)

def fetch_projects():
    return pd.read_sql_query("SELECT * FROM projects", conn)

def add_timesheet(employee_id, project_id, date, hours_worked, description):
    c.execute('''
        INSERT INTO timesheets (employee_id, project_id, date, hours_worked, description)
        VALUES (?, ?, ?, ?, ?)
    ''', (employee_id, project_id, date, hours_worked, description))
    conn.commit()

def fetch_timesheets():
    return pd.read_sql_query('''
        SELECT t.id, e.name AS employee, p.project_name AS project, t.date, t.hours_worked, t.description
        FROM timesheets t
        JOIN employees e ON t.employee_id = e.id
        JOIN projects p ON t.project_id = p.id
    ''', conn)



# Streamlit App
st.set_page_config(
    page_title="Employee & Project Management System",
    initial_sidebar_state="expanded"  # Sidebar options: "expanded", "collapsed"
)

# Main Dashboard
def main_dashboard():
    """Display the main application with role-based tabs."""
    st.sidebar.write(f"Logged in as: {st.session_state['username']} ({st.session_state['role']})")

    if st.sidebar.button("Logout"):
        st.session_state["logged_in"] = False
        st.session_state["username"] = None
        st.session_state["role"] = None
        st.rerun()

    # Tabs for navigation
    tabs = st.tabs(["Home", "Manage Employees", "Manage Projects", "Generate Reports", "Timesheet"])

    # Home Tab
    with tabs[0]:
        st.header("Welcome to the Employee Management System")

    # Other tabs depending on role
    if st.session_state["role"] == "admin":
        with tabs[1]:
            st.header("Manage Employees")
            emp_menu = st.selectbox("Action", ["Add", "Update", "Delete", "View All"])

            if emp_menu == "Add":
                with st.form("add_employee_form"):
                    name = st.text_input("Name")
                    role = st.text_input("Role")
                    department = st.text_input("Department")
                    submitted = st.form_submit_button("Add Employee")
                    if submitted:
                        add_employee(name, role, department)
                        st.success("Employee added successfully!")
            elif emp_menu == "Update":
                employees = fetch_employees()
                emp_id = st.selectbox("Select Employee", employees["id"])
                name = st.text_input("Name", employees.loc[employees["id"] == emp_id, "name"].values[0])
                role = st.text_input("Role", employees.loc[employees["id"] == emp_id, "role"].values[0])
                department = st.text_input("Department",
                                           employees.loc[employees["id"] == emp_id, "department"].values[0])
                if st.button("Update Employee"):
                    update_employee(emp_id, name, role, department)
                    st.success("Employee updated successfully!")
            elif emp_menu == "Delete":
                employees = fetch_employees()
                emp_id = st.selectbox("Select Employee", employees["id"])
                if st.button("Delete Employee"):
                    delete_employee(emp_id)
                    st.success("Employee deleted successfully!")
            elif emp_menu == "View All":
                st.dataframe(fetch_employees())
        with tabs[2]:
            st.header("Manage Projects")
            proj_menu = st.selectbox("Action", ["Add", "View All"])

            if proj_menu == "Add":
                with st.form("add_project_form"):
                    project_name = st.text_input("Project Name")
                    employees = fetch_employees()
                    assigned_to = st.selectbox("Assign To", employees["id"])
                    deadline = st.date_input("Deadline")
                    submitted = st.form_submit_button("Add Project")
                    if submitted:
                        add_project(project_name, assigned_to, deadline)
                        st.success("Project added successfully!")
            elif proj_menu == "View All":
                st.dataframe(fetch_projects())
    elif st.session_state["role"] == "employee":
        with tabs[4]:
            st.header("Timesheet Entry")

            employees = fetch_employees()
            projects = fetch_projects()

            with st.form("timesheet_entry_form"):
                employee_id = st.selectbox("Employee", employees["id"],
                                           format_func=lambda x: employees.loc[employees["id"] == x, "name"].values[0])
                project_id = st.selectbox("Project", projects["id"],
                                          format_func=lambda x:
                                          projects.loc[projects["id"] == x, "project_name"].values[0])
                date = st.date_input("Date")
                hours_worked = st.number_input("Hours Worked", min_value=0.0, step=0.5)
                description = st.text_area("Description")
                submitted = st.form_submit_button("Submit Timesheet")

                if submitted:
                    add_timesheet(employee_id, project_id, date, hours_worked, description)
                    st.success("Timesheet entry added successfully!")

            st.subheader("Timesheet Records")
            st.dataframe(fetch_timesheets())

    with tabs[3]:
        st.header("Generate Reports")
        report_menu = st.selectbox("Report Type", ["Employee Overview", "Project Overview"])

        if report_menu == "Employee Overview":
            st.dataframe(fetch_employees())
        elif report_menu == "Project Overview":
            st.dataframe(fetch_projects())


# Main App Logic
if not st.session_state["logged_in"]:
    login()
else:
    main_dashboard()
