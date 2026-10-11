# Built for the SDK.py recreated version
# To see a mod that was built for SDK.py v1.0 see the built-in mod creator

import os
try:
    import requests
except ImportError:
    requests = None
try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None
try:
    import html2text
except ImportError:
    html2text = None
from SDK import ModSDK


def fetch_page(url):
    #online, this uses requests and html2text
    if url.startswith("http://") or url.startswith("https://"):
        try:
            response = requests.get(url, timeout=8)
            response.raise_for_status()
            is_html = "text/html" in response.headers.get("Content-Type", "").lower()
            return response.text, is_html, None
        except requests.exceptions.ConnectionError:
            return None, False, "CONNECTION ERROR: Could not reach the internet or server."
        except requests.exceptions.Timeout:
            return None, False, "TIMEOUT ERROR: The server took too long to respond."
        except requests.exceptions.HTTPError as e:
            return None, False, f"HTTP ERROR: {e}"
        except Exception as e:
            return None, False, f"NETWORK ERROR: {e}"

    #offline
    elif url.endswith(".txt") or url.endswith(".html"):
        if not os.path.exists(url):
            return None, False, "404"
        try:
            with open(url, "r", encoding="utf-8") as f:
                content = f.read()
            is_html = url.endswith(".html")
            return content, is_html, None
        except Exception as e:
            return None, False, f"FILE ERROR: Could not read file. ({e})"

    else:
        return None, False, "UNSUPPORTED: Local files must end in .txt or .html"


def render_page(content, is_html):
    if not is_html:
        return content

    soup = BeautifulSoup(content, "html.parser")
    for element in soup(["script", "style", "header", "footer", "nav"]):
        element.decompose()

    converter = html2text.HTML2Text()
    converter.ignore_links = False
    converter.body_width = 0      
    return converter.handle(str(soup))


def run_mod(os_instance):
    sdk = ModSDK(os_instance)

    current_url = "HOME.txt"
    history = []

    while True:
        sdk.screen.header(f"THINK-BROWSER v2.0 | URL: {current_url}")

        content, is_html, error = fetch_page(current_url)

        if error == "404":
            print("\n" + "="*58)
            print(" PROBLEM 404 - FILE NOT FOUND")
            print("="*58)
            print(f"The file '{current_url}' could not be found.")
            print("Did you check to see if this exist? Did you install Requests, BS4, and html2text?")
            print("="*58 + "\n")
        elif error:
            print(f"\n[!] BROWSER ERROR: {error}\n")
        else:
            print("\n" + "-"*60)
            try:
                rendered = render_page(content, is_html)
                wrapped = sdk.utils.wrap_text(rendered, width=58)
                print(wrapped)
            except Exception as e:
                print(f"[!] RENDERING ERROR: Failed to format page content. ({e})")
            print("-"*60 + "\n")

        print("BROWSER MENU:")
        print("1) Enter New URL")
        print("2) Go Back")
        print("3) Exit Browser")
        print()

        choice = sdk.input.get_string("Choose an option: ", allowed_chars="123")

        if choice == "1":
            new_url = sdk.input.get_string("Enter URL or File: ")
            if new_url.strip():
                history.append(current_url)
                current_url = new_url.strip()

        elif choice == "2":
            if history:
                current_url = history.pop()
            else:
                print("\n[!] No history to go back to.\n")
                sdk.utils.sleep(1)

        elif choice == "3":
            print("\nClosing Think Browser... Returning to Desktop.")
            sdk.utils.sleep(1)
            break
