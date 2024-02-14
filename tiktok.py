import os
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
from util.util import (
    updating_sheet,
    scroll_tiktok,
    filter_tiktok,
)
from time import sleep

load_dotenv("env.env")
# the subject to be scraped
KEYWORD = os.environ.get("KEYWORD")
USER_AGENT = os.environ.get("USER_AGENT")
# Get Tiktok Credentials
TIKTOK_BASE_URL = os.environ.get("TIKTOK_BASE_URL")


def tiktok_scraping():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            # most common desktop viewport is 1920x1080
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()
        if USER_AGENT:
            page.set_extra_http_headers({"User-Agent": USER_AGENT})
        page.goto(TIKTOK_BASE_URL + "/tag/" + KEYWORD)
        page.wait_for_load_state("load")
        sleep(3)
        # scroll through tiktok and return the result details
        all_tiktoks = scroll_tiktok(page)
        print("all tiktoks", all_tiktoks)
        final_tiktoks = filter_tiktok(page, all_tiktoks, 50)
        print("final tiktoks", final_tiktoks)
        updating_sheet(final_tiktoks, "tiktok")
        # Close the browser
        context.close()


if __name__ == "__main__":
    tiktok_scraping()
