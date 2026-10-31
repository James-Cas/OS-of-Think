"""
Think OS SDK (SDK.py) - recreated from the "Think OS SDK - Complete Beginner's
Guide" (v1.0).

Place this file in the SAME folder as the Think OS main file (NOT inside
think_os_mods/). Mods use it like this:

    from SDK import ModSDK

    def run_mod(os_instance):
        sdk = ModSDK(os_instance)
        sdk.screen.header("MY MOD")
        name = sdk.input.get_string("What is your name? ")
        print(f"Hello, {name}!")
        sdk.input.wait()

Components (all reachable from a ModSDK instance):
    sdk.screen   - display helpers
    sdk.input    - validated user input
    sdk.menu     - menus and list selection
    sdk.storage  - documents and per-mod saved data
    sdk.utils    - general helpers
"""

import datetime
import json
import os
import random
import textwrap
import time

SDK_VERSION = "1.0"

# Per-mod saved data (save_mod_data / load_mod_data) lives in this JSON file,
# stored next to the Think OS data file.
MOD_DATA_FILE = "think_os_mod_data.json"

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ============================================================================
# SCREEN
# ============================================================================
class Screen:
    """Display formatting helpers."""

    def __init__(self, os_instance):
        self._os = os_instance

    def clear(self):
        """Clear the terminal screen."""
        clear = getattr(self._os, "clear_screen", None)
        if callable(clear):
            clear()
        else:
            os.system("cls" if os.name == "nt" else "clear")

    def header(self, title, width=50, clear=True):
        """Clear the screen and show a title between two divider lines.

        Pass clear=False to draw the header without clearing first.
        """
        if clear:
            self.clear()
        print("=" * width)
        print("        " + str(title))
        print("=" * width)
        print()

    def box(self, text, width=50):
        """Print text inside a +---+ / | | box. Width includes the borders."""
        width = max(int(width), 6)
        inner = width - 4
        lines = []
        for line in str(text).split("\n"):
            lines.extend(textwrap.wrap(line, width=inner) or [""])
        print("+" + "-" * (width - 2) + "+")
        for line in lines:
            print("| " + line.ljust(inner) + " |")
        print("+" + "-" * (width - 2) + "+")

    def divider(self, width=50, char="="):
        """Print a line made of one repeated character."""
        print((str(char) or "=")[0] * width)

    def centered(self, text, width=50):
        """Print text centered within the given width."""
        print(str(text).center(width))

    def progress_bar(self, current, total, width=30, label="Progress"):
        """Print e.g.  Progress: [███████░░░░░░░░] 50%"""
        if total <= 0:
            fraction = 0.0
        else:
            fraction = min(max(current / total, 0.0), 1.0)
        filled = int(width * fraction)
        bar = "█" * filled + "░" * (width - filled)
        print(f"{label}: [{bar}] {int(fraction * 100)}%")


# ============================================================================
# INPUT
# ============================================================================
class Input:
    """User input that keeps asking until the answer is valid."""

    def get_string(self, prompt, allow_empty=False, allowed_chars=None):
        """Get text from the user (surrounding spaces removed).

        allow_empty   - accept an empty answer (returns "")
        allowed_chars - optional string; every typed character must be one of
                        these, e.g. allowed_chars="123" for a 3-option menu
        """
        while True:
            value = input(prompt).strip()
            if not value and not allow_empty:
                print("Input cannot be empty!")
                continue
            if allowed_chars is not None and value:
                bad = [c for c in value if c not in allowed_chars]
                if bad:
                    options = " ".join(allowed_chars)
                    print(f"Invalid input! Allowed characters: {options}")
                    continue
            return value

    def get_int(self, prompt, min_val=None, max_val=None):
        """Get a whole number, optionally within min_val..max_val."""
        while True:
            raw = input(prompt).strip()
            try:
                number = int(raw)
            except ValueError:
                print("Please enter a number!")
                continue

            if min_val is not None and number < min_val:
                if max_val is not None:
                    print(f"Please enter a number between {min_val} and {max_val}!")
                else:
                    print(f"Number must be at least {min_val}!")
                continue
            if max_val is not None and number > max_val:
                if min_val is not None:
                    print(f"Please enter a number between {min_val} and {max_val}!")
                else:
                    print(f"Number must be at most {max_val}!")
                continue
            return number

    def get_choice(self, prompt, valid_choices=None):
        """Get one answer from valid_choices (case-insensitive).

        Returns the matching item exactly as it appears in valid_choices.
        With no valid_choices, any non-empty answer is accepted.
        """
        if valid_choices is None:
            return self.get_string(prompt)

        lookup = {str(choice).lower(): choice for choice in valid_choices}
        while True:
            value = input(prompt).strip().lower()
            if value in lookup:
                return lookup[value]
            shown = ", ".join(str(c) for c in valid_choices)
            print(f"Invalid choice! Options: {shown}")

    def yes_no(self, prompt):
        """True for y/yes, False for n/no."""
        while True:
            value = input(prompt).strip().lower()
            if value in ("y", "yes"):
                return True
            if value in ("n", "no"):
                return False
            print("Please enter 'y' or 'n'.")

    def wait(self, prompt="Press Enter to continue..."):
        """Pause until the user presses Enter."""
        input(prompt)


