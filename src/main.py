import asyncio
from typing import List
import pickle

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


async def debug_extension(vscode_process: VSProcess, extension: Extension):
    """Install extension in vscode and run tests on it"""
    # await extension.install()
    # TODO: Run tests on extension

    # await asyncio.wait([asyncio.sleep(5)])
    await extension.uninstall()


async def debug_extensions(all_extensions: List[Extension]):
    """Install all extensions in vscode and run tests on them"""
    vscode_process = VSProcess()

    try:
        # await vscode_process.start()
        for extension in all_extensions:
            await debug_extension(vscode_process, extension)
    finally:
        # await asyncio.wait([asyncio.sleep(5)])
        # await vscode_process.kill()
        ...


if __name__ == "__main__":
    # Pull extensions from marketplace
    # puller = VSExtensionPuller()
    # extensions = asyncio.run(puller.pull(KEYWORDS_TO_SEARCH))
    # asyncio.run(download_extensions(extensions))

    # extension = [ext for ext in extensions if ext.downloaded]

    # Save extensions to file
    # with open("extensions.pickle", "wb") as f:
    #     pickle.dump(extensions, f)

    # Load extensions from file
    with open("extensions.pickle", "rb") as f:
        downloaded_extensions = pickle.load(f)

    # Start Vscode sub process and install extensions from downloads folder
    asyncio.run(debug_extensions(downloaded_extensions[:5]))
