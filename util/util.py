from time import sleep
import html, langid
import google.generativeai as genai
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
import os
from google.api_core.exceptions import InvalidArgument

load_dotenv("env.env")
# loading env variables
TWITTER_LOGIN = os.environ.get("TWITTER_LOGIN")
TWITTER_BASE_URL = os.environ.get("TWITTER_BASE_URL")
TIKTOK_BASE_URL = os.environ.get("TIKTOK_BASE_URL")
QUERY = os.environ.get("QUERY_MESSAGE")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GOOGLE_SHEET = os.environ.get("GOOGLE_SHEET_NAME")
genai.configure(api_key=GEMINI_API_KEY)

# initializing empty list for fetching data
all_tweets = []
all_tiktoks = []


def is_english(text: str) -> bool:
    """
    returns true if the text provided is in english
    """
    language, confidence = langid.classify(text)
    return language == "en"


def gemini_response(message: str) -> bool:
    """
    gemini response for the query
    """
    supported_res_lang = is_english(message)
    print("language supported", supported_res_lang)
    if supported_res_lang:
        try:
            model = genai.GenerativeModel(model_name='gemini-pro')
            response = model.generate_content(message)
            generated_text = response.text

            # Check if generated_text is not None before processing
            if generated_text is not None:
                # logic for processing the generated text
                print("generated text", generated_text.lower())
                if "yes" in generated_text.lower():
                    return True
                elif "no" in generated_text.lower():
                    return False
                else:
                    print("unknown response", generated_text.lower())
                    return False
            else:
                # Handle the case where response.result is None
                print("Generated text is None.")
                return False

        except InvalidArgument as e:
            # Handle the specific exception
            print(f"Error: {e}")
            # You might want to log the error or take appropriate action here
            return False
    else:
        print("language not supported")
        return False


def twitter_login(page, username: str, password: str):
    """
    Login to twitter homepage
    """
    # Navigate to Twitter
    page.goto(TWITTER_LOGIN)
    # Wait for the page to fully load
    page.wait_for_load_state()
    # fill out username and password
    sleep(3)
    page.get_by_label("Phone, email address, or").click(timeout=15000)
    page.get_by_label("Phone, email address, or").fill(username)
    page.get_by_role("button", name="Next").click()
    page.wait_for_load_state("load")
    page.get_by_label("Password", exact=True).click()
    page.get_by_label("Password", exact=True).fill(password)
    page.get_by_test_id("LoginForm_Login_Button").click()
    # wait for page to load after loggin in
    page.wait_for_load_state("load")
    sleep(3)


def search_twitter(page, subject: str):
    """
    Search Twitter
    """
    print("funciton ran")
    page.get_by_test_id("SearchBox_Search_Input").click()
    page.get_by_test_id("SearchBox_Search_Input").fill(subject)
    page.get_by_test_id("SearchBox_Search_Input").press("Enter")
    # go to people's tab to search for people only
    # page.get_by_role("tab", name="People").click()
    sleep(5)


def check_twitter_bio(page, link: str):
    """
    Fetch user profile description from the profile link and check using Palm Model to confirm our query
    """
    print("going to link", link)
    page.goto(link, timeout=60000)
    page.wait_for_load_state("load")
    sleep(4)
    user_description = page.get_by_test_id("UserDescription")
    # check if retry button exists
    retry_button = page.locator('div[role="button"] span:has-text("Retry")').nth(0)
    # Click the button if found
    if retry_button.is_visible():
        retry_button.click()
        print("Clicked the Retry button")
    # Check if user description exists
    print("User Desc visible", user_description.is_visible())
    if user_description.is_visible():
        description_text = user_description.evaluate("(element) => element.innerText")
        escaped_text = html.escape(description_text)
        print("user description", escaped_text)
        message = f"{QUERY}{escaped_text}"
        print("query message", message)
        res = gemini_response(message)
        sleep(1)
        print("palm response", res)
        if res:
            return escaped_text
    return False


