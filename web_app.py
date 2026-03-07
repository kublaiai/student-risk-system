from flask import Flask, request, render_template_string, send_file
import pandas as pd
import os
from io import BytesIO
from urllib.parse import quote

app = Flask(__name__)
LAST_REPORT_DF = None
LAST_EMAIL_DF = None
LAST_FILENAME = None
LAST_COUNTS = None
LAST_INSTRUCTOR_NAME = "Your Instructor"

HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Early Warning System</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      margin: 0;
      background: #f6f8fb;
      color: #1f2937;
    }
    .wrap {
      max-width: 1200px;
      margin: 36px auto;
      padding: 0 20px 40px;
    }
    .card {
      background: white;
      border-radius: 18px;
      padding: 24px;
      box-shadow: 0 10px 28px rgba(15, 23, 42, 0.08);
      margin-bottom: 20px;
    }
    h1, h2, h3 {
      margin-top: 0;
    }
    .muted {
      color: #667085;
    }
    .btn {
      background: #2563eb;
      color: white;
      border: 0;
      border-radius: 10px;
      padding: 12px 18px;
      cursor: pointer;
      font-size: 15px;
      text-decoration: none;
      display: inline-block;
    }
    .btn.secondary {
      background: #0f766e;
    }
    .btn.mail {
      background: #7c3aed;
      padding: 8px 12px;
      font-size: 13px;
    }
    .btn:hover {
      opacity: 0.95;
    }
    .hero {
      background: linear-gradient(135deg, #eff6ff 0%, #f8fafc 100%);
      border: 1px solid #dbeafe;
    }
    .hero p {
      max-width: 900px;
      line-height: 1.6;
      margin-bottom: 0;
    }
    .info-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 16px;
      margin-top: 18px;
    }
    .info-box {
      background: #f8fafc;
      border: 1px solid #e5e7eb;
      border-radius: 16px;
      padding: 18px;
    }
    .info-box h3 {
      margin-bottom: 10px;
      font-size: 18px;
    }
    .info-box ol,
    .info-box ul {
      margin: 0;
      padding-left: 18px;
      line-height: 1.6;
    }
    .risk-mini-table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 10px;
      font-size: 13px;
    }
    .risk-mini-table th,
    .risk-mini-table td {
      border: 1px solid #e5e7eb;
      padding: 8px;
      text-align: left;
    }
    .risk-mini-table th {
      background: #f1f5f9;
    }
    .upload-box {
      border: 2px dashed #cbd5e1;
      border-radius: 16px;
      padding: 20px;
      background: #f8fafc;
      margin-top: 14px;
    }
    .summary-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 16px;
      margin-top: 18px;
    }
    .metric {
      border-radius: 16px;
      padding: 18px;
      font-weight: bold;
    }
    .metric .label {
      display: block;
      font-size: 13px;
      font-weight: 600;
      opacity: 0.85;
      margin-bottom: 8px;
    }
    .metric .value {
      font-size: 32px;
      line-height: 1;
    }
    .high {
      background: #fee2e2;
      color: #991b1b;
    }
    .medium {
      background: #fef3c7;
      color: #92400e;
    }
    .low {
      background: #dcfce7;
      color: #166534;
    }
    .total {
      background: #dbeafe;
      color: #1d4ed8;
    }
    .actions {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      margin-top: 18px;
    }
    .section-title {
      margin-top: 28px;
      margin-bottom: 10px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 12px;
      font-size: 14px;
      background: white;
      border-radius: 12px;
      overflow: hidden;
    }
    th, td {
      padding: 10px 12px;
      border-bottom: 1px solid #e5e7eb;
      text-align: left;
      vertical-align: top;
    }
    th {
      background: #f8fafc;
      font-weight: 700;
    }
    tr:last-child td {
      border-bottom: none;
    }
    .insight-list {
      margin: 10px 0 0;
      padding-left: 18px;
    }
    .tag {
      display: inline-block;
      padding: 6px 10px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 700;
      margin-right: 8px;
    }
    .tag-high {
      background: #fee2e2;
      color: #991b1b;
    }
    .tag-medium {
      background: #fef3c7;
      color: #92400e;
    }
    .small {
      font-size: 13px;
    }
    input[type=file] {
      margin: 10px 0 16px;
    }
    input[type=text] {
      padding: 10px;
      width: 320px;
      max-width: 100%;
      margin: 8px 0 16px;
      border: 1px solid #cbd5e1;
      border-radius: 10px;
    }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card hero">
      <h1>AI Early Warning System for Math Students</h1>
      <p>
        This tool analyzes MyLabMath gradebook data to identify students who may be at risk of failing
        earlier than traditional indicators. It helps instructors quickly review risk levels, identify
        likely areas of concern, and take early action through outreach and intervention.
      </p>
    </div>

    <div class="info-grid">
      <div class="info-box">
        <h3>How to Export the File</h3>
        <ol>
          <li>Open <strong>MyLabMath</strong>.</li>
          <li>Go to the <strong>Gradebook</strong>.</li>
          <li>Select <strong>Overview of Student Averages</strong>.</li>
          <li>Export the file.</li>
          <li>Save it as a <strong>CSV</strong>.</li>
        </ol>
      </div>

      <div class="info-box">
        <h3>How to Use This Tool</h3>
        <ol>
          <li>Enter your <strong>Instructor Name</strong>.</li>
          <li>Upload the MyLabMath <strong>CSV</strong> file.</li>
          <li>Click <strong>Analyze Student Risk</strong>.</li>
          <li>Review flagged students, download reports, or send emails.</li>
        </ol>
      </div>

      <div class="info-box">
        <h3>How Risk Is Calculated</h3>
        <table class="risk-mini-table">
          <tr>
            <th>Indicator</th>
            <th>Risk Trigger</th>
          </tr>
          <tr>
            <td>Overall Score</td>
            <td>Below 70</td>
          </tr>
          <tr>
            <td>Homework Average</td>
            <td>Below 70</td>
          </tr>
          <tr>
            <td>Quiz Average</td>
            <td>Below 65</td>
          </tr>
          <tr>
            <td>Test Average</td>
            <td>Below 65</td>
          </tr>
        </table>
        <p class="small muted" style="margin-top:10px;">
          Risk levels: <strong>0–2 = Low</strong>, <strong>3–5 = Medium</strong>, <strong>6+ = High</strong>.
        </p>
      </div>
    </div>

    <div class="card">
      <form method="post" action="/analyze" enctype="multipart/form-data">
        <div class="upload-box">
          <strong>Upload MyLabMath CSV</strong><br><br>

          <label for="instructor_name"><strong>Instructor Name</strong></label><br>
          <input type="text" name="instructor_name" id="instructor_name" placeholder="Enter instructor name" required>
          <br>

          <input type="file" name="file" accept=".csv" required>
          <br>
          <button class="btn" type="submit">Analyze Student Risk</button>
        </div>
      </form>
    </div>

    {% if analyzed %}
    <div class="card">
      <h2>Results for {{ filename }}</h2>
      <p class="muted">This analysis flags students using overall score, homework average, quiz average when available, and test average.</p>

      <div class="summary-grid">
        <div class="metric total">
          <span class="label">TOTAL STUDENTS</span>
          <span class="value">{{ total_students }}</span>
        </div>
        <div class="metric high">
          <span class="label">HIGH RISK</span>
          <span class="value">{{ counts.get('HIGH', 0) }}</span>
        </div>
        <div class="metric medium">
          <span class="label">MEDIUM RISK</span>
          <span class="value">{{ counts.get('MEDIUM', 0) }}</span>
        </div>
        <div class="metric low">
          <span class="label">LOW RISK</span>
          <span class="value">{{ counts.get('LOW', 0) }}</span>
        </div>
      </div>

      <div class="actions">
        <a href="/download-report" class="btn">Download At-Risk Report</a>
        <a href="/download-emails" class="btn secondary">Download Email Drafts</a>
      </div>
    </div>

    <div class="card">
      <h3>Instructor Insights</h3>
      <ul class="insight-list">
        <li><strong>Most common high-risk reason:</strong> {{ top_reason }}</li>
        <li><strong>Recommended focus:</strong> Reach out first to students with the highest risk scores and lowest test averages.</li>
        <li><strong>Immediate action:</strong> Use the Send Email buttons or download the email drafts file.</li>
      </ul>
    </div>

    <div class="card">
      <h3 class="section-title">High Risk Students</h3>
      <div class="small muted"><span class="tag tag-high">HIGH</span>Students needing immediate attention</div>
      {{ high_table|safe }}

      <h3 class="section-title">Medium Risk Students</h3>
      <div class="small muted"><span class="tag tag-medium">MEDIUM</span>Students showing warning signs</div>
      {{ medium_table|safe }}
    </div>
    {% endif %}
  </div>
