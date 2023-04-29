import asyncio
import os
from pathlib import Path
from typing import List, AnyStr

import nest_asyncio
import pyautogui
import time
import json
import socket
import http.client

from httpx import AsyncClient

from src import KEY
from networkmapper.nmap import Nmap
from src.utils.logman import logger
from src.utils.utils import run_lsof_command
from src.vsextension.Command import Command
from src.vsextension.editor_context import EditorContext

from src.vsextension.extention import Extension
from src.vsextension.keybinding import KeyBinding
from src.vsextension.palette import CommandPalette
from src.vsprocess.vsprocess import VSProcess
from vsextension.vsepuller import VSExtensionPuller

TRAVERSAL_KEYWORDS_TO_SEARCH = ["live", "live server", "open", "preview"]
ZIP_KEYWORDS_TO_SEARCH = ["zip", "compress", "unzip", "compressed", "archive"]

nest_asyncio.apply()
loop = asyncio.get_event_loop()
IP = None
client = AsyncClient()

ATTACK = {
    "path_traversal_attack": {
        "keywords_to_search": TRAVERSAL_KEYWORDS_TO_SEARCH,
        "library_path": Path(__file__).parent.joinpath("library.json"),
        "save_vul_path": "vulnerable_extensions.json",
        "file_to_open": "index.html",
    },
    "zip_slip_attack": {
        "keywords_to_search": ZIP_KEYWORDS_TO_SEARCH,
        "library_path": Path(__file__).parent.joinpath("library_zip.json"),
        "save_vul_path": "vulnerable_extensions.json",
        "file_to_open": "testingzip.zip",
    },
}

LIBRARY_PATH = ATTACK[KEY]["library_path"]
SAVE_VUL_PATH = ATTACK[KEY]["save_vul_path"]
FILE_TO_OPEN = ATTACK[KEY]["file_to_open"]
KEYWORDS_TO_SEARCH = ATTACK[KEY]["keywords_to_search"]

POSSIBLE_ACTIVATION_EVENTS = {
    "onLanguage:html": {"extension": "html", "content": "<html> <head> TEST </head> </html>"},
    "onLanguage:ini": {"extension": "ini", "content": "[test]"},
    "onLanguage:javascript": {"extension": "js", "content": "console.log('test')"},
    "onLanguage:json": {"extension": "json", "content": '{"test": "test"}'},
    "onLanguage:jsonc": {"extension": "jsonc", "content": '{"test": "test"}'},
    "onLanguage:markdown": {"extension": "md", "content": "# test"},
    "onLanguage:php": {"extension": "php", "content": "<?php echo 'test'; ?>"},
    "onLanguage:typescript": {"extension": "ts", "content": "console.log('test')"},
    "onLanguage:yaml": {"extension": "yaml", "content": "test: test"},
    # "onLanguage:bat",
    # "onLanguage:javascriptreact",
    # "onLanguage:scss",
    # "onLanguage:sql",
    # "onLanguage:typescriptreact",
    # "onLanguage:xml",
}


def create_key(extension_name: AnyStr) -> AnyStr:
    """Create a key out of extension name"""
    return extension_name.replace(" ", "---").lower()


def save_vulnerable_extension(_extension: Extension):
    """Save vulnerable extension in a json file including Key value pairs of publisher,
    extension name, version, short description, published date, last updated, versions
    """
    vuln_path = Path(__file__).parent.joinpath(SAVE_VUL_PATH)
    if vuln_path.exists():
        file = open(vuln_path, mode="r")
        data = json.load(file)
        file.close()
        Path(vuln_path).unlink()
    else:
        data = dict()
    new_key = create_key(_extension.extension_name)
    if new_key not in data:
        data[new_key] = {
            "publisherName": _extension.publisher.publisher_name,
            "extensionName": _extension.extension_name,
            "version": _extension.version,
            "shortDescription": _extension.short_description,
            "publishedDate": _extension.published_date,
            "lastUpdated": _extension.last_updated,
        }
    file = open(SAVE_VUL_PATH, mode="w")
    json.dump(data, file, indent=4)


def refresh_library(_extensions: List[Extension]):
    """Save extensions json to library.json"""
    data = dict()

    if LIBRARY_PATH.exists():
        library_file = open(LIBRARY_PATH, mode="r")
        data = json.load(library_file)
        library_file.close()

    for _extension in _extensions:
        data[_extension.extension_name] = _extension.to_json()

    with open(LIBRARY_PATH, "w") as file:
        json.dump(data, file, indent=4)

    return [Extension.from_json(extension) for extension in data.values()]