def process_tweets(page) -> list:
    """
    Fetching Tweets Details Found For the Search Results
    """
    tweet_articles = page.query_selector_all(
        "//*[@aria-label='Timeline: Search timeline']/div/div/div/div/article"
    )
    print("type of", type(tweet_articles))
    if isinstance(tweet_articles, list):
        tweet_details = []
        for tweet_article in tweet_articles:
            # //*[@aria-label='Timeline: Search timeline']/div/div/div/div/article/div/div/div[2]/div[2]/div[1]/div/div[1]/div/div/div/div/a/div/div/span/span
            profile_name = tweet_article.query_selector(
                "div >> div >> div:nth-child(2) >> div:nth-child(2) >> div:nth-child(1) >> div >> div:nth-child(1) >> div >> div >> div >> a >> div >> div >> span >> span"
            ).text_content()
            # //*[@aria-label='Timeline: Search timeline']/div/div/div/div/article/div/div/div[2]/div[2]/div[1]/div/div[1]/div/div/div/div/a
            profile_link = tweet_article.query_selector(
                "div >> div >> div:nth-child(2) >> div:nth-child(2) >> div:nth-child(1) >> div >> div:nth-child(1) >> div >> div >> div >> a "
            ).get_attribute("href")
            # //*[@aria-label='Timeline: Search timeline']/div/div/div/div/article/div/div/div[2]/div[2]/div[1]/div/div[1]/div/div/div[2]/div/div/a/div/span
            user_name = tweet_article.query_selector(
                "div >> div >> div:nth-child(2) >> div:nth-child(2) >> div:nth-child(1) >> div:nth-child(1) >> div >> div:nth-child(2) >> div >> div >> a >> div >> span"
            ).text_content()
            # //*[@aria-label='Timeline: Search timeline']/div/div/div/div/article/div/div/div[2]/div[2]/div[1]/div/div[1]/div/div/div[2]/div/div[3]/a
            tweet_link = tweet_article.query_selector(
                "div >> div >> div:nth-child(2) >> div:nth-child(2) >> div:nth-child(1) >> div:nth-child(1) >> div >> div:nth-child(2) >> div >> div:nth-child(3) >> a"
            ).get_attribute("href")

            # appending data to list and storing all the search results in a list
            tweet_details.append(
                {
                    "profile_name": profile_name,
                    "profile_link": TWITTER_BASE_URL + profile_link,
                    "user_name": user_name,
                    "tweet_link": TWITTER_BASE_URL + tweet_link,
                }
            )
            print("appended")
            sleep(2)

        return tweet_details
    return False


def scroll_twitter(page) -> list:
    """
    Infinite scrolling twitter and fetching searched tweet details and returning them
    """
    # Get the current height of the page
    prev_height = page.evaluate("document.body.scrollHeight")
    while True:
        print("scrollling")
        # fetch all the initial tweets before scrolling down
        tweets = process_tweets(page)
        if tweets:
            for new_tweet in tweets:
                # Extract the user_name from the new tweet
                new_user_name = new_tweet["user_name"]

                # Check if the user_name already exists in the all_tweets list
                if not any(
                    existing_tweet["user_name"] == new_user_name
                    for existing_tweet in all_tweets
                ):
                    # User_name doesn't exist, so append the new tweet to the all_tweets list
                    all_tweets.append(new_tweet)
                else:
                    print(
                        f"Duplicate entry for user_name: {new_user_name}. Skipping..."
                    )
        # Scroll to the bottom of the page
        page.evaluate("window.scrollTo(0, document.body.scrollHeight);")

        # Wait for some time to allow content to load
        sleep(1)

        # Get the new height of the page
        new_height = page.evaluate("document.body.scrollHeight")

        # If the height didn't change, break the loop as there's no more content to load
        if new_height == prev_height:
            break

        # Update the previous height
        prev_height = new_height

    sleep(2)
    return all_tweets


