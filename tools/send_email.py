"""완성된 초안(drafts/<job_id>.html)을 네이버 SMTP로 사용자 본인 메일에 전달한다.

API 크레딧이 필요 없는 로컬 스케줄 경로(경로 B)의 마지막 배송 단계.
NAVER_SMTP_USER/NAVER_SMTP_APP_PASSWORD가 없으면 예외를 발생시키고, 호출부(스킬)가
"결과는 drafts/ 폴더에 그대로 남아있다"는 로컬 폴백으로 처리하게 한다.
"""

from __future__ import annotations

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

SMTP_HOST = "smtp.naver.com"
SMTP_PORT = 587


def send_draft_email(job_id: str, draft_html_path: str, to_addr: str | None = None) -> None:
    user = os.environ["NAVER_SMTP_USER"]
    from_addr = user if "@" in user else f"{user}@naver.com"
    app_password = os.environ["NAVER_SMTP_APP_PASSWORD"]
    to_addr = to_addr or os.environ["NOTIFY_EMAIL_TO"]

    body_html = Path(draft_html_path).read_text(encoding="utf-8")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[AutoPost] 오늘의 블로그 초안 — {job_id}"
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(user, app_password)
        server.sendmail(from_addr, [to_addr], msg.as_string())


if __name__ == "__main__":
    import sys

    from dotenv import load_dotenv

    load_dotenv()

    if len(sys.argv) < 3:
        print("사용법: python -m tools.send_email <job_id> <draft_html_path>")
        raise SystemExit(1)

    send_draft_email(sys.argv[1], sys.argv[2])
    print(f"메일 발송 완료: {sys.argv[1]}")
