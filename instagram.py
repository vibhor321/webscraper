import os
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
from util.util import (
    instagram_login,
    search_instagram,
    fetch_top_ig_posts,
    fetch_ig_hashtags_links,
    fetch_ig_profile,
    filter_ig_profiles,
    updating_sheet,
)
from time import sleep
import pprint

load_dotenv("env.env")
# the subject to be scraped
keyword = os.environ.get("KEYWORD")

USER_AGENT = os.environ.get("USER_AGENT")
# Get Instagram Credentials
INSTAGRAM_USERNAME = os.environ.get("INSTAGRAM_USERNAME")
INSTAGRAM_PASSWORD = os.environ.get("INSTAGRAM_PASSWORD")


def instagram_scraping():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            # most common desktop viewport is 1920x1080
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()
        if USER_AGENT:
            page.set_extra_http_headers({"User-Agent": USER_AGENT})
        # log into Instagram
        instagram_login(page, INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
        # wait for page to load after loggin in
        page.wait_for_load_state("load")
        print("page loaded after user logged in")
        # search Instagram and fetches the result links
        search_results = search_instagram(page, keyword)
        hashtags = fetch_ig_hashtags_links(search_results)
        if hashtags:
            print("These are the hashtags: ", hashtags)
            top_ig_posts = []
            for hashtag in hashtags:
                ig_posts = fetch_top_ig_posts(page, hashtag)
                if ig_posts:
                    print("posts found here: ", ig_posts)
                    top_ig_posts.extend(ig_posts)
            print("all links:", top_ig_posts)
        if top_ig_posts:
            ig_profile_data = []
            for top_ig_post in top_ig_posts:
                user_data = fetch_ig_profile(page, top_ig_post)
                if user_data:
                    new_user_name = user_data["user_name"]
                    if not any(
                        profile_data["user_name"] == new_user_name
                        for profile_data in ig_profile_data
                    ):
                        # User_name doesn't exist, so append the new ig to the all_tweets list
                        ig_profile_data.append(user_data)
                        print("appended", new_user_name)
                    else:
                        print(
                            f"Duplicate entry for user_name: {new_user_name}. Skipping..."
                        )
                else:
                    print("userdata not found")
            print("Data", ig_profile_data)
            final_profiles = filter_ig_profiles(page, ig_profile_data)
            print("Final Data", final_profiles)
            updating_sheet(final_profiles, "instagram")
        # Close the browser
        context.close()


if __name__ == "__main__":
    instagram_scraping()
