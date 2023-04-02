import asyncio
from typing import List
import pyautogui
import pickle
import time

from src.vsextension.extention import Extension
from src.vsprocess.vsprocess import VSProcess
from vsextension.vsepuller import VSExtensionPuller


KEYWORDS_TO_SEARCH = ["live server", "Latex", "Json", "Open in"]


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


def debug_extension(extension: Extension):
    """Run tests on extension"""
    time.sleep(10)

    print(f"\n==> Running tests on extension: {extension.extension_name} by {extension.publisher.publisher_name} <==")
    for command in extension.commands:
        command_to_run = f"{command['category']}:" if "category" in command else ""
        command_to_run += f"{command['title']}"
        print(f"$> Running command: {command_to_run}")
        pyautogui.click(x=200, y=200)  # Replace x and y with coordinates inside the VS Code window
        pyautogui.hotkey('command', 'shift', 'p')
        pyautogui.typewrite('Go to File...')
        pyautogui.press('enter')
        pyautogui.typewrite('index.html')
        pyautogui.press('enter')

        pyautogui.hotkey('command', 'shift', 'p')
        # Allow time for Command Palette to open
        time.sleep(1)
        pyautogui.typewrite(command_to_run)
        pyautogui.press('enter')


async def debug_extensions(all_extensions: List[Extension]):
    """Install all extensions in vscode and run tests on them"""
    vscode_process = VSProcess()

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

        await asyncio.wait([asyncio.sleep(5)])
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
        downloaded_extensions = pickle.load(f)

    # Start Vscode sub process and install extensions from downloads folder
    asyncio.run(debug_extensions(downloaded_extensions[5:10]))
