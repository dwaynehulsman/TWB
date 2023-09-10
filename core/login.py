import json
from playwright.sync_api import sync_playwright
import os
from twocaptcha import TwoCaptcha
import requests
import urllib.parse


def login_and_navigate():
    # Load configuration from config.json
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.json")
    
    with open(config_path) as f:
        config = json.load(f)
    
    login_endpoint = config['server']['login_endpoint']
    endpoint = config['server']['endpoint']
    username = config['server']['username']
    password = config['server']['password']
    world = config['server']['world']
    capthca_api_key = config['server']['2capthca_api_key']
    user_agent = config['bot']['user_agent']

    solver = TwoCaptcha(capthca_api_key)

    with sync_playwright() as p:
        # set headed to True to see the browser


        browser = p.chromium.launch()
        context = browser.new_context()

        page = browser.new_page()
        

        # Navigate to the login page
        page.goto(login_endpoint)

        # Fill in the credentials and login
        page.fill("input[name='username']", username)
        page.fill("input[name='password']", password)
        page.click("a.btn-login")

        page.wait_for_load_state("networkidle")


        try:
            # Wait for the iframe element with the specified src to be loaded, with a maximum timeout of 10 seconds
            iframe_element = page.wait_for_selector("iframe[src^='https://newassets.hcaptcha.com']", timeout=10000)
        
            # Get the iframe's Playwright page object
            iframe_page = iframe_element.content_frame()
            
            # Evaluate the 'src' within the iframe's own context
            iframe_src = iframe_page.evaluate("document.location.href")

            # find div on the page with id #captcha get the data-sitekey attribute
            sitekey = page.query_selector("#captcha").get_attribute("data-sitekey")
            
            print(f"The src URL of the iframe is: {iframe_src}")

            #sitekey = iframe_src.split("sitekey=")[1].split("&")[0]
            current_url = page.url
            iframe_url = iframe_src
            
            page.evaluate("document.querySelector('textarea[name=\"h-captcha-response\"]').style.display = 'block'")
            result = solver.hcaptcha(sitekey, current_url)

            cookies = page.context.cookies()
            cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])

            url = "https://www.tribalwars.nl/page/auth"

            payload = "username={username}&password={password}&remember=1&token={token}".format(username=username, password=password, token=result['code'])
            headers = {
                "cookie": cookie_str,
                "authority": login_endpoint,
                "accept": "application/json, text/javascript, */*; q=0.01",
                "accept-language": "en-US,en;q=0.9",
                "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                "origin": login_endpoint,
                "referer": login_endpoint + "/",
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": "Windows",
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
                "user-agent": user_agent,
                "x-requested-with": "XMLHttpRequest"
            }

            response = requests.request("POST", url, data=payload, headers=headers)

            cookie_data = response.cookies.get_dict()

            playwright_cookies = [{"name": name, "value": value, "domain": "." + login_endpoint.replace("https://", "").replace("/", ""), "path": "/"} for name, value in cookie_data.items()]

            context.add_cookies(playwright_cookies)
            page = context.new_page()
            page.goto(endpoint)

        except TimeoutError:
            print("Iframe not found within 10 seconds. Continuing gracefully.")
        
        # Navigate to the world /page/play/worldname
        page.goto(endpoint)
        # reload page
        page.reload()

        # Wait for the page to load
        page.wait_for_load_state("networkidle")

        # wait for .worlds-container
        page.wait_for_selector(".worlds-container")

        # Click on the a tag in worlds-container with the text of the world in the href

        page.goto(login_endpoint + "/page/play/" + world)

        # Extract cookies
        cookies = page.context.cookies()
        cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}

      # Save cookies to cache/session.json
        session_file_path = os.path.join(os.path.dirname(__file__), "..", "cache", "session.json")

        # Read existing data
        existing_data = {}
        if os.path.exists(session_file_path):
            with open(session_file_path, 'r') as f:
                existing_data = json.load(f)

        # Update the 'cookies' key
        existing_data['cookies'] = cookie_dict

        # Write updated data back to the file
        with open(session_file_path, 'w') as f:
            json.dump(existing_data, f)



        browser.close()
        return cookie_dict


