import os
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from datetime import datetime
import pickle
import numpy as np

app = Flask(__name__)
app.secret_key = 'hackathon_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def get_db_connection():
    return mysql.connector.connect(
        host="localhost", user="root", password="PK289", database="fedex_dca"
    )

def log_audit(case_id, user_id, action_type, description):
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = """
        INSERT INTO audit_logs (case_id, action_by_user_id, action_type, description, timestamp)
        VALUES (%s, %s, %s, %s, %s)
    """
    val = (case_id, user_id, action_type, description, datetime.now())
    cursor.execute(sql, val)
    conn.commit()
    conn.close()

try:
    model = pickle.load(open('risk_model.pkl', 'rb'))
except:
    model = None
    print("⚠️ Model not found. Please run train_model.py first.")

# --- NEW ROUTE: PREDICT RISK (AI SCORING) ---
# --- UPDATED ROUTE: PREDICT RISK (WITH MODERATE) ---
@app.route('/run_ai_scoring', methods=['POST'])
def run_ai_scoring():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT case_id, amount_due, days_overdue FROM cases WHERE status = 'New'")
    new_cases = cursor.fetchall()
    
    updates = 0
    if model:
        for case in new_cases:
            # Prepare input
            features = np.array([[case['amount_due'], case['days_overdue']]])
            
            # GET PROBABILITY INSTEAD OF JUST YES/NO
            # predict_proba returns [prob_of_0, prob_of_1]
            # We want prob_of_1 (Probability they WILL PAY)
            prob_pay = model.predict_proba(features)[0][1]
            
            # --- THE NEW LOGIC ---
            if prob_pay > 0.70:       # More than 70% sure they will pay
                risk_label = 'Low Risk'
            elif prob_pay < 0.30:     # Less than 30% chance they will pay
                risk_label = 'High Risk'
            else:                     # Somewhere in between
                risk_label = 'Moderate Risk'
            
            # Save to DB
            cursor.execute("UPDATE cases SET risk_score = %s WHERE case_id = %s", (risk_label, case['case_id']))
            updates += 1
            
        conn.commit()
        log_audit(None, session['id'], 'AI_PREDICTION', f"AI scored {updates} cases (High/Mod/Low).")
    
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/update_risk_settings', methods=['POST'])
def update_risk_settings():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    # Get list of checked IDs from the form (returns list like ['2', '3'])
    selected_agency_ids = request.form.getlist('agency_ids')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. First, RESET everyone to 0 (Remove permission from all)
    cursor.execute("UPDATE users SET can_handle_risk = 0 WHERE role = 'agency'")
    
    # 2. Then, enable ONLY the selected ones
    if selected_agency_ids:
        # This weird SQL syntax (tuple(ids)) creates a string like "(2, 3)"
        format_strings = ','.join(['%s'] * len(selected_agency_ids))
        cursor.execute(f"UPDATE users SET can_handle_risk = 1 WHERE id IN ({format_strings})", tuple(selected_agency_ids))
        
    conn.commit()
    conn.close()
    
    return redirect(url_for('admin_dashboard'))

