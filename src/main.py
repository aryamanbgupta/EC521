import asyncio
from typing import List

from src.vsextension.extention import Extension
from vsextension.puller import VSExtensionPuller


KEYWORDS_TO_SEARCH = ["live server", "Latex", "Json", "Open in"]


async def download_extensions(all_extensions: List[Extension]):
    for extension in all_extensions:
        print(str(extension))
        await extension.download()


if __name__ == "__main__":
    puller = VSExtensionPuller()
    extensions = asyncio.run(puller.pull(KEYWORDS_TO_SEARCH))
    asyncio.run(download_extensions(extensions))