# ============================================================================
# MENU
# ============================================================================
class Menu:
    """Numbered menus."""

    def __init__(self, screen, input_helper):
        self._screen = screen
        self._input = input_helper

    def create(self, title, options, show_exit=True):
        """Show a numbered menu and return the chosen index.

        Returns 0 for the first option, 1 for the second, and so on,
        or -1 if the automatic Exit entry was chosen.
        """
        options = list(options)
        if not options and not show_exit:
            return -1

        self._screen.header(str(title).upper(), clear=False)
        for number, option in enumerate(options, 1):
            print(f"{number}) {option}")
        total = len(options)
        if show_exit:
            total += 1
            print(f"{total}) Exit")
        print()

        choice = self._input.get_int("Select option: ", min_val=1, max_val=total)
        if show_exit and choice == total:
            return -1
        return choice - 1

    def list_select(self, title, items, show_cancel=True):
        """Pick one item from a list. Returns the item, or None if cancelled."""
        items = list(items)
        if not items:
            return None

        self._screen.header(str(title).upper(), clear=False)
        for number, item in enumerate(items, 1):
            print(f"{number}) {item}")
        total = len(items)
        if show_cancel:
            total += 1
            print(f"{total}) Cancel")
        print()

        choice = self._input.get_int("Select option: ", min_val=1, max_val=total)
        if show_cancel and choice == total:
            return None
        return items[choice - 1]


# ============================================================================
# STORAGE
# ============================================================================
class Storage:
    """Think OS documents and per-mod saved data."""

    def __init__(self, os_instance):
        self._os = os_instance

    # ---- documents (shared with the Documents menu) ----------------------

    @staticmethod
    def _clean_name(name):
        """Add .txt if missing. Returns None for unusable names."""
        name = str(name).strip()
        if not name:
            return None
        if "/" in name or "\\" in name or ".." in name or os.sep in name:
            return None
        if not name.lower().endswith(".txt"):
            name += ".txt"
        return name

    @staticmethod
    def _is_locked(entry):
        return isinstance(entry, dict) and bool(entry.get("encrypted"))

    def save_document(self, name, content):
        """Save text to Think OS documents. Returns True on success.

        Refuses (returns False) to overwrite a password-protected document,
        so a mod can't silently strip someone's protection.
        """
        filename = self._clean_name(name)
        if filename is None:
            print("Warning: invalid document name.")
            return False

        files = self._os.user_files
        if self._is_locked(files.get(filename)):
            print(f"Warning: '{filename}' is password-protected; not overwritten.")
            return False

        text = content if isinstance(content, str) else str(content)
        files[filename] = text

        writer = getattr(self._os, "_write_document_to_disk", None)
        if callable(writer):
            writer(filename, text)
        self._os.save_data()
        return True

    def load_document(self, name):
        """Return a document's text, or None if it doesn't exist.

        Password-protected documents also return None (a mod has no password).
        """
        filename = self._clean_name(name)
        if filename is None:
            return None
        entry = self._os.user_files.get(filename)
        if isinstance(entry, str):
            return entry
        return None

    def delete_document(self, name):
        """Delete a document. Returns True if something was deleted."""
        filename = self._clean_name(name)
        if filename is None or filename not in self._os.user_files:
            return False

        del self._os.user_files[filename]
        remover = getattr(self._os, "_delete_document_from_disk", None)
        if callable(remover):
            remover(filename)
        self._os.save_data()
        return True

    def list_documents(self, prefix=None):
        """List document names (as shown in Documents), optionally filtered."""
        names = list(self._os.user_files.keys())
        if prefix:
            names = [n for n in names if n.startswith(prefix)]
        return names

    # ---- per-mod data -----------------------------------------------------

    def _mod_data_path(self):
        data_file = getattr(self._os, "data_file", None)
        folder = os.path.dirname(os.path.abspath(data_file)) if data_file else _BASE_DIR
        return os.path.join(folder, MOD_DATA_FILE)

    def _read_all(self):
        path = self._mod_data_path()
        if not os.path.exists(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            # Keep the damaged file instead of overwriting it on the next save
            backup = path + ".corrupt"
            try:
                os.replace(path, backup)
                print(f"Warning: mod data file was damaged; kept as {backup}")
            except OSError:
                print("Warning: mod data file was damaged and could not be read.")
            return {}
        except OSError as e:
            print(f"Warning: could not read mod data ({e})")
            return {}

    def save_mod_data(self, mod_name, data):
        """Save JSON-friendly data (dict, list, str, numbers...) for a mod.

        Returns True on success.
        """
        all_data = self._read_all()
        all_data[str(mod_name)] = data

        path = self._mod_data_path()
        temp_path = path + ".tmp"
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(all_data, f, indent=2)
            os.replace(temp_path, path)
            return True
        except (TypeError, ValueError) as e:
            print(f"Warning: mod data for '{mod_name}' can't be saved ({e})")
        except OSError as e:
            print(f"Warning: could not save mod data ({e})")
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except OSError:
            pass
        return False

    def load_mod_data(self, mod_name):
        """Return a mod's saved data, or None if nothing was saved yet."""
        return self._read_all().get(str(mod_name))


# ============================================================================
# UTILS
# ============================================================================
class WrappedText(str):
    """Wrapped text that works both ways.

    print(wrapped)          -> prints the whole block
    for line in wrapped:    -> goes through it line by line
    """

    def __iter__(self):
        return iter(self.lines)

    @property
    def lines(self):
        return self.split("\n") if str.__len__(self) else []


class Utils:
    """General helpers."""

    def countdown(self, seconds, message="Starting in"):
        """Print 'Starting in 5...' down to 1, one per second."""
        for remaining in range(int(seconds), 0, -1):
            print(f"{message} {remaining}...")
            time.sleep(1)

    def sleep(self, seconds):
        time.sleep(seconds)

    def random_choice(self, items):
        return random.choice(items)

    def random_int(self, min_val, max_val):
        """Random whole number from min_val to max_val, both included."""
        return random.randint(min_val, max_val)

    def get_date(self):
        """Today's date as YYYY-MM-DD."""
        return str(datetime.date.today())

    def get_time(self):
        """Current time as HH:MM:SS."""
        return datetime.datetime.now().strftime("%H:%M:%S")

    def format_number(self, number):
        """1234567 -> '1,234,567'"""
        try:
            return f"{number:,}"
        except (TypeError, ValueError):
            return str(number)

    def truncate(self, text, length, suffix="..."):
        """Shorten text to at most `length` characters, suffix included."""
        text = str(text)
        if len(text) <= length:
            return text
        keep = max(length - len(suffix), 0)
        return text[:keep] + suffix

    def wrap_text(self, text, width=50):
        """Wrap text to a width, keeping existing line breaks and blank lines.

        Returns a WrappedText: print it directly, or loop over it for lines.
        """
        if not text:
            return WrappedText("")
        wrapped = []
        for line in str(text).split("\n"):
            if line == "":
                wrapped.append("")
            else:
                wrapped.extend(textwrap.wrap(line, width=width) or [""])
        return WrappedText("\n".join(wrapped))


# ============================================================================
# MAIN CLASS
# ============================================================================
class ModSDK:
    """Entry point:  sdk = ModSDK(os_instance)"""

    def __init__(self, os_instance):
        self.os = os_instance
        self.version = SDK_VERSION
        self.screen = Screen(os_instance)
        self.input = Input()
        self.menu = Menu(self.screen, self.input)
        self.storage = Storage(os_instance)
        self.utils = Utils()
