# 📦 FedEx SmartRecover: AI-Powered Debt Collection Optimization

### Reimagining Debt Collection Agency (DCA) Management through Digital & AI Solutions.

**SmartRecover** is a full-stack enterprise application designed to transform the debt recovery process from a manual, spreadsheet-heavy workflow into an intelligent, automated, and data-driven command center.

---

## 🚩 The Problem
Current DCA management processes are manual, reactive, and inefficient:
* **Manual Allocation:** Managers spend hours slicing Excel files to email cases to agencies.
* **Zero Intelligence:** High-risk debts ($50k+) are treated with the same urgency as low-risk debts ($50).
* **Lack of Governance:** No real-time tracking of agency performance or enforcement of Service Level Agreements (SLAs).
* **Security Risks:** Sensitive financial data is shared via insecure email attachments.

## 💡 The Solution
**SmartRecover** centralizes the entire workflow into a secure web platform. It uses **Machine Learning (Random Forest)** to predict payment risk, **Automated Round-Robin logic** to assign cases instantly, and **SLA Watchdogs** to ensure accountability.

---

## 🚀 Key Features

### 1. 🔮 AI-Driven Risk Scoring
* Uses a **Random Forest Classifier** to analyze historical payment data.
* Automatically tags cases as **🔴 High Risk**, **🟠 Moderate Risk**, or **🟢 Low Risk**.
* Enables strategic prioritization (tackling the hardest/highest value cases first).

### 2. 🤖 Intelligent Automation
* **One-Click Allocation:** Replaces manual emails with an automated **Round-Robin** distribution system.
* **Skill-Based Routing:** Ensures complex High-Risk cases are only routed to certified agencies.

### 3. 🛡️ Governance & SLA Enforcement
* **SLA Watchdog:** Automatically flags any case that has been untouched for **>5 Days** with a **⚠️ SLA BREACHED** warning.
* **Audit Trails:** Immutable logs of every assignment, status update, and login.

### 4. 📊 Agency Performance Portal
* **Secure Access:** Agencies log in to a restricted view (seeing only their assigned cases).
* **Gamification:** "My Performance" charts motivate agencies to improve recovery rates.
* **Accept/Reject Workflow:** Agencies can accept or decline work based on capacity.

### 5. 📈 Real-Time Analytics
* **Executive Dashboard:** Tracks Total Debt, Cash Recovered, and Recovery Rate %.
* **Visual Insights:** Interactive Chart.js visualizations for Case Status and Risk Distribution.

---

## 🛠️ Tech Stack

* **Backend:** Python (Flask)
* **Database:** MySQL (Relational Data & Transaction Management)
* **Machine Learning:** Scikit-Learn (Random Forest Model)
* **Frontend:** HTML5, CSS3, JavaScript, Jinja2
* **Visualization:** Chart.js
* **Tools:** MySQL Workbench, VS Code

---
