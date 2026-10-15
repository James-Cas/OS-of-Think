# ============================================================================
# PYTHON 3.13 COMPATIBILITY FIX
# ============================================================================
import sys
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
import warnings

warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', message='.*collections.*')

try:
    import collections
    if not hasattr(collections, 'Callable'):
        import collections.abc
        collections.Callable = collections.abc.Callable
except:
    pass

# ============================================================================
# IMPORTS
# ============================================================================
import time
import datetime
import json
import random
import hashlib
import textwrap
import base64
from pathlib import Path

# Optional dependency for password-protected text files (same pattern
# Think_Browser.py uses for its own optional imports: try it, and fall
# back gracefully if it isn't installed).
try:
    from cryptography.fernet import Fernet, InvalidToken
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

KDF_ITERATIONS = 390_000


class ThinkOS:
    def __init__(self):
        self.current_user = None
        self.user_files = {}
        self.password_hash = None  # Stored as SHA-256 hash
        self.data_file = "think_os_data.json"
        self.game_stats = {}
        self.mods_folder = "think_os_mods"
        self.documents_folder = "think_os_documents"
        self.installed_mods = {}
        self.load_data()
        self.load_mods()
        self._ensure_documents_folder()
        # First-run: prompt to set a password if none saved
        if not self.password_hash:
            self._first_run_setup()

    def _hash_password(self, password):
        """Return SHA-256 hex digest of a password string"""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    def _first_run_setup(self):
        """Prompt the user to set an admin password on first run"""
        import os as _os
        _os.system('cls' if _os.name == 'nt' else 'clear')
        print("=" * 50)
        print("        THINK OS - FIRST RUN SETUP")
        print("=" * 50)
        print()
        print("Welcome! Please set an admin password.")
        print()
        while True:
            pw1 = input("Enter new password: ")
            pw2 = input("Confirm password:   ")
            if not pw1:
                print("Password cannot be empty. Try again.")
                continue
            if pw1 == pw2:
                self.password_hash = self._hash_password(pw1)
                self.save_data()
                print()
                print("Remember it, there is no recovery. Unless you edit the file.")
                input("Press Enter to continue...")
                print()
                print("Writing info to JSON file.")
                print("Writing info to RAM.")
                break
            else:
                print("Passwords doesn't match. Try again.")

    def _check_password(self, password):
        """Return True if password matches stored hash"""
        return self._hash_password(password) == self.password_hash

    def load_data(self):
        """Load saved user files from disk"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.user_files = data.get('user_files', {})
                    self.password_hash = data.get('password_hash', None)
                    self.game_stats = data.get('game_stats', {
                        'tic_tac_toe': {'wins': 0, 'losses': 0, 'draws': 0},
                        'rps': {'wins': 0, 'losses': 0, 'draws': 0},
                        'monopoly': {'games_played': 0, 'money_record': 0},
                        'oregon_trail': {'games_completed': 0, 'best_score': 0}
                    })
                    self.installed_mods = data.get('installed_mods', {})
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: Could not load saved data ({e}). Starting fresh.")
            self.user_files = {}
            self.password_hash = None
            self.game_stats = {
                'tic_tac_toe': {'wins': 0, 'losses': 0, 'draws': 0},
                'rps': {'wins': 0, 'losses': 0, 'draws': 0},
                'monopoly': {'games_played': 0, 'money_record': 0},
                'oregon_trail': {'games_completed': 0, 'best_score': 0}
            }
            self.installed_mods = {}

    def save_data(self):
        """Save user files to disk"""
        try:
            data = {
                'user_files': self.user_files,
                'game_stats': self.game_stats,
                'installed_mods': self.installed_mods,
                'password_hash': self.password_hash
            }
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except OSError as e:
            print(f"Warning: Could not save data ({e})")

    def load_mods(self):
        """Load community mods from mods folder"""
        try:
            if not os.path.exists(self.mods_folder):
                os.makedirs(self.mods_folder)
                readme_path = os.path.join(self.mods_folder, "README.txt")
                try:
                    with open(readme_path, 'w', encoding='utf-8') as f:
                        f.write("THINK OS MODS FOLDER\n")
                        f.write("=" * 50 + "\n\n")
                        f.write("Place your mod .py files in this folder.\n")
                        f.write("Mods should contain: def run_mod(os_instance):\n")
                except OSError as e:
                    print(f"Warning: Could not create mods README ({e})")
        except OSError as e:
            print(f"Warning: Could not create mods folder ({e})")

    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def boot_screen(self):
        """Main login screen"""
        while True:
            self.clear_screen()
            print("=" * 50)
            print("        THINK OS - BOOT SEQUENCE")
            print("=" * 50)
            print()
            password = input("Password: ")

            if self._check_password(password):
                self.current_user = "Admin"
                self.desktop()
                return
            else:
                result = self.boot_screen_two()
                if result == "retry":
                    continue
                elif result == "guest":
                    self.ltd_desktop()
                    return

    def boot_screen_two(self):
        """Screen shown after wrong password"""
        self.clear_screen()
        print("That was the wrong password")
        print()
        print("1) Admin Login")
        print("2) Guest login")
        print()

        choice = input("Select option: ")

        if choice == "1":
            return "retry"
        elif choice == "2":
            self.current_user = "guest"
            return "guest"
        return "retry"

    def desktop(self):
        """Main desktop for admin users"""
        while True:
            self.clear_screen()
            print("=" * 50)
            print("████████╗██╗░░██╗██╗███╗░░██╗██╗░░██╗░░░░░░░█████╗░░██████╗")
            print("╚══██╔══╝██║░░██║██║████╗░██║██║░██╔╝░░░░░░██╔══██╗██╔════╝")
            print("░░░██║░░░███████║██║██╔██╗██║█████═╝░█████╗██║░░██║╚█████╗░")
            print("░░░██║░░░██╔══██║██║██║╚████║██╔═██╗░╚════╝██║░░██║░╚═══██╗")
            print("░░░██║░░░██║░░██║██║██║░╚███║██║░╚██╗░░░░░░╚█████╔╝██████╔╝")
            print("░░░╚═╝░░░╚═╝░░╚═╝╚═╝╚═╝░░╚══╝╚═╝░░╚═╝░░░░░░░╚════╝░╚═════╝░")
            print("=" * 50 )
            print()
            print("Welcome to THINK OS 2.0")
            print()
            print("=" * 50)
            print(f"Date: {datetime.date.today()}")
            print(f"Time: {datetime.datetime.now().strftime('%H:%M:%S')}")
            print()
            print("1) Write text file      2) Documents...")
            print("3) Calculator...        4) Games...")
            print("5) Terminal...          6) System Info..")
            print("7) Mods...              8) Settings")
            print("9) Logout")
            print("=" * 50) 
            print()

            choice = input("Select option: ")

            if choice == "1" or choice.lower() == "write text file":
                self.write_application()
            elif choice == "2" or choice.lower() == "documents":
                self.browse_documents()
            elif choice == "3" or choice.lower() == "calculator":
                self.calculator()
            elif choice == "4" or choice.lower() == "games":
                self.games_folder()
            elif choice == "5" or choice.lower() == "terminal":
                self.terminal_ide()
            elif choice == "6" or choice.lower() == "system info":
                self.system_info()
            elif choice == "7" or choice.lower() == "mods":
                self.mods_menu()
            elif choice == "8" or choice.lower() == "settings":
                self.settings_menu()
            elif choice == "9" or choice.lower() == "logout":
                self.logout()
                break

    # ========================================================================
    # MODS SYSTEM - NEW SECTION
    # ========================================================================

    def mods_menu(self):
        """Mods management menu"""
        while True:
            try:
                self.clear_screen()
                print("=" * 50)
                print("        THINK OS - MODS CENTER")
                print("=" * 50)
                print()
                print("Community Mods & Extensions")
                print()
                print(f"Mods Folder: {self.mods_folder}/")
                print(f"Installed Mods: {len(self.installed_mods)}")
                print()
                print("1) Browse Available Mods")
                print("2) Install New Mod")
                print("3) Run Installed Mod")
                print("4) Manage Mods")
                print("5) Create Mod Template")
                print("6) Back to Desktop")
                print()

                choice = input("Select option: ")

                if choice == "1":
                    self.browse_mods()
                elif choice == "2":
                    self.install_mod()
                elif choice == "3":
                    self.run_mod()
                elif choice == "4":
                    self.manage_mods()
                elif choice == "5":
                    self.create_mod_template()
                elif choice == "6":
                    break
            except Exception as e:
                print(f"Error in mods menu: {e}")
                input("Press Enter to continue...")

    def browse_mods(self):
        """Browse available mods"""
        try:
            self.clear_screen()
            print("=" * 50)
            print("        AVAILABLE MODS")
            print("=" * 50)
            print()

            if os.path.exists(self.mods_folder):
                mod_files = [f for f in os.listdir(self.mods_folder) 
                            if f.endswith('.py') and f != '__init__.py']
            else:
                mod_files = []

            if not mod_files:
                print("No mod files found in the mods folder.")
                print()
                print(f"Place .py mod files in: {self.mods_folder}/")
            else:
                print("Available mod files:")
                print()
                for i, mod_file in enumerate(mod_files, 1):
                    mod_name = mod_file[:-3]
                    status = "✓ INSTALLED" if mod_name in self.installed_mods else "○ Not Installed"
                    print(f"{i}) {mod_file} - {status}")
                    
                    if mod_name in self.installed_mods:
                        mod_info = self.installed_mods[mod_name]
                        if 'description' in mod_info:
                            print(f"   Description: {mod_info['description']}")
                    print()

            print()
            input("Press Enter to return...")
        except Exception as e:
            print(f"Error: {e}")
            input("Press Enter to return...")

    def install_mod(self):
        """Install a new mod"""
        try:
            self.clear_screen()
            print("=" * 50)
            print("        INSTALL MOD")
            print("=" * 50)
            print()

            if os.path.exists(self.mods_folder):
                mod_files = [f for f in os.listdir(self.mods_folder) 
                            if f.endswith('.py') and f != '__init__.py']
            else:
                mod_files = []

            if not mod_files:
                print("No mod files found to install.")
                print()
                input("Press Enter to return...")
                return

            print("Available mods to install:")
            print()
            for i, mod_file in enumerate(mod_files, 1):
                mod_name = mod_file[:-3]
                status = "Already Installed" if mod_name in self.installed_mods else "Ready to Install"
                print(f"{i}) {mod_file} - {status}")

            print(f"{len(mod_files) + 1}) Cancel")
            print()

            try:
                choice = int(input("Select mod to install: "))
                if 1 <= choice <= len(mod_files):
                    mod_file = mod_files[choice - 1]
                    mod_name = mod_file[:-3]

                    if mod_name in self.installed_mods:
                        print()
                        print("This mod is already installed!")
                        print()
                        overwrite = input("Reinstall? (y/n): ").lower()
                        if overwrite != 'y':
                            return

                    print()
                    print(f"Installing {mod_name}...")
                    time.sleep(1)

                    description = input("Enter mod description (optional): ").strip()
                    author = input("Enter mod author (optional): ").strip()

                    self.installed_mods[mod_name] = {
                        'filename': mod_file,
                        'description': description or "No description provided",
                        'author': author or "Unknown",
                        'installed_date': str(datetime.date.today()),
                        'runs': 0
                    }

                    self.save_data()

                    print()
                    print("✓ Mod installed successfully!")
                    print()
                    input("Press Enter to return...")

            except ValueError:
                print("Invalid input!")
                time.sleep(1)
        except Exception as e:
            print(f"Error: {e}")
            input("Press Enter to return...")

    def run_mod(self):
        """Run an installed mod"""
        try:
            self.clear_screen()
            print("=" * 50)
            print("        RUN MOD")
            print("=" * 50)
            print()

            if not self.installed_mods:
                print("No mods installed yet!")
                print()
                input("Press Enter to return...")
                return

            print("Installed mods:")
            print()
            mod_list = list(self.installed_mods.keys())
            for i, mod_name in enumerate(mod_list, 1):
                mod_info = self.installed_mods[mod_name]
                print(f"{i}) {mod_name}")
                print(f"   Author: {mod_info.get('author', 'Unknown')}")
                print(f"   Runs: {mod_info.get('runs', 0)}")
                print()

            print(f"{len(mod_list) + 1}) Cancel")
            print()

            try:
                choice = int(input("Select mod to run: "))
                if 1 <= choice <= len(mod_list):
                    mod_name = mod_list[choice - 1]
                    mod_info = self.installed_mods[mod_name]
                    mod_file = mod_info['filename']
                    mod_path = os.path.join(self.mods_folder, mod_file)

                    if not os.path.exists(mod_path):
                        print()
                        print("ERROR: Mod file not found!")
                        print()
                        input("Press Enter to return...")
                        return

                    print()
                    print(f"Running {mod_name}...")
                    print("=" * 50)
                    print()
                    print("WARNING: Mods run all correct python code following the SDK rules.")
                    print("Only run mods you trust!")
                    print()
                    confirm = input("Continue? (y/n): ").lower()
                    if confirm != 'y':
                        return
                    print()
                    time.sleep(1)

                    try:
                        # Add current directory to Python path for SDK imports
                        current_dir = os.path.dirname(os.path.abspath(__file__))
                        if current_dir not in sys.path:
                            sys.path.insert(0, current_dir)
                        
                        with open(mod_path, 'r', encoding='utf-8') as f:
                            mod_code = f.read()

                        mod_namespace = {
                            'os_instance': self,
                            'print': print,
                            'input': input,
                            'time': time,
                            'random': random,
                            'datetime': datetime,
                            'os': os,
                            'json': json
                        }

                        exec(mod_code, mod_namespace)

                        if 'run_mod' in mod_namespace:
                            mod_namespace['run_mod'](self)
                        else:
                            print()
                            print("Note: Mod does not have a 'run_mod' function.")

                        self.installed_mods[mod_name]['runs'] += 1
                        self.save_data()

                    except Exception as e:
                        print()
                        print(f"ERROR running mod: {e}")
                        import traceback
                        traceback.print_exc()
                        print()

                    print()
                    print("=" * 50)
                    print("Mod execution finished.")
                    input("Press Enter to return...")

            except ValueError:
                print("Invalid input!")
                time.sleep(1)
        except Exception as e:
            print(f"Error: {e}")
            input("Press Enter to return...")

    def manage_mods(self):
        """Manage installed mods"""
        while True:
            try:
                self.clear_screen()
                print("=" * 50)
                print("        MANAGE MODS")
                print("=" * 50)
                print()

                if not self.installed_mods:
                    print("No mods installed yet!")
                    print()
                    input("Press Enter to return...")
                    return

                print("Installed mods:")
                print()
                mod_list = list(self.installed_mods.keys())
                for i, mod_name in enumerate(mod_list, 1):
                    mod_info = self.installed_mods[mod_name]
                    print(f"{i}) {mod_name}")
                    print(f"   Description: {mod_info.get('description', 'N/A')}")
                    print(f"   Author: {mod_info.get('author', 'Unknown')}")
                    print(f"   Total Runs: {mod_info.get('runs', 0)}")
                    print()

                print(f"{len(mod_list) + 1}) Uninstall a mod")
                print(f"{len(mod_list) + 2}) Back")
                print()

                try:
                    choice = int(input("Select option: "))
                    if choice == len(mod_list) + 1:
                        self.uninstall_mod()
                    elif choice == len(mod_list) + 2:
                        break
                except ValueError:
                    print("Invalid input!")
                    time.sleep(1)
            except Exception as e:
                print(f"Error: {e}")
                input("Press Enter to continue...")
                break

    def uninstall_mod(self):
        """Uninstall a mod"""
        try:
            self.clear_screen()
            print("=" * 50)
            print("        UNINSTALL MOD")
            print("=" * 50)
            print()

            if not self.installed_mods:
                print("No mods to uninstall!")
                print()
                input("Press Enter to return...")
                return

            mod_list = list(self.installed_mods.keys())
            for i, mod_name in enumerate(mod_list, 1):
                print(f"{i}) {mod_name}")

            print(f"{len(mod_list) + 1}) Cancel")
            print()

            try:
                choice = int(input("Select mod to uninstall: "))
                if 1 <= choice <= len(mod_list):
                    mod_name = mod_list[choice - 1]
                    
                    print()
                    confirm = input(f"Uninstall '{mod_name}'? (y/n): ").lower()
                    
                    if confirm == 'y':
                        del self.installed_mods[mod_name]
                        self.save_data()
                        print()
                        print("✓ Mod uninstalled successfully!")
                        print("(Mod file still exists in mods folder)")
                        print()
                    else:
                        print("Cancelled.")
                        print()
                    
                    input("Press Enter to return...")

            except ValueError:
                print("Invalid input!")
                time.sleep(1)
        except Exception as e:
            print(f"Error: {e}")
            input("Press Enter to return...")

    def create_mod_template(self):
        """Create a template mod file"""
        try:
            self.clear_screen()
            print("=" * 50)
            print("        CREATE MOD TEMPLATE")
            print("=" * 50)
            print()

            mod_name = input("Enter mod name (no spaces): ").strip().replace(' ', '_')
            
            if not mod_name:
                print("Invalid mod name!")
                time.sleep(1)
                return

            filename = f"{mod_name}.py"
            filepath = os.path.join(self.mods_folder, filename)

            if os.path.exists(filepath):
                print()
                print("A mod with this name already exists!")
                print()
                input("Press Enter to return...")
                return

            template = f'''# Think OS Mod: {mod_name}
# Created: {datetime.date.today()}

def run_mod(os_instance):
    """Main mod function"""
    
    os_instance.clear_screen()
    
    print("=" * 50)
    print("        {mod_name.upper()}")
    print("=" * 50)
    print()
    
    print(f"Hello from {mod_name} mod!")
    print()
    
    # Your mod code goes here
    # Access user files: os_instance.user_files
    # Save data: os_instance.save_data()
    
    input("Press Enter to return...")

MOD_INFO = {{
    "name": "{mod_name}",
    "version": "1.0",
    "author": "Your Name",
    "description": "Describe your mod"
}}
'''

            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(template)
                
                print()
                print(f"✓ Template created: {filename}")
                print()
                print(f"Location: {filepath}")
                print()
                input("Press Enter to return...")
            
            except Exception as e:
                print()
                print(f"Error creating template: {e}")
                print()
                input("Press Enter to return...")
        except Exception as e:
            print(f"Error: {e}")
            input("Press Enter to return...")

    # ========================================================================
    # SETTINGS MENU
    # ========================================================================

    def settings_menu(self):
        """Settings and preferences menu"""
        while True:
            self.clear_screen()
            print("=" * 50)
            print("        THINK OS - SETTINGS")
            print("=" * 50)
            print()
            print(f"Logged in as: {self.current_user}")
            print()
            print("1) Change Password")
            print("2) Back to Desktop")
            print()

            choice = input("Select option: ")

            if choice == "1":
                self.change_password()
            elif choice == "2":
                break

    def change_password(self):
        """Allow admin to change their password"""
        self.clear_screen()
        print("=" * 50)
        print("        CHANGE PASSWORD")
        print("=" * 50)
        print()

        current = input("Enter current password: ")
        if not self._check_password(current):
            print()
            print("Incorrect password. Cancelled.")
            input("Press Enter to return...")
            return

        print()
        while True:
            pw1 = input("Enter new password: ")
            pw2 = input("Confirm new password: ")
            if not pw1:
                print("Password cannot be empty.")
                continue
            if pw1 == pw2:
                self.password_hash = self._hash_password(pw1)
                self.save_data()
                print()
                print("✓ Password changed successfully!")
                input("Press Enter to return...")
                return
            else:
                print("Passwords do not match. Try again.")

    # ========================================================================
    # ORIGINAL THINK OS FEATURES
    # ========================================================================

    def games_folder(self):
        """Games folder menu"""
        while True:
            self.clear_screen()
            print("=" * 50)
            print("        THINK OS - GAMES FOLDER")
            print("=" * 50)
            print()
            print("Welcome to the Games Collection!")
            print()
            print("Sometimes at the end of the game there will be a error note.")
            print("Just end the program")
            print()
            print("Available Games:")
            print("1) Tic Tac Toe")
            print("2) Rock Paper Scissors")
            print("3) Monopoly")
            print("4) The Oregon Trail")
            print("5) Game Statistics")
            print("6) Back to Desktop")
            print()

            choice = input("Select game: ")

            if choice == "1":
                self.tic_tac_toe()
            elif choice == "2":
                self.rock_paper_scissors()
            elif choice == "3":
                self.monopoly()
            elif choice == "4":
                self.oregon_trail()
            elif choice == "5":
                self.game_statistics()
            elif choice == "6":
                break

    def tic_tac_toe(self):
        """Tic Tac Toe game"""
        self.clear_screen()
        print("=" * 50)
        print("        TIC TAC TOE")
        print("=" * 50)
        print()

        # Initialize board
        board = [' ' for _ in range(9)]
        player = 'X'
        computer = 'O'

        def print_board():
            print(f" {board[0]} | {board[1]} | {board[2]} ")
            print("-----------")
            print(f" {board[3]} | {board[4]} | {board[5]} ")
            print("-----------")
            print(f" {board[6]} | {board[7]} | {board[8]} ")
            print()
            print("Positions:")
            print(" 1 | 2 | 3 ")
            print("-----------")
            print(" 4 | 5 | 6 ")
            print("-----------")
            print(" 7 | 8 | 9 ")

        def check_winner():
            win_patterns = [
                [0, 1, 2], [3, 4, 5], [6, 7, 8],  # rows
                [0, 3, 6], [1, 4, 7], [2, 5, 8],  # columns
                [0, 4, 8], [2, 4, 6]  # diagonals
            ]

            for pattern in win_patterns:
                if board[pattern[0]] == board[pattern[1]] == board[pattern[2]] != ' ':
                    return board[pattern[0]]

            if ' ' not in board:
                return 'Draw'
            return None

        def computer_move():
            """Minimax AI - plays optimally"""
            def score(b, depth):
                w = check_winner_board(b)
                if w == computer: return 10 - depth
                if w == player:   return depth - 10
                return 0

            def check_winner_board(b):
                wins = [[0,1,2],[3,4,5],[6,7,8],[0,3,6],[1,4,7],[2,5,8],[0,4,8],[2,4,6]]
                for p in wins:
                    if b[p[0]] == b[p[1]] == b[p[2]] != ' ':
                        return b[p[0]]
                if ' ' not in b:
                    return 'Draw'
                return None

            def minimax(b, is_max, depth):
                result = check_winner_board(b)
                if result is not None:
                    return score(b, depth)
                best = -100 if is_max else 100
                for i in range(9):
                    if b[i] == ' ':
                        b[i] = computer if is_max else player
                        val = minimax(b, not is_max, depth + 1)
                        b[i] = ' '
                        best = max(best, val) if is_max else min(best, val)
                return best

            best_score, best_move = -100, None
            for i in range(9):
                if board[i] == ' ':
                    board[i] = computer
                    s = minimax(board, False, 0)
                    board[i] = ' '
                    if s > best_score:
                        best_score, best_move = s, i
            return best_move

        print("You are X, Computer is O")
        print()

        while True:
            self.clear_screen()
            print("=" * 50)
            print("        TIC TAC TOE")
            print("=" * 50)
            print()
            print_board()
            print()

            # Player move
            try:
                move = int(input("Enter position (1-9): ")) - 1
                if 0 <= move <= 8 and board[move] == ' ':
                    board[move] = player
                else:
                    print("Invalid move! Try again.")
                    time.sleep(1)
                    continue
            except ValueError:
                print("Please enter a number!")
                time.sleep(1)
                continue

            # Check if player won
            winner = check_winner()
            if winner:
                self.clear_screen()
                print("=" * 50)
                print("        GAME OVER")
                print("=" * 50)
                print_board()
                print()
                if winner == 'X':
                    print("🎉 You WIN! 🎉")
                    self.game_stats['tic_tac_toe']['wins'] += 1
                elif winner == 'O':
                    print("👻 Computer WINS!")
                    self.game_stats['tic_tac_toe']['losses'] += 1
                else:
                    print("🤝 It's a DRAW!")
                    self.game_stats['tic_tac_toe']['draws'] += 1

                self.save_data()
                input("Press Enter to return to games...")
                break

            # Computer move
            comp_move = computer_move()
            board[comp_move] = computer

            # Check if computer won
            winner = check_winner()
            if winner:
                self.clear_screen()
                print("=" * 50)
                print("        GAME OVER")
                print("=" * 50)
                print_board()
                print()
                if winner == 'X':
                    print("🎉 You WIN! 🎉")
                    self.game_stats['tic_tac_toe']['wins'] += 1
                elif winner == 'O':
                    print("👻 Computer WINS!")
                    self.game_stats['tic_tac_toe']['losses'] += 1
                else:
                    print("🤝 It's a DRAW!")
                    self.game_stats['tic_tac_toe']['draws'] += 1

                self.save_data()
                input("Press Enter to return to games...")
                break

    def rock_paper_scissors(self):
        """Rock Paper Scissors game"""
        if 'rps' not in self.game_stats:
            self.game_stats['rps'] = {'wins': 0, 'losses': 0, 'draws': 0}

        choices = ['rock', 'paper', 'scissors']
        emojis = {'rock': '🪨', 'paper': '📄', 'scissors': '✂️'}

        def outcome(player, computer):
            if player == computer:
                return 'draw'
            if (player == 'rock' and computer == 'scissors') or \
               (player == 'scissors' and computer == 'paper') or \
               (player == 'paper' and computer == 'rock'):
                return 'win'
            return 'loss'

        while True:
            self.clear_screen()
            stats = self.game_stats['rps']
            print("=" * 50)
            print("        ROCK PAPER SCISSORS")
            print("=" * 50)
            print()
            print(f"  W: {stats['wins']}   L: {stats['losses']}   D: {stats['draws']}")
            print()
            print("1) 🪨  Rock")
            print("2) 📄  Paper")
            print("3) ✂️   Scissors")
            print("4) Back to Games")
            print()

            choice = input("Your choice: ")

            if choice == "4":
                break
            elif choice in ("1", "2", "3"):
                player_pick = choices[int(choice) - 1]
            else:
                print("Invalid choice!")
                time.sleep(1)
                continue

            computer_pick = random.choice(choices)
            result = outcome(player_pick, computer_pick)

            self.clear_screen()
            print("=" * 50)
            print("        ROCK PAPER SCISSORS")
            print("=" * 50)
            print()
            print(f"  You:      {emojis[player_pick]}  {player_pick.capitalize()}")
            print(f"  Computer: {emojis[computer_pick]}  {computer_pick.capitalize()}")
            print()

            if result == 'win':
                print("🎉 You WIN!")
                self.game_stats['rps']['wins'] += 1
            elif result == 'loss':
                print("👻 Computer WINS!")
                self.game_stats['rps']['losses'] += 1
            else:
                print("🤝 It's a DRAW!")
                self.game_stats['rps']['draws'] += 1

            self.save_data()
            print()
            input("Press Enter to play again (or choose 4 to exit)...")


    def monopoly(self):
        """Simplified Monopoly game"""
        self.clear_screen()
        print("=" * 50)
        print("        MONOPOLY")
        print("=" * 50)
        print()

        properties = [
            "GO", "Mediterranean Ave", "Community Chest", "Baltic Ave",
            "Income Tax", "Reading Railroad", "Oriental Ave", "Chance",
            "Vermont Ave", "Connecticut Ave", "Jail", "St. Charles Place",
            "Electric Company", "States Ave", "Virginia Ave", "Pennsylvania Railroad",
            "St. James Place", "Community Chest", "Tennessee Ave", "New York Ave",
            "Free Parking", "Kentucky Ave", "Chance", "Indiana Ave",
            "Illinois Ave", "B&O Railroad", "Atlantic Ave", "Ventnor Ave",
            "Water Works", "Marvin Gardens", "Go To Jail", "Pacific Ave",
            "North Carolina Ave", "Community Chest", "Pennsylvania Ave", "Short Line",
            "Chance", "Park Place", "Luxury Tax", "Boardwalk"
        ]

        player_money = 1500
        player_position = 0
        computer_money = 1500
        computer_position = 0

        print("🏠 Welcome to Monopoly! 🏠")
        print(f"You start with ${player_money}")
        print()
        input("Press Enter to start the game...")

        for turn in range(20):  # 20 turns simplified game
            self.clear_screen()
            print("=" * 50)
            print(f"        MONOPOLY - TURN {turn + 1}")
            print("=" * 50)
            print()
            print(f"💰 Your money: ${player_money}")
            print(f"📍 Your position: {properties[player_position]}")
            print()

            input("Press Enter to roll dice...")

            # Player turn
            dice1 = random.randint(1, 6)
            dice2 = random.randint(1, 6)
            roll = dice1 + dice2

            print(f"🎲 You rolled: {dice1} + {dice2} = {roll}")

            player_position = (player_position + roll) % len(properties)
            current_property = properties[player_position]

            print(f"📍 You landed on: {current_property}")

            # Simple money transactions
            if "Ave" in current_property or "Place" in current_property:
                cost = random.randint(50, 200)
                print(f"💸 Pay rent: ${cost}")
                player_money -= cost
            elif current_property == "GO":
                print("💰 Collect $200 for passing GO!")
                player_money += 200
            elif "Railroad" in current_property:
                cost = 200
                print(f"🚂 Railroad rent: ${cost}")
                player_money -= cost

            print(f"💰 Your money: ${player_money}")

            if player_money <= 0:
                print("💸 You're bankrupt! Game Over!")
                break

            time.sleep(3)

            # Computer turn (simplified)
            comp_roll = random.randint(2, 12)
            computer_position = (computer_position + comp_roll) % len(properties)
            computer_money += random.randint(-100, 150)

        self.clear_screen()
        print("=" * 50)
        print("        MONOPOLY GAME FINISHED")
        print("=" * 50)
        print()
        print(f"Final Money: ${player_money}")

        if player_money > self.game_stats['monopoly']['money_record']:
            print("🏆 NEW MONEY RECORD! 🏆")
            self.game_stats['monopoly']['money_record'] = player_money

        self.game_stats['monopoly']['games_played'] += 1
        self.save_data()
        print()
        input("Press Enter to return to games...")

    def oregon_trail(self):
        """The Oregon Trail game - faithful recreation"""
        import random

        # Game state variables
        money = 0
        oxen = 0
        food = 0
        ammunition = 0
        clothing = 0
        miscellaneous = 0

        # Party members
        party_names = []
        party_health = []

        # Game progress
        miles_traveled = 0
        total_miles = 2040  # Miles from Independence to Oregon
        current_date = [3, 1, 1848]  # March 1, 1848
        weather = "fair"

        # Landmarks
        landmarks = [
            (102, "Kansas River crossing"),
            (185, "Big Blue River crossing"),
            (304, "Fort Kearney"),
            (555, "Chimney Rock"),
            (635, "Fort Laramie"),
            (725, "Independence Rock"),
            (987, "South Pass"),
            (1067, "Green River crossing"),
            (1155, "Fort Bridger"),
            (1395, "Soda Springs"),
            (1505, "Fort Hall"),
            (1675, "Snake River crossing"),
            (1722, "Fort Boise"),
            (1869, "Blue Mountains"),
            (1950, "The Dalles"),
            (2040, "Oregon City - You made it!")
        ]

        # Profession selection
        self.clear_screen()
        print("=" * 60)
        print("        THE OREGON TRAIL")
        print("=" * 60)
        print()
        print("Many kinds of people made the trip to Oregon.")
        print()
        print("You may:")
        print("1. Be a banker from Boston")
        print("2. Be a carpenter from Ohio")
        print("3. Be a farmer from Illinois")
        print("4. Find out the differences between these choices")
        print("5. Ask for advice")
        print()

        while True:
            choice = input("What is your choice? ")
            if choice == "1":
                money = 1600
                profession = "banker"
                difficulty_multiplier = 1.0
                break
            elif choice == "2":
                money = 2500
                profession = "carpenter"
                difficulty_multiplier = 1.3
                break
            elif choice == "3":
                money = 2500
                profession = "farmer"
                difficulty_multiplier = 1.6
                break
            elif choice == "4":
                print("\nTraveling to Oregon isn't easy! But if you're a")
                print("banker, you'll have more money for supplies")
                print("and services than a carpenter or a farmer.")
                print("\nHowever, the harder you have it, the more")
                print("points you deserve! Farmers get 3 times the")
                print("points that bankers get.")
                print()
            elif choice == "5":
                print("\nDon't spend all your money before leaving")
                print("Independence. You need to save money to buy")
                print("supplies along the way.")
                print()
            else:
                print("That isn't a choice.")

        # Get party member names
        self.clear_screen()
        print("=" * 60)
        print("        THE OREGON TRAIL")
        print("=" * 60)
        print()
        print("What are the names of the four other members")
        print("in your party?")
        print()

        for i in range(4):
            name = input(f"What is the name of the {i + 1}. person? ")
            party_names.append(name.strip())
            party_health.append("Good")

        # Shopping in Independence
        self.clear_screen()
        print("=" * 60)
        print("        INDEPENDENCE GENERAL STORE")
        print("=" * 60)
        print()
        print("Before leaving Independence you should buy")
        print("equipment and supplies. You have $" + str(money))
        print("for the trip.")
        print()

        while True:
            print("=" * 40)
            print("Matt's General Store")
            print("Independence, Missouri")
            print(f"March 1, 1848")
            print("=" * 40)
            print()
            print("1. Oxen                   $200-300 each")
            print("2. Food                   $0.20 per pound")
            print("3. Ammunition             $2.00 per box")
            print("4. Clothing               $10.00 per set")
            print("5. Miscellaneous supplies $5.00 per part")
            print("6. Review purchases")
            print("7. Leave store")
            print()
            print(f"Amount you have: ${money}")
            print()

            choice = input("Which item would you like to buy? ")

            if choice == "1":  # Oxen
                print("\nThere are 2 oxen in a yoke; I recommend at")
                print("least 3 yoke. I charge $200-300 per ox.")
                while True:
                    try:
                        num_oxen = int(input("How many oxen? "))
                        cost = num_oxen * random.randint(200, 300)
                        if cost <= money:
                            money -= cost
                            oxen += num_oxen
                            print(f"You bought {num_oxen} oxen for ${cost}")
                            break
                        else:
                            print("You don't have enough money.")
                            break
                    except ValueError:
                        print("Please enter a number.")

            elif choice == "2":  # Food
                print("\nI recommend you take at least 200 pounds of")
                print("food for each person in your family. I sell")
                print("food for 20 cents a pound.")
                while True:
                    try:
                        pounds = int(input("How many pounds of food? "))
                        cost = int(pounds * 0.20)
                        if cost <= money:
                            money -= cost
                            food += pounds
                            print(f"You bought {pounds} pounds of food for ${cost}")
                            break
                        else:
                            print("You don't have enough money.")
                            break
                    except ValueError:
                        print("Please enter a number.")

            elif choice == "3":  # Ammunition
                print("\nI sell ammunition in boxes of 20 bullets.")
                print("Each box costs $2.00.")
                while True:
                    try:
                        boxes = int(input("How many boxes? "))
                        cost = boxes * 2
                        if cost <= money:
                            money -= cost
                            ammunition += boxes * 20
                            print(f"You bought {boxes} boxes for ${cost}")
                            break
                        else:
                            print("You don't have enough money.")
                            break
                    except ValueError:
                        print("Please enter a number.")

            elif choice == "4":  # Clothing
                print("\nYou'll need warm clothing in the mountains.")
                print("I recommend taking at least 2 sets of clothes")
                print("per person. Each set is $10.00.")
                while True:
                    try:
                        sets = int(input("How many sets? "))
                        cost = sets * 10
                        if cost <= money:
                            money -= cost
                            clothing += sets
                            print(f"You bought {sets} sets of clothing for ${cost}")
                            break
                        else:
                            print("You don't have enough money.")
                            break
                    except ValueError:
                        print("Please enter a number.")

            elif choice == "5":  # Miscellaneous
                print("\nMiscellaneous supplies include such things as")
                print("medicine, bandages, soap, cookware, etc.")
                print("Everything is $5 per part.")
                while True:
                    try:
                        parts = int(input("How many parts? "))
                        cost = parts * 5
                        if cost <= money:
                            money -= cost
                            miscellaneous += parts
                            print(f"You bought {parts} parts for ${cost}")
                            break
                        else:
                            print("You don't have enough money.")
                            break
                    except ValueError:
                        print("Please enter a number.")

            elif choice == "6":  # Review
                print("\n" + "=" * 40)
                print("YOUR PURCHASES:")
                print(f"Oxen: {oxen}")
                print(f"Food: {food} pounds")
                print(f"Ammunition: {ammunition} bullets")
                print(f"Clothing: {clothing} sets")
                print(f"Miscellaneous: {miscellaneous} parts")
                print(f"Money left: ${money}")
                print("=" * 40)
                input("\nPress Enter to continue...")

            elif choice == "7":  # Leave
                if oxen < 6:
                    print("\nYou should have at least 6 oxen to pull")
                    print("your wagon.")
                    continue
                break

            self.clear_screen()
            print("=" * 60)
            print("        INDEPENDENCE GENERAL STORE")
            print("=" * 60)
            print()

        # Main game loop
        days_traveled = 0

        def advance_date(days):
            current_date[1] += days
            if current_date[1] > 30:
                current_date[0] += current_date[1] // 30
                current_date[1] = current_date[1] % 30
                if current_date[0] > 12:
                    current_date[2] += 1
                    current_date[0] = 1

        def get_date_string():
            months = ["", "January", "February", "March", "April", "May", "June",
                      "July", "August", "September", "October", "November", "December"]
            return f"{months[current_date[0]]} {current_date[1]}, {current_date[2]}"

        def check_landmarks():
            for mile, landmark in landmarks:
                if miles_traveled >= mile and miles_traveled - 15 < mile:
                    return landmark
            return None

        def random_event():
            events = [
                ("wagon_break", 0.1),
                ("illness", 0.08),
                ("bad_weather", 0.15),
                ("thief", 0.05),
                ("injured", 0.06),
                ("lost", 0.04),
                ("find_food", 0.03),
                ("indian_help", 0.02)
            ]

            if random.random() < 0.4:  # 40% chance of event
                event_type = random.choices([e[0] for e in events],
                                            weights=[e[1] for e in events])[0]
                return event_type
            return None

        # Main travel loop
        while miles_traveled < total_miles:
            landmark = check_landmarks()

            self.clear_screen()
            print("=" * 60)
            print("        THE OREGON TRAIL")
            print("=" * 60)
            print()
            print(get_date_string())
            print(f"Weather: {weather}")
            print(f"Health: Good")  # Simplified for this version
            print(f"Food: {food} pounds")
            print(f"Bullets: {ammunition}")
            print(f"Clothing: {clothing}")
            print(f"Money: ${money}")
            print()
            print(f"Miles traveled: {miles_traveled}")
            print(f"Miles to Oregon: {total_miles - miles_traveled}")
            print()

            if landmark:
                print(f"🏛️  You have reached: {landmark}")
                print()

            print("You may:")
            print("1. Continue on trail")
            print("2. Rest")
            print("3. Trade")
            print("4. Hunt")
            print("5. Buy supplies")
            print("6. Check map")
            print()

            choice = input("What is your choice? ")

            if choice == "1":  # Continue
                # Travel for the day
                if oxen <= 0:
                    print("You cannot continue without oxen!")
                    input("Press Enter to continue...")
                    continue

                miles_today = random.randint(12, 25)
                miles_traveled += miles_today
                food -= 8  # Food consumption per day
                days_traveled += 1
                advance_date(1)

                # Weather changes
                weather_options = ["fair", "rainy", "cloudy", "hot", "cold"]
                weather = random.choice(weather_options)

                # Random events
                event = random_event()
                if event == "wagon_break":
                    print("\nYour wagon axle broke!")
                    if miscellaneous > 0:
                        print("You use spare parts to fix it.")
                        miscellaneous -= 1
                    else:
                        print("You have no spare parts. You lose 3 days.")
                        advance_date(3)
                    input("Press Enter to continue...")

                elif event == "illness":
                    sick_person = random.choice(party_names)
                    print(f"\n{sick_person} has become ill!")
                    if miscellaneous > 0:
                        print("You use medicine to help them recover.")
                        miscellaneous -= 1
                    else:
                        print("You have no medicine. They will recover slowly.")
                        advance_date(2)
                    input("Press Enter to continue...")

                elif event == "bad_weather":
                    if weather == "rainy":
                        print("\nHeavy rains! You lose a day waiting for weather to clear.")
                        advance_date(1)
                    elif weather == "cold":
                        print("\nVery cold weather! You use extra clothing.")
                        if clothing > 0:
                            clothing -= 1
                    input("Press Enter to continue...")

                elif event == "thief":
                    stolen = random.randint(10, 50)
                    if food >= stolen:
                        food -= stolen
                        print(f"\nThieves stole {stolen} pounds of food!")
                    else:
                        print("\nThieves tried to steal food but you had none!")
                    input("Press Enter to continue...")

                elif event == "find_food":
                    found = random.randint(20, 80)
                    food += found
                    print(f"\nYou found {found} pounds of wild food!")
                    input("Press Enter to continue...")

                if food <= 0:
                    print("\nYou are out of food! Your party is starving!")
                    # In original game, party members would die
                    print("You must hunt or buy food immediately!")
                    input("Press Enter to continue...")

            elif choice == "2":  # Rest
                print("\nHow many days would you like to rest?")
                try:
                    rest_days = int(input("Days: "))
                    if rest_days > 0:
                        advance_date(rest_days)
                        food -= rest_days * 8
                        print(f"You rested for {rest_days} days.")
                        print("Your party's health improves.")
                        input("Press Enter to continue...")
                except ValueError:
                    print("Please enter a number.")

            elif choice == "3":  # Trade
                print("\nYou meet another wagon train.")
                print("They are willing to trade.")
                print()
                print("1. Trade food for ammunition")
                print("2. Trade ammunition for food")
                print("3. Trade clothing for food")
                print("4. Don't trade")

                trade_choice = input("Your choice: ")
                if trade_choice == "1" and food >= 50:
                    food -= 50
                    ammunition += 25
                    print("You traded 50 pounds of food for 25 bullets.")
                elif trade_choice == "2" and ammunition >= 25:
                    ammunition -= 25
                    food += 30
                    print("You traded 25 bullets for 30 pounds of food.")
                elif trade_choice == "3" and clothing >= 2:
                    clothing -= 2
                    food += 40
                    print("You traded 2 sets of clothing for 40 pounds of food.")
                input("Press Enter to continue...")

            elif choice == "4":  # Hunt
                if ammunition <= 0:
                    print("You have no ammunition for hunting!")
                    input("Press Enter to continue...")
                    continue

                print("\nYou go hunting...")
                print("Type BANG when you see an animal!")
                print()

                # Simple hunting mini-game
                animals = ["rabbit", "deer", "buffalo", "squirrel"]
                animal = random.choice(animals)

                print(f"You see a {animal}!")
                hunt_input = input("Type BANG: ").upper()

                if hunt_input == "BANG":
                    success = random.random() < 0.7  # 70% success rate
                    if success:
                        if animal == "buffalo":
                            meat = random.randint(200, 400)
                        elif animal == "deer":
                            meat = random.randint(100, 200)
                        else:
                            meat = random.randint(50, 100)

                        food += meat
                        ammunition -= 10
                        print(f"You shot the {animal}!")
                        print(f"You got {meat} pounds of meat!")
                    else:
                        ammunition -= 5
                        print("You missed!")
                else:
                    print("You were too slow!")

                input("Press Enter to continue...")

            elif choice == "5":  # Buy supplies (at landmarks)
                if landmark and "Fort" in landmark:
                    print(f"\n{landmark} - Trading Post")
                    print("1. Food - $0.50 per pound")
                    print("2. Ammunition - $3.00 per box")
                    print("3. Clothing - $15.00 per set")
                    print("4. Don't buy anything")

                    buy_choice = input("What would you like to buy? ")
                    if buy_choice == "1":
                        try:
                            pounds = int(input("Pounds of food: "))
                            cost = int(pounds * 0.5)
                            if cost <= money:
                                money -= cost
                                food += pounds
                                print(f"You bought {pounds} pounds of food.")
                        except ValueError:
                            pass
                    elif buy_choice == "2":
                        try:
                            boxes = int(input("Boxes of ammunition: "))
                            cost = boxes * 3
                            if cost <= money:
                                money -= cost
                                ammunition += boxes * 20
                                print(f"You bought {boxes} boxes of ammunition.")
                        except ValueError:
                            pass
                else:
                    print("There are no trading posts here.")
                input("Press Enter to continue...")

            elif choice == "6":  # Check map
                print("\n" + "=" * 50)
                print("MAP OF THE OREGON TRAIL")
                print("=" * 50)
                progress = int((miles_traveled / total_miles) * 40)
                map_line = "Independence" + "-" * progress + "*" + "-" * (40 - progress) + "Oregon"
                print(map_line)
                print(f"\nYou are {miles_traveled} miles from Independence")
                print(f"You have {total_miles - miles_traveled} miles to go")
                print("\nLandmarks:")
                for mile, name in landmarks:
                    if mile <= miles_traveled + 100:
                        status = "PASSED" if mile <= miles_traveled else f"{mile - miles_traveled} miles ahead"
                        print(f"{name}: {status}")
                input("\nPress Enter to continue...")

            # Check for game over conditions
            if miles_traveled >= total_miles:
                break

        # End game
        self.clear_screen()
        print("=" * 60)
        print("        CONGRATULATIONS!")
        print("=" * 60)
        print()
        print("🎉 You have successfully reached Oregon City! 🎉")
        print()
        print(f"You traveled {miles_traveled} miles in {days_traveled} days.")
        print(f"You arrived on {get_date_string()}")
        print()
        print("Final supplies:")
        print(f"Food: {food} pounds")
        print(f"Ammunition: {ammunition} bullets")
        print(f"Clothing: {clothing} sets")
        print(f"Money: ${money}")
        print()

        # Calculate score (like original game)
        points = 0
        if profession == "banker":
            points = miles_traveled * 1
        elif profession == "carpenter":
            points = miles_traveled * 2
        else:  # farmer
            points = miles_traveled * 3

        print(f"Your score as a {profession}: {points} points")
        print()
        print("Thanks for playing The Oregon Trail!")
        print()

        # Update game stats
        if 'oregon_trail' not in self.game_stats:
            self.game_stats['oregon_trail'] = {'games_completed': 0, 'best_score': 0}

        self.game_stats['oregon_trail']['games_completed'] += 1
        if points > self.game_stats['oregon_trail']['best_score']:
            self.game_stats['oregon_trail']['best_score'] = points

        self.save_data()
        input("Press Enter to return to games...")

    def game_statistics(self):
        """Display game statistics"""
        self.clear_screen()
        print("=" * 50)
        print("        GAME STATISTICS")
        print("=" * 50)
        print()

        print("🎯 Tic Tac Toe:")
        print(f"   Wins: {self.game_stats['tic_tac_toe']['wins']}")
        print(f"   Losses: {self.game_stats['tic_tac_toe']['losses']}")
        print(f"   Draws: {self.game_stats['tic_tac_toe']['draws']}")
        print()

        print("✂️  Rock Paper Scissors:")
        rps = self.game_stats.get('rps', {'wins': 0, 'losses': 0, 'draws': 0})
        print(f"   Wins: {rps['wins']}")
        print(f"   Losses: {rps['losses']}")
        print(f"   Draws: {rps['draws']}")
        print()

        print("🏠 Monopoly:")
        print(f"   Games Played: {self.game_stats['monopoly']['games_played']}")
        print(f"   Money Record: ${self.game_stats['monopoly']['money_record']}")
        print()

        print("🚂 The Oregon Trail:")
        print(f"   Games Completed: {self.game_stats.get('oregon_trail', {}).get('games_completed', 0)}")
        print(f"   Best Score: {self.game_stats.get('oregon_trail', {}).get('best_score', 0)}")
        print()

        input("Press Enter to return to games...")

    # ========================================================================
    # TEXT EDITOR HELPERS
    # ========================================================================

    def _ensure_documents_folder(self):
        """Make sure the documents folder exists on disk, same as mods_folder"""
        try:
            if not os.path.exists(self.documents_folder):
                os.makedirs(self.documents_folder)
                readme_path = os.path.join(self.documents_folder, "README.txt")
                try:
                    with open(readme_path, 'w', encoding='utf-8') as f:
                        f.write("THINK OS DOCUMENTS FOLDER\n")
                        f.write("=" * 50 + "\n\n")
                        f.write("Every text file you create or edit with the Write\n")
                        f.write("application shows up here as a real .txt file, so you\n")
                        f.write("can open it outside Think OS too.\n\n")
                        f.write("Password-protected files are saved using the same\n")
                        f.write("ENC1 format as Text_Editor.py, so that tool can open\n")
                        f.write("them as well.\n")
                except OSError as e:
                    print(f"Warning: Could not create documents README ({e})")
        except OSError as e:
            print(f"Warning: Could not create documents folder ({e})")

    def _document_disk_path(self, filename):
        """Full path to a document's .txt mirror on disk"""
        return os.path.join(self.documents_folder, filename)

    def _write_document_to_disk(self, filename, disk_text):
        """Write the given raw text to the document's .txt file on disk"""
        self._ensure_documents_folder()
        path = self._document_disk_path(filename)
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(disk_text)
        except OSError as e:
            print(f"Warning: Could not save '{filename}' to {self.documents_folder}/ ({e})")

    def _delete_document_from_disk(self, filename):
        path = self._document_disk_path(filename)
        try:
            if os.path.exists(path):
                os.remove(path)
        except OSError as e:
            print(f"Warning: Could not remove '{filename}' from {self.documents_folder}/ ({e})")

    def _rename_document_on_disk(self, old_filename, new_filename):
        old_path = self._document_disk_path(old_filename)
        new_path = self._document_disk_path(new_filename)
        try:
            if os.path.exists(old_path):
                os.rename(old_path, new_path)
        except OSError as e:
            print(f"Warning: Could not rename file in {self.documents_folder}/ ({e})")

    def _read_multiline_text(self):
        """Read lines from the user until they type SAVE on its own line"""
        print("Enter your text (type 'SAVE' on a new line to finish):")
        print()
        content = []
        while True:
            line = input()
            if line.strip().upper() == "SAVE":
                break
            content.append(line)
        return "\n".join(content)

    def _wrap_text(self, text, width=60):
        """Wrap text for readable display, preserving existing line breaks"""
        if not text:
            return ""
        wrapped_lines = []
        for line in text.split("\n"):
            if line == "":
                wrapped_lines.append("")
            else:
                wrapped_lines.extend(textwrap.wrap(line, width=width) or [""])
        return "\n".join(wrapped_lines)

    def _is_encrypted_entry(self, entry):
        """A file is password-protected if it's stored as a dict marker,
        instead of the plain string used for normal files."""
        return isinstance(entry, dict) and entry.get("encrypted")

    def _get_new_password(self):
        """Ask for a new password with confirmation. Returns None on cancel."""
        while True:
            pw1 = input("Set a password for this file (leave blank to skip): ")
            if not pw1:
                return None
            pw2 = input("Confirm password: ")
            if pw1 != pw2:
                print("Passwords didn't match. Try again.\n")
                continue
            return pw1

    def _derive_file_key(self, password, salt):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=KDF_ITERATIONS,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))

    def _encrypt_file_content(self, text, password):
        """Return a dict marker holding the salt + encrypted text"""
        salt = os.urandom(16)
        key = self._derive_file_key(password, salt)
        token = Fernet(key).encrypt(text.encode("utf-8"))
        return {
            "encrypted": True,
            "salt": base64.urlsafe_b64encode(salt).decode("ascii"),
            "data": token.decode("ascii"),
        }

    def _decrypt_file_content(self, entry):
        """Prompt for the password (3 tries) and return the plaintext,
        or None if the user cancels or runs out of attempts."""
        salt = base64.urlsafe_b64decode(entry["salt"].encode("ascii"))
        for attempt in range(3):
            password = input("Enter password (blank to cancel): ")
            if not password:
                return None
            key = self._derive_file_key(password, salt)
            try:
                plaintext = Fernet(key).decrypt(entry["data"].encode("ascii"))
                return plaintext.decode("utf-8")
            except InvalidToken:
                remaining = 2 - attempt
                if remaining > 0:
                    print(f"Wrong password. {remaining} attempt(s) left.\n")
                else:
                    print("Wrong password. Access denied.\n")
        return None

    def _prompt_protect_and_save(self, filename, content):
        """Ask whether to password-protect content, then save it under filename
        (both in the JSON store and as a real .txt file on disk)"""
        protect = False
        if CRYPTO_AVAILABLE:
            choice = input("Password-protect this file? (y/n): ").strip().lower()
            protect = choice == "y"
        else:
            print()
            print("[Note: password protection is unavailable because the")
            print(" 'cryptography' package isn't installed. Saving as a")
            print(" normal, unprotected file. (pip install cryptography)]")

        password = self._get_new_password() if protect else None

        if password:
            entry = self._encrypt_file_content(content, password)
            self.user_files[filename] = entry
            # Same marker format Text_Editor.py uses, so that tool can open it too
            self._write_document_to_disk(filename, f"ENC1:{entry['salt']}\n{entry['data']}")
        else:
            self.user_files[filename] = content
            self._write_document_to_disk(filename, content)

        self.save_data()

    def write_application(self):
        """Text file creation application"""
        self.clear_screen()
        print("=" * 50)
        print("        THINK OS - WRITE APPLICATION")
        print("=" * 50)
        print()
        print("Welcome to Write, an application which lets you write text files...")
        print()

        filename = input("What will be the name of your text file? ").strip()
        if not filename:
            print("\nFilename cannot be empty.")
            input("Press Enter to return to desktop...")
            return
        if not filename.lower().endswith(".txt"):
            filename += ".txt"

        if filename in self.user_files:
            confirm = input(
                f"'{filename}' already exists. Overwrite it? (y/n): "
            ).strip().lower()
            if confirm != "y":
                print("\nCancelled.")
                time.sleep(1)
                return

        print()
        print(f"Creating file: {filename}")
        protect_hint = " (with optional password protection)" if CRYPTO_AVAILABLE else ""
        print(f"File ready to write{protect_hint}.")
        print()
        input("Press Enter to continue...")

        self.clear_screen()
        print(f"Editing: {filename}")
        print()
        content = self._read_multiline_text()

        print()
        self._prompt_protect_and_save(filename, content)

        print()
        print("File saved successfully!")
        print("Redirecting to desktop...")
        time.sleep(2)

    def browse_documents(self):
        """Browse saved documents"""
        while True:
            self.clear_screen()
            print("=" * 50)
            print("        THINK OS - DOCUMENTS")
            print("=" * 50)
            print()

            if not self.user_files:
                print("No documents found. Create some files first!")
                print()
                input("Press Enter to return to desktop...")
                break

            print("Available documents:")
            file_list = list(self.user_files.keys())
            for i, filename in enumerate(file_list, 1):
                lock = " [locked]" if self._is_encrypted_entry(self.user_files[filename]) else ""
                print(f"{i}) {filename}{lock}")

            print(f"{len(file_list) + 1}) Back to desktop")
            print()

            choice = input("Select document: ")

            try:
                choice_num = int(choice)
                if choice_num == len(file_list) + 1:
                    break
                elif 1 <= choice_num <= len(file_list):
                    selected_file = file_list[choice_num - 1]
                    self.view_document(selected_file)
                else:
                    print("Invalid choice!")
                    time.sleep(1)
            except ValueError:
                print("Please enter a number!")
                time.sleep(1)

    def view_document(self, filename):
        """View a specific document with edit/delete/rename options"""
        while True:
            self.clear_screen()
            print("=" * 50)
            print(f"        VIEWING: {filename}")
            print("=" * 50)
            print()

            entry = self.user_files[filename]

            if self._is_encrypted_entry(entry):
                if not CRYPTO_AVAILABLE:
                    print("=" * 58)
                    print(" PROBLEM - MISSING DEPENDENCY")
                    print("=" * 58)
                    print(f"'{filename}' is password-protected, but the")
                    print("'cryptography' package isn't installed, so it can't")
                    print("be unlocked here. Try: pip install cryptography")
                    print("=" * 58)
                    input("\nPress Enter to return to documents...")
                    return

                print("[This file is password-protected.]")
                print()
                text = self._decrypt_file_content(entry)
                if text is None:
                    print("\nCould not open file.")
                    input("Press Enter to return to documents...")
                    return
            else:
                text = entry

            print("-" * 58)
            print(self._wrap_text(text, width=58))
            print("-" * 58)
            print()
            print("1) Edit this file")
            print("2) Rename this file")
            print("3) Delete this file")
            print("4) Back to documents")
            print()
            choice = input("Select option: ").strip().lower()

            if choice in ("4", "back", "back to documents"):
                break

            elif choice in ("1", "edit", "edit this file"):
                self.clear_screen()
                print(f"Editing: {filename}")
                print()
                print("----- CURRENT CONTENT -----")
                print(self._wrap_text(text, width=58))
                print("----- END -----")
                print()
                print("Type your new text below (retype/extend the above, or")
                print("start fresh) - type SAVE on its own line when done.")
                print()
                new_content = self._read_multiline_text()

                print()
                self._prompt_protect_and_save(filename, new_content)

                print("\nFile updated successfully!")
                time.sleep(1.5)
                break

            elif choice in ("2", "rename", "rename this file"):
                new_name = input("Enter new filename: ").strip()
                if new_name and not new_name.lower().endswith(".txt"):
                    new_name += ".txt"
                if new_name and new_name not in self.user_files:
                    self.user_files[new_name] = self.user_files.pop(filename)
                    self.save_data()
                    self._rename_document_on_disk(filename, new_name)
                    filename = new_name
                    print(f"Renamed to '{new_name}'.")
                    time.sleep(1)
                elif new_name in self.user_files:
                    print("A file with that name already exists.")
                    time.sleep(1)

            elif choice in ("3", "delete", "delete this file"):
                confirm = input(f"Delete '{filename}'? (y/n): ").lower()
                if confirm == 'y':
                    del self.user_files[filename]
                    self.save_data()
                    self._delete_document_from_disk(filename)
                    print("File deleted.")
                    time.sleep(1)
                    break
            else:
                print("Invalid choice.")
                time.sleep(1)

    def calculator(self):
        """Simple calculator application"""
        self.clear_screen()
        print("=" * 50)
        print("        THINK OS 2.0v - CALCULATOR")
        print("=" * 50)
        print()
        num1 = float(input("Enter first number: "))
        operator = input("Enter operator (+, -, *, /): ")
        num2 = float(input("Enter second number: "))

        if operator == "+":
            result = num1 + num2
        elif operator == "-":
            result = num1 - num2
        elif operator == "*":
            result = num1 * num2
        elif operator == "/":
            if num2 == 0:
                result = "Error: Cannot divide by zero"
            else:
                result = num1 / num2
        else:
            result = "Error: Invalid operator"

        print()
        print("Result:", result)
        print()

        input("Press Enter to return to desktop...")

    def system_info(self):
        """Display system information"""
        self.clear_screen()
        print("=" * 50)
        print("        THINK OS - SYSTEM INFO")
        print("=" * 50)
        print()
        print("  +==========================================+")
        print("  |                                          |")
        print("  |            T H I N K   O S               |")
        print("  |                                          |")
        print("  |              Version 2.0                 |")
        print("  |                                          |")
        print("  +==========================================+")
        print()
        print(f"Operating System: Think OS v2.0")
        print(f"<c> HBREW INC for the based software.")
        print(f"<c> IdeaThink CO for the update to v2.0.")
        print(f"User: {self.current_user}")
        print(f"Current Date: {datetime.date.today()}")
        print(f"Current Time: {datetime.datetime.now().strftime('%H:%M:%S')}")
        print(f"Total Documents: {len(self.user_files)}")
        print(f"Installed Mods: {len(self.installed_mods)}")
        print(f"Python Version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
        print()
        input("Press Enter to return to desktop...")

    def ltd_desktop(self):
        """Limited desktop for guest users"""
        self.clear_screen()
        print("=" * 100)
        print()

        print("######## ##     ## #### ##    ## ##    ##     #######   ######                 #######        #####")
        time.sleep(0.4)
        print("   ##    ##     ##  ##  ###   ## ##   ##     ##     ## ##    ##               ##     ##      ##   ##")
        time.sleep(0.4)
        print("   ##    ##     ##  ##  ####  ## ##  ##      ##     ## ##                            ##     ##     ##")
        time.sleep(0.4)
        print("   ##    #########  ##  ## ## ## #####       ##     ##  ######     #######     #######      ##     ##")
        time.sleep(0.4)
        print("   ##    ##     ##  ##  ##  #### ##  ##      ##     ##       ##               ##            ##     ##")
        time.sleep(0.4)
        print("   ##    ##     ##  ##  ##   ### ##   ##     ##     ## ##    ##               ##        ###  ##   ##")
        time.sleep(0.4)
        print("   ##    ##     ## #### ##    ## ##    ##     #######   ######                ######### ###   #####")
        time.sleep(0.4)

        print()
        print("=" * 100)
        print()
        print("Welcome, Guest!")
        print("You have access to: Calculator, Clock, and Games.")
        print("File creation/browsing requires an Admin login.")
        print()
        input("Press Enter to continue...")

        while True:
            self.clear_screen()
            print("=" * 100)
            print()

            print("######## ##     ## #### ##    ## ##    ##     #######   ######                 #######        #####")
            print("   ##    ##     ##  ##  ###   ## ##   ##     ##     ## ##    ##               ##     ##      ##   ##")
            print("   ##    ##     ##  ##  ####  ## ##  ##      ##     ## ##                            ##     ##     ##")
            print("   ##    #########  ##  ## ## ## #####       ##     ##  ######     #######     #######      ##     ##")
            print("   ##    ##     ##  ##  ##  #### ##  ##      ##     ##       ##               ##            ##     ##")
            print("   ##    ##     ##  ##  ##   ### ##   ##     ##     ## ##    ##               ##        ###  ##   ##")
            print("   ##    ##     ## #### ##    ## ##    ##     #######   ######                ######### ###   #####")

            print()
            print("=" * 100)
            print()
            print(f"Date: {datetime.date.today()}  |  Time: {datetime.datetime.now().strftime('%H:%M:%S')}")
            print()
            print("1) Calculator")
            print("2) Clock")
            print("3) Games...")
            print("4) Logout")
            print()

            choice = input("Select option: ")

            if choice == "1" or choice.lower() == "calculator":
                self.calculator()
            elif choice == "2" or choice.lower() == "clock":
                self.clock()
            elif choice == "3" or choice.lower() == "games":
                self.games_folder()
            elif choice == "4" or choice.lower() == "logout":
                self.logout()
                break

    def clock(self):
        """Display current date and time"""
        self.clear_screen()
        print("=" * 50)
        print("        THINK OS - CLOCK")
        print("=" * 50)
        print()
        print(f"Current Date: {datetime.date.today()}")
        print(f"Current Time: {datetime.datetime.now().strftime('%H:%M:%S')}")
        print()
        input("Press Enter to return...")

    def logout(self):
        """Logout current user"""
        self.clear_screen()
        print("Logging out...")
        time.sleep(1)
        self.current_user = None

    def terminal_ide(self):
        """Terminal application"""
        current_program = []
        current_line = 10
        variables = {}

        self.clear_screen()
        print("=" * 60)
        print("        THINK OS - TERMINAL")
        print("=" * 60)
        print()
        print("THINK OS TERMINAL V1.0")
        print("<c> HBREW Inc. All rights reserved.")
        print("READY")
        print()
        print("Type HELP for available commands")
        print()

        while True:
            command = input("] ").strip().upper()

            if not command:
                continue

            # Split command and arguments
            parts = command.split()
            cmd = parts[0] if parts else ""
            args = parts[1:] if len(parts) > 1 else []

            if cmd == "HELP":
                print()
                print("AVAILABLE COMMANDS:")
                print("LIST - Display current program")
                print("RUN - Execute current program")
                print("NEW - Clear current program")
                print("LOAD [filename] - Load a program")
                print("SAVE [filename] - Save current program")
                print("AUTO [line] - Set auto line numbering")
                print("RENUM - Renumber program lines")
                print("DELETE [line] - Delete a line")
                print("CATALOG - Show saved programs")
                print("HOME - Clear screen")
                print("POKE [address] [value] - Set memory value")
                print("PEEK [address] - Read memory value")
                print("PRINT [expression] - Print value")
                print("HELLO - Display greeting")
                print("CALL -151 - Enter monitor mode")
                print("CONT - Continue program")
                print("NEOFETCH - About this system")
                print("EXIT - Return to desktop")
                print()
                print("PROGRAMMING:")
                print("10 PRINT \"HELLO WORLD\"")
                print("20 FOR I=1 TO 10")
                print("30 PRINT I")
                print("40 NEXT I")
                print()

            elif cmd == "LIST":
                if not current_program:
                    print("NO PROGRAM IN MEMORY")
                else:
                    print()
                    for line_num, line_code in sorted(current_program):
                        print(f"{line_num} {line_code}")
                print()

            elif cmd == "RUN":
                if not current_program:
                    print("NO PROGRAM TO RUN")
                    print()
                    continue

                print()
                self.execute_basic_program(current_program, variables)
                print()
                print("PROGRAM FINISHED")
                print()

            elif cmd == "NEW":
                current_program = []
                variables = {}
                current_line = 10
                print("PROGRAM CLEARED")
                print()

            elif cmd == "LOAD":
                if args:
                    filename = args[0]
                    if filename in self.user_files:
                        # Load program from file
                        content = self.user_files[filename]
                        current_program = []
                        for line in content.split('\n'):
                            if line.strip():
                                try:
                                    parts = line.split(' ', 1)
                                    line_num = int(parts[0])
                                    code = parts[1] if len(parts) > 1 else ""
                                    current_program.append((line_num, code))
                                except:
                                    pass
                        print(f"LOADED: {filename}")
                    else:
                        print(f"FILE NOT FOUND: {filename}")
                else:
                    print("SYNTAX: LOAD [FILENAME]")
                print()

            elif cmd == "SAVE":
                if args and current_program:
                    filename = args[0]
                    # Save program to file
                    content = []
                    for line_num, line_code in sorted(current_program):
                        content.append(f"{line_num} {line_code}")
                    self.user_files[filename] = '\n'.join(content)
                    self.save_data()
                    print(f"SAVED: {filename}")
                elif not current_program:
                    print("NO PROGRAM TO SAVE")
                else:
                    print("SYNTAX: SAVE [FILENAME]")
                print()

            elif cmd == "AUTO":
                if args:
                    try:
                        current_line = int(args[0])
                        print(f"AUTO LINE NUMBERING SET TO {current_line}")
                    except:
                        print("INVALID LINE NUMBER")
                else:
                    current_line = 10
                    print("AUTO LINE NUMBERING SET TO 10")
                print()

            elif cmd == "RENUM":
                if current_program:
                    new_program = []
                    line_num = 10
                    for _, code in sorted(current_program):
                        new_program.append((line_num, code))
                        line_num += 10
                    current_program = new_program
                    print("PROGRAM RENUMBERED")
                else:
                    print("NO PROGRAM TO RENUMBER")
                print()

            elif cmd == "DELETE":
                if args:
                    try:
                        del_line = int(args[0])
                        current_program = [(num, code) for num, code in current_program if num != del_line]
                        print(f"LINE {del_line} DELETED")
                    except:
                        print("INVALID LINE NUMBER")
                else:
                    print("SYNTAX: DELETE [LINE NUMBER]")
                print()

            elif cmd == "CATALOG":
                print()
                print("SAVED PROGRAMS:")
                basic_files = [f for f in self.user_files.keys() if f.upper().endswith('.BAS') or not '.' in f]
                if basic_files:
                    for filename in basic_files:
                        print(f"  {filename}")
                else:
                    print("  NO PROGRAMS SAVED")
                print()

            elif cmd == "HOME":
                self.clear_screen()
                print("SCREEN CLEARED")
                print()

            elif cmd == "POKE":
                if len(args) >= 2:
                    try:
                        address = int(args[0])
                        value = int(args[1])
                        print(f"POKE {address},{value}")
                        # Simulate memory operation
                        if address == 32:  # Text color
                            print("TEXT COLOR CHANGED")
                        elif address == 49200:  # Bell
                            print("BEEP!")
                    except:
                        print("INVALID POKE COMMAND")
                else:
                    print("SYNTAX: POKE [ADDRESS] [VALUE]")
                print()

            elif cmd == "NEOFETCH":
                print(f"Operating System: Think OS v2.0")
                print(f"Based idea for ThinkOS")
                print(f"<c> HBREW INC.")
                print(f"Programmed By Elian")
                print(f"Update to v2.0")
                print(f"<c> IdeaThink CO.")
                print(f"Updated By JC")
                print(f"Current Date: {datetime.date.today()}")
                print(f"Current Time: {datetime.datetime.now().strftime('%H:%M:%S')}")
                print(f"Total Documents: {len(self.user_files)}")
                print(f"Installed Mods: {len(self.installed_mods)}")
                print(f"Version: 2.0 Python Port")
                print()

            elif cmd == "PEEK":
                if args:
                    try:
                        address = int(args[0])
                        # Simulate memory read
                        value = random.randint(0, 255)
                        print(f"PEEK({address}) = {value}")
                    except:
                        print("INVALID ADDRESS")
                else:
                    print("SYNTAX: PEEK [ADDRESS]")
                print()

            elif cmd == "PRINT":
                if args:
                    expression = ' '.join(args)
                    # Simple expression evaluator
                    try:
                        if '"' in expression:
                            # String literal
                            result = expression.strip('"')
                        else:
                            # Math expression
                            result = eval(expression, {"__builtins__": {}}, variables)
                        print(result)
                    except:
                        print("SYNTAX ERROR")
                else:
                    print("SYNTAX: PRINT [EXPRESSION]")
                print()

            elif cmd == "HELLO":
                print()
                print("HELLO, WELCOME TO THINK OS TERMINAL")
                print()

            elif command == "CALL -151":
                print()
                print("ENTERING MONITOR MODE...")
                self.monitor_mode()
                print("EXITING MONITOR MODE")
                print()

            elif cmd == "CONT":
                print("PROGRAM CONTINUED")
                print()

            elif cmd == "EXIT":
                break

            # Check if it's a program line (starts with number)
            elif cmd.isdigit():
                try:
                    line_num = int(cmd)
                    line_code = ' '.join(args)

                    if line_code:  # Add or replace line
                        # Remove existing line with same number
                        current_program = [(num, code) for num, code in current_program if num != line_num]
                        # Add new line
                        current_program.append((line_num, line_code))
                        print(f"LINE {line_num} ENTERED")
                    else:  # Delete line
                        current_program = [(num, code) for num, code in current_program if num != line_num]
                        print(f"LINE {line_num} DELETED")

                except:
                    print("SYNTAX ERROR")
                print()

            else:
                print(f"?SYNTAX ERROR: {command}")
                print()

    def execute_basic_program(self, program, variables):
        """Execute a BASIC program"""
        lines = dict(sorted(program))
        line_numbers = sorted(lines.keys())
        current_index = 0
        for_stack = []  # Stack for FOR loops

        while current_index < len(line_numbers):
            line_num = line_numbers[current_index]
            code = lines[line_num].strip()

            if not code:
                current_index += 1
                continue

            # Parse command
            parts = code.split()
            if not parts:
                current_index += 1
                continue

            cmd = parts[0].upper()

            try:
                if cmd == "PRINT":
                    # Handle PRINT statement
                    if len(parts) > 1:
                        content = ' '.join(parts[1:])
                        if content.startswith('"') and content.endswith('"'):
                            print(content[1:-1])
                        else:
                            # Try to evaluate as expression
                            try:
                                result = eval(content, {"__builtins__": {}}, variables)
                                print(result)
                            except:
                                print(content)
                    else:
                        print()

                elif cmd == "LET":
                    # Variable assignment: LET X = 5
                    if "=" in code:
                        var_part, val_part = code.split("=", 1)
                        var_name = var_part.split()[-1].strip()
                        try:
                            value = eval(val_part.strip(), {"__builtins__": {}}, variables)
                            variables[var_name] = value
                        except:
                            pass

                elif cmd == "FOR":
                    # FOR I = 1 TO 10
                    try:
                        parts = code.replace("=", " = ").split()
                        var_name = parts[1]
                        start_val = int(eval(parts[3], {"__builtins__": {}}, variables))
                        end_val = int(eval(parts[5], {"__builtins__": {}}, variables))

                        variables[var_name] = start_val
                        for_stack.append({
                            'var': var_name,
                            'end': end_val,
                            'line_index': current_index
                        })
                    except:
                        pass

                elif cmd == "NEXT":
                    # NEXT I
                    if for_stack:
                        loop_info = for_stack[-1]
                        var_name = loop_info['var']

                        if var_name in variables:
                            variables[var_name] += 1

                            if variables[var_name] <= loop_info['end']:
                                # Continue loop
                                current_index = loop_info['line_index']
                                continue
                            else:
                                # End loop
                                for_stack.pop()

                elif cmd == "GOTO":
                    # GOTO 100
                    if len(parts) > 1:
                        target_line = int(parts[1])
                        if target_line in line_numbers:
                            current_index = line_numbers.index(target_line)
                            continue

                elif cmd == "IF":
                    # IF X > 5 THEN PRINT "BIG"
                    if "THEN" in code.upper():
                        condition_part, then_part = code.upper().split("THEN", 1)
                        condition = condition_part[2:].strip()  # Remove "IF"

                        try:
                            if eval(condition, {"__builtins__": {}}, variables):
                                # Execute THEN part
                                then_command = then_part.strip()
                                if then_command.startswith("GOTO"):
                                    target = int(then_command.split()[1])
                                    if target in line_numbers:
                                        current_index = line_numbers.index(target)
                                        continue
                                elif then_command.startswith("PRINT"):
                                    content = then_command[5:].strip()
                                    if content.startswith('"') and content.endswith('"'):
                                        print(content[1:-1])
                        except:
                            pass

                elif cmd == "INPUT":
                    # INPUT X
                    if len(parts) > 1:
                        var_name = parts[1]
                        try:
                            value = input(f"{var_name}? ")
                            variables[var_name] = float(value) if '.' in value else int(value)
                        except:
                            variables[var_name] = value

                elif cmd == "REM":
                    # Comment - do nothing
                    pass

                elif cmd == "END":
                    break

            except Exception as e:
                print(f"ERROR IN LINE {line_num}: {e}")
                break

            current_index += 1

    def monitor_mode(self):
        """Monitor Mode simulation"""
        print("THINK OS MONITOR")
        print()

        while True:
            command = input("* ").strip().upper()

            if not command:
                continue

            if command in ["G", "CTRL-C"]:
                break
            elif command.startswith("L"):
                print("MEMORY LISTING:")
                for i in range(8):
                    addr = 2048 + i * 8
                    values = [f"{random.randint(0, 255):02X}" for _ in range(8)]
                    print(f"{addr:04X}: {' '.join(values)}")
                print()
            elif command.startswith("D"):
                print("DISASSEMBLY:")
                print("0800: A9 00    LDA #$00")
                print("0802: 8D 00 04 STA $0400")
                print("0805: 60       RTS")
                print()
            elif ":" in command:
                print("MEMORY SET")
                print()
            else:
                print("MONITOR COMMANDS:")
                print("L - List memory")
                print("D - Disassemble")
                print("ADDR:VALUE - Set memory")
                print("G - Go (exit monitor)")
                print()

    def run(self):
        """Main run loop"""
        while True:
            self.boot_screen()


# ============================================================================
# RUN THINK OS
# ============================================================================
if __name__ == "__main__":
    print()
    start_up = ("Booting Up", "Starting Program", "Reading Python", "Opening files", "Wasting Ram", "Reading 1984", "Doing Math", "Testing Games", "Running Functions", "Taking a Break", "'Back on Track' – RobTop", "Counting Numbers")
    for showing_start in start_up:
        print(showing_start)
        time.sleep(0.15)
    print()
    for show_num in range(10):
        print(show_num, show_num)
        time.sleep(0.15)
    print()
    print("Done with Nothing")
    print()
    print("Starting Think OS v2.0...")
    time.sleep(2)
    os_instance = ThinkOS()
    os_instance.run()