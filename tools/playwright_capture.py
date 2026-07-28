"""몰 무관 상세페이지 캡쳐 도구.

URL만 받으면 되고, 어떤 몰인지는 신경 쓰지 않는다 (재사용성 확보).
"""

from __future__ import annotations

from pathlib import Path

IMAGES_DIR = Path(__file__).resolve().parent.parent / "images"


def capture_product_image(url: str, product_id: str, selector: str | None = None) -> str:
    """헤드리스 브라우저로 url에 접속해 대표 이미지 영역을 캡쳐하고 저장 경로를 반환한다.

    selector가 주어지면 해당 요소만, 없으면 전체 화면을 캡쳐한다.
    """
    from playwright.sync_api import sync_playwright

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    output_path = IMAGES_DIR / f"{product_id}.png"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")

        if selector:
            page.locator(selector).first.screenshot(path=str(output_path))
        else:
            page.screenshot(path=str(output_path))

        browser.close()

    return str(output_path)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("사용법: python playwright_capture.py <url> <product_id> [selector]")
        raise SystemExit(1)

    path = capture_product_image(
        sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None
    )
    print(f"저장됨: {path}")
