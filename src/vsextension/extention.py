import json
import traceback
from pathlib import Path
from typing import AnyStr
import asyncio

import aiofiles
from httpx import AsyncClient

from src.vsextension.publisher import Publisher
from src.vsextension.versions import Version


class Extension:
    """Represents an extension"""

    DOWNLOAD_LOCATION = Path(__file__).parent.parent.joinpath("downloads")
    TIMEOUT = 160
    client = AsyncClient()

    def __init__(
        self,
        publisher: Publisher,
        extension_id: AnyStr,
        extension_name: AnyStr,
        published_date: AnyStr,
        last_updated: AnyStr,
        short_description: AnyStr,
        versions: AnyStr,
    ):
        self.publisher = publisher
        self.extension_id = extension_id
        self.extension_name = extension_name
        self.published_date = published_date
        self.last_updated = last_updated
        self.short_description = short_description
        self.versions = [
            Version(version[Version.VERSION], version[Version.LAST_UPDATED])
            for version in versions
        ]
        self.downloaded = False

    @property
    def version(self):
        return self.versions[0].version if len(self.versions) > 0 else ""

    @property
    def full_path(self):
        return Path.joinpath(
            self.DOWNLOAD_LOCATION,
            f"{self.publisher.publisher_name}-{self.extension_name}-{self.version}.vsix",
        )

    def get_vsix_download_url(self):
        """Returns the download url for the vsix file"""
        return f"https://marketplace.visualstudio.com/_apis/public/gallery/publishers/{self.publisher.publisher_name}/vsextensions/{self.extension_name}/{self.version}/vspackage"

    async def download(self):
        """Downloads the vsix file"""
        print(
            f"Downloading {self.extension_name} by {self.publisher.publisher_name}... into {self.DOWNLOAD_LOCATION}"
        )
        version = f"-{self.version}" if self.version else ""
        extension_file = Path.joinpath(
            self.DOWNLOAD_LOCATION,
            f"{self.publisher.publisher_name}-{self.extension_name}{version}.vsix",
        )

        if not extension_file.parent.exists():
            extension_file.parent.mkdir(parents=True, exist_ok=True)

        response = await self.client.get(
            self.get_vsix_download_url(),
            headers={
                "Accept": "application/octet-stream",
            },
        )

        if response.status_code != 200:
            print(
                f"Failed to download {self.extension_name}, retrying... after 10 seconds"
            )
            # sleep for 10 seconds and try again
            await asyncio.sleep(10)
            try:
                response = await self.client.get(
                    self.get_vsix_download_url(),
                    headers={
                        "Accept": "application/octet-stream",
                    },
                )
            except Exception as e:
                print(f"Failed to download {self.extension_name} after retrying")
                print(f"Skipping... extension {self.extension_name}")
                return self

        if response.status_code == 200:
            async with aiofiles.open(extension_file, "wb") as file:
                await file.write(response.content)
            self.downloaded = True
        else:
            # TODO: (shubham) store in a ledger json file that this extension failed to download
            print(f"Failed to download {self.extension_name}")
        return self

    async def install(self):
        """Installs the extension"""
        print(
            f"Installing extension {self.extension_name} by {self.publisher.publisher_name}"
        )
        subp = await asyncio.create_subprocess_shell(
            f"code --install-extension {self.full_path}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                subp.communicate(), timeout=self.TIMEOUT
            )
            if stderr is None:
                print("Extension installed successfully")
                print("Output: ", stdout)
            else:
                print("Error installing extension")
                print("Error: ", stderr)
        except Exception as e:
            print("Exception installing extension")
            print(traceback.print_exc())

    async def uninstall(self):
        """Uninstalls the extension"""
        print(
            f"Uninstalling extension {self.extension_name} by {self.publisher.publisher_name}"
        )
        subp = await asyncio.create_subprocess_shell(
            f"code --uninstall-extension {self.publisher.publisher_name}.{self.extension_name}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                subp.communicate(), timeout=self.TIMEOUT
            )
            if stderr is None:
                print("Extension uninstalled successfully")
                print("Output: ", stdout)
            else:
                print("Error uninstalling extension")
                print("Error: ", stderr)
        except Exception as e:
            print("Exception uninstalling extension")
            print(traceback.print_exc())

    def __str__(self):
        return f"Extension: {self.extension_name} by {self.publisher.publisher_name}"
