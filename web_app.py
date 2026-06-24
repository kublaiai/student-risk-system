from flask import Flask, request, render_template_string, send_file
import csv
import os
import re
from io import BytesIO, StringIO
from urllib.parse import quote

import pandas as pd

app = Flask(__name__)

LAST_REPORT_DF = None
LAST_EMAIL_DF = None
LAST_FILENAME = None
LAST_COUNTS = None
LAST_INSTRUCTOR_NAME = "Your Instructor"
LAST_WEIGHTS = {
    "homework": 20.0,
    "quiz": 10.0,
    "test": 60.0,
    "other": 10.0,
}
LAST_MYLAB_UPLOAD = None
LAST_CANVAS_UPLOAD = None
LAST_CANVAS_WEIGHTS = {
    "homework": 25.0,
    "quiz": 20.0,
    "test": 30.0,
    "final_exam": 25.0,
    "overall": 100.0,
}

HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Early Warning System</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    body { font-family: Arial, sans-serif; margin: 0; background: #F7F9FC; color: #1E3A5F; }
    .wrap { max-width: 1240px; margin: 40px auto; padding: 0 24px 56px; }
    .card { background: white; border-radius: 18px; padding: 30px; box-shadow: 0 4px 20px rgba(0,0,0,.05); margin-bottom: 24px; }
    h1, h2, h3 { margin-top: 0; }
    .muted { color: #56697d; }
    .btn { background: #1E3A5F; color: white; border: 0; border-radius: 10px; padding: 13px 18px; cursor: pointer; font-size: 15px; text-decoration: none; display: inline-block; }
    .btn.secondary { background: #0F766E; }
    .btn.light { background: #e8eef5; color: #1E3A5F; }
    .btn:hover { opacity: 0.95; }
    .hero { background: white; }
    .hero h1 { font-size: 44px; line-height: 1.08; margin-bottom: 8px; color: #1E3A5F; }
    .hero-subtitle { font-size: 20px; font-weight: 700; color: #0F766E; margin-bottom: 12px; }
    .hero-tagline { font-size: 14px; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; color: #64748b; margin-bottom: 18px; }
    .hero p { max-width: 940px; line-height: 1.78; margin-bottom: 0; font-size: 16px; }
    .kpi-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 18px; margin: 0 0 24px; }
    .kpi-card { background: white; border-radius: 18px; padding: 24px; box-shadow: 0 4px 20px rgba(0,0,0,.05); }
    .kpi-label { font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: .05em; color: #64748b; }
    .kpi-value { font-size: 30px; font-weight: 800; color: #1E3A5F; margin-top: 10px; }
    .kpi-subtext { font-size: 13px; color: #56697d; margin-top: 6px; }
    .info-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 18px; margin-top: 8px; }
    .info-box { background: white; border-radius: 18px; padding: 24px; box-shadow: 0 4px 20px rgba(0,0,0,.05); }
    .info-box h3 { margin-bottom: 14px; font-size: 18px; color: #1E3A5F; }
    .info-box ol, .info-box ul { margin: 0; padding-left: 18px; line-height: 1.9; color: #334155; }
    .section-label { font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: .05em; color: #64748b; margin: 0 0 14px; }
    .risk-chip-list { display: grid; gap: 12px; }
    .risk-level-item { display: grid; gap: 6px; }
    .risk-badge { display: inline-flex; align-items: center; gap: 8px; padding: 8px 12px; border-radius: 999px; font-size: 13px; font-weight: 700; }
    .risk-badge.on-track { background: #dcfce7; color: #166534; }
    .risk-badge.needs { background: #e0f2fe; color: #075985; }
    .risk-badge.at-risk { background: #fef3c7; color: #92400e; }
    .risk-badge.high { background: #fee2e2; color: #991b1b; }
    .risk-description { font-size: 14px; color: #56697d; line-height: 1.5; }
    .workflow-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; }
    .workflow-card { min-height: 210px; display: flex; flex-direction: column; justify-content: space-between; }
    .workflow-card h3 { margin-bottom: 10px; }
    .workflow-card p { line-height: 1.65; margin: 0 0 16px; }
    @media (max-width: 960px) {
      .hero h1 { font-size: 34px; }
      .kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .workflow-grid { grid-template-columns: 1fr; }
    }
    @media (max-width: 640px) {
      .wrap { padding: 0 16px 40px; }
      .card, .kpi-card, .info-box { padding: 22px; }
      .kpi-grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card hero">
      <h1>Student Success Intelligence Platform</h1>
      <div class="hero-subtitle">AI-Powered Student Risk Detection & Intervention</div>
      <div class="hero-tagline">Early Identification • Targeted Intervention • Better Outcomes</div>
      <p>
        The Student Success Intelligence Platform helps faculty identify at-risk students earlier using gradebook analytics, assessment trends, and intervention planning tools. By transforming Canvas and MyLabMath data into actionable insights, the platform supports proactive outreach, targeted academic support, and improved student success outcomes.
      </p>
    </div>

    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-label">Gradebook Sources</div>
        <div class="kpi-value">2</div>
        <div class="kpi-subtext">Canvas + MyLabMath</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Risk Categories</div>
        <div class="kpi-value">4</div>
        <div class="kpi-subtext">On Track → High Risk</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Intervention Support</div>
        <div class="kpi-value" style="font-size:24px;">AI-Powered</div>
        <div class="kpi-subtext">Guided outreach and planning</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Analysis Time</div>
        <div class="kpi-value">&lt; 2 Minutes</div>
        <div class="kpi-subtext">From upload to insights</div>
      </div>
    </div>

    <div class="card">
      <div class="section-label">Choose a Gradebook Source</div>
      <div class="workflow-grid">
        <div class="info-box workflow-card">
          <div>
          <h3>Analyze MyLabMath Gradebook</h3>
          <p class="muted">Upload the MyLabMath Overview of Student Averages CSV file, confirm assessment weights, and generate a student success report.</p>
          </div>
          <a class="btn" href="/mylab-upload">Analyze MyLabMath Gradebook</a>
        </div>
        <div class="info-box workflow-card">
          <div>
          <h3>Analyze Canvas Gradebook</h3>
          <p class="muted">Upload a Canvas Gradebook CSV export, auto-detect categories, and generate intervention recommendations.</p>
          </div>
          <a class="btn secondary" href="/canvas-upload">Analyze Canvas Gradebook</a>
        </div>
      </div>
    </div>

    <div class="info-grid">
      <div class="info-box">
        <h3>Student Success Indicators</h3>
        <ul>
          <li>✓ Course Performance Trends</li>
          <li>✓ Homework Completion</li>
          <li>✓ Quiz Performance</li>
          <li>✓ Exam Performance</li>
          <li>✓ Missing Major Assessments</li>
        </ul>
      </div>

      <div class="info-box">
        <h3>AI Intervention Support</h3>
        <ul>
          <li>✓ Risk Classification</li>
          <li>✓ Outreach Recommendations</li>
          <li>✓ Personalized Student Emails</li>
          <li>✓ Instructor Action Planning</li>
          <li>✓ Progress Monitoring</li>
        </ul>
      </div>

      <div class="info-box">
        <h3>Academic Risk Levels</h3>
        <div class="risk-chip-list">
          <div class="risk-level-item">
            <span class="risk-badge on-track">🟢 On Track</span>
            <div class="risk-description">Meeting course expectations</div>
          </div>
          <div class="risk-level-item">
            <span class="risk-badge needs">🔵 Needs Attention</span>
            <div class="risk-description">Monitor progress and provide support</div>
          </div>
          <div class="risk-level-item">
            <span class="risk-badge at-risk">🟡 At Risk</span>
            <div class="risk-description">Outreach recommended</div>
          </div>
          <div class="risk-level-item">
            <span class="risk-badge high">🔴 High Risk</span>
            <div class="risk-description">Immediate intervention recommended</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</body>
</html>
"""

MYLAB_UPLOAD_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MyLabMath Gradebook Upload</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 0; background: #f6f8fb; color: #1f2937; }
    .wrap { max-width: 1200px; margin: 36px auto; padding: 0 20px 40px; }
    .card { background: white; border-radius: 18px; padding: 24px; box-shadow: 0 10px 28px rgba(15, 23, 42, 0.08); margin-bottom: 20px; }
    .hero { background: linear-gradient(135deg, #eff6ff 0%, #f8fafc 100%); border: 1px solid #dbeafe; }
    .btn { background: #2563eb; color: white; border: 0; border-radius: 10px; padding: 12px 18px; cursor: pointer; font-size: 15px; text-decoration: none; display: inline-block; }
    .btn.secondary { background: #0f766e; }
    .btn.light { background: #e2e8f0; color: #1e293b; }
    .btn:disabled { background: #94a3b8; cursor: not-allowed; }
    .btn:hover { opacity: 0.95; }
    .muted { color: #667085; }
    .subtle { color: #475467; font-size: 13px; }
    .error-box { border: 1px solid #fecaca; background: #fff1f2; color: #b91c1c; }
    .flow-grid { display: grid; grid-template-columns: 1.25fr 1fr; gap: 16px; }
    .step-card { border: 1px solid #dbe5ef; border-radius: 16px; background: #f8fafc; padding: 20px; margin-top: 16px; }
    .step-label { display: inline-block; font-size: 12px; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; color: #2563eb; margin-bottom: 10px; }
    .upload-box { border: 2px dashed #cbd5e1; border-radius: 16px; padding: 20px; background: white; margin-top: 12px; }
    input[type=file], input[type=text], input[type=number] { padding: 10px; width: 320px; max-width: 100%; margin: 8px 0 16px; border: 1px solid #cbd5e1; border-radius: 10px; background: white; }
    .weights-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; margin: 8px 0 4px; }
    .weights-grid label { font-size: 13px; font-weight: 700; color: #334155; display: block; }
    .weights-grid input[type=number] { width: 100%; margin-top: 6px; margin-bottom: 0; }
    .status-row { display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; margin-top: 12px; }
    .validation-note { display: inline-flex; align-items: center; gap: 8px; padding: 10px 12px; border-radius: 12px; background: #fff7e6; color: #b45309; font-size: 13px; font-weight: 700; }
    .validation-note.valid { background: #ecfdf3; color: #047857; }
    .validation-icon { width: 22px; height: 22px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; background: rgba(255,255,255,0.8); font-size: 12px; font-weight: 900; }
    .summary-list { display: grid; gap: 10px; margin-top: 12px; }
    .summary-item { display: flex; justify-content: space-between; gap: 12px; padding: 12px 14px; border-radius: 12px; background: white; border: 1px solid #e2e8f0; }
    .detected-list { margin: 0; padding-left: 18px; line-height: 1.8; }
    .table-wrap { overflow-x: auto; border: 1px solid #e5e7eb; border-radius: 12px; margin-top: 12px; background: white; }
    .table-wrap table { width: 100%; border-collapse: collapse; margin-top: 0; min-width: 760px; }
    th, td { padding: 10px 12px; border-bottom: 1px solid #e5e7eb; text-align: left; vertical-align: top; }
    th { background: #f8fafc; font-weight: 700; font-size: 12px; text-transform: uppercase; letter-spacing: .04em; color: #475467; }
    .panel { background: #f8fafc; border: 1px solid #e5e7eb; border-radius: 14px; padding: 16px; }
    @media (max-width: 960px) { .flow-grid { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card hero">
      <h1>MyLabMath Gradebook Upload</h1>
      <p class="muted">Upload the MyLabMath Overview of Student Averages CSV file, review the detected categories, confirm the course weights from your syllabus, and generate the early warning report.</p>
      <div style="margin-top:16px;">
        <a class="btn light" href="/">Back to Home</a>
      </div>
    </div>

    {% if error_message %}
    <div class="card error-box">
      <strong>MyLabMath Upload Error</strong>
      <p style="margin-top:8px;">{{ error_message }}</p>
    </div>
    {% endif %}

    {% if not upload_ready %}
    <div class="card">
      <div class="step-card" style="margin-top:0;">
        <div class="step-label">Step 1</div>
        <h2>Upload MyLabMath CSV</h2>
        <p class="subtle" style="margin-top:0;">Please upload a CSV file.</p>
        <p class="subtle" style="margin-top:0;">Export the Overview of Student Averages from MyLabMath as a CSV file.</p>
        <form method="post" action="/mylab-upload" enctype="multipart/form-data">
          <div class="upload-box">
            <label for="instructor_name"><strong>Instructor Name</strong></label><br>
            <input type="text" name="instructor_name" id="instructor_name" placeholder="Enter instructor name" value="{{ instructor_name }}" required>
            <br>
            <label for="file"><strong>MyLabMath CSV</strong></label><br>
            <input type="file" name="file" id="file" accept=".csv" required>
            <br>
            <button class="btn" type="submit">Upload and Detect Categories</button>
          </div>
        </form>
      </div>
    </div>
    {% else %}
    <div class="flow-grid">
      <div class="card">
        <p class="muted">File: <strong>{{ filename }}</strong></p>

        <div class="step-card" style="margin-top:0;">
          <div class="step-label">Step 2</div>
          <h3>Detect Available Categories</h3>
          <ul class="detected-list">
            {% for item in detected_category_list %}
            <li>{{ item }}</li>
            {% endfor %}
          </ul>
        </div>

        <div class="step-card">
          <div class="step-label">Step 3</div>
          <h3>MyLabMath Categories Detected</h3>
          <div class="summary-list">
            {% for item in category_summary %}
            <div class="summary-item">
              <strong>{{ item.label }}</strong>
              <span class="muted">{{ item.status }}</span>
            </div>
            {% endfor %}
          </div>
        </div>

        <div class="step-card">
          <div class="step-label">Step 5</div>
          <h3>Weighted Components Preview</h3>
          <p class="subtle" style="margin-top:0;">Only relevant grade columns are shown below.</p>
          <div class="table-wrap">
            {{ preview_table|safe }}
          </div>
        </div>
      </div>

      <div class="card">
        <form method="post" action="/analyze" id="mylab-workflow-form">
          <input type="hidden" name="use_last_mylab_upload" value="1">
          <input type="hidden" name="instructor_name" value="{{ instructor_name }}">

          <div class="step-card" style="margin-top:0;">
            <div class="step-label">Step 4</div>
            <h3>Confirm Course Assessment Weights</h3>
            <p class="subtle">Enter the grading weights used in your course syllabus.</p>
            <div class="weights-grid">
              <div>
                <label for="weight_homework">Homework %</label>
                <input type="number" step="0.1" min="0" max="100" name="weight_homework" id="weight_homework" value="{{ weights.homework }}" required>
              </div>
              <div>
                <label for="weight_quiz">Quiz %</label>
                <input type="number" step="0.1" min="0" max="100" name="weight_quiz" id="weight_quiz" value="{{ weights.quiz }}" required>
              </div>
              <div>
                <label for="weight_test">Test %</label>
                <input type="number" step="0.1" min="0" max="100" name="weight_test" id="weight_test" value="{{ weights.test }}" required>
              </div>
              <div>
                <label for="weight_other">Other %</label>
                <input type="number" step="0.1" min="0" max="100" name="weight_other" id="weight_other" value="{{ weights.other }}" required>
              </div>
            </div>
            <div class="status-row">
              <div>
                <div style="font-weight:700;">Weights must total 100%.</div>
                <div class="subtle">Overall Score remains a universal risk indicator.</div>
              </div>
              <div id="weight-validation" class="validation-note" role="status" aria-live="polite">
                <span class="validation-icon" id="weight-validation-icon">!</span>
                <span id="weight-validation-text">Waiting for a valid 100% total</span>
              </div>
            </div>
          </div>

          <div class="step-card">
            <div class="step-label">Step 6</div>
            <h3>Generate MyLabMath Risk Report</h3>
            <p class="subtle" style="margin-top:0;">The existing risk and weighting logic will be applied to this upload.</p>
            <button class="btn secondary" type="submit" id="generate-report-button">Generate MyLabMath Risk Report</button>
          </div>
        </form>
      </div>
    </div>
    {% endif %}
  </div>
  <script>
    (function setupWeightValidation() {
      const inputs = [
        document.getElementById('weight_homework'),
        document.getElementById('weight_quiz'),
        document.getElementById('weight_test'),
        document.getElementById('weight_other')
      ].filter(Boolean);
      const button = document.getElementById('generate-report-button');
      const note = document.getElementById('weight-validation');
      const noteText = document.getElementById('weight-validation-text');
      const noteIcon = document.getElementById('weight-validation-icon');
      if (!inputs.length || !button || !note || !noteText || !noteIcon) return;

      function valueOf(input) {
        const value = parseFloat(input.value);
        return Number.isFinite(value) ? value : 0;
      }

      function updateValidation() {
        const total = inputs.reduce((sum, input) => sum + valueOf(input), 0);
        const valid = Math.abs(total - 100) < 0.01;
        note.classList.toggle('valid', valid);
        noteIcon.textContent = valid ? '✓' : '!';
        noteText.textContent = valid ? `Weights total ${total.toFixed(1)}%` : `Current total: ${total.toFixed(1)}%`;
        button.disabled = !valid;
      }

      inputs.forEach(input => input.addEventListener('input', updateValidation));
      updateValidation();
    })();
  </script>
</body>
</html>
"""

MYLAB_RESULTS_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MyLabMath Risk Report</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    body { font-family: Arial, sans-serif; margin: 0; background: #f6f8fb; color: #1f2937; }
    .wrap { max-width: 1280px; margin: 36px auto; padding: 0 20px 40px; }
    .card { background: white; border-radius: 18px; padding: 24px; box-shadow: 0 10px 28px rgba(15, 23, 42, 0.08); margin-bottom: 20px; }
    .hero { background: linear-gradient(135deg, #eff6ff 0%, #f8fafc 100%); border: 1px solid #dbeafe; }
    .btn { background: #2563eb; color: white; border: 0; border-radius: 10px; padding: 12px 18px; cursor: pointer; font-size: 15px; text-decoration: none; display: inline-block; }
    .btn.secondary { background: #0f766e; }
    .btn.light { background: #e2e8f0; color: #1e293b; }
    .muted { color: #667085; }
    .summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-top: 18px; }
    .metric { border-radius: 16px; padding: 18px; font-weight: bold; }
    .metric .label { display: block; font-size: 13px; font-weight: 600; opacity: 0.85; margin-bottom: 8px; }
    .metric .value { font-size: 32px; line-height: 1; }
    .total { background: #dbeafe; color: #1d4ed8; }
    .high { background: #fee2e2; color: #991b1b; }
    .medium { background: #fef3c7; color: #92400e; }
    .low { background: #dcfce7; color: #166534; }
    .analytics-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 16px; margin-top: 16px; }
    .panel { background: #f8fafc; border: 1px solid #e5e7eb; border-radius: 14px; padding: 14px; }
    .panel h4 { margin: 0 0 10px; font-size: 14px; text-transform: uppercase; letter-spacing: .04em; color: #475467; }
    .risk-bars { display: grid; gap: 10px; margin-top: 8px; }
    .risk-line { display: grid; grid-template-columns: 120px 1fr 55px; gap: 10px; align-items: center; font-size: 13px; }
    .bar-track { background: #e5e7eb; border-radius: 999px; height: 10px; overflow: hidden; }
    .bar-fill { height: 100%; border-radius: 999px; }
    .bar-fill.high { background: #d9a4a4; }
    .bar-fill.medium { background: #d9c08f; }
    .bar-fill.low { background: #9fc5af; }
    .kpi-row { display: grid; grid-template-columns: repeat(4, minmax(120px, 1fr)); gap: 10px; }
    .kpi { background: white; border: 1px solid #e5e7eb; border-radius: 12px; padding: 12px; }
    .kpi .kpi-label { font-size: 12px; color: #667085; font-weight: 600; }
    .kpi .kpi-value { font-size: 22px; font-weight: 800; margin-top: 6px; }
    .actions { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 18px; }
    .table-wrap { overflow-x: auto; border: 1px solid #e5e7eb; border-radius: 12px; margin-top: 12px; }
    .table-wrap table { width: 100%; margin-top: 0; border-collapse: collapse; min-width: 1220px; }
    th, td { padding: 10px 12px; border-bottom: 1px solid #e5e7eb; text-align: left; vertical-align: top; }
    th { background: #f8fafc; font-size: 12px; text-transform: uppercase; letter-spacing: .04em; color: #475467; }
    .toolbar { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; margin-top: 14px; }
    .toolbar input[type=text] { padding: 10px; width: 320px; max-width: 100%; margin: 0; border: 1px solid #cbd5e1; border-radius: 10px; }
    .chart-wrap { height: 190px; }
    .insight-list { margin: 10px 0 0; padding-left: 18px; line-height: 1.6; }
    .risk-badge { display:inline-block; padding:4px 10px; border-radius:999px; font-size:12px; font-weight:700; }
    .risk-badge.high { background:#fee2e2; color:#991b1b; }
    .risk-badge.medium { background:#fef3c7; color:#92400e; }
    .risk-badge.low { background:#dcfce7; color:#166534; }
    .mail-link { display:inline-block; padding:7px 11px; border-radius:999px; background:#e8eefc; color:#1d4ed8; font-size:12px; font-weight:700; text-decoration:none; }
    @media (max-width: 960px) {
      .analytics-grid { grid-template-columns: 1fr; }
      .kpi-row { grid-template-columns: repeat(2, minmax(120px, 1fr)); }
      .risk-line { grid-template-columns: 100px 1fr 48px; }
      .chart-wrap { height: 170px; }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card hero">
      <h1>MyLabMath Early Warning Dashboard</h1>
      <p class="muted">Instructor: <strong>{{ instructor_name }}</strong> | File: <strong>{{ filename }}</strong></p>
      <p class="muted">Course weights — Homework: <strong>{{ weights.homework }}%</strong>, Quiz: <strong>{{ weights.quiz }}%</strong>, Test: <strong>{{ weights.test }}%</strong>, Other: <strong>{{ weights.other }}%</strong>.</p>
      <div class="actions">
        <a class="btn light" href="/">Home</a>
        <a class="btn light" href="/mylab-upload">New MyLabMath Upload</a>
        <a class="btn" href="/download-report">Download Full Risk Report</a>
        <a class="btn secondary" href="/download-emails">Download Suggested Messages</a>
      </div>
    </div>

    <div class="card">
      <p class="muted">Excluded test/demo records: {{ excluded_count }}</p>
      {% if excluded_count > 0 %}
      <details>
        <summary style="cursor:pointer; font-weight:700; color:#1e293b;">Show excluded records</summary>
        <ul class="insight-list">
          {% for name in excluded_names %}
          <li>{{ name }}</li>
          {% endfor %}
        </ul>
      </details>
      {% endif %}

      <div class="summary-grid">
        <div class="metric total"><span class="label">TOTAL STUDENTS</span><span class="value">{{ total_students }}</span></div>
        <div class="metric high"><span class="label">HIGH RISK</span><span class="value">{{ counts.get('HIGH', 0) }}</span></div>
        <div class="metric medium"><span class="label">MEDIUM RISK</span><span class="value">{{ counts.get('MEDIUM', 0) }}</span></div>
        <div class="metric low"><span class="label">LOW RISK</span><span class="value">{{ counts.get('LOW', 0) }}</span></div>
      </div>

      <div class="analytics-grid">
        <div class="panel">
          <h4>Risk Distribution</h4>
          <div class="risk-bars">
            <div class="risk-line">
              <strong>High</strong>
              <div class="bar-track"><div class="bar-fill high" style="width: {{ percentages.high }}%"></div></div>
              <span>{{ percentages.high }}%</span>
            </div>
            <div class="risk-line">
              <strong>Medium</strong>
              <div class="bar-track"><div class="bar-fill medium" style="width: {{ percentages.medium }}%"></div></div>
              <span>{{ percentages.medium }}%</span>
            </div>
            <div class="risk-line">
              <strong>Low</strong>
              <div class="bar-track"><div class="bar-fill low" style="width: {{ percentages.low }}%"></div></div>
              <span>{{ percentages.low }}%</span>
            </div>
          </div>
        </div>

        <div class="panel">
          <h4>Class Snapshot</h4>
          <div class="kpi-row">
            <div class="kpi">
              <div class="kpi-label">Avg Overall</div>
              <div class="kpi-value">{{ class_summary.avg_overall }}</div>
            </div>
            <div class="kpi">
              <div class="kpi-label">Avg Homework</div>
              <div class="kpi-value">{{ class_summary.avg_homework }}</div>
            </div>
            <div class="kpi">
              <div class="kpi-label">Avg Quiz</div>
              <div class="kpi-value">{{ class_summary.avg_quiz }}</div>
            </div>
            <div class="kpi">
              <div class="kpi-label">Avg Test</div>
              <div class="kpi-value">{{ class_summary.avg_test }}</div>
            </div>
          </div>
        </div>
      </div>

      <div class="panel" style="margin-top:16px;">
        <h4>Risk Count Bar Chart</h4>
        <div class="chart-wrap">
          <canvas id="mylabRiskChart" aria-label="MyLabMath risk distribution chart" role="img"></canvas>
        </div>
      </div>
    </div>

    <div class="card">
      <h3>Instructor Insights</h3>
      <ul class="insight-list">
        <li><strong>Most common high-risk reason:</strong> {{ top_reason }}</li>
        <li><strong>Main concept gap:</strong> {{ main_concept_gap }}</li>
        <li><strong>Class weighted grade average:</strong> {{ class_weighted_avg }}</li>
        <li><strong>Recommended focus:</strong> Reach out first to students with the highest risk scores and lowest test averages.</li>
      </ul>
    </div>

    <div class="card">
      <div class="toolbar">
        <label for="search-all"><strong>Search Students</strong></label>
        <input id="search-all" type="text" placeholder="Type student, risk level, or reason..." oninput="filterTable('mylab-report-table', this.value)">
      </div>
      {{ full_table|safe }}
    </div>
  </div>
  <script>
    function filterTable(tableId, query) {
      const table = document.getElementById(tableId);
      if (!table) return;
      const q = (query || '').toLowerCase().trim();
      const rows = table.querySelectorAll('tbody tr');
      rows.forEach(row => {
        const text = row.innerText.toLowerCase();
        row.style.display = (!q || text.includes(q)) ? '' : 'none';
      });
    }

    (function renderMyLabRiskChart() {
      const canvas = document.getElementById('mylabRiskChart');
      if (!canvas || typeof Chart === 'undefined') return;
      new Chart(canvas, {
        type: 'bar',
        data: {
          labels: ['High', 'Medium', 'Low'],
          datasets: [{
            label: 'Students',
            data: [{{ counts.get('HIGH', 0) }}, {{ counts.get('MEDIUM', 0) }}, {{ counts.get('LOW', 0) }}],
            backgroundColor: ['#d9a4a4', '#d9c08f', '#9fc5af'],
            borderColor: ['#b77777', '#b99958', '#6f9f84'],
            borderWidth: 1.2,
            borderRadius: 8
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            y: {
              beginAtZero: true,
              ticks: { precision: 0 },
              title: { display: true, text: 'Number of Students' }
            }
          }
        }
      });
    })();
  </script>
</body>
</html>
"""

CANVAS_UPLOAD_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Canvas Gradebook Upload</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 0; background: #f6f8fb; color: #1f2937; }
    .wrap { max-width: 1200px; margin: 36px auto; padding: 0 20px 40px; }
    .card { background: white; border-radius: 18px; padding: 24px; box-shadow: 0 10px 28px rgba(15, 23, 42, 0.08); margin-bottom: 20px; }
    .hero { background: linear-gradient(135deg, #eff6ff 0%, #f8fafc 100%); border: 1px solid #dbeafe; }
    .btn { background: #2563eb; color: white; border: 0; border-radius: 10px; padding: 12px 18px; cursor: pointer; font-size: 15px; text-decoration: none; display: inline-block; }
    .btn.secondary { background: #0f766e; }
    .btn.light { background: #e2e8f0; color: #1e293b; }
    .btn:hover { opacity: 0.95; }
    .muted { color: #667085; }
    .error-box { border: 1px solid #fecaca; background: #fff1f2; color: #b91c1c; }
    .upload-box { border: 2px dashed #cbd5e1; border-radius: 16px; padding: 20px; background: #f8fafc; margin-top: 14px; }
    input[type=file], input[type=text], input[type=number], select { padding: 10px; width: 320px; max-width: 100%; margin: 8px 0 16px; border: 1px solid #cbd5e1; border-radius: 10px; background: white; }
    table { width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 14px; background: white; }
    th, td { padding: 10px 12px; border-bottom: 1px solid #e5e7eb; text-align: left; vertical-align: top; }
    th { background: #f8fafc; font-weight: 700; }
    .table-wrap { overflow-x: auto; border: 1px solid #e5e7eb; border-radius: 12px; margin-top: 12px; }
    .table-wrap table { margin-top: 0; min-width: 900px; }
    .weights-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 12px; margin: 8px 0 4px; }
    .weights-grid label { font-size: 13px; font-weight: 700; color: #334155; display: block; }
    .weights-grid input[type=number], .weights-grid select { width: 100%; margin-top: 6px; margin-bottom: 0; }
    .flow-grid { display: grid; grid-template-columns: 1.2fr 1fr; gap: 16px; }
    .candidate-list { margin: 0; padding-left: 18px; line-height: 1.7; }
    .subtle { color: #475467; font-size: 13px; }
    @media (max-width: 960px) { .flow-grid { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card hero">
      <h1>Canvas Gradebook Upload</h1>
      <p class="muted">Canvas exports vary by course, so this workflow keeps the instructor in control: upload the Canvas Gradebook CSV file, confirm the header row, map the columns, and then generate the same early-warning dashboard.</p>
      <div style="margin-top:16px;">
        <a class="btn light" href="/">Back to Home</a>
      </div>
    </div>

    {% if error_message %}
    <div class="card error-box">
      <strong>Canvas Upload Error</strong>
      <p style="margin-top:8px;">{{ error_message }}</p>
    </div>
    {% endif %}

    {% if not mapping_ready %}
    <div class="card">
      <p class="subtle" style="margin-top:0;">Please upload a CSV file.</p>
      <p class="subtle" style="margin-top:0;">Export the Canvas Gradebook as a CSV file.</p>
      <form method="post" action="/canvas-upload" enctype="multipart/form-data">
        <div class="upload-box">
          <strong>Upload Canvas Gradebook CSV</strong><br><br>
          <label for="instructor_name"><strong>Instructor Name</strong></label><br>
          <input type="text" name="instructor_name" id="instructor_name" placeholder="Enter instructor name" value="{{ instructor_name }}" required>
          <input type="file" name="file" accept=".csv" required>
          <br>
          <button class="btn" type="submit">Upload and Preview Columns</button>
        </div>
      </form>
      <p class="subtle" style="margin-top:12px;">A sample file has been added at <code>{{ sample_path }}</code> if you want a quick test case.</p>
    </div>
    {% else %}
    <div class="flow-grid">
      <div class="card">
        <p class="muted">File: <strong>{{ filename }}</strong></p>
        {% if header_detection_confident %}
        <p class="subtle" style="margin-top:0;">Canvas gradebook detected successfully.</p>
        {% else %}
        <h2>Header Review</h2>
        <p class="muted">Header detection needs confirmation for this file. Choose the best header row and refresh the preview.</p>
        <ol class="candidate-list">
          {% for candidate in header_candidates %}
          <li>
            <strong>Row {{ candidate.index + 1 }}</strong>:
            {{ candidate.preview }}
          </li>
          {% endfor %}
        </ol>

        <form method="post" action="/canvas-upload">
          <input type="hidden" name="action" value="refresh">
          <input type="hidden" name="instructor_name" value="{{ instructor_name }}">
          <label for="header_row"><strong>Header Row</strong></label><br>
          <select name="header_row" id="header_row">
            {% for candidate in header_candidates %}
            <option value="{{ candidate.index }}" {% if candidate.index == selected_header_row %}selected{% endif %}>
              Row {{ candidate.index + 1 }} - {{ candidate.preview }}
            </option>
            {% endfor %}
          </select>
          <br>
          <button class="btn light" type="submit">Refresh Mapping Preview</button>
        </form>
        {% endif %}

        <h3 style="margin-top:18px;">Weighted Components Preview</h3>
        <p class="subtle" style="margin-top:0;">This preview mirrors the weighted category columns instructors see in Canvas Gradebook.</p>
        <div class="table-wrap">
          {{ weighted_preview_table|safe }}
        </div>

        <details style="margin-top:16px;">
          <summary style="cursor:pointer; font-weight:700; color:#1e293b;">Show Full Canvas Export</summary>
          <div class="table-wrap" style="margin-top:12px;">
            {{ full_preview_table|safe }}
          </div>
        </details>
      </div>

      <div class="card">
        <div class="info-box" style="margin-bottom:18px;">
          <h3>Canvas Categories Detected</h3>
          <div class="subtle" style="line-height:1.8;">
            <div><strong>Overall:</strong> {{ detected_overall_label }}</div>
            <div><strong>Homework:</strong> {{ detected_homework_label }}</div>
            <div><strong>Quiz:</strong> {{ detected_quiz_label }}</div>
            <div><strong>Midterm/Test:</strong> {{ detected_test_label }}</div>
            <div><strong>Final:</strong> {{ detected_final_exam_label }}</div>
          </div>
        </div>
        <form method="post" action="/canvas-analyze">
          <input type="hidden" name="header_row" value="{{ selected_header_row }}">
          <input type="hidden" name="instructor_name" value="{{ instructor_name }}">

          <details style="margin-bottom:18px;">
            <summary style="cursor:pointer; font-weight:700; color:#1e293b;">Advanced: Change Detected Columns</summary>
            <div style="margin-top:14px;">
              {% if show_identity_controls %}
              <label for="student_name_column"><strong>Student Name Column</strong></label><br>
              <select name="student_name_column" id="student_name_column" required>
                {{ student_name_options|safe }}
              </select><br>

              <label for="student_id_column"><strong>Student ID Column (optional)</strong></label><br>
              <select name="student_id_column" id="student_id_column">
                {{ student_id_options|safe }}
              </select><br>
              {% else %}
              <input type="hidden" name="student_name_column" value="{{ detected_student_name_value }}">
              <input type="hidden" name="student_id_column" value="{{ detected_student_id_value }}">
              {% endif %}

              {% if not show_weights %}
              <input type="hidden" name="overall_grade_column" value="{{ detected_overall_value }}">
              {% else %}
              <label for="overall_grade_column"><strong>Canvas Total Score Column</strong></label><br>
              <p class="subtle" style="margin:-4px 0 6px;">This is Canvas’s weighted total course score. If present, the risk report uses this as the main overall grade.</p>
              <select name="overall_grade_column" id="overall_grade_column">
                {{ overall_grade_options|safe }}
              </select><br>
              {% endif %}

              <label for="homework_column"><strong>Homework Column/Category (optional)</strong></label><br>
              <select name="homework_column" id="homework_column">
                {{ homework_options|safe }}
              </select><br>

              <label for="quiz_column"><strong>Quiz Column/Category (optional)</strong></label><br>
              <select name="quiz_column" id="quiz_column">
                {{ quiz_options|safe }}
              </select><br>

              <label for="test_column"><strong>Test/Exam Column/Category (optional)</strong></label><br>
              <select name="test_column" id="test_column">
                {{ test_options|safe }}
              </select><br>

              <label for="final_exam_column"><strong>Final Exam Column/Category (optional)</strong></label><br>
              <select name="final_exam_column" id="final_exam_column">
                {{ final_exam_options|safe }}
              </select><br>
            </div>
          </details>

          {% if show_weights %}
          <label><strong>Weights</strong></label>
          <div class="weights-grid">
            <div>
              <label for="canvas_weight_homework">Homework %</label>
              <input type="number" step="0.1" min="0" max="100" name="canvas_weight_homework" id="canvas_weight_homework" value="{{ weights.homework }}">
            </div>
            <div>
              <label for="canvas_weight_quiz">Quiz %</label>
              <input type="number" step="0.1" min="0" max="100" name="canvas_weight_quiz" id="canvas_weight_quiz" value="{{ weights.quiz }}">
            </div>
            <div>
              <label for="canvas_weight_test">Test/Exam %</label>
              <input type="number" step="0.1" min="0" max="100" name="canvas_weight_test" id="canvas_weight_test" value="{{ weights.test }}">
            </div>
            <div>
              <label for="canvas_weight_final_exam">Final Exam %</label>
              <input type="number" step="0.1" min="0" max="100" name="canvas_weight_final_exam" id="canvas_weight_final_exam" value="{{ weights.final_exam }}">
            </div>
            <div>
              <label for="canvas_weight_overall">Overall Grade %</label>
              <input type="number" step="0.1" min="0" max="100" name="canvas_weight_overall" id="canvas_weight_overall" value="{{ weights.overall }}">
            </div>
          </div>
          <p class="subtle" style="margin:10px 0 14px;">If you choose an Overall Grade column, the system will use it directly for risk scoring. If you leave Overall Grade blank, the mapped component weights must add up to 100%.</p>
          {% else %}
          <input type="hidden" name="canvas_weight_homework" value="{{ weights.homework }}">
          <input type="hidden" name="canvas_weight_quiz" value="{{ weights.quiz }}">
          <input type="hidden" name="canvas_weight_test" value="{{ weights.test }}">
          <input type="hidden" name="canvas_weight_final_exam" value="{{ weights.final_exam }}">
          <input type="hidden" name="canvas_weight_overall" value="{{ weights.overall }}">
          {% endif %}

          <button class="btn secondary" type="submit">Generate Canvas Risk Report</button>
        </form>
      </div>
    </div>
    {% endif %}
  </div>
</body>
</html>
"""

CANVAS_RESULTS_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Canvas Risk Report</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    body { font-family: Arial, sans-serif; margin: 0; background: #f6f8fb; color: #1f2937; }
    .wrap { max-width: 1280px; margin: 36px auto; padding: 0 20px 40px; }
    .card { background: white; border-radius: 18px; padding: 24px; box-shadow: 0 10px 28px rgba(15, 23, 42, 0.08); margin-bottom: 20px; }
    .hero { background: linear-gradient(135deg, #eff6ff 0%, #f8fafc 100%); border: 1px solid #dbeafe; }
    .btn { background: #2563eb; color: white; border: 0; border-radius: 10px; padding: 12px 18px; cursor: pointer; font-size: 15px; text-decoration: none; display: inline-block; }
    .btn.secondary { background: #0f766e; }
    .btn.light { background: #e2e8f0; color: #1e293b; }
    .muted { color: #667085; }
    .summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-top: 18px; }
    .metric { border-radius: 16px; padding: 18px; font-weight: bold; }
    .metric .label { display: block; font-size: 13px; font-weight: 600; opacity: 0.85; margin-bottom: 8px; }
    .metric .value { font-size: 32px; line-height: 1; }
    .total { background: #dbeafe; color: #1d4ed8; }
    .high { background: #fee2e2; color: #991b1b; }
    .medium { background: #fef3c7; color: #92400e; }
    .needs { background: #e0f2fe; color: #075985; }
    .low { background: #dcfce7; color: #166534; }
    .analytics-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 16px; margin-top: 16px; }
    .panel { background: #f8fafc; border: 1px solid #e5e7eb; border-radius: 14px; padding: 14px; }
    .panel h4 { margin: 0 0 10px; font-size: 14px; text-transform: uppercase; letter-spacing: .04em; color: #475467; }
    .risk-bars { display: grid; gap: 10px; margin-top: 8px; }
    .risk-line { display: grid; grid-template-columns: 140px 1fr 55px; gap: 10px; align-items: center; font-size: 13px; }
    .bar-track { background: #e5e7eb; border-radius: 999px; height: 10px; overflow: hidden; }
    .bar-fill { height: 100%; border-radius: 999px; }
    .bar-fill.high { background: #d88b8b; }
    .bar-fill.medium { background: #d7b173; }
    .bar-fill.needs { background: #7eb2cf; }
    .bar-fill.low { background: #84b79d; }
    .kpi-row { display: grid; grid-template-columns: repeat(4, minmax(120px, 1fr)); gap: 10px; }
    .kpi { background: white; border: 1px solid #e5e7eb; border-radius: 12px; padding: 12px; }
    .kpi .kpi-label { font-size: 12px; color: #667085; font-weight: 600; }
    .kpi .kpi-value { font-size: 22px; font-weight: 800; margin-top: 6px; }
    .actions { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 18px; }
    .table-wrap { overflow-x: auto; border: 1px solid #e5e7eb; border-radius: 12px; margin-top: 12px; }
    .table-wrap table { width: 100%; margin-top: 0; border-collapse: collapse; min-width: 1100px; }
    th, td { padding: 10px 12px; border-bottom: 1px solid #e5e7eb; text-align: left; vertical-align: top; }
    th { background: #f8fafc; font-size: 12px; text-transform: uppercase; letter-spacing: .04em; color: #475467; }
    .toolbar { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; margin-top: 14px; }
    .toolbar input[type=text] { padding: 10px; width: 320px; max-width: 100%; margin: 0; border: 1px solid #cbd5e1; border-radius: 10px; }
    .chart-wrap { height: 190px; }
    .insight-list { margin: 10px 0 0; padding-left: 18px; line-height: 1.6; }
    .risk-badge { display:inline-block; padding:4px 10px; border-radius:999px; font-size:12px; font-weight:700; }
    .risk-badge.high { background:#fee2e2; color:#991b1b; }
    .risk-badge.at-risk { background:#fef3c7; color:#92400e; }
    .risk-badge.needs { background:#e0f2fe; color:#075985; }
    .risk-badge.on-track { background:#dcfce7; color:#166534; }
    .name-cell { display:inline-block; max-width:220px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; vertical-align:bottom; }
    .mail-link { display:inline-block; padding:7px 11px; border-radius:999px; background:#e8eefc; color:#1d4ed8; font-size:12px; font-weight:700; text-decoration:none; }
    @media (max-width: 960px) {
      .analytics-grid { grid-template-columns: 1fr; }
      .kpi-row { grid-template-columns: repeat(2, minmax(120px, 1fr)); }
      .risk-line { grid-template-columns: 120px 1fr 48px; }
      .chart-wrap { height: 170px; }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card hero">
      <h1>Canvas Early Warning Dashboard</h1>
      <p class="muted">Instructor: <strong>{{ instructor_name }}</strong> | File: <strong>{{ filename }}</strong></p>
      <p class="muted">Overall/current grade is {% if used_overall_direct %}coming directly from the mapped Canvas overall column{% else %}calculated from the mapped weighted components{% endif %}.</p>
      <div class="actions">
        <a class="btn light" href="/">Home</a>
        <a class="btn light" href="/canvas-upload">New Canvas Upload</a>
        <a class="btn" href="/download-report">Download Full Risk Report</a>
        <a class="btn secondary" href="/download-emails">Download Suggested Messages</a>
      </div>
    </div>

    <div class="card">
      <p class="subtle" style="margin-top:0;">Excluded test/demo records: {{ excluded_count }}</p>
      {% if excluded_count > 0 %}
      <details>
        <summary style="cursor:pointer; font-weight:700; color:#1e293b;">Show excluded records</summary>
        <ul class="insight-list">
          {% for name in excluded_names %}
          <li>{{ name }}</li>
          {% endfor %}
        </ul>
      </details>
      {% endif %}
      <div class="summary-grid">
        <div class="metric total"><span class="label">TOTAL STUDENTS</span><span class="value">{{ total_students }}</span></div>
        <div class="metric high"><span class="label">HIGH RISK</span><span class="value">{{ counts.get('High Risk', 0) }}</span></div>
        <div class="metric medium"><span class="label">AT RISK</span><span class="value">{{ counts.get('At Risk', 0) }}</span></div>
        <div class="metric needs"><span class="label">NEEDS ATTENTION</span><span class="value">{{ counts.get('Needs Attention', 0) }}</span></div>
        <div class="metric low"><span class="label">ON TRACK</span><span class="value">{{ counts.get('On Track', 0) }}</span></div>
      </div>

      <div class="analytics-grid">
        <div class="panel">
          <h4>Risk Distribution</h4>
          <div class="risk-bars">
            <div class="risk-line">
              <strong>High Risk</strong>
              <div class="bar-track"><div class="bar-fill high" style="width: {{ percentages.high }}%"></div></div>
              <span>{{ percentages.high }}%</span>
            </div>
            <div class="risk-line">
              <strong>At Risk</strong>
              <div class="bar-track"><div class="bar-fill medium" style="width: {{ percentages.at_risk }}%"></div></div>
              <span>{{ percentages.at_risk }}%</span>
            </div>
            <div class="risk-line">
              <strong>Needs Attention</strong>
              <div class="bar-track"><div class="bar-fill needs" style="width: {{ percentages.needs_attention }}%"></div></div>
              <span>{{ percentages.needs_attention }}%</span>
            </div>
            <div class="risk-line">
              <strong>On Track</strong>
              <div class="bar-track"><div class="bar-fill low" style="width: {{ percentages.on_track }}%"></div></div>
              <span>{{ percentages.on_track }}%</span>
            </div>
          </div>
        </div>

        <div class="panel">
          <h4>Class Snapshot</h4>
          <div class="kpi-row">
            <div class="kpi">
              <div class="kpi-label">Avg Overall</div>
              <div class="kpi-value">{{ class_summary.avg_overall }}</div>
            </div>
            <div class="kpi">
              <div class="kpi-label">Avg Homework</div>
              <div class="kpi-value">{{ class_summary.avg_homework }}</div>
            </div>
            <div class="kpi">
              <div class="kpi-label">Avg Quiz</div>
              <div class="kpi-value">{{ class_summary.avg_quiz }}</div>
            </div>
            <div class="kpi">
              <div class="kpi-label">Avg Test</div>
              <div class="kpi-value">{{ class_summary.avg_test }}</div>
            </div>
          </div>
        </div>
      </div>

      <div class="panel" style="margin-top:16px;">
        <h4>Risk Count Bar Chart</h4>
        <div class="chart-wrap">
          <canvas id="canvasRiskChart" aria-label="Canvas risk distribution chart" role="img"></canvas>
        </div>
      </div>
    </div>

    <div class="card">
      <h3>Instructor Insights</h3>
      <ul class="insight-list">
        <li><strong>Most common risk reason:</strong> {{ top_reason }}</li>
        <li><strong>Weighted mode used:</strong> {{ "Direct Overall Grade" if used_overall_direct else "Mapped Weighted Components" }}</li>
        <li><strong>Major exam status:</strong> {{ major_exam_status }}</li>
        <li><strong>Recommended focus:</strong> Reach out first to students with low overall grades or missing major exams.</li>
      </ul>
    </div>

    <div class="card">
      <div class="toolbar">
        <label for="search-all"><strong>Search Students</strong></label>
        <input id="search-all" type="text" placeholder="Type name, risk level, or reason..." oninput="filterTable('canvas-report-table', this.value)">
      </div>
      {{ full_table|safe }}
    </div>
  </div>
  <script>
    function filterTable(tableId, query) {
      const table = document.getElementById(tableId);
      if (!table) return;
      const q = (query || '').toLowerCase().trim();
      const rows = table.querySelectorAll('tbody tr');
      rows.forEach(row => {
        const text = row.innerText.toLowerCase();
        row.style.display = (!q || text.includes(q)) ? '' : 'none';
      });
    }

    (function renderCanvasRiskChart() {
      const canvas = document.getElementById('canvasRiskChart');
      if (!canvas || typeof Chart === 'undefined') return;
      new Chart(canvas, {
        type: 'bar',
        data: {
          labels: ['High Risk', 'At Risk', 'Needs Attention', 'On Track'],
          datasets: [{
            label: 'Students',
            data: [
              {{ counts.get('High Risk', 0) }},
              {{ counts.get('At Risk', 0) }},
              {{ counts.get('Needs Attention', 0) }},
              {{ counts.get('On Track', 0) }}
            ],
            backgroundColor: ['#d9a4a4', '#d9c08f', '#9fc3d7', '#9fc5af'],
            borderColor: ['#b77777', '#b99958', '#6f9fb8', '#6f9f84'],
            borderWidth: 1.2,
            borderRadius: 8
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false }
          },
          scales: {
            y: {
              beginAtZero: true,
              ticks: { precision: 0 },
              title: { display: true, text: 'Number of Students' }
            }
          }
        }
      });
    })();
  </script>
</body>
</html>
"""


def usable_column(df, col_name):
    return col_name in df.columns and df[col_name].notna().sum() > 0


def risk_level(score):
    if score >= 6:
        return "HIGH"
    if score >= 3:
        return "MEDIUM"
    return "LOW"


def mylab_student_name(row):
    full_name = str(row.get("Student_Display_Name", "") or "").strip()
    if full_name:
        return full_name
    first_name = str(row.get("First_Name", "") or "").strip()
    return first_name or "Student"


def format_preview_grade(value):
    if pd.isna(value):
        return "not posted"
    return f"{float(value):.1f}%"


def clean_reason_text(reason):
    text = str(reason or "").strip()
    if not text:
        return ""
    text = re.sub(r"\s*\(normalized weight [^)]+\)", "", text).strip()
    return text


def posted_categories_for_preview(row, workflow_type):
    if workflow_type == "canvas":
        categories = [
            ("overall/current grade", row.get("Overall_Current_Grade")),
            ("homework", row.get("Homework_Avg")),
            ("quiz", row.get("Quiz_Avg")),
            ("test", row.get("Test_Avg")),
            ("final exam", row.get("Final_Exam_Avg")),
        ]
    else:
        categories = [
            ("overall grade", row.get("Overall_Score")),
            ("homework", row.get("Homework_Avg")),
            ("quiz", row.get("Quiz_Avg")),
            ("test", row.get("Test_Avg")),
            ("other", row.get("Other_Avg")),
        ]
    return [(label, float(value)) for label, value in categories if pd.notna(value)]


def strongest_and_weakest_categories(row, workflow_type):
    categories = posted_categories_for_preview(row, workflow_type)
    academic_categories = [(label, value) for label, value in categories if label != "overall/current grade" and label != "overall grade"]
    if not academic_categories:
        return None, None
    strongest = max(academic_categories, key=lambda item: item[1])
    weakest = min(academic_categories, key=lambda item: item[1])
    return strongest, weakest


def build_student_ai_summary(row, workflow_type):
    risk_level_value = str(row.get("Risk_Level", "") or "")
    risk_level = risk_level_value if workflow_type == "canvas" else {
        "HIGH": "High Risk",
        "MEDIUM": "At Risk",
        "LOW": "On Track",
    }.get(risk_level_value, risk_level_value)

    reasons = [clean_reason_text(reason) for reason in str(row.get("Risk_Reasons", "") or "").split(";") if clean_reason_text(reason)]
    reason_text = " ".join(reasons).lower()
    strongest, weakest = strongest_and_weakest_categories(row, workflow_type)
    overall_value = row.get("Overall_Current_Grade") if workflow_type == "canvas" else row.get("Overall_Score")

    if risk_level == "High Risk":
        if "missing" in reason_text and "posted" in reason_text:
            return "Immediate meeting about missing posted work"
        if weakest:
            label = weakest[0]
            if label == "homework":
                return "Discuss homework recovery plan immediately"
            if label == "quiz":
                return "Urgent support for quiz performance"
            if label == "test":
                return "Immediate test recovery plan needed"
            if label == "final exam":
                return "Immediate final exam support needed"
            if label == "other":
                return "Immediate help with other coursework"
        if pd.notna(overall_value) and float(overall_value) < 60:
            return "Immediate meeting to improve overall grade"
        return "Urgent intervention needed"

    if risk_level in {"At Risk", "Medium Risk", "MEDIUM"}:
        if weakest:
            label = weakest[0]
            if label == "homework":
                return "Improve homework completion"
            if label == "quiz":
                return "Focus on quiz performance"
            if label == "test":
                return "Strengthen test preparation"
            if label == "final exam":
                return "Prepare for final exam improvement"
            if label == "other":
                return "Improve other course components"
        if pd.notna(overall_value):
            return "Improve overall course performance"
        return "Discuss steps to improve performance"

    if risk_level == "Needs Attention":
        if "missing" in reason_text and "posted" in reason_text:
            return "Monitor missing posted assessment"
        if weakest:
            label = weakest[0]
            if label == "homework":
                return "Watch homework progress"
            if label == "quiz":
                return "Continue improving quiz performance"
            if label == "test":
                return "Monitor test progress closely"
            if label == "final exam":
                return "Monitor final exam preparation"
            if label == "other":
                return "Monitor other coursework progress"
        return "Monitor progress before next assessment"

    if strongest:
        label = strongest[0]
        if label == "homework":
            return "Keep up strong homework performance"
        if label == "quiz":
            return "Keep up the good work"
        if label == "test":
            return "Stay consistent with test preparation"
        if label == "final exam":
            return "Stay consistent and engaged"
        if label == "other":
            return "Continue current performance"
    return "Stay consistent and engaged"


def build_student_email_preview(row, workflow_type):
    first_name = str(row.get("First_Name", "") or "").strip() or mylab_student_name(row).split()[0]
    risk_level_value = str(row.get("Risk_Level", "") or "")

    if workflow_type == "canvas":
        overall_value = row.get("Overall_Current_Grade")
        test_value = row.get("Test_Avg")
        final_exam_value = row.get("Final_Exam_Avg")
        risk_level = risk_level_value
    else:
        overall_value = row.get("Overall_Score")
        test_value = row.get("Test_Avg")
        final_exam_value = pd.NA
        risk_level = {"HIGH": "High Risk", "MEDIUM": "At Risk", "LOW": "On Track"}.get(risk_level_value, risk_level_value)

    homework_value = row.get("Homework_Avg")
    quiz_value = row.get("Quiz_Avg")
    reasons = [clean_reason_text(reason) for reason in str(row.get("Risk_Reasons", "") or "").split(";") if clean_reason_text(reason)]
    reason_sentence = reasons[0] if reasons else ""
    strongest, weakest = strongest_and_weakest_categories(row, workflow_type)

    performance_parts = [f"your current overall grade is {format_preview_grade(overall_value)}"]
    if pd.notna(homework_value):
        performance_parts.append(f"homework is {format_preview_grade(homework_value)}")
    if pd.notna(quiz_value):
        performance_parts.append(f"quiz is {format_preview_grade(quiz_value)}")
    if pd.notna(test_value):
        performance_parts.append(f"test is {format_preview_grade(test_value)}")
    if pd.notna(final_exam_value):
        performance_parts.append(f"final exam is {format_preview_grade(final_exam_value)}")

    missing_reason = any("missing" in reason.lower() and "posted" in reason.lower() for reason in reasons)

    if risk_level == "High Risk":
        details = []
        if strongest and strongest[1] >= 70:
            details.append(f"One strength to build on is your {strongest[0]} performance at {strongest[1]:.1f}%.")
        if weakest:
            details.append(f"The main concern right now is {weakest[0]} at {weakest[1]:.1f}%.")
        elif reason_sentence:
            details.append(f"The main concern right now is {reason_sentence}.")

        closing = "Please contact me immediately so we can discuss a plan to improve your grade moving forward."
        if missing_reason:
            closing = "Please contact me immediately so we can discuss missed work, make-up options, and a plan to improve your grade moving forward."

        body_parts = [
            f"Hi {first_name}, I am reaching out because your current results place you in the {risk_level} category.",
            "Right now, " + ", ".join(performance_parts) + ".",
        ]
        body_parts.extend(details)
        if reason_sentence and (not weakest or reason_sentence not in details[-1]):
            body_parts.append(f"I also noticed {reason_sentence}.")
        body_parts.append(closing)
        return " ".join(body_parts)

    if risk_level in {"At Risk", "Medium Risk", "MEDIUM"}:
        main_concern = reason_sentence
        if weakest:
            main_concern = f"your {weakest[0]} is currently {weakest[1]:.1f}%"
        body_parts = [
            f"Hi {first_name}, I noticed some warning signs in your current results and you are currently in the {risk_level} category.",
            "At the moment, " + ", ".join(performance_parts) + ".",
        ]
        if main_concern:
            body_parts.append(f"The main concern right now is {main_concern}.")
        body_parts.append("Please reach out so we can discuss your progress and identify steps to improve your grade moving forward.")
        return " ".join(body_parts)

    if risk_level == "Needs Attention":
        monitor_area = reason_sentence
        if weakest:
            monitor_area = f"your {weakest[0]} at {weakest[1]:.1f}%"
        body_parts = [
            f"Hi {first_name}, Great work so far.",
            "Your current results show that " + ", ".join(performance_parts) + ".",
        ]
        if monitor_area:
            body_parts.append(f"One area to keep monitoring is {monitor_area}.")
        body_parts.append("Please continue your progress and reach out if you would like help planning your next steps.")
        return " ".join(body_parts)

    strength = None
    if strongest:
        strength = f"your {strongest[0]} is currently {strongest[1]:.1f}%"
    elif pd.notna(overall_value):
        strength = f"your overall grade is {format_preview_grade(overall_value)}"
    body_parts = [
        f"Hi {first_name}, you are currently on track in the course.",
    ]
    if strength:
        body_parts.append(f"One of your strengths right now is that {strength}.")
    body_parts.append("Keep following the same study habits and stay consistent.")
    return " ".join(body_parts)


def intervention_action(row):
    return build_student_email_preview(row, "mylab")


def draft_email(row, instructor_name):
    return build_student_email_preview(row, "mylab")


def draft_encouragement_email(row, instructor_name):
    return f"""Subject: Great Progress in the Course

Hi {row['First_Name']},

You are doing a great job in the course so far. Keep up the strong work and continue the study habits that are helping you succeed.

Best regards,
{instructor_name}
"""


def build_mailto(email, subject, body):
    return f"mailto:{quote(str(email))}?subject={quote(subject)}&body={quote(body)}"


def read_mylab_upload(file_storage):
    raw_bytes = file_storage.read()
    file_storage.stream.seek(0)
    if not raw_bytes:
        raise ValueError("The uploaded CSV appears to be empty.")
    return raw_bytes


def parse_mylab_gradebook(file_stream):
    df = pd.read_csv(file_stream, header=2)

    if len(df.columns) == 12:
        df.columns = [
            "Last_Name", "First_Name", "Email", "Login", "Student_ID",
            "Overall_Score", "Homework_Avg", "Quiz_Avg", "Test_Avg",
            "Other_Avg", "StudyPlan_Avg", "Extra"
        ]
    elif len(df.columns) == 11:
        df.columns = [
            "Last_Name", "First_Name", "Email", "Login", "Student_ID",
            "Overall_Score", "Homework_Avg", "Quiz_Avg", "Test_Avg",
            "Other_Avg", "StudyPlan_Avg"
        ]
    else:
        raise ValueError(
            f"Unexpected number of columns in uploaded file: {len(df.columns)}. "
            "Please upload the MyLabMath 'Overview of Student Averages' export saved as CSV."
        )

    df = df[df["Last_Name"] != "Last name"]
    df = df[~df["Last_Name"].astype(str).str.contains("Inactive", case=False, na=False)]
    df = df.dropna(how="all").reset_index(drop=True)

    for col in ["Overall_Score", "Homework_Avg", "Quiz_Avg", "Test_Avg", "Other_Avg"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["Student_Display_Name"] = (
        df["First_Name"].fillna("").astype(str).str.strip() + " " +
        df["Last_Name"].fillna("").astype(str).str.strip()
    ).str.strip()
    return df


def looks_like_mdc_login(value):
    text = str(value or "").strip()
    return bool(re.fullmatch(r"[A-Za-z][A-Za-z0-9._-]{2,}", text))


def resolve_mylab_contact_target(row):
    email = str(row.get("Email", "") or "").strip()
    login = str(row.get("Login", "") or "").strip()

    if "@" in email:
        return email
    if "@" in login:
        return login
    if looks_like_mdc_login(login):
        return f"{login}@mymdc.net"
    return ""


def mylab_detection_summary(df):
    labels = [
        ("Overall_Score", "Overall Score"),
        ("Homework_Avg", "Homework Average"),
        ("Quiz_Avg", "Quiz Average"),
        ("Test_Avg", "Test Average"),
        ("Other_Avg", "Other Average"),
    ]
    return [f"✓ {label}" for col, label in labels if usable_column(df, col)]


def mylab_category_summary(df):
    labels = [
        ("Overall_Score", "Overall"),
        ("Homework_Avg", "Homework"),
        ("Quiz_Avg", "Quiz"),
        ("Test_Avg", "Test"),
        ("Other_Avg", "Other"),
    ]
    return [
        {"label": label, "status": "Detected" if usable_column(df, col) else "Not found in file"}
        for col, label in labels
    ]


def build_mylab_preview_table(df):
    preview = df.copy()
    preview_columns = [("Student_Display_Name", "Student"), ("Overall_Score", "Overall")]
    for source, label in [
        ("Homework_Avg", "Homework"),
        ("Quiz_Avg", "Quiz"),
        ("Test_Avg", "Test"),
        ("Other_Avg", "Other"),
    ]:
        if usable_column(preview, source):
            preview_columns.append((source, label))

    selected = preview[[source for source, _ in preview_columns]].head(8).copy()
    for column in selected.columns:
        if column != "Student_Display_Name":
            selected[column] = selected[column].apply(lambda value: "N/A" if pd.isna(value) else f"{float(value):.2f}")
    selected = selected.rename(columns={source: label for source, label in preview_columns})
    return selected.to_html(index=False, escape=False, table_id="mylab-preview-table")


def build_mylab_report_table(df):
    display = df[[
        "Student_Display_Name",
        "Overall_Score",
        "Homework_Avg",
        "Quiz_Avg",
        "Test_Avg",
        "Other_Avg",
        "Weighted_Grade",
        "Risk_Level",
        "Risk_Score",
        "Risk_Reasons",
    ]].copy()

    display["AI Summary"] = df.apply(lambda row: build_student_ai_summary(row, "mylab"), axis=1)

    display["Email Action"] = df.apply(
        lambda row: (
            f'<a class="mail-link" href="{build_mailto(row["Contact_Target"], "Course Progress Check-In", row["Draft_Email"] if pd.notna(row["Draft_Email"]) else "")}">Email Student</a>'
            if str(row.get("Contact_Target", "")).strip()
            else "Email unavailable"
        ),
        axis=1
    )

    badge_map = {
        "HIGH": '<span class="risk-badge high">High Risk</span>',
        "MEDIUM": '<span class="risk-badge medium">Medium Risk</span>',
        "LOW": '<span class="risk-badge low">Low Risk</span>',
    }
    display["Risk_Level"] = display["Risk_Level"].map(badge_map).fillna("N/A")

    for column in ["Overall_Score", "Homework_Avg", "Quiz_Avg", "Test_Avg", "Other_Avg", "Weighted_Grade", "Risk_Score"]:
        display[column] = display[column].apply(lambda value: "N/A" if pd.isna(value) else f"{float(value):.2f}")

    display["Risk_Reasons"] = display["Risk_Reasons"].apply(
        lambda value: "No major concerns identified" if pd.isna(value) or str(value).strip() == "" else value
    )
    display.columns = [
        "Student",
        "Overall",
        "Homework",
        "Quiz",
        "Test",
        "Other",
        "Weighted Grade",
        "Risk Level",
        "Risk Score",
        "Risk Factors",
        "AI Summary",
        "Email Action",
    ]

    sort_levels = df["Risk_Level"].map({"HIGH": 0, "MEDIUM": 1, "LOW": 2})
    display["_sort_level"] = sort_levels
    display["_sort_score"] = pd.to_numeric(df["Risk_Score"], errors="coerce")
    display = display.sort_values(by=["_sort_level", "_sort_score"], ascending=[True, False]).drop(columns=["_sort_level", "_sort_score"])
    return f"<div class='table-wrap'>{display.to_html(index=False, escape=False, classes='small', table_id='mylab-report-table')}</div>"


def render_mylab_upload(error_message=None, upload_ready=False, **kwargs):
    defaults = {
        "error_message": error_message,
        "upload_ready": upload_ready,
        "filename": "",
        "instructor_name": LAST_INSTRUCTOR_NAME,
        "detected_category_list": [],
        "category_summary": [],
        "preview_table": "<p class='muted'>No preview available yet.</p>",
        "weights": LAST_WEIGHTS,
    }
    defaults.update(kwargs)
    return render_template_string(MYLAB_UPLOAD_HTML, **defaults)


def validate_csv_filename(filename):
    if not filename or not filename.lower().endswith(".csv"):
        raise ValueError(
            "This tool only accepts CSV files. Please export your gradebook as a CSV file and upload it again."
        )


def parse_grading_weights(form_data):
    try:
        weights = {
            "homework": float(form_data.get("weight_homework", LAST_WEIGHTS["homework"])),
            "quiz": float(form_data.get("weight_quiz", LAST_WEIGHTS["quiz"])),
            "test": float(form_data.get("weight_test", LAST_WEIGHTS["test"])),
            "other": float(form_data.get("weight_other", LAST_WEIGHTS["other"])),
        }
    except ValueError as exc:
        raise ValueError("Please enter valid numeric values for all four weights.") from exc

    for label, value in weights.items():
        if value < 0:
            raise ValueError(f"{label.title()} weight cannot be negative.")

    total = round(sum(weights.values()), 2)
    if abs(total - 100.0) > 0.01:
        raise ValueError(f"Your weights currently add to {total}%. Please adjust them so they total 100%.")

    return weights


def get_active_normalized_weights(row, df, weights):
    mapping = {
        "homework": "Homework_Avg",
        "quiz": "Quiz_Avg",
        "test": "Test_Avg",
        "other": "Other_Avg",
    }

    active_raw_weights = {}
    for key, col in mapping.items():
        weight = float(weights.get(key, 0.0))
        if weight <= 0:
            continue
        if col in df.columns and pd.notna(row.get(col)):
            active_raw_weights[key] = weight

    total_active_weight = sum(active_raw_weights.values())
    if total_active_weight <= 0:
        return {}, mapping

    normalized = {key: value / total_active_weight for key, value in active_raw_weights.items()}
    return normalized, mapping


def calculate_weighted_grade(row, df, weights):
    normalized_weights, mapping = get_active_normalized_weights(row, df, weights)
    if not normalized_weights:
        return pd.NA

    weighted_sum = 0.0
    for key, normalized_weight in normalized_weights.items():
        col = mapping[key]
        weighted_sum += float(row[col]) * normalized_weight

    return round(weighted_sum, 2)


def calculate_risk_score(row, df, weights):
    score = 0.0
    reasons = []

    if usable_column(df, "Overall_Score") and pd.notna(row["Overall_Score"]) and row["Overall_Score"] < 70:
        score += 3.0
        reasons.append("overall score below 70")

    normalized_weights, _ = get_active_normalized_weights(row, df, weights)
    category_rules = [
        ("homework", "Homework_Avg", 70, "homework average below 70"),
        ("quiz", "Quiz_Avg", 65, "quiz average below 65"),
        ("test", "Test_Avg", 65, "test average below 65"),
        ("other", "Other_Avg", 70, "other average below 70"),
    ]
    category_risk_budget = 5.0

    for key, col, threshold, reason in category_rules:
        if key not in normalized_weights:
            continue
        if row[col] < threshold:
            pts = round(normalized_weights[key] * category_risk_budget, 2)
            score += pts
            reasons.append(f"{reason} (normalized weight {round(normalized_weights[key] * 100, 1)}%)")

    return pd.Series([round(score, 2), "; ".join(reasons)])


def process_mylab_csv(file_stream, instructor_name, weights):
    df = parse_mylab_gradebook(file_stream)

    df[["Risk_Score", "Risk_Reasons"]] = df.apply(lambda row: calculate_risk_score(row, df, weights), axis=1)
    df["Weighted_Grade"] = df.apply(lambda row: calculate_weighted_grade(row, df, weights), axis=1)
    df["Risk_Level"] = df["Risk_Score"].apply(risk_level)
    df["Intervention"] = df.apply(intervention_action, axis=1)
    df["Draft_Email"] = df.apply(lambda row: draft_email(row, instructor_name), axis=1)
    df["Encouragement_Email"] = df.apply(lambda row: draft_encouragement_email(row, instructor_name), axis=1)
    df["Contact_Target"] = df.apply(resolve_mylab_contact_target, axis=1)
    return df


def identify_main_concept_gap(df):
    category_map = {
        "Homework_Avg": "Homework",
        "Quiz_Avg": "Quiz",
        "Test_Avg": "Test",
        "Other_Avg": "Other",
    }
    means = {}
    for col, label in category_map.items():
        if col in df.columns:
            series = pd.to_numeric(df[col], errors="coerce")
            if series.notna().any():
                means[label] = float(series.mean())

    if not means:
        return "Insufficient assessment data to determine a concept gap"

    lowest_category = min(means, key=means.get)
    return f"{lowest_category} is the lowest performing assessment category (avg {means[lowest_category]:.1f})"


def most_common_reason(df):
    flagged = df[df["Risk_Level"] != "LOW"]
    if flagged.empty:
        return "No major risk patterns detected"

    all_reasons = []
    for reasons in flagged["Risk_Reasons"].dropna():
        all_reasons.extend([reason.strip() for reason in str(reasons).split(";") if reason.strip()])

    if not all_reasons:
        return "No major risk patterns detected"

    return pd.Series(all_reasons).value_counts().index[0]


def build_display_table(df, level, table_id):
    filtered = df[df["Risk_Level"] == level].copy()
    if filtered.empty:
        return f"<p class='muted'>No {level.lower()}-risk students found.</p>"

    filtered["Email_Action"] = filtered.apply(
        lambda row: f'<a class="btn mail" href="{build_mailto(row["Email"], f"{level.title()} Risk Check-In", row["Draft_Email"])}">Send Email</a>',
        axis=1
    )

    display_cols = [
        "First_Name", "Last_Name", "Weighted_Grade", "Risk_Score",
        "Risk_Reasons", "Intervention", "Email_Action"
    ]
    filtered = filtered[display_cols].sort_values(by="Risk_Score", ascending=False)
    table_html = filtered.to_html(index=False, escape=False, classes="small", table_id=table_id)
    return f"<div class='table-wrap'>{table_html}</div>"


def build_positive_recognition_table(df, table_id):
    recognized = df[
        (df["Risk_Level"] == "LOW") &
        (
            (pd.to_numeric(df["Overall_Score"], errors="coerce") >= 85) |
            (pd.to_numeric(df["Weighted_Grade"], errors="coerce") >= 85)
        )
    ].copy()

    if recognized.empty:
        return "<p class='muted'>No students currently meet the recognition criteria.</p>"

    recognized["Encouragement_Action"] = recognized.apply(
        lambda row: f'<a class="btn mail" href="{build_mailto(row["Email"], "Great Progress in the Course", row["Encouragement_Email"])}">Send Encouragement</a>',
        axis=1
    )

    display_cols = [
        "First_Name", "Last_Name", "Overall_Score", "Weighted_Grade", "Encouragement_Action"
    ]
    recognized = recognized[display_cols].sort_values(by=["Weighted_Grade", "Overall_Score"], ascending=False)
    table_html = recognized.to_html(index=False, escape=False, classes="small", table_id=table_id)
    return f"<div class='table-wrap'>{table_html}</div>"


def read_canvas_rows(file_storage):
    raw_bytes = file_storage.read()
    file_storage.stream.seek(0)
    text = raw_bytes.decode("utf-8-sig", errors="replace")
    rows = list(csv.reader(StringIO(text)))
    if not rows:
        raise ValueError("The uploaded CSV appears to be empty.")
    return raw_bytes, rows


def score_header_candidate(row):
    joined = " ".join(str(cell).strip().lower() for cell in row if str(cell).strip())
    if not joined:
        return -1
    score = 0
    keywords = ["student", "name", "id", "score", "grade", "current", "final", "section", "quiz", "exam", "homework"]
    for keyword in keywords:
        if keyword in joined:
            score += 3
    score += min(sum(1 for cell in row if str(cell).strip()), 20)
    if "points possible" in joined:
        score -= 10
    return score


def detect_canvas_header_candidates(rows):
    inspected = rows[: min(len(rows), 8)]
    scored = []
    for index, row in enumerate(inspected):
        preview = " | ".join(str(cell).strip() for cell in row[:8] if str(cell).strip())
        scored.append({"index": index, "preview": preview or "(blank row)", "score": score_header_candidate(row)})

    ordered = sorted(scored, key=lambda item: (-item["score"], item["index"]))
    unique = []
    seen = set()
    for item in ordered:
        if item["index"] in seen:
            continue
        unique.append({"index": item["index"], "preview": item["preview"]})
        seen.add(item["index"])
        if len(unique) == min(5, len(scored)):
            break

    return sorted(unique, key=lambda item: item["index"])


def header_detection_confident(rows):
    inspected = rows[: min(len(rows), 8)]
    scored = [{"index": index, "score": score_header_candidate(row)} for index, row in enumerate(inspected)]
    if not scored:
        return False
    ordered = sorted(scored, key=lambda item: (-item["score"], item["index"]))
    top = ordered[0]
    second_score = ordered[1]["score"] if len(ordered) > 1 else -999
    return top["score"] >= 18 and (top["score"] - second_score) >= 4


def dedupe_headers(headers):
    seen = {}
    clean_headers = []
    for index, header in enumerate(headers):
        value = str(header).strip() or f"Column_{index + 1}"
        count = seen.get(value, 0)
        if count:
            clean_headers.append(f"{value}_{count + 1}")
        else:
            clean_headers.append(value)
        seen[value] = count + 1
    return clean_headers


def build_canvas_dataframe(rows, header_row):
    max_cols = max(len(row) for row in rows)
    padded_rows = [row + [""] * (max_cols - len(row)) for row in rows]
    headers = dedupe_headers(padded_rows[header_row])
    df = pd.DataFrame(padded_rows[header_row + 1:], columns=headers)
    df = df.dropna(how="all")
    df = df[~df.apply(lambda row: all(str(value).strip() == "" for value in row), axis=1)]

    if not df.empty:
        first_col = df.columns[0]
        df = df[~df[first_col].astype(str).str.contains("Points Possible", case=False, na=False)]
        df = df[~df[first_col].astype(str).str.contains("^Student$", case=False, na=False)]

    return df.reset_index(drop=True)


def canvas_preview_table(rows, header_row):
    df = build_canvas_dataframe(rows, header_row)
    preview = df.head(8).copy()
    table_html = preview.to_html(index=False, escape=False, table_id="canvas-preview-table")
    return table_html, list(df.columns)


def guess_canvas_column(columns, keywords):
    for column in columns:
        lowered = column.lower()
        if any(keyword in lowered for keyword in keywords):
            return column
    return ""


CANVAS_TOTAL_COLUMNS = {
    "current score",
    "final score",
    "current grade",
    "final grade",
    "unposted current score",
    "unposted final score",
    "unposted current grade",
    "unposted final grade",
}


def is_canvas_summary_score_column(column):
    lowered = column.strip().lower()
    if lowered in CANVAS_TOTAL_COLUMNS:
        return False
    if "unposted" in lowered:
        return False
    if not (lowered.endswith("current score") or lowered.endswith("final score")):
        return False

    # Canvas assignment export columns often include section numbers or numeric assignment IDs.
    noisy_patterns = [
        r"\(\d+\)\s*$",
        r"\bsection\s+\d",
        r"\bmodule\s+\d",
        r"\bunit\s+\d",
        r"\bchapter\s+\d",
        r"\bweek\s+\d",
    ]
    return not any(re.search(pattern, lowered) for pattern in noisy_patterns)


def canvas_summary_sort_key(column):
    lowered = column.lower()
    return (0 if lowered.endswith("current score") else 1, len(column), lowered)


def detect_canvas_category_columns(columns):
    summary_columns = [column for column in columns if is_canvas_summary_score_column(column)]
    ordered_summary_columns = sorted(summary_columns, key=canvas_summary_sort_key)

    keyword_map = {
        "overall": [["current score"], ["final score"], ["current grade"], ["final grade"]],
        "homework": [["homework"], ["assignments"], ["hw"]],
        "quiz": [["quizzes"], ["quiz"]],
        "final_exam": [["final"]],
        "test": [["midterm"], ["proctored"], ["test"], ["exam"]],
    }

    def matches_keywords(column, keywords):
        lowered = column.lower()
        return any(keyword in lowered for keyword in keywords)

    detected = {
        "summary_columns": ordered_summary_columns,
        "overall": "Current Score" if "Current Score" in columns else guess_canvas_column(columns, ["current score", "current grade", "final score", "final grade"]),
        "homework": "",
        "quiz": "",
        "test": "",
        "final_exam": "",
    }

    for category in ["homework", "quiz", "final_exam", "test"]:
        for keyword_group in keyword_map[category]:
            match = next((column for column in ordered_summary_columns if matches_keywords(column, keyword_group)), "")
            if match:
                detected[category] = match
                break

    if detected["final_exam"]:
        filtered_test_columns = [column for column in ordered_summary_columns if column != detected["final_exam"]]
    else:
        filtered_test_columns = ordered_summary_columns

    if not detected["test"]:
        for keyword_group in keyword_map["test"]:
            match = next((column for column in filtered_test_columns if matches_keywords(column, keyword_group)), "")
            if match:
                detected["test"] = match
                break

    return detected


def detection_label(value):
    return value if value else "Not detected — select manually."


def find_first_column(columns, names):
    lowered_map = {column.strip().lower(): column for column in columns}
    for name in names:
        if name in lowered_map:
            return lowered_map[name]
    return ""


def build_canvas_student_email(series):
    cleaned = series.fillna("").astype(str).str.strip()
    return cleaned.apply(lambda value: f"{value}@mymdc.net" if value else "")


def build_weighted_components_preview(rows, header_row):
    df = build_canvas_dataframe(rows, header_row)
    columns = list(df.columns)
    detected = detect_canvas_category_columns(columns)

    student_column = find_first_column(columns, ["student", "name"]) or guess_canvas_column(columns, ["student", "name"])
    id_column = find_first_column(columns, ["id", "student id", "sis user id"])
    overall_current_score = find_first_column(columns, ["current score"])
    current_grade = find_first_column(columns, ["current grade"])

    preview_columns = []
    rename_map = {}
    for source, label in [
        (student_column, "Student"),
        (id_column, "ID"),
        (detected["homework"], "Homework Category Score"),
        (detected["quiz"], "Quiz Category Score"),
        (detected["test"], "Midterm/Test Category Score"),
        (detected["final_exam"], "Final Exam Category Score"),
        (overall_current_score, "Overall Current Score"),
        (current_grade, "Current Grade"),
    ]:
        if source and source in df.columns and source not in preview_columns:
            preview_columns.append(source)
            rename_map[source] = label

    if not preview_columns:
        return "<p class='muted'>No weighted Canvas component columns were detected yet.</p>", columns, detected

    preview = df[preview_columns].head(8).rename(columns=rename_map)
    table_html = preview.to_html(index=False, escape=False, table_id="canvas-weighted-preview-table")
    return table_html, columns, detected


def build_canvas_mapping_context(columns, selected_mapping=None, weights=None):
    selected_mapping = selected_mapping or {}
    detected = detect_canvas_category_columns(columns)
    undetected_label = "Not detected — select manually."
    overall_options = []
    for name in ["Current Score", "Final Score", "Current Grade", "Final Grade"]:
        if name in columns and name not in overall_options:
            overall_options.append(name)

    weighted_component_options = detected["summary_columns"]
    detected_student_name = selected_mapping.get("student_name_column", guess_canvas_column(columns, ["student", "name"]))
    detected_student_id = selected_mapping.get("student_id_column", guess_canvas_column(columns, ["sis user id", "student id", "sis login id", "id"]))
    show_identity_controls = not (detected_student_name and detected_student_id)
    show_weights = not bool(detected["overall"])

    return {
        "student_name_options": build_select_options(
            columns,
            detected_student_name,
            allow_blank=False,
        ),
        "student_id_options": build_select_options(
            columns,
            detected_student_id,
        ),
        "overall_grade_options": build_select_options(
            overall_options or columns,
            selected_mapping.get("overall_grade_column", detected["overall"]),
            blank_label=undetected_label,
        ),
        "homework_options": build_select_options(
            weighted_component_options,
            selected_mapping.get("homework_column", detected["homework"]),
            blank_label=undetected_label,
        ),
        "quiz_options": build_select_options(
            weighted_component_options,
            selected_mapping.get("quiz_column", detected["quiz"]),
            blank_label=undetected_label,
        ),
        "test_options": build_select_options(
            weighted_component_options,
            selected_mapping.get("test_column", detected["test"]),
            blank_label=undetected_label,
        ),
        "final_exam_options": build_select_options(
            weighted_component_options,
            selected_mapping.get("final_exam_column", detected["final_exam"]),
            blank_label=undetected_label,
        ),
        "detected_overall_label": detection_label(detected["overall"]),
        "detected_overall_value": detected["overall"],
        "detected_student_name_value": detected_student_name,
        "detected_student_id_value": detected_student_id,
        "detected_homework_label": detection_label(detected["homework"]),
        "detected_quiz_label": detection_label(detected["quiz"]),
        "detected_test_label": detection_label(detected["test"]),
        "detected_final_exam_label": detection_label(detected["final_exam"]),
        "show_identity_controls": show_identity_controls,
        "show_weights": show_weights,
        "weights": weights or LAST_CANVAS_WEIGHTS,
    }


def build_select_options(columns, selected_value, allow_blank=True, blank_label="-- Not Selected --"):
    options = []
    if allow_blank:
        selected_attr = " selected" if not selected_value else ""
        options.append(f'<option value=""{selected_attr}>{blank_label}</option>')

    for column in columns:
        selected_attr = " selected" if column == selected_value else ""
        options.append(f'<option value="{column}"{selected_attr}>{column}</option>')
    return "\n".join(options)


def parse_canvas_weights(form_data):
    try:
        weights = {
            "homework": float(form_data.get("canvas_weight_homework", LAST_CANVAS_WEIGHTS["homework"]) or 0),
            "quiz": float(form_data.get("canvas_weight_quiz", LAST_CANVAS_WEIGHTS["quiz"]) or 0),
            "test": float(form_data.get("canvas_weight_test", LAST_CANVAS_WEIGHTS["test"]) or 0),
            "final_exam": float(form_data.get("canvas_weight_final_exam", LAST_CANVAS_WEIGHTS["final_exam"]) or 0),
            "overall": float(form_data.get("canvas_weight_overall", LAST_CANVAS_WEIGHTS["overall"]) or 0),
        }
    except ValueError as exc:
        raise ValueError("Please enter valid numeric values for the Canvas weights.") from exc

    for label, value in weights.items():
        if value < 0:
            raise ValueError(f"{label.replace('_', ' ').title()} weight cannot be negative.")

    return weights


def coerce_canvas_numeric(series):
    cleaned = (
        series.astype(str)
        .str.replace("%", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.replace(r"[^\d.\-]", "", regex=True)
        .replace("", pd.NA)
    )
    return pd.to_numeric(cleaned, errors="coerce")


def split_canvas_name(value):
    text = str(value).strip()
    if not text:
        return "", ""
    if "," in text:
        last_name, first_name = [part.strip() for part in text.split(",", 1)]
        return first_name, last_name
    parts = text.split()
    if len(parts) == 1:
        return parts[0], ""
    return " ".join(parts[:-1]), parts[-1]


EXCLUDED_NAME_PATTERNS = [
    "test student",
    "student, test",
    "demo student",
    "sample student",
    "practice student",
]


def is_excluded_student_name(name):
    text = "" if pd.isna(name) else str(name).strip()
    if not text:
        return True
    lowered = text.lower()
    if any(pattern in lowered for pattern in EXCLUDED_NAME_PATTERNS):
        return True
    return lowered.startswith("test") or lowered.startswith("demo")


def apply_exclusion_flags(df, name_column):
    working = df.copy()
    working[name_column] = working[name_column].fillna("").astype(str).str.strip()
    working["Excluded_From_Analytics"] = working[name_column].apply(is_excluded_student_name)
    working["Excluded_Display_Name"] = working[name_column].replace("", "Blank student name")
    excluded_names = (
        working.loc[working["Excluded_From_Analytics"], "Excluded_Display_Name"]
        .dropna()
        .astype(str)
        .tolist()
    )
    analytics_df = working[~working["Excluded_From_Analytics"]].copy().reset_index(drop=True)
    return working, analytics_df, excluded_names


def column_administered_to_class(series, threshold=0.25):
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.empty:
        return False
    return (numeric.notna().mean() >= threshold)


def normalize_canvas_mapping(df, mapping, weights, instructor_name):
    working = df.copy()
    sis_login_column = find_first_column(list(working.columns), ["sis login id"])
    student_name_column = mapping["student_name_column"]
    working["Student_Name"] = working[student_name_column].astype(str).str.strip()
    working = working[working["Student_Name"] != ""].copy()

    if mapping["student_id_column"]:
        working["Student_ID"] = working[mapping["student_id_column"]].astype(str).str.strip()
    else:
        working["Student_ID"] = ""

    if sis_login_column and sis_login_column in working.columns:
        working["Student_Email"] = build_canvas_student_email(working[sis_login_column])
    else:
        working["Student_Email"] = ""

    exam_administered = {"test": False, "final_exam": False}

    for source_col, target_col in [
        (mapping["overall_grade_column"], "Overall_Current_Grade"),
        (mapping["homework_column"], "Homework_Avg"),
        (mapping["quiz_column"], "Quiz_Avg"),
        (mapping["test_column"], "Test_Avg"),
        (mapping["final_exam_column"], "Final_Exam_Avg"),
    ]:
        if source_col:
            working[target_col] = coerce_canvas_numeric(working[source_col])
            if target_col == "Test_Avg":
                exam_administered["test"] = column_administered_to_class(working[target_col])
            if target_col == "Final_Exam_Avg":
                exam_administered["final_exam"] = column_administered_to_class(working[target_col])
        else:
            working[target_col] = pd.NA

    use_direct_overall = bool(mapping["overall_grade_column"])
    if use_direct_overall:
        working["Calculated_Grade"] = working["Overall_Current_Grade"]
    else:
        weighted_pairs = [
            ("Homework_Avg", weights["homework"]),
            ("Quiz_Avg", weights["quiz"]),
            ("Test_Avg", weights["test"]),
            ("Final_Exam_Avg", weights["final_exam"]),
        ]

        def compute_weighted(row):
            weighted_total = 0.0
            total_weight = 0.0
            for column, weight in weighted_pairs:
                value = row[column]
                if weight > 0 and pd.notna(value):
                    weighted_total += float(value) * weight
                    total_weight += weight
            if total_weight <= 0:
                return pd.NA
            return round(weighted_total / total_weight, 2)

        working["Calculated_Grade"] = working.apply(compute_weighted, axis=1)
        working["Overall_Current_Grade"] = working["Calculated_Grade"]

    first_last = working["Student_Name"].apply(split_canvas_name)
    working["First_Name"] = first_last.apply(lambda pair: pair[0])
    working["Last_Name"] = first_last.apply(lambda pair: pair[1])

    def canvas_risk_details(row):
        reasons = []
        overall = row["Overall_Current_Grade"]
        homework = row["Homework_Avg"]
        quiz = row["Quiz_Avg"]
        test = row["Test_Avg"]
        final_exam = row["Final_Exam_Avg"]

        missing_major = False
        if mapping["test_column"] and exam_administered["test"] and pd.isna(test):
            missing_major = True
            reasons.append("midterm/test score missing after class assessment was posted")
        if mapping["final_exam_column"] and exam_administered["final_exam"] and pd.isna(final_exam):
            missing_major = True
            reasons.append("final exam score missing after class assessment was posted")

        if pd.isna(overall):
            reasons.append("overall/current grade unavailable")
        elif overall < 60:
            reasons.append("overall grade below 60")

        if pd.notna(overall) and 60 <= overall <= 69:
            reasons.append("overall grade between 60 and 69")

        if pd.notna(overall) and 70 <= overall <= 79:
            reasons.append("overall grade between 70 and 79")

        if pd.notna(homework) and homework < 70:
            reasons.append("homework average below 70")

        if pd.notna(quiz) and quiz < 70:
            reasons.append("quiz average below 70")

        if pd.notna(overall) and overall < 60:
            risk = "High Risk"
        elif pd.notna(overall) and 60 <= overall <= 69:
            risk = "At Risk"
        elif (
            (pd.notna(overall) and 70 <= overall <= 79) or
            (pd.notna(homework) and homework < 70) or
            (pd.notna(quiz) and quiz < 70) or
            missing_major
        ):
            risk = "Needs Attention"
        elif pd.isna(overall):
            risk = "At Risk"
        else:
            risk = "On Track"

        return pd.Series(
            [
                risk,
                "; ".join(dict.fromkeys(reasons)) if reasons else "no major concerns identified",
                missing_major,
            ]
        )

    working[["Risk_Level", "Risk_Reasons", "Missing_Major_Assessments"]] = working.apply(
        canvas_risk_details,
        axis=1
    )
    working["Suggested_Intervention_Message"] = working.apply(
        lambda row: build_student_email_preview(row, "canvas"),
        axis=1
    )
    working["Risk_Score"] = working["Risk_Level"].map({
        "On Track": 1,
        "Needs Attention": 2,
        "At Risk": 3,
        "High Risk": 4,
    })
    working["Intervention"] = working["Suggested_Intervention_Message"]
    working["Weighted_Grade"] = working["Calculated_Grade"]
    working["Draft_Email"] = working["Suggested_Intervention_Message"]
    working["Email"] = working["Student_Email"]
    working["Instructor_Name"] = instructor_name
    working["Test_Administered"] = exam_administered["test"]
    working["Final_Exam_Administered"] = exam_administered["final_exam"]
    return working.reset_index(drop=True), use_direct_overall


def validate_canvas_mapping(mapping, weights):
    if not mapping["student_name_column"]:
        raise ValueError("Please select a Student Name column.")

    has_overall = bool(mapping["overall_grade_column"])
    selected_component_columns = [
        mapping["homework_column"],
        mapping["quiz_column"],
        mapping["test_column"],
        mapping["final_exam_column"],
    ]
    has_components = any(selected_component_columns)

    if not has_overall and not has_components:
        raise ValueError("Please select an Overall Grade column or at least one weighted component column.")

    if not has_overall:
        selected_weights = {
            "homework": weights["homework"] if mapping["homework_column"] else 0.0,
            "quiz": weights["quiz"] if mapping["quiz_column"] else 0.0,
            "test": weights["test"] if mapping["test_column"] else 0.0,
            "final_exam": weights["final_exam"] if mapping["final_exam_column"] else 0.0,
        }
        active_total = round(sum(selected_weights.values()), 2)
        if active_total <= 0:
            raise ValueError("Please select at least one weighted component with a weight greater than 0.")
        if abs(active_total - 100.0) > 0.01:
            raise ValueError(f"The selected weighted components add up to {active_total}%. Please adjust them so they total 100%.")


def canvas_top_reason(df):
    all_reasons = []
    for reasons in df["Risk_Reasons"].dropna():
        all_reasons.extend([reason.strip() for reason in str(reasons).split(";") if reason.strip()])
    if not all_reasons:
        return "No major risk patterns detected"
    return pd.Series(all_reasons).value_counts().index[0]


def format_avg(series):
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.notna().any():
        return f"{numeric.mean():.1f}%"
    return "N/A"


def build_canvas_report_table(df):
    display = df[[
        "Student_Name",
        "Overall_Current_Grade",
        "Homework_Avg",
        "Quiz_Avg",
        "Test_Avg",
        "Risk_Level",
        "Risk_Reasons",
    ]].copy()
    display["AI Summary"] = df.apply(lambda row: build_student_ai_summary(row, "canvas"), axis=1)
    display["Email Student"] = df.apply(
        lambda row: (
            f'<a class="mail-link" href="{build_mailto(row["Student_Email"], "Course Progress Check-In", row["Suggested_Intervention_Message"] if pd.notna(row["Suggested_Intervention_Message"]) else "")}">Email Student</a>'
            if pd.notna(row["Student_Email"]) and str(row["Student_Email"]).strip()
            else "Email unavailable."
        ),
        axis=1
    )
    display = display.fillna(pd.NA)
    display["Student_Name"] = display["Student_Name"].apply(
        lambda value: f'<span class="name-cell" title="{str(value)}">{str(value)}</span>' if pd.notna(value) else "N/A"
    )
    display["Risk_Level"] = display["Risk_Level"].map({
        "High Risk": '<span class="risk-badge high">High Risk</span>',
        "At Risk": '<span class="risk-badge at-risk">At Risk</span>',
        "Needs Attention": '<span class="risk-badge needs">Needs Attention</span>',
        "On Track": '<span class="risk-badge on-track">On Track</span>',
    }).fillna("N/A")

    for column in ["Overall_Current_Grade", "Homework_Avg", "Quiz_Avg", "Test_Avg"]:
        display[column] = display[column].apply(lambda value: "N/A" if pd.isna(value) else f"{float(value):.2f}")

    for column in ["Risk_Reasons"]:
        display[column] = display[column].apply(lambda value: "Not posted" if pd.isna(value) or str(value).strip() == "" else value)

    display.columns = [
        "Student Name",
        "Overall/Current Grade",
        "Homework Average",
        "Quiz Average",
        "Test Average",
        "Risk Level",
        "Risk Reasons",
        "AI Summary",
        "Email Action",
    ]
    display = display.sort_values(by=["Risk Level", "Overall/Current Grade"], ascending=[True, True], na_position="last")
    return f"<div class='table-wrap'>{display.to_html(index=False, escape=False, classes='small', table_id='canvas-report-table')}</div>"


def render_canvas_upload(error_message=None, mapping_ready=False, **kwargs):
    defaults = {
        "error_message": error_message,
        "mapping_ready": mapping_ready,
        "filename": "",
        "instructor_name": LAST_INSTRUCTOR_NAME,
        "header_candidates": [],
        "selected_header_row": 0,
        "weighted_preview_table": "",
        "full_preview_table": "",
        "student_name_options": "",
        "student_id_options": "",
        "overall_grade_options": "",
        "homework_options": "",
        "quiz_options": "",
        "test_options": "",
        "final_exam_options": "",
        "detected_overall_label": detection_label(""),
        "detected_homework_label": detection_label(""),
        "detected_quiz_label": detection_label(""),
        "detected_test_label": detection_label(""),
        "detected_final_exam_label": detection_label(""),
        "detected_overall_value": "",
        "detected_student_name_value": "",
        "detected_student_id_value": "",
        "show_identity_controls": True,
        "show_weights": True,
        "header_detection_confident": False,
        "weights": LAST_CANVAS_WEIGHTS,
        "sample_path": "/Users/nashinikhan/Desktop/student_risk_system/sample_canvas_gradebook.csv",
    }
    defaults.update(kwargs)
    return render_template_string(CANVAS_UPLOAD_HTML, **defaults)


@app.route("/", methods=["GET"])
def home():
    return render_template_string(HTML)


@app.route("/health", methods=["GET"])
def health():
    return "ok", 200


@app.route("/mylab-upload", methods=["GET", "POST"])
def mylab_upload():
    global LAST_MYLAB_UPLOAD, LAST_INSTRUCTOR_NAME

    if request.method == "GET":
        return render_mylab_upload()

    instructor_name = request.form.get("instructor_name", "").strip() or "Your Instructor"
    LAST_INSTRUCTOR_NAME = instructor_name

    try:
        uploaded = request.files.get("file")
        if not uploaded or uploaded.filename == "":
            raise ValueError("Please upload a MyLabMath CSV file.")
        validate_csv_filename(uploaded.filename)

        raw_bytes = read_mylab_upload(uploaded)
        preview_df = parse_mylab_gradebook(BytesIO(raw_bytes))
        LAST_MYLAB_UPLOAD = {
            "filename": uploaded.filename,
            "raw_bytes": raw_bytes,
        }

        return render_mylab_upload(
            upload_ready=True,
            filename=uploaded.filename,
            instructor_name=instructor_name,
            detected_category_list=mylab_detection_summary(preview_df),
            category_summary=mylab_category_summary(preview_df),
            preview_table=build_mylab_preview_table(preview_df),
            weights=LAST_WEIGHTS,
        )
    except Exception as exc:
        return render_mylab_upload(error_message=str(exc), instructor_name=instructor_name), 400


@app.route("/canvas-upload", methods=["GET", "POST"])
def canvas_upload():
    global LAST_CANVAS_UPLOAD, LAST_INSTRUCTOR_NAME

    if request.method == "GET":
        return render_canvas_upload()

    instructor_name = request.form.get("instructor_name", "").strip() or "Your Instructor"
    LAST_INSTRUCTOR_NAME = instructor_name

    try:
        if request.form.get("action") == "refresh":
            if not LAST_CANVAS_UPLOAD:
                raise ValueError("Please upload a Canvas CSV file first.")
            header_row = int(request.form.get("header_row", LAST_CANVAS_UPLOAD["selected_header_row"]))
            rows = LAST_CANVAS_UPLOAD["rows"]
            weighted_preview_table, columns, _ = build_weighted_components_preview(rows, header_row)
            full_preview_table, _ = canvas_preview_table(rows, header_row)
            LAST_CANVAS_UPLOAD["selected_header_row"] = header_row
            return render_canvas_upload(
                mapping_ready=True,
                filename=LAST_CANVAS_UPLOAD["filename"],
                instructor_name=instructor_name,
                header_candidates=LAST_CANVAS_UPLOAD["header_candidates"],
                selected_header_row=header_row,
                header_detection_confident=LAST_CANVAS_UPLOAD.get("header_detection_confident", False),
                weighted_preview_table=weighted_preview_table,
                full_preview_table=full_preview_table,
                **build_canvas_mapping_context(columns, weights=LAST_CANVAS_WEIGHTS),
            )

        uploaded = request.files.get("file")
        if not uploaded or uploaded.filename == "":
            raise ValueError("Please upload a Canvas gradebook CSV file.")
        validate_csv_filename(uploaded.filename)

        raw_bytes, rows = read_canvas_rows(uploaded)
        header_candidates = detect_canvas_header_candidates(rows)
        selected_header_row = header_candidates[0]["index"] if header_candidates else 0
        LAST_CANVAS_UPLOAD = {
            "filename": uploaded.filename,
            "raw_bytes": raw_bytes,
            "rows": rows,
            "header_candidates": header_candidates,
            "selected_header_row": selected_header_row,
            "header_detection_confident": header_detection_confident(rows),
        }
        weighted_preview_table, columns, _ = build_weighted_components_preview(rows, selected_header_row)
        full_preview_table, _ = canvas_preview_table(rows, selected_header_row)
        return render_canvas_upload(
            mapping_ready=True,
            filename=uploaded.filename,
            instructor_name=instructor_name,
            header_candidates=header_candidates,
            selected_header_row=selected_header_row,
            header_detection_confident=LAST_CANVAS_UPLOAD["header_detection_confident"],
            weighted_preview_table=weighted_preview_table,
            full_preview_table=full_preview_table,
            **build_canvas_mapping_context(columns, weights=LAST_CANVAS_WEIGHTS),
        )
    except Exception as exc:
        return render_canvas_upload(error_message=str(exc), instructor_name=instructor_name), 400


@app.route("/canvas-analyze", methods=["POST"])
def canvas_analyze():
    global LAST_REPORT_DF, LAST_EMAIL_DF, LAST_FILENAME, LAST_COUNTS, LAST_CANVAS_WEIGHTS, LAST_INSTRUCTOR_NAME

    if not LAST_CANVAS_UPLOAD:
        return render_canvas_upload(error_message="Please upload a Canvas CSV file first."), 400

    instructor_name = request.form.get("instructor_name", "").strip() or "Your Instructor"
    LAST_INSTRUCTOR_NAME = instructor_name

    try:
        header_row = int(request.form.get("header_row", LAST_CANVAS_UPLOAD["selected_header_row"]))
        weights = parse_canvas_weights(request.form)
        mapping = {
            "student_name_column": request.form.get("student_name_column", "").strip(),
            "student_id_column": request.form.get("student_id_column", "").strip(),
            "overall_grade_column": request.form.get("overall_grade_column", "").strip(),
            "homework_column": request.form.get("homework_column", "").strip(),
            "quiz_column": request.form.get("quiz_column", "").strip(),
            "test_column": request.form.get("test_column", "").strip(),
            "final_exam_column": request.form.get("final_exam_column", "").strip(),
        }
        validate_canvas_mapping(mapping, weights)

        df = build_canvas_dataframe(LAST_CANVAS_UPLOAD["rows"], header_row)
        full_report_df, used_overall_direct = normalize_canvas_mapping(df, mapping, weights, instructor_name)
        full_report_df, report_df, excluded_names = apply_exclusion_flags(full_report_df, "Student_Name")
        LAST_CANVAS_WEIGHTS = weights
        LAST_FILENAME = LAST_CANVAS_UPLOAD["filename"]
        LAST_COUNTS = report_df["Risk_Level"].value_counts().to_dict()

        LAST_REPORT_DF = report_df[[
            "Student_Name",
            "Student_ID",
            "Student_Email",
            "Overall_Current_Grade",
            "Homework_Avg",
            "Quiz_Avg",
            "Test_Avg",
            "Final_Exam_Avg",
            "Risk_Level",
            "Risk_Reasons",
            "Suggested_Intervention_Message",
        ]].copy()

        LAST_EMAIL_DF = report_df[[
            "Student_Name",
            "Student_ID",
            "Student_Email",
            "Risk_Level",
            "Suggested_Intervention_Message",
        ]].copy()

        total_students = len(report_df)

        def pct(label):
            return round((int(LAST_COUNTS.get(label, 0)) / total_students) * 100) if total_students else 0

        class_summary = {
            "avg_overall": format_avg(report_df["Overall_Current_Grade"]),
            "avg_homework": format_avg(report_df["Homework_Avg"]),
            "avg_quiz": format_avg(report_df["Quiz_Avg"]),
            "avg_test": format_avg(report_df["Test_Avg"]),
        }
        test_administered = bool(report_df["Test_Administered"].iloc[0]) if not report_df.empty else False
        final_exam_administered = bool(report_df["Final_Exam_Administered"].iloc[0]) if not report_df.empty else False
        if test_administered or final_exam_administered:
            major_exam_status = f"{int(report_df['Missing_Major_Assessments'].sum())} students are missing a posted major exam score."
        else:
            major_exam_status = "Major exams appear not yet administered or not yet posted."

        return render_template_string(
            CANVAS_RESULTS_HTML,
            instructor_name=instructor_name,
            filename=LAST_FILENAME,
            total_students=total_students,
            excluded_count=len(excluded_names),
            excluded_names=excluded_names,
            counts=LAST_COUNTS,
            percentages={
                "high": pct("High Risk"),
                "at_risk": pct("At Risk"),
                "needs_attention": pct("Needs Attention"),
                "on_track": pct("On Track"),
            },
            class_summary=class_summary,
            top_reason=canvas_top_reason(report_df),
            full_table=build_canvas_report_table(report_df),
            used_overall_direct=used_overall_direct,
            major_exam_status=major_exam_status,
        )
    except Exception as exc:
        rows = LAST_CANVAS_UPLOAD["rows"]
        header_row = int(request.form.get("header_row", LAST_CANVAS_UPLOAD["selected_header_row"]))
        weighted_preview_table, columns, _ = build_weighted_components_preview(rows, header_row)
        full_preview_table, _ = canvas_preview_table(rows, header_row)
        return render_canvas_upload(
            error_message=str(exc),
            mapping_ready=True,
            filename=LAST_CANVAS_UPLOAD["filename"],
            instructor_name=instructor_name,
            header_candidates=LAST_CANVAS_UPLOAD["header_candidates"],
            selected_header_row=header_row,
            header_detection_confident=LAST_CANVAS_UPLOAD.get("header_detection_confident", False),
            weighted_preview_table=weighted_preview_table,
            full_preview_table=full_preview_table,
            **build_canvas_mapping_context(
                columns,
                selected_mapping={
                    "student_name_column": request.form.get("student_name_column", ""),
                    "student_id_column": request.form.get("student_id_column", ""),
                    "overall_grade_column": request.form.get("overall_grade_column", ""),
                    "homework_column": request.form.get("homework_column", ""),
                    "quiz_column": request.form.get("quiz_column", ""),
                    "test_column": request.form.get("test_column", ""),
                    "final_exam_column": request.form.get("final_exam_column", ""),
                },
                weights={
                    "homework": request.form.get("canvas_weight_homework", LAST_CANVAS_WEIGHTS["homework"]),
                    "quiz": request.form.get("canvas_weight_quiz", LAST_CANVAS_WEIGHTS["quiz"]),
                    "test": request.form.get("canvas_weight_test", LAST_CANVAS_WEIGHTS["test"]),
                    "final_exam": request.form.get("canvas_weight_final_exam", LAST_CANVAS_WEIGHTS["final_exam"]),
                    "overall": request.form.get("canvas_weight_overall", LAST_CANVAS_WEIGHTS["overall"]),
                },
            ),
        ), 400


@app.route("/analyze", methods=["POST"])
def analyze():
    global LAST_REPORT_DF, LAST_EMAIL_DF, LAST_FILENAME, LAST_COUNTS, LAST_INSTRUCTOR_NAME, LAST_WEIGHTS, LAST_MYLAB_UPLOAD

    uploaded = request.files.get("file")
    instructor_name = request.form.get("instructor_name", "").strip() or "Your Instructor"
    LAST_INSTRUCTOR_NAME = instructor_name

    try:
        selected_weights = parse_grading_weights(request.form)
    except ValueError as exc:
        preview_table = "<p class='muted'>No preview available yet.</p>"
        detected_category_list = []
        category_summary = []
        if LAST_MYLAB_UPLOAD:
            try:
                preview_df = parse_mylab_gradebook(BytesIO(LAST_MYLAB_UPLOAD["raw_bytes"]))
                preview_table = build_mylab_preview_table(preview_df)
                detected_category_list = mylab_detection_summary(preview_df)
                category_summary = mylab_category_summary(preview_df)
            except Exception:
                pass
        return render_mylab_upload(
            error_message=str(exc),
            upload_ready=bool(LAST_MYLAB_UPLOAD),
            filename=LAST_MYLAB_UPLOAD["filename"] if LAST_MYLAB_UPLOAD else "",
            instructor_name=LAST_INSTRUCTOR_NAME,
            detected_category_list=detected_category_list,
            category_summary=category_summary,
            preview_table=preview_table,
            weights=LAST_WEIGHTS,
        ), 400

    try:
        if uploaded and uploaded.filename:
            raw_bytes = read_mylab_upload(uploaded)
            LAST_MYLAB_UPLOAD = {
                "filename": uploaded.filename,
                "raw_bytes": raw_bytes,
            }
            file_stream = BytesIO(raw_bytes)
            active_filename = uploaded.filename
        elif request.form.get("use_last_mylab_upload") == "1" and LAST_MYLAB_UPLOAD:
            file_stream = BytesIO(LAST_MYLAB_UPLOAD["raw_bytes"])
            active_filename = LAST_MYLAB_UPLOAD["filename"]
        else:
            raise ValueError("Please upload a CSV file.")

        LAST_WEIGHTS = selected_weights
        full_df = process_mylab_csv(file_stream, LAST_INSTRUCTOR_NAME, LAST_WEIGHTS)
        full_df, df, excluded_names = apply_exclusion_flags(full_df, "Student_Display_Name")
        LAST_FILENAME = active_filename
        LAST_COUNTS = df["Risk_Level"].value_counts().to_dict()

        LAST_REPORT_DF = df[df["Risk_Level"] != "LOW"][
            ["Last_Name", "First_Name", "Email", "Login", "Overall_Score", "Homework_Avg",
             "Quiz_Avg", "Test_Avg", "Other_Avg", "Weighted_Grade", "Risk_Score", "Risk_Level", "Risk_Reasons",
             "Intervention"]
        ].copy()

        LAST_EMAIL_DF = df[df["Risk_Level"] != "LOW"][
            ["First_Name", "Last_Name", "Contact_Target", "Risk_Level", "Risk_Score", "Draft_Email"]
        ].copy().rename(columns={"Contact_Target": "Email_or_Login", "Draft_Email": "Email_Draft"})

        total_students = len(df)
        high_count = int(LAST_COUNTS.get("HIGH", 0))
        medium_count = int(LAST_COUNTS.get("MEDIUM", 0))
        low_count = int(LAST_COUNTS.get("LOW", 0))

        def pct(count):
            return round((count / total_students) * 100) if total_students else 0

        class_summary = {
            "avg_overall": format_avg(df["Overall_Score"]),
            "avg_homework": format_avg(df["Homework_Avg"]),
            "avg_quiz": format_avg(df["Quiz_Avg"]),
            "avg_test": format_avg(df["Test_Avg"]),
        }

        return render_template_string(
            MYLAB_RESULTS_HTML,
            filename=LAST_FILENAME,
            instructor_name=LAST_INSTRUCTOR_NAME,
            weights=LAST_WEIGHTS,
            total_students=total_students,
            excluded_count=len(excluded_names),
            excluded_names=excluded_names,
            counts=LAST_COUNTS,
            percentages={
                "high": pct(high_count),
                "medium": pct(medium_count),
                "low": pct(low_count),
            },
            class_summary=class_summary,
            top_reason=most_common_reason(df),
            main_concept_gap=identify_main_concept_gap(df),
            class_weighted_avg=format_avg(df["Weighted_Grade"]),
            full_table=build_mylab_report_table(df),
        )
    except Exception as exc:
        preview_table = "<p class='muted'>No preview available yet.</p>"
        detected_category_list = []
        category_summary = []
        if LAST_MYLAB_UPLOAD:
            try:
                preview_df = parse_mylab_gradebook(BytesIO(LAST_MYLAB_UPLOAD["raw_bytes"]))
                preview_table = build_mylab_preview_table(preview_df)
                detected_category_list = mylab_detection_summary(preview_df)
                category_summary = mylab_category_summary(preview_df)
            except Exception:
                pass
        return render_mylab_upload(
            error_message=(
                "Unable to process this file. Please make sure you uploaded the "
                "MyLabMath 'Overview of Student Averages' export saved as CSV. "
                f"Technical error: {str(exc)}"
            ),
            upload_ready=bool(LAST_MYLAB_UPLOAD),
            filename=LAST_MYLAB_UPLOAD["filename"] if LAST_MYLAB_UPLOAD else "",
            instructor_name=LAST_INSTRUCTOR_NAME,
            detected_category_list=detected_category_list,
            category_summary=category_summary,
            preview_table=preview_table,
            weights=selected_weights,
        ), 400


@app.route("/download-report", methods=["GET"])
def download_report():
    global LAST_REPORT_DF, LAST_FILENAME
    if LAST_REPORT_DF is None:
        return "No report available. Please analyze a file first.", 400

    output = BytesIO()
    LAST_REPORT_DF.to_csv(output, index=False)
    output.seek(0)

    base = os.path.splitext(LAST_FILENAME or "report.csv")[0]
    return send_file(
        output,
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"{base}_risk_report.csv",
    )


@app.route("/download-emails", methods=["GET"])
def download_emails():
    global LAST_EMAIL_DF, LAST_FILENAME
    if LAST_EMAIL_DF is None:
        return "No message draft file available. Please analyze a file first.", 400

    output = BytesIO()
    LAST_EMAIL_DF.to_csv(output, index=False)
    output.seek(0)

    base = os.path.splitext(LAST_FILENAME or "report.csv")[0]
    return send_file(
        output,
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"{base}_message_drafts.csv",
    )


application = app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    auto_reload = os.environ.get("AUTO_RELOAD", "1") == "1"
    debug_mode = os.environ.get("DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug_mode, use_reloader=auto_reload)
