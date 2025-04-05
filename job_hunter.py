# job_hunter.py
# QA Job Alert Bot for Upender (Canada/Remote QA roles)

import requests
import os
from bs4 import BeautifulSoup
import yagmail
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import time

# === CONFIGURATION ===
EMAIL = os.getenv("EMAIL")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")
SHEET_NAME = "QA Job Alerts"
GOOGLE_CREDENTIALS_FILE = "google-credentials.json"  # Must be in the same folder

# === JOB TITLES TO SEARCH ===
job_roles = [
    "QA Automation Engineer", "Senior QA", "QA Lead", "SDET", "Salesforce QA",
    "Salesforce Tester", "QA Analyst", "QA with Selenium", "QA Engineer",
    "API Automation Tester", "Mobile QA Automation", "Test Automation Lead"
]

# === Build DuckDuckGo search queries ===
queries = [
    f'"{role}" ("remote" OR "hybrid") site:careers.*.ca OR site:jobs.*.ca OR site:*.ca "apply now" OR "submit resume"'
    for role in job_roles
]

# === Setup Google Sheets access ===
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDENTIALS_FILE, scope)
client = gspread.authorize(creds)
sheet = client.open(SHEET_NAME).sheet1

# === Setup Gmail sending ===
yag = yagmail.SMTP(EMAIL, EMAIL_APP_PASSWORD)

# === Main Script ===
today = datetime.now().strftime("%Y-%m-%d")
found_jobs = []

headers = {"User-Agent": "Mozilla/5.0"}

for query in queries:
    url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    for a in soup.select("a.result__a"):
        link = a["href"]
        title = query.split('"')[1]
        if "job" in link or "career" in link:
            found_jobs.append((today, title, link))

    time.sleep(5)

# === Notify + Log ===
if found_jobs:
    print(f"🔍 Found {len(found_jobs)} job links.")
    body = "\n".join([f"{title}: {url}" for _, title, url in found_jobs])

    # Send Email
    yag.send(
        to=EMAIL,
        subject=f"🧠 QA Job Alerts - {today}",
        contents=f"Here are your QA job matches:\n\n{body}"
    )

    # Log to Sheet
    for entry in found_jobs:
        sheet.append_row(list(entry))
else:
    print("ℹ️ No new job listings found.")