</body>
</html>
"""


def usable_column(df, col_name):
    return col_name in df.columns and df[col_name].notna().sum() > 0


def risk_level(score):
    if score >= 6:
        return "HIGH"
    elif score >= 3:
        return "MEDIUM"
    else:
        return "LOW"


def intervention_action(row):
    if row["Risk_Level"] == "HIGH":
        return "Immediate outreach, office hours invitation, tutoring referral"
    elif row["Risk_Level"] == "MEDIUM":
        return "Warning email and encourage office hours"
    else:
        return "No immediate action needed"


def draft_email(row, instructor_name):
    if row["Risk_Level"] == "HIGH":
        return f"""Subject: Quick Check-In About Your Progress

Hi {row['First_Name']},

I wanted to check in because current course performance data suggests that you may be at risk of falling behind.

Areas of concern: {row['Risk_Reasons']}

I strongly encourage you to attend office hours and complete any missing work as soon as possible.

Please reply and let me know your plan for getting back on track.

Best regards,
{instructor_name}
"""
    elif row["Risk_Level"] == "MEDIUM":
        return f"""Subject: Check-In About Your Progress

Hi {row['First_Name']},

I wanted to check in because I noticed some signs that you may need additional support in the course.

Areas to improve: {row['Risk_Reasons']}