def filter_tweets(page, tweets) -> list:
    """
    Operate on the tweets found from the search and check from the profile link if the user is a coach. Returns the filtered data of coaches
    """
    if isinstance(tweets, list):
        result = []
        for tweet in tweets:
            is_coach = check_twitter_bio(page, tweet["profile_link"])
            if is_coach:
                tweet["coach_bio"] = is_coach
                result.append(tweet)
        return result
    return False


def get_twitter_profile(tweets, desired_keys):
    filtered_values = [d[key] for d in tweets for key in desired_keys if key in d]
    return filtered_values


def extract_user_details_from_tiktok(page):
    # Use Playwright to locate anchor tags with the specified attribute
    tiktok_users = page.query_selector_all('[data-e2e="challenge-item-username"]')
    if isinstance(tiktok_users, list):
        print("users list found")
        users_details = []
        # Extract and print data from each anchor tag
        for tiktok_user in tiktok_users:
            # profile_link = twitter_user.get_attribute("href")
            # text_content = anchor_tag.text_content()
            user_name = html.escape(
                tiktok_user.evaluate("(element) => element.innerText")
            )
            users_details.append(
                {
                    "profile_link": TIKTOK_BASE_URL + "/@" + user_name + "?lang=en",
                    "user_name": user_name,
                }
            )
        print("User details", users_details)
        return users_details
    return False


def scroll_tiktok(page):
    """
    Infinite scrolling tiktok and fetching searched tiktok details and returning them
    """
    # Allow sometime for page to load
    sleep(5)
    prev_height = page.evaluate("document.body.scrollHeight")
    while True:
        print("scrollling")
        # Scroll to the bottom of the page
        page.evaluate("window.scrollTo(0, document.body.scrollHeight);")

        # Wait for some time to allow new content to load
        sleep(3)

        # Get the new height of the page
        new_height = page.evaluate("document.body.scrollHeight")
        print("New Height", new_height)
        print("Previous Height", prev_height)
        # If the height didn't change, break the loop as there's no more content to load
        if new_height == prev_height:
            # fetch all the tiktoks at the end of scroll
            tiktoks = extract_user_details_from_tiktok(page)
            if tiktoks:
                for tiktok in tiktoks:
                    # Extract the user_name from the new tweet
                    new_user_name = tiktok["user_name"]

                    # Check if the user_name already exists in the all_tweets list
                    if not any(
                        existing_tiktok["user_name"] == new_user_name
                        for existing_tiktok in all_tiktoks
                    ):
                        # User_name doesn't exist, so append the new tweet to the all_tweets list
                        all_tiktoks.append(tiktok)
                        print("appended", new_user_name)
                    else:
                        print(
                            f"Duplicate entry for user_name: {new_user_name}. Skipping..."
                        )
            break

        # Update the previous height
        prev_height = new_height
    sleep(2)
    return all_tiktoks


def filter_tiktok(page, tiktoks, target_iterations=50):
    """
    Operate on the tiktoks found from the search and check from the profile link if the user is a coach. Returns the filtered data of coaches
    """
    if isinstance(tiktoks, list):
        result = []

        # Counter for the number of iterations
        iteration_count = 0

        for tiktok in tiktoks:
            coach_bio = check_tiktok_bio(page, tiktok["profile_link"])
            if coach_bio:
                tiktok["coach_bio"] = coach_bio
                result.append(tiktok)

            # Increment the iteration count
            iteration_count += 1

            # Check if the target_iterations is reached
            if iteration_count >= target_iterations:
                break

        return result
    return False


def check_tiktok_bio(page, link):
    """
    Fetch user profile description from the profile link and check using Palm Model to confirm our query
    """
    print("going to link", link)
    page.goto(link, timeout=60000)
    page.wait_for_load_state("load")
    sleep(4)
    user_description = page.query_selector('[data-e2e="user-bio"]')
    # Check if user description exists
    print("User Desc visible", user_description.is_visible())
    if user_description.is_visible():
        description_text = user_description.evaluate("(element) => element.innerText")
        escaped_text = html.escape(description_text)
        print("user description", escaped_text)
        message = f"{QUERY} '{escaped_text}'"
        res = gemini_response(message)
        sleep(1)
        print("palm response", res)
        if res:
            return escaped_text
    return False


