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
<html>
<head>
<title>AI Early Warning System</title>
<style>
body {font-family: Arial; background:#f4f6fb; margin:40px;}
.card {background:white; padding:20px; border-radius:12px; margin-bottom:20px; box-shadow:0 4px 10px rgba(0,0,0,0.05);}
.btn {background:#2563eb;color:white;padding:10px 14px;border-radius:8px;text-decoration:none;border:0;cursor:pointer;}
.btn.secondary {background:#0f766e;}
.hero {background:#eef2ff;}
table {width:100%;border-collapse:collapse;}
th,td{padding:8px;border-bottom:1px solid #e5e7eb;}
</style>
</head>
<body>

<div class="card hero">
<h1>AI Early Warning System for Math Students</h1>
<p>This tool analyzes MyLabMath gradebook exports to identify students who may be at risk earlier than traditional indicators.</p>
</div>

<div class="card">
<h3>How to Export the File</h3>
<ol>
<li>Open MyLabMath</li>
<li>Go to Gradebook</li>
<li>Select <strong>Overview of Student Averages</strong></li>
<li>Export</li>
<li>Save as CSV</li>
</ol>
</div>

<div class="card">
<form method="post" action="/analyze" enctype="multipart/form-data">
<label>Instructor Name</label><br>
<input type="text" name="instructor_name" required><br><br>
<input type="file" name="file" accept=".csv" required><br><br>
<button class="btn">Analyze Student Risk</button>
</form>
</div>

{% if error_message %}
<div class="card">
<strong>Error:</strong> {{error_message}}
</div>
{% endif %}

{% if analyzed %}

<div class="card">
<h2>Results for {{filename}}</h2>
<p>Total Students: {{total_students}}</p>
<p>High Risk: {{counts.get('HIGH',0)}}</p>
<p>Medium Risk: {{counts.get('MEDIUM',0)}}</p>
<p>Low Risk: {{counts.get('LOW',0)}}</p>

<a class="btn" href="/download-report">Download At-Risk Report</a>
<a class="btn secondary" href="/download-emails">Download Email Drafts</a>
</div>

<div class="card">
<h3>High Risk Students</h3>
{{high_table|safe}}

<h3>Medium Risk Students</h3>
{{medium_table|safe}}
</div>

{% endif %}

</body>
</html>
"""

def risk_level(score):
    if score >= 6:
        return "HIGH"
    elif score >= 3:
        return "MEDIUM"
    return "LOW"

def draft_email(row,instructor):
    return f"""Subject: Quick Check-In

Hi {row['First_Name']},

I noticed you may be falling behind in the course.

Areas of concern: {row['Risk_Reasons']}

Please consider attending office hours so we can discuss strategies to get back on track.

Best,
{instructor}
"""

def calculate_risk(row,df):

    score = 0
    reasons = []

    if "Overall_Score" in df.columns and pd.notna(row["Overall_Score"]):
        if row["Overall_Score"] < 70:
            score += 3
            reasons.append("overall score below 70")

    if "Homework_Avg" in df.columns and pd.notna(row["Homework_Avg"]):
        if row["Homework_Avg"] < 70:
            score += 2
            reasons.append("homework average below 70")

    if "Quiz_Avg" in df.columns and pd.notna(row["Quiz_Avg"]):
        if row["Quiz_Avg"] < 65:
            score += 1
            reasons.append("quiz average below 65")

    if "Test_Avg" in df.columns and pd.notna(row["Test_Avg"]):
        if row["Test_Avg"] < 65:
            score += 3
            reasons.append("test average below 65")

    return pd.Series([score,"; ".join(reasons)])

def process_mylab_csv(file,instructor):

    df = pd.read_csv(file,header=2)

    if len(df.columns) == 12:
        df.columns = ["Last_Name","First_Name","Email","Login","Student_ID","Overall_Score","Homework_Avg","Quiz_Avg","Test_Avg","Other_Avg","StudyPlan_Avg","Extra"]

    elif len(df.columns) == 11:
        df.columns = ["Last_Name","First_Name","Email","Login","Student_ID","Overall_Score","Homework_Avg","Quiz_Avg","Test_Avg","Other_Avg","StudyPlan_Avg"]

    else:
        raise ValueError("Unexpected MyLabMath format.")

    df = df[df["Last_Name"]!="Last name"]

    for col in ["Overall_Score","Homework_Avg","Quiz_Avg","Test_Avg"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col],errors="coerce")

    df[["Risk_Score","Risk_Reasons"]] = df.apply(lambda r: calculate_risk(r,df),axis=1)

    df["Risk_Level"] = df["Risk_Score"].apply(risk_level)

    df["Draft_Email"] = df.apply(lambda r: draft_email(r,instructor),axis=1)

    return df

def build_table(df,level):

    d = df[df["Risk_Level"]==level]

    if d.empty:
        return "<p>No students</p>"

    d = d[["First_Name","Last_Name","Risk_Score","Risk_Reasons"]]

    return d.to_html(index=False)

@app.route("/")
def home():
    return render_template_string(HTML,analyzed=False,error_message=None)

@app.route("/analyze",methods=["POST"])
def analyze():

    global LAST_REPORT_DF,LAST_EMAIL_DF,LAST_FILENAME,LAST_COUNTS,LAST_INSTRUCTOR_NAME

    file = request.files["file"]
    instructor = request.form.get("instructor_name","Your Instructor")

    try:

        df = process_mylab_csv(file,instructor)

        LAST_FILENAME = file.filename
        LAST_COUNTS = df["Risk_Level"].value_counts().to_dict()

        LAST_REPORT_DF = df[df["Risk_Level"]!="LOW"]
        LAST_EMAIL_DF = df[df["Risk_Level"]!="LOW"][["First_Name","Last_Name","Email","Draft_Email"]]

        return render_template_string(
            HTML,
            analyzed=True,
            filename=file.filename,
            counts=LAST_COUNTS,
            total_students=len(df),
            high_table=build_table(df,"HIGH"),
            medium_table=build_table(df,"MEDIUM"),
            error_message=None
        )

    except Exception as e:

        return render_template_string(
            HTML,
            analyzed=False,
            error_message=str(e)
        )

@app.route("/download-report")
def download_report():

    output = BytesIO()
    LAST_REPORT_DF.to_csv(output,index=False)
    output.seek(0)

    return send_file(output,mimetype="text/csv",download_name="at_risk_report.csv",as_attachment=True)

@app.route("/download-emails")
def download_emails():

    output = BytesIO()
    LAST_EMAIL_DF.to_csv(output,index=False)
    output.seek(0)

    return send_file(output,mimetype="text/csv",download_name="email_drafts.csv",as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=5000)
