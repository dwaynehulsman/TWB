import json
from playwright.sync_api import sync_playwright
import os
from twocaptcha import TwoCaptcha
import requests
import urllib.parse


def verify_bot():
    # Load configuration from config.json
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.json")
    
    with open(config_path) as f:
        config = json.load(f)

    endpoint = config['server']['endpoint']
    username = config['server']['username']
    password = config['server']['password']
    world = config['server']['world']
    captcha_api_key = config['server']['2capthca_api_key']
    user_agent = config['bot']['user_agent']
    captcha_url = 'https://' + config['server']['world'] + '.tribalwars' + config['server']['site_extension'] + '/game.php?village=21300&screen=report&mode=all'

    solver = TwoCaptcha(captcha_api_key)

    with sync_playwright() as p:
        # set headed to True to see the browser


        browser = p.chromium.launch()
        context = browser.new_context()

        page = browser.new_page()
        

        # Navigate to the login page
        page.goto(captcha_url)

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

            url = "https://"+ config['server']['world'] + ".tribalwars.nl/game.php?screen=botcheck&ajaxaction=verify"

            payload = "response={token}".format(response=result['code'])
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


            page.reload()

        except TimeoutError:
            print("Iframe not found within 10 seconds. Continuing gracefully.")

        browser.close()
        return true