# --- UPDATED: SMART AUTO-ALLOCATE (ROUND ROBIN) ---
@app.route('/auto_allocate', methods=['POST'])
def auto_allocate():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # 1. FILTER: Only select agencies who have the Checkbox checked (can_handle_risk = 1)
    cursor.execute("SELECT id, username FROM users WHERE role='agency' AND can_handle_risk = 1")
    approved_agencies = cursor.fetchall()
    
    if not approved_agencies:
        conn.close()
        # You might want to flash a message here, but for now we just return
        return "Error: No agencies are configured to handle High Risk! Please check the boxes in settings."

    # 2. Find High Risk cases that are New
    cursor.execute("SELECT case_id FROM cases WHERE risk_score = 'High Risk' AND status = 'New'")
    hard_cases = cursor.fetchall()
    
    count = 0
    num_agencies = len(approved_agencies)
    
    # 3. ROUND ROBIN LOOP (Only among approved agencies)
    for i, case in enumerate(hard_cases):
        agency_index = i % num_agencies
        selected_agency = approved_agencies[agency_index]
        
        cursor.execute("UPDATE cases SET assigned_to_agency_id = %s, status = 'Assigned' WHERE case_id = %s", 
                       (selected_agency['id'], case['case_id']))
        count += 1
        
    conn.commit()
    log_audit(None, session['id'], 'AUTO_ALLOCATE', f"Distributed {count} High Risk cases to {num_agencies} certified agencies.")
    
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password))
        account = cursor.fetchone()
        conn.close()

        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['role'] = account['role']
            session['username'] = account['username']
            
            if account['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('agency_dashboard'))
        else:
            msg = 'Incorrect username or password!'
    return render_template('login.html', msg=msg)

@app.route('/admin')
def admin_dashboard():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # --- 1. CORE DATA ---
    cursor.execute("SELECT * FROM cases")
    all_cases = cursor.fetchall()
    
    cursor.execute("""
        SELECT a.timestamp, u.username, a.action_type, a.description 
        FROM audit_logs a JOIN users u ON a.action_by_user_id = u.id 
        ORDER BY a.timestamp DESC LIMIT 10
    """)
    recent_logs = cursor.fetchall()
    
    cursor.execute("SELECT * FROM users WHERE role = 'agency'")
    agencies = cursor.fetchall()

    # --- 2. KPI CARDS (THE MONEY STATS) ---
    cursor.execute("SELECT SUM(amount_due) as total FROM cases")
    result = cursor.fetchone()
    total_debt = result['total'] if result and result['total'] else 0
    
    cursor.execute("SELECT SUM(amount_due) as recovered FROM cases WHERE status='Paid'")
    result_rec = cursor.fetchone()
    total_recovered = result_rec['recovered'] if result_rec and result_rec['recovered'] else 0
    
    if total_debt > 0:
        recovery_rate = round((total_recovered / total_debt) * 100, 1)
    else:
        recovery_rate = 0

    # --- 3. CHART 1: STATUS SPLIT ---
    cursor.execute("SELECT status, COUNT(*) as count FROM cases GROUP BY status")
    status_res = cursor.fetchall()
    status_labels = [row['status'] for row in status_res]
    status_counts = [row['count'] for row in status_res]

    # --- 4. CHART 2: RISK SPLIT ---
    cursor.execute("SELECT risk_score, COUNT(*) as count FROM cases GROUP BY risk_score")
    risk_res = cursor.fetchall()
    risk_labels = [row['risk_score'] if row['risk_score'] else 'Unscored' for row in risk_res]
    risk_counts = [row['count'] for row in risk_res]

    conn.close()
    return render_template('admin_dashboard.html', 
                           cases=all_cases, 
                           logs=recent_logs, 
                           agencies=agencies,
                           # KPIs
                           total_debt="{:,.2f}".format(total_debt), 
                           total_recovered="{:,.2f}".format(total_recovered),
                           recovery_rate=recovery_rate,
                           # Charts
                           status_labels=status_labels, status_counts=status_counts,
                           risk_labels=risk_labels, risk_counts=risk_counts)

@app.route('/add_agency', methods=['POST'])
def add_agency():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    username = request.form['username']
    password = request.form['password']
    agency_name = request.form['agency_name']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Create the new agency user
        cursor.execute(
            "INSERT INTO users (username, password, role, agency_name) VALUES (%s, %s, 'agency', %s)", 
            (username, password, agency_name)
        )
        conn.commit()
        
        # Log the action
        conn.close() # Close before calling log_audit to avoid conflict
        log_audit(None, session['id'], 'ADD_AGENCY', f"Onboarded new agency: {agency_name}")
        
    except Exception as e:
        print(f"Error adding agency: {e}")
        if conn.is_connected():
            conn.close()
        
    return redirect(url_for('admin_dashboard'))

@app.route('/upload_data', methods=['POST'])
def upload_data():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    if 'file' not in request.files:
        return redirect(url_for('admin_dashboard'))

    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('admin_dashboard'))

    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        try:
            df = pd.read_csv(filepath)
            conn = get_db_connection()
            cursor = conn.cursor()
            count = 0
            
            for index, row in df.iterrows():
                sql = "INSERT INTO cases (customer_name, amount_due, days_overdue, status) VALUES (%s, %s, %s, 'New')"
                val = (row['customer_name'], row['amount_due'], row['days_overdue'])
                cursor.execute(sql, val)
                count += 1
            
            conn.commit()
            conn.close()
            
            # Log outside the loop to be safe
            log_audit(None, session['id'], 'BULK_UPLOAD', f"Uploaded {count} cases via {file.filename}")
            
        except Exception as e:
            return f"Error processing file: {e}"

    return redirect(url_for('admin_dashboard'))

@app.route('/assign_case', methods=['POST'])
def assign_case():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    case_id = request.form['case_id']
    agency_id = request.form['agency_id']

    conn = get_db_connection()
    cursor = conn.cursor()

    
    sql = "UPDATE cases SET assigned_to_agency_id = %s, status = 'Assigned' WHERE case_id = %s"
    cursor.execute(sql, (agency_id, case_id))
    
    cursor.execute("SELECT username FROM users WHERE id = %s", (agency_id,))
    agency_name = cursor.fetchone()[0]

    conn.commit()
    log_audit(case_id, session['id'], 'MANUAL_ASSIGN', f"Assigned Case #{case_id} to Agency '{agency_name}'")
    
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/update_case_status', methods=['POST'])
def update_case_status():
    if 'role' not in session or session['role'] != 'agency':
        return redirect(url_for('login'))

    case_id = request.form['case_id']
    new_status = request.form['new_status']
    agency_id = session['id']

    conn = get_db_connection()
    cursor = conn.cursor()
    
    sql = "UPDATE cases SET status = %s WHERE case_id = %s AND assigned_to_agency_id = %s"
    cursor.execute(sql, (new_status, case_id, agency_id))
    
    conn.commit()

    log_audit(case_id, agency_id, 'STATUS_UPDATE', f"Agency updated status to '{new_status}'")
    
    conn.close()
    
    return redirect(url_for('agency_dashboard'))

@app.route('/agency')
def agency_dashboard():
    if 'role' not in session or session['role'] != 'agency':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    agency_id = session['id']
    
    # 1. Fetch My Cases
    cursor.execute("SELECT * FROM cases WHERE assigned_to_agency_id = %s", (agency_id,))
    my_cases = cursor.fetchall()
    
    # 2. Calculate Stats (Three Categories now)
    completed_count = 0
    pending_count = 0
    rejected_count = 0  # <--- NEW VARIABLE
    
    for case in my_cases:
        if case['status'] == 'Paid':
            completed_count += 1
        elif case['status'] == 'Rejected':
            rejected_count += 1
        else:
            # Only "Assigned", "In Progress", "Contacted" count as actual work
            pending_count += 1
            
    conn.close()
    
    return render_template('agency_dashboard.html', 
                           cases=my_cases, 
                           completed_count=completed_count, 
                           pending_count=pending_count,
                           rejected_count=rejected_count) # Pass this new number

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)