def updating_sheet(data, worksheet):
    """
    Updating the scraped results in the sheet
    """
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_file(
        "credentials.json",
        scopes=scopes,
    )
    client = gspread.authorize(creds)
    sheet = client.open(GOOGLE_SHEET)
    # Select the specific worksheet
    worksheet = sheet.worksheet(worksheet)

    # Extract headers from the first data entry
    headers = list(data[0].keys())
    print(headers)

    # Ensure headers are present in the worksheet
    if not worksheet.row_values(1):
        worksheet.append_row(headers)

    # Define the unique identifier column
    unique_identifier_column = "user_name"

    # Extract existing data from the sheet
    existing_data = worksheet.get_all_records()

    # Extract values for each entry and append to the worksheet only if it doesn't exist
    for entry in data:
        unique_identifier_value = entry[unique_identifier_column]

        # Check if the data with the same unique identifier already exists
        if not any(
            existing_entry[unique_identifier_column] == unique_identifier_value
            for existing_entry in existing_data
        ):
            # Data doesn't exist, so append it to the worksheet
            print(
                f"Data with {unique_identifier_column}={unique_identifier_value} added to the Google Sheet."
            )
            values = [entry[header] for header in headers]
            worksheet.append_row(values)
        else:
            print(
                f"Data with {unique_identifier_column}={unique_identifier_value} already exists in the Google Sheet."
            )

    print("Data has been written to the Google Sheet.")


def instagram_login(page, username: str, password: str):
    """
    Login to Instagram homepage
    """
    # Navigate to Instagram
    page.goto("https://instagram.com/")
    # Wait for the page to fully load
    page.wait_for_load_state()
    # fill out username and password
    sleep(3)
    page.get_by_label("Phone number, username or email address").click(timeout=15000)
    page.get_by_label("Phone number, username or email address").fill(username)

    page.get_by_label("Password", exact=True).click()
    page.get_by_label("Password", exact=True).fill(password)

    page.locator("//button[contains(@type, 'submit')]").click()
    # wait for page to load after loggin in
    page.wait_for_load_state("load")
    sleep(3)


def search_instagram(page, subject: str):
    """
    Search Instagram and go to the first tag name
    """
    print("funciton ran")
    page.get_by_role("link", name="Search Search").click()
    page.get_by_placeholder("Search").click()
    # hashtag so that the user search keyword tags
    page.get_by_placeholder("Search").fill("#" + subject)
    page.get_by_placeholder("Search").press("Enter")
    # click first hashtag
    print("clicked search, now waiting for results")
    # page.get_by_role("link", name="Hashtag #" + subject + "1,").click()
    sleep(3)
    # /html/body/div[2]/div/div/div[2]/div/div/div[1]/div[1]/div[1]/div/div/div[2]/div/div/div[2]/div/div/div[2]/div/a
    search_results = page.query_selector_all(
        "html >> body >> div:nth-child(2) >> div >> div >> div:nth-child(2) >> div >> div >>div >> div >> div:nth-child(2) >> div >> div >> div:nth-child(2) >> div >> div >> div:nth-child(2) >> div >> a"
    )
    return search_results or False


def instagram_scroll(page) -> list:
    """
    Infinite scrolling instagram and fetching searched tweet details and returning them
    """
    # Get the current height of the page
    prev_height = page.evaluate("document.body.scrollHeight")
    while True:
        print("scrollling")
        # fetch all the initial tweets before scrolling down
        # /html/body/div[2]/div/div/div[2]/div/div/div[1]/div[1]/div[2]/section/main/article/div/div/div/div[1]/div[1]/a
        top_hashtags = page.query_selector_all(
            "html >> body >> div:nth-child(2) >> div >> div >> div:nth-child(2) >> div >> div >> div >> div >> div:nth-child(2) >> section >> main >> article >> div >> div >> div >> a"
        )
        print("top hashtags", top_hashtags)
        sleep(2)


def fetch_ig_hashtags_links(search_results):
    if isinstance(search_results, list):
        hashtags_link = []
        for index, search_result in enumerate(search_results):
            post_link = "https://www.instagram.com" + search_result.get_attribute(
                "href"
            )
            # only fetch top 3 hashtags
            print("fetching hashtag number", index)
            if index == 3:
                break
            hashtags_link.append(post_link)
        return hashtags_link
    return False


def fetch_top_ig_posts(page, tag_link):
    print("going to ", tag_link)
    page.goto(tag_link)
    sleep(5)
    page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
    page.wait_for_load_state()
    # find top posts with the associated tag and save them
    top_hashtags_posts = page.query_selector_all(
        "html >> body >> div:nth-child(2) >> div >> div >> div:nth-child(2) >> div >> div >> div >> div >> div:nth-child(2) >> section >> main >> article >> div >> div >> div >> a"
    )
    if isinstance(top_hashtags_posts, list):
        all_posts_link = []
        for top_hashtags_post in top_hashtags_posts:
            link = top_hashtags_post.get_attribute("href")
            print("adding link", link)
            all_posts_link.append("https:www.instagram.com" + link)
        return all_posts_link
    return False


def fetch_ig_profile(page, link):
    try:
        sleep(1)
        page.goto(link)
        page.wait_for_load_state()
        sleep(3)
        profile_data = page.query_selector("//section/main/div/div[1]/div/div[2]/div/div[1]/div/div[2]/div/div[1]/div[1]/div/span/span/div/a")
        
        if profile_data:
            profile_link = "https://www.instagram.com" + profile_data.get_attribute("href")
            user_name = profile_data.text_content()
            print("link: " + profile_link)
            print("profile name: " + user_name)
            return {"profile_link": profile_link, "user_name": user_name} or False
        else:
            print("profiledata not found")

    except Exception as e:
        # Handle the exception here
        print(f"Hashtag link does not exist. An error occurred: {e}. ")
        return False


def fetching_business_account_type(page, link) -> str:
    """
    Returns the bussiness account type of the user. Usually returns 'Coach' for coaches
    """
    page.goto(link)
    sleep(30)
    page.wait_for_load_state()
    # /html/body/div[2]/div/div/div[2]/div/div/div[1]/div[1]/div[2]/div[2]/section/main/div/header/section/div[3]/div[3]/div
    account_type = page.query_selector(
        "//header/section/div[3]/div[3]/div"
    ).text_content()
    return account_type or False


def filter_ig_profiles(page, profiles):
    if isinstance(profiles, list):
        result = []
        for profile in profiles:
            print('Going to profile', profile["profile_link"])
            page.goto(profile["profile_link"])
            page.wait_for_load_state()
            sleep(5)
            # fetch user bio
            # //header/section/div[3]/h1
            bio = page.query_selector("//header/section/div[3]/h1")
            # //header/section/div[3]/div[1]/span
            profile_name_node = page.query_selector(
                "//header/section/div[3]/div[1]/span"
            )
            #Check if user does not have any profile name
            if profile_name_node is None:
                profile_name = profile["user_name"]
            else:
                profile_name = profile_name_node.text_content()
            print('profile name', profile_name)
            if bio.is_visible():
                description_text = bio.evaluate("(element) => element.innerText")
                escaped_text = html.escape(description_text)
                print('bio visible', escaped_text)
                message = f"{QUERY} '{escaped_text}'"
                res = gemini_response(message)
                sleep(1)
                print("palm response", res)
                if res:
                    print("This is a coach", profile["user_name"])
                    profile["profile_name"] = profile_name
                    profile["coach_bio"] = escaped_text
                    result.append(profile)
        print("final results", result)
        return result
    return False