I encourage you to review your recent work and come to office hours if needed.

Best regards,
{instructor_name}
"""
    return ""


def build_mailto(email, subject, body):
    return f"mailto:{quote(str(email))}?subject={quote(subject)}&body={quote(body)}"


def calculate_risk_score(row, df):
    score = 0
    reasons = []

    if usable_column(df, "Overall_Score") and pd.notna(row["Overall_Score"]):
        if row["Overall_Score"] < 70:
            score += 3
            reasons.append("overall score below 70")

    if usable_column(df, "Homework_Avg") and pd.notna(row["Homework_Avg"]):
        if row["Homework_Avg"] < 70:
            score += 2
            reasons.append("homework average below 70")

    if usable_column(df, "Quiz_Avg") and pd.notna(row["Quiz_Avg"]):
        if row["Quiz_Avg"] < 65:
            score += 1
            reasons.append("quiz average below 65")

    if usable_column(df, "Test_Avg") and pd.notna(row["Test_Avg"]):
        if row["Test_Avg"] < 65:
            score += 3
            reasons.append("test average below 65")

    return pd.Series([score, "; ".join(reasons)])


def process_mylab_csv(file_stream, instructor_name):
    df = pd.read_csv(file_stream, header=2)
    df.columns = [
        "Last_Name",
        "First_Name",
        "Email",
        "Login",
        "Student_ID",
        "Overall_Score",
        "Homework_Avg",
        "Quiz_Avg",
        "Test_Avg",
        "Other_Avg",
        "StudyPlan_Avg",
        "Extra",
    ]

    df = df[df["Last_Name"] != "Last name"]
    df = df[~df["Last_Name"].astype(str).str.contains("Inactive", case=False, na=False)]
    df = df.dropna(how="all").reset_index(drop=True)

    for col in ["Overall_Score", "Homework_Avg", "Quiz_Avg", "Test_Avg"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df[["Risk_Score", "Risk_Reasons"]] = df.apply(lambda row: calculate_risk_score(row, df), axis=1)
    df["Risk_Level"] = df["Risk_Score"].apply(risk_level)
    df["Intervention"] = df.apply(intervention_action, axis=1)
    df["Draft_Email"] = df.apply(lambda row: draft_email(row, instructor_name), axis=1)

    return df


def most_common_reason(df):
    flagged = df[df["Risk_Level"] != "LOW"]
    if flagged.empty:
        return "No major risk patterns detected"

    all_reasons = []
    for reasons in flagged["Risk_Reasons"].dropna():
        all_reasons.extend([r.strip() for r in reasons.split(";") if r.strip()])

    if not all_reasons:
        return "No major risk patterns detected"

    reason_counts = pd.Series(all_reasons).value_counts()
    return reason_counts.index[0]


def build_display_table(df, level):
    filtered = df[df["Risk_Level"] == level].copy()
    if filtered.empty:
        return f"<p class='muted'>No {level.lower()}-risk students found.</p>"

    filtered["Email_Action"] = filtered.apply(
        lambda row: f'<a class="btn mail" href="{build_mailto(row["Email"], f"{level.title()} Risk Check-In", row["Draft_Email"])}">Send Email</a>',
        axis=1
    )

    display_cols = [
        "First_Name",
        "Last_Name",
        "Risk_Score",
        "Risk_Reasons",
        "Intervention",
        "Email_Action",
    ]

    filtered = filtered[display_cols].sort_values(by="Risk_Score", ascending=False)
    return filtered.to_html(index=False, escape=False, classes="small")


@app.route("/", methods=["GET"])
def home():
    return render_template_string(HTML, analyzed=False)


@app.route("/analyze", methods=["POST"])
def analyze():
    global LAST_REPORT_DF, LAST_EMAIL_DF, LAST_FILENAME, LAST_COUNTS, LAST_INSTRUCTOR_NAME

    uploaded = request.files.get("file")
    instructor_name = request.form.get("instructor_name", "").strip()

    if not instructor_name:
        instructor_name = "Your Instructor"

    LAST_INSTRUCTOR_NAME = instructor_name

    if not uploaded or uploaded.filename == "":
        return render_template_string(HTML, analyzed=False)

    df = process_mylab_csv(uploaded, LAST_INSTRUCTOR_NAME)
    LAST_FILENAME = uploaded.filename
    LAST_COUNTS = df["Risk_Level"].value_counts().to_dict()

    LAST_REPORT_DF = df[df["Risk_Level"] != "LOW"][[
        "Last_Name",
        "First_Name",
        "Email",
        "Overall_Score",
        "Homework_Avg",
        "Quiz_Avg",
        "Test_Avg",
        "Risk_Score",
        "Risk_Level",
        "Risk_Reasons",
        "Intervention",
    ]].copy()

    LAST_EMAIL_DF = df[df["Risk_Level"] != "LOW"][[
        "First_Name",
        "Last_Name",
        "Email",
        "Risk_Level",
        "Risk_Score",
        "Draft_Email",
    ]].copy()

    LAST_EMAIL_DF = LAST_EMAIL_DF.rename(columns={
        "Draft_Email": "Email_Draft"
    })

    high_table = build_display_table(df, "HIGH")
    medium_table = build_display_table(df, "MEDIUM")

    return render_template_string(
        HTML,
        analyzed=True,
        filename=LAST_FILENAME,
        counts=LAST_COUNTS,
        total_students=len(df),
        top_reason=most_common_reason(df),
        high_table=high_table,
        medium_table=medium_table,
    )


@app.route("/download-report", methods=["GET"])
def download_report():
    global LAST_REPORT_DF, LAST_FILENAME
    if LAST_REPORT_DF is None:
        return "No report available. Please analyze a file first.", 400

    output = BytesIO()
    LAST_REPORT_DF.to_csv(output, index=False)
    output.seek(0)

    base = os.path.splitext(LAST_FILENAME or "report.csv")[0]
    download_name = f"{base}_at_risk_report.csv"
    return send_file(output, mimetype="text/csv", as_attachment=True, download_name=download_name)


@app.route("/download-emails", methods=["GET"])
def download_emails():
    global LAST_EMAIL_DF, LAST_FILENAME
    if LAST_EMAIL_DF is None:
        return "No email draft file available. Please analyze a file first.", 400

    output = BytesIO()
    LAST_EMAIL_DF.to_csv(output, index=False)
    output.seek(0)

    base = os.path.splitext(LAST_FILENAME or "report.csv")[0]
    download_name = f"{base}_email_drafts.csv"
    return send_file(output, mimetype="text/csv", as_attachment=True, download_name=download_name)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
