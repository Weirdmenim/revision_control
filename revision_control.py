import os
import shutil
import pandas as pd
from git import Repo
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

# 1) Load env vars
load_dotenv()
DRAWING_DIR = os.getenv("DRAWING_DIR", "drawings")
REPO_PATH   = os.getenv("REPO_PATH", ".")
SMTP_HOST   = os.getenv("SMTP_HOST")
SMTP_PORT   = int(os.getenv("SMTP_PORT", 587))
SMTP_USER   = os.getenv("SMTP_USER")
SMTP_PASS   = os.getenv("SMTP_PASS")
EMAIL_RECIP = os.getenv("EMAIL_RECIP")

# 2) Read change list
df = pd.read_csv("change_list.csv")

# 3) Rename files and collect mapping
mapping = []
for _, row in df.iterrows():
    orig = os.path.join(DRAWING_DIR, row.original_file)
    if not os.path.exists(orig):
        raise FileNotFoundError(f"{row.original_file} not found in {DRAWING_DIR}")
    name, ext = os.path.splitext(row.original_file)
    new_name = f"{name}_rev{row.revision_code}{ext}"
    new_path = os.path.join(DRAWING_DIR, new_name)

    # backup (optional)
    shutil.copy2(orig, orig + ".bak")
    os.rename(orig, new_path)
    mapping.append((row.original_file, new_name))

# 4) Git stage, commit, push
repo = Repo(REPO_PATH)
repo.git.add(DRAWING_DIR)
commit_msg = "Auto‐revision update:\n" + "\n".join(f"{o}→{n}" for o,n in mapping)
repo.index.commit(commit_msg)
origin = repo.remote(name="origin")
origin.push()

# 5) Email summary
msg = EmailMessage()
msg["Subject"] = "Drawing Revision Update"
msg["From"] = SMTP_USER
msg["To"]   = EMAIL_RECIP
body = "The following files have been revised:\n\n" + \
       "\n".join(f"{o}  →  {n}" for o,n in mapping)
msg.set_content(body)

with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
    s.starttls()
    s.login(SMTP_USER, SMTP_PASS)
    s.send_message(msg)

print("Revision complete, commit pushed, and summary emailed.")