def mark_tested(_extension):
    """Mark extensions as tested"""
    data = dict()
    logger.info("Marking " + _extension.extension_name + " as tested")

    if LIBRARY_PATH.exists():
        library_file = open(LIBRARY_PATH, mode="r")
        data = json.load(library_file)
        library_file.close()

    data[_extension.extension_name]["tested"] = True

    with open(LIBRARY_PATH, "w") as file:
        json.dump(data, file, indent=4)

    logger.info("Marked " + _extension.extension_name + " as tested")


async def download_extensions(all_extensions: List[Extension]):
    """Download all extensions"""
    tasks = list()
    asyncio_semaphore = asyncio.BoundedSemaphore(50)
    async with asyncio_semaphore:
        for _extension in all_extensions:
            if not _extension.downloaded:
                tasks.append(_extension.download())
        await asyncio.gather(*tasks)


async def install_and_unzip_extension(extension: Extension):
    """Install extension in vscode and run tests on it"""
    await extension.install()
    await extension.unzip()


async def uninstall_and_cleanup_extension(extension: Extension):
    """Uninstall extension in vscode and cleanup"""
    await extension.uninstall()
    # await extension.cleanup()  # TODO: Uncomment this while running in production


async def pull_commands(extension: Extension):
    """Pull commands from package.json from extensions"""
    await extension.pull_commands()


def get_ip():
    """Get current IP assigned to machine"""
    global IP
    if IP is None:
        hostname = socket.gethostname()
        IP = socket.gethostbyname(hostname)
        logger.info("Running on IP: " + IP)
    return IP


def get_ports():
    """Run nmap using Nmap class and return open ports"""
    nmap = Nmap("localhost")
    loop.run_until_complete(nmap.scan())
    return nmap.open_ports


def validate_response(ip: AnyStr, port: int, url: AnyStr, extension: Extension):
    """Hit multiple urls asynchronously and check the response"""
    logger.info("Testing " + url + " on " + ip + ":" + str(port))

    uri_ = f"http://{ip}:{port}/{url}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/111.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
    }

    try:
        conn = http.client.HTTPConnection(ip, port)
        conn.request('GET', uri_, headers=headers)
        response = conn.getresponse()
        if response.status == 200 and "You are under attack by a cookiehere!" in str(response.read()):
            logger.critical(
                "Path traversal attack success on port "
                + str(port)
                + " for extension "
                + extension.extension_name
            )
            return True
        else:
            logger.info(
                "Path traversal attack failed on port "
                + str(port)
                + " for extension "
                + extension.extension_name
            )
    except Exception as e:
        logger.error(
            "Path traversal attack errored on port "
            + str(port)
            + " for extension "
            + extension.extension_name
        )
        logger.error(e, exc_info=True)
    return False


def validate_extracted_files(extension: Extension):
    """Validate files extracted from extension"""
    logger.info("Validating files extracted from " + extension.extension_name)
    current_directory = Path(__file__).parent
    parent_parent_directory = current_directory.parent.parent

    # check if file with name "exploit" exists in parent_parent_directory
    if (parent_parent_directory / "exploit").exists():
        logger.critical(
            "Path traversal attack success on extension "
            + extension.extension_name
            + " using file "
            + str(parent_parent_directory / "exploit")
        )
        return True
    return False


def try_path_traversal_hack(extension: Extension):
    """
    Get all ports that are open on this machine using nmap and lsof
    Hit each port and test of the path traversal attack is successful
    """

    host_ip = get_ip()
    ports = get_ports() + run_lsof_command()
    logger.info(
        "Open ports for extension " + extension.extension_name + " are: " + str(ports)
    )

    jobs = list()
    for port in ports:
        url1 = "../../cookiehere.html"
        url2 = "../cookiehere.html"
        url3 = "../../../cookiehere.html"

        jobs.append((host_ip, port, url1, extension))
        jobs.append((host_ip, port, url2, extension))
        jobs.append((host_ip, port, url3, extension))

    for job in jobs:  # TODO: Use multithreading
        if validate_response(*job):
            return True
    return False


