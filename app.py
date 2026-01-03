import os
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'hackathon_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads'

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
    
    cursor.execute("""
        SELECT a.timestamp, u.username, a.action_type, a.description 
        FROM audit_logs a 
        JOIN users u ON a.action_by_user_id = u.id 
        ORDER BY a.timestamp DESC LIMIT 10
    """)
    recent_logs = cursor.fetchall()
    
    cursor.execute("SELECT * FROM cases")
    all_cases = cursor.fetchall()
    conn.close()
    
    return render_template('admin_dashboard.html', cases=all_cases, logs=recent_logs)

@app.route('/upload_data', methods=['POST'])
def upload_data():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    file = request.files['file']
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
            log_audit(None, session['id'], 'BULK_UPLOAD', f"Uploaded {count} cases via {file.filename}")
            
            conn.close()
            return redirect(url_for('admin_dashboard'))
            
        except Exception as e:
            return f"Error: {e}"

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)