import os
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
from util.util import (
    twitter_login,
    search_twitter,
    scroll_twitter,
    filter_tweets,
    updating_sheet,
)

load_dotenv("env.env")
# the subject to be scraped
KEYWORD = os.environ.get("KEYWORD")
USER_AGENT = os.environ.get("USER_AGENT")

# Get Twitter Credentials
TWITTER_USERNAME = os.environ.get("TWITTER_USERNAME")
TWITTER_PASSWORD = os.environ.get("TWITTER_PASSWORD")


def twitter_scraping():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            # most common desktop viewport is 1920x1080
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()
        if USER_AGENT:
            page.set_extra_http_headers({"User-Agent": USER_AGENT})
        # log into twitter
        twitter_login(page, TWITTER_USERNAME, TWITTER_PASSWORD)
        # wait for page to load after loggin in
        page.wait_for_load_state("load")
        print("page loaded after user logged in")
        # search twitter
        search_twitter(page, KEYWORD)
        # Perform unlimited scroll
        searched_tweets = scroll_twitter(page)
        page.wait_for_load_state("load")
        print("all tweets", searched_tweets)

        final_tweets = filter_tweets(page, searched_tweets)
        print("final_caoches", final_tweets)
        print("Updating data to the sheet")
        updating_sheet(final_tweets, "twitter")
        # Close the browser
        context.close()


if __name__ == "__main__":
    twitter_scraping()
