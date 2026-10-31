# Built for SDK.py (recreated from the SDK v1.0 guide)

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

BROWSER_VERSION = "2.0"
USER_AGENT = f"Mozilla/5.0 (compatible; ThinkBrowser/{BROWSER_VERSION}; Think OS)"
DEPENDENCY_HINT = "pip install requests beautifulsoup4 html2text"


def fetch_page(url):
    #online, this uses requests and html2text
    if url.lower().startswith(("http://", "https://")):
        if requests is None:
            return None, False, f"MISSING DEPENDENCY: 'requests' is needed to open web pages. ({DEPENDENCY_HINT})"
        try:
            # Some sites refuse the default python-requests user agent
            response = requests.get(url, timeout=8, headers={"User-Agent": USER_AGENT})
            response.raise_for_status()

            content_type = response.headers.get("Content-Type", "").lower()
            is_text = (not content_type or content_type.startswith("text/")
                       or "json" in content_type or "xml" in content_type)
            if not is_text:
                kind = content_type.split(";")[0].strip()
                return None, False, f"UNSUPPORTED: This page is '{kind}', not text or HTML."

            # With no charset in the header, requests assumes Latin-1 and
            # garbles UTF-8 text (café -> cafÃ©), so detect the encoding instead.
            if "charset" not in content_type:
                response.encoding = response.apparent_encoding or "utf-8"

            is_html = "html" in content_type
            return response.text, is_html, None
        # Timeout must come first: ConnectTimeout is also a ConnectionError
        except requests.exceptions.Timeout:
            return None, False, "TIMEOUT ERROR: The server took too long to respond."
        except requests.exceptions.ConnectionError:
            return None, False, "CONNECTION ERROR: Could not reach the internet or server."
        except requests.exceptions.HTTPError as e:
            return None, False, f"HTTP ERROR: {e}"
        except Exception as e:
            return None, False, f"NETWORK ERROR: {e}"

    #offline
    elif url.lower().endswith((".txt", ".html")):
        if not os.path.exists(url):
            return None, False, "404"
        try:
            with open(url, "r", encoding="utf-8") as f:
                content = f.read()
            is_html = url.lower().endswith(".html")
            return content, is_html, None
        except Exception as e:
            return None, False, f"FILE ERROR: Could not read file. ({e})"

    else:
        return None, False, "UNSUPPORTED: Local files must end in .txt or .html (websites must start with http:// or https://)"


def render_page(content, is_html):
    if not is_html:
        return content

    missing = [name for name, module in (("beautifulsoup4", BeautifulSoup),
                                         ("html2text", html2text)) if module is None]
    if missing:
        raise RuntimeError(f"Missing {' and '.join(missing)} - run: {DEPENDENCY_HINT}")

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
        sdk.screen.header(f"THINK-BROWSER v{BROWSER_VERSION} | URL: {current_url}")

        content, is_html, error = fetch_page(current_url)

        if error == "404":
            print("\n" + "="*58)
            print(" PROBLEM 404 - FILE NOT FOUND")
            print("="*58)
            print(f"The file '{current_url}' could not be found.")
            print("Check the spelling, and that it is in the folder you started Think OS from.")
            print("="*58 + "\n")
        elif error:
            print(f"\n[!] BROWSER ERROR: {error}\n")
        else:
            print("\n" + "-"*60)
            try:
                rendered = render_page(content, is_html)
                if rendered.strip():
                    wrapped = sdk.utils.wrap_text(rendered, width=58)
                    print(wrapped)
                else:
                    print("[This page has no readable text.]")
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
