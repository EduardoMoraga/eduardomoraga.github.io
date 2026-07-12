"""Mantiene despiertas las apps de Streamlit Community Cloud del portfolio.

Streamlit hiberna las apps gratuitas tras ~12 h sin sesiones reales (websocket).
Este script abre cada app en un Chromium headless, aprieta el botón de "wake up"
si la app estaba dormida, y mantiene la sesión abierta ~45 s para que cuente
como actividad. Corre cada 6 h vía GitHub Actions.
"""

import asyncio
import sys

from playwright.async_api import async_playwright

APPS = [
    "https://latam-economic-dashboard-5ianvbjdquf2urrutmbhoy.streamlit.app/",
    "https://stock-price-predictor-vr5aubmeapze59cho3rnkd.streamlit.app/",
    "https://retail-price-tracker-2zmycjminl99dbvp8sevpn.streamlit.app/",
]

WAKE_TEXTS = ["Yes, get this app back up", "get this app back up"]
SESSION_SECONDS = 45


async def visit(browser, url: str) -> bool:
    page = await browser.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=120_000)
        await page.wait_for_timeout(5_000)

        woke = False
        for text in WAKE_TEXTS:
            btn = page.get_by_text(text, exact=False)
            if await btn.count():
                await btn.first.click()
                woke = True
                print(f"  {url} → estaba dormida, despertando…", flush=True)
                # despertar toma ~30-60 s; esperar a que arranque
                await page.wait_for_timeout(75_000)
                break

        # mantener la sesión websocket abierta para que cuente como actividad
        await page.wait_for_timeout(SESSION_SECONDS * 1_000)
        state = "despertada" if woke else "activa"
        print(f"  {url} → OK ({state})", flush=True)
        return True
    except Exception as exc:  # noqa: BLE001 — reportar y seguir con las demás
        print(f"  {url} → ERROR: {exc}", flush=True)
        return False
    finally:
        await page.close()


async def main() -> int:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        results = []
        for url in APPS:
            print(f"→ visitando {url}", flush=True)
            results.append(await visit(browser, url))
        await browser.close()
    failed = results.count(False)
    print(f"\nResumen: {results.count(True)}/{len(APPS)} apps OK")
    return 1 if failed == len(APPS) else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
