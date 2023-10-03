import json
from playwright.sync_api import sync_playwright
import os
from twocaptcha import TwoCaptcha
import requests
import urllib.parse


def verify_bot():
    # Load configuration from config.json
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.json")
    session_path = os.path.join(os.path.dirname(__file__), "../cache", "session.json")
    
    with open(config_path) as f:
        config = json.load(f)

    with open(session_path) as f:
        session = json.load(f)

    cookies = session['cookies']

    login_endpoint = config['server']['login_endpoint']
    world = config['server']['world']
    captcha_api_key = config['server']['2capthca_api_key']
    user_agent = config['bot']['user_agent']
    site_extension = config['server']['site_extension']
    captcha_url = 'https://' + world + '.tribalwars' + site_extension + '/game.php?screen=overview&mode=all'
    second_captcha_url = 'https://' + world + '.tribalwars' + site_extension + '/game.php?screen=overview'
    cooke_path = 'https://'+ world + '.tribalwars' + site_extension
    domain = world + '.tribalwars' + site_extension


    solver = TwoCaptcha(captcha_api_key)

    with sync_playwright() as p:
        # set headed to True to see the browser
        browser = p.chromium.launch()
        page = browser.new_page()

        # convert the cookie object to array include the key and value
        cookie_array = []
        for key, value in cookies.items():
            cookie_array.append({'name': key, 'value': value, 'url': cooke_path})

        page.context.add_cookies(cookie_array)


        # Navigate to the login page
        page.goto(captcha_url)

        page.wait_for_load_state("networkidle")

        page.goto(second_captcha_url)
        # Wait for #bot_check a to be visible
        page.wait_for_selector("#bot_check a")
        page.screenshot(path="screenshot-1.png")

        page.click("#bot_check a")

        # Click on the a tag in worlds-container with the text of the world in the href

        try:
            # Wait for the iframe element with the specified src to be loaded, with a maximum timeout of 10 seconds
            iframe_element = page.wait_for_selector("iframe[src^='https://newassets.hcaptcha.com']", timeout=10000)

            # wait 2 seconds
            page.wait_for_timeout(2000)

            # Get the iframe's Playwright page object
            iframe_page = iframe_element.content_frame()
            
            # Evaluate the 'src' within the iframe's own context
            iframe_src = iframe_page.evaluate("document.location.href")

            # find div on the page with id #captcha get the data-sitekey attribute
            sitekey = iframe_src.split("sitekey=")[1].split("&")[0]
            
            print(f"The src URL of the iframe is: {iframe_src}")

            current_url = page.url
            
            page.evaluate("document.querySelector('textarea[name=\"h-captcha-response\"]').style.display = 'block'")
            result = solver.hcaptcha(sitekey, current_url)

            cookies = page.context.cookies()
            cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])

            url = "https://"+ config['server']['world'] + ".tribalwars" + site_extension  + "/game.php?screen=botcheck&ajaxaction=verify"

            # Find csrf_token variable on the page this is a js variable
            csrf_token = page.evaluate("window.csrf_token")


            payload = "response={token}&h={h}".format(token=result['code'], h=csrf_token)
            headers = {
                "cookie": cookie_str,
                "authority": domain,
                "accept": "application/json, text/javascript, */*; q=0.01",
                "accept-language": "en-US,en;q=0.9",
                "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                "origin": cooke_path,
                "referer": second_captcha_url,
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": "Windows",
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
                "user-agent": user_agent,
                "x-requested-with": "XMLHttpRequest"
            }

            response = requests.request("POST", url, data=payload, headers=headers)

            page.screenshot(path="screenshot-3.png")
            page.reload()
            page.screenshot(path="screenshot-4.png")



        except TimeoutError:
            print("Iframe not found within 10 seconds. Continuing gracefully.")

        browser.close()