def switch_back_to_vscode():
    """Go back to VS Code window"""
    time.sleep(1)
    pyautogui.hotkey("command", "space")
    pyautogui.typewrite("Visual Studio Code")
    time.sleep(1)
    pyautogui.press("enter")
    time.sleep(1)


def open_file_in_editor(file_name):
    """Click on the VS Code window and go to file"""
    pyautogui.click(
        x=900, y=900
    )  # Replace x and y with coordinates inside the VS Code window
    time.sleep(1)
    pyautogui.hotkey("command", "shift", "p")
    time.sleep(1)
    pyautogui.typewrite("Go to File...")
    pyautogui.press("enter")
    time.sleep(1)
    pyautogui.typewrite(file_name)
    pyautogui.press("enter")
    time.sleep(1)


def try_zip_slip_hack(extension: Extension, command: Command):  # TODO: Fix this after right click for MAC
    """Test ZIP slip attack in extension"""

    stop_test = False
    pyautogui.click(x=900, y=900)
    time.sleep(10)
    pyautogui.hotkey('shift', 'command', 'e')
    # Allow time for Command Palette to open
    time.sleep(2)
    pyautogui.typewrite("testingzip.zip", interval=0.1)
    time.sleep(2)
    pyautogui.hotkey('shift', 'f10')
    time.sleep(1)
    search = [char for char in str(command)[0:5]] + ['enter']
    pyautogui.typewrite(search, interval=0.1)
    pyautogui.press("enter")
    time.sleep(2)

    if validate_extracted_files(extension):
        stop_test = True

    time.sleep(2)
    switch_back_to_vscode()
    return stop_test


def command_palette_success(command: Command, command_palette: List[CommandPalette], extension: Extension, file_to_open: AnyStr = "index.html"):
    """Test commands for command palette"""

    stop_test = False
    if command.command in command_palette:
        _palette = [palette for palette in command_palette if palette == command.command]
        if _palette and _palette[0].when == 'false':
            return stop_test

    open_file_in_editor(file_to_open)
    pyautogui.hotkey("command", "shift", "p")
    pyautogui.typewrite(str(command))
    pyautogui.press("enter")
    time.sleep(1)
    if try_path_traversal_hack(extension):
        stop_test = True
    switch_back_to_vscode()

    return stop_test


def editor_context_success(editor_contexts: List[EditorContext], extension: Extension, file_to_open: AnyStr = "index.html"):

    stop_test = False
    for editor_context in editor_contexts:
        open_file_in_editor(file_to_open)

        # Right-click on the text editor
        pyautogui.rightClick(900, 900)
        # Wait for the context menu to appear
        time.sleep(1)
        # Choose an option from the context menu, e.g. 'Format Document'
        # You can replace 'Format Document' with the desired option
        search = [char for char in str(editor_context)] + ['enter']
        pyautogui.typewrite(search, interval=0.1)

        if try_path_traversal_hack(extension):
            stop_test = True
            break
        switch_back_to_vscode()

    return stop_test


def command_explorer_success(command: Command, extension: Extension, file_to_look: AnyStr = "testingzip.zip"):
    """Test commands for command explorer"""
    return try_zip_slip_hack(extension, command)


# TODO: Future work
def keybinding_success(keybindings: List[KeyBinding], extension: Extension):
    pass


# TODO: Future work
def editor_title_context_success(param, extension):
    pass


def process_on_language_event(activation_event, extension):
    """Create a file with the language specified in the activation event
    also set the default path in .vscode/settings.json to the same file"""

    event = POSSIBLE_ACTIVATION_EVENTS.get(activation_event, None)
    if event:
        ext = event["extension"]
        file_name = "index." + ext
        file_path = os.path.join(os.getcwd(), file_name)
        with open(file_path, "w") as f:
            f.write(event["content"])

        return file_path
    else:
        logger.error("Invalid activation event: " + activation_event)
        return None


def process_activation_events(extension):
    """Take necessary steps to activate the extension"""

    for activation_event in extension.activation_events:
        if activation_event == "*":
            logger.info("Activating extension: " + extension.extension_name)
            break
        elif activation_event.startswith("onLanguage:"):
            logger.info("Activating extension: " + extension.extension_name)
            return process_on_language_event(activation_event, extension)


