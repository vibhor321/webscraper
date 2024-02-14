from playwright.sync_api import sync_playwright
from time import sleep


def linkedin_scraping():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            # most common desktop viewport is 1920x1080
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36"
        page.set_extra_http_headers({"User-Agent": user_agent})
        page.goto("https://www.linkedin.com/")
        sleep(2)
        page.get_by_label("Email or phone").click()
        page.get_by_label("Email or phone").fill(LEmail)
        sleep(2)
        page.get_by_label("Password", exact=True).click()
        page.get_by_label("Password", exact=True).fill(LPassword)
        page.get_by_role("button", name="Sign in").click()
        sleep(2)
        page.wait_for_load_state("load")
        page.get_by_placeholder("Search", exact=True).click()
        page.get_by_placeholder("Search", exact=True).fill(subject)
        page.get_by_placeholder("Search", exact=True).press("Enter")
        page.get_by_role("button", name="People").click()
        sleep(5)
        twitter_list = []
        count = 0
        while True:
            search_results = page.query_selector_all(
                "ul.reusable-search__entity-result-list li.reusable-search__result-container"
            )
            if isinstance(search_results, list):
                # print("results found", search_results)
                for result in search_results:
                    # /html/body/div[5]/div[3]/div[2]/div/div[1]/main/div/div/div[2]/div/ul/li/div/div/div/div[2]/div[1]/div[1]/div/span[1]/span/a/span/span[1]
                    title_element = result.query_selector(
                        "div >> div >> div >> div:nth-child(2) >> div >> div >> span:nth-child(1) >> a >> span >> span:nth-child(1)"
                    )

                    if title_element:
                        # print("inside for", title_element.text_content().strip())
                        twitter_list.append(title_element.text_content().strip())
                    else:
                        print("No title element found for the result.")
            count += 1
            sleep(2)
            next_btn = page.get_by_label("Next")
            if next_btn:
                print("button found")
                next_btn.click()
                sleep(3)
            else:
                break
            if count == 10:
                break
        sleep(5)
        print(twitter_list)