def debug_extension(extension: Extension):
    """
    Debug extension is an extensive function to test several type of commands
    It will run each command from `extension.commands` and test it

    Running a command can be done in several ways:
        - Using Command Palette
        - Using Keybinding
        - Using EditorContext Menu
        - Using Editor Title Menu

    This will give priority to Command Palette, then EditorContext Menu, then Keybinding
    and then Editor Title Menu. If any of the above shows that the extension is vulnerable
    it will stop the test and return the result. Otherwise, it will continue to the next
    """

    logger.info(
        "Running tests on extension: "
        + extension.extension_name
        + " by "
        + extension.publisher.publisher_name
    )

    file_path = process_activation_events(extension)
    if file_path is None or file_path == "":
        file_path = "index.html"

    for _, command in extension.commands.items():

        if (command_palette_success(command, command.all_type_commands["commandPalette"], extension, file_path)
                or editor_context_success(command.all_type_commands["editorContext"], extension, file_path)
                or keybinding_success(command.all_type_commands["keyBinding"], extension)
                or editor_title_context_success(command.all_type_commands["editorTitleContext"], extension)):
            save_vulnerable_extension(extension)
            break

    logger.info("Finished running tests on extension: " + extension.extension_name)
    # mark_tested(extension)  # TODO : Uncomment


def debug_zextension(extension: Extension):
    """
    Debug zip extensions extensively by simulating right clicks with options
    """
    logger.info(
        "Running tests on zip extension: "
        + extension.extension_name
        + " by "
        + extension.publisher.publisher_name
    )

    zip_file_path = "testingzip.zip"

    for _, command in extension.commands.items():
        if command_explorer_success(command, extension, zip_file_path):
            save_vulnerable_extension(extension)
            break

    logger.info("Finished running tests on zip extension: " + extension.extension_name)
    # mark_tested(extension)


async def debug_extensions(all_extensions: List[Extension], vscode_process, limiter):
    """Install all extensions in vscode and run tests on them"""

    async with limiter:
        try:
            # # install all extensions
            # tasks = list()
            # for extension in all_extensions:
            #     if not extension.tested:
            #         tasks.append(install_and_unzip_extension(extension))
            # await asyncio.gather(*tasks)

            # Pull commands from package.json from extensions
            tasks = list()
            for extension in all_extensions:
                if not extension.tested:
                    tasks.append(pull_commands(extension))
            await asyncio.gather(*tasks)

            # Let extensions install
            await asyncio.sleep(2)  # TODO: Change to 10

            # start vscode
            await asyncio.gather(vscode_process.start())

            # debug all extensions
            for extension in all_extensions:
                if not extension.tested:
                    if KEY == "path_traversal_attack":
                        debug_extension(extension)
                    elif KEY == "zip_slip_attack":
                        debug_zextension(extension)
                    else:
                        logger.error("Please configure the right KEY inside __init__.py")

            await asyncio.sleep(2)  # TODO: Change to 10
            await asyncio.gather(vscode_process.kill())
        finally:
            # uninstall all extensions
            tasks = list()
            # for extension in all_extensions:
            #     if not extension.tested:
            #         tasks.append(uninstall_and_cleanup_extension(extension))
            # await asyncio.gather(*tasks)


async def start(_downloaded_extensions: List[Extension]):
    asyncio_semaphore = asyncio.BoundedSemaphore(1)
    vscode_process = VSProcess()

    try:
        jobs = []
        for i in range(len(_downloaded_extensions)):
            jobs.append(
                asyncio.ensure_future(
                    debug_extensions(
                        _downloaded_extensions[i: i + 1],
                        vscode_process,
                        asyncio_semaphore,
                    )
                )
            )
        await asyncio.gather(*jobs)
    finally:
        time.sleep(5)
        await vscode_process.kill()


if __name__ == "__main__":
    # Pull extensions from marketplace
    extensions = list()

    ###########################################
    # NOTE uncomment to pull from marketplace #
    ###########################################
    # puller = VSExtensionPuller()
    # extensions = asyncio.run(puller.pull(KEYWORDS_TO_SEARCH))

    extensions = refresh_library(extensions)
    asyncio.run(download_extensions(extensions))
    extensions = refresh_library(extensions)

    # Filter extensions that are already downloaded
    extensions = [ext for ext in extensions if ext.downloaded]

    ########################
    # GO SLOW ON THIS PART #
    ########################

    # Filter extensions that are already tested
    asyncio.run(
        start(extensions[0:1])
    )
