import json
import shutil
import traceback
from pathlib import Path
from typing import AnyStr
import asyncio
from zipfile import ZipFile

import aiofiles
from httpx import AsyncClient

from src.vsextension.publisher import Publisher
from src.vsextension.versions import Version
from src.utils.logman import logger


class Extension:
    """Represents an extension"""

    DOWNLOAD_LOCATION = Path(__file__).parent.parent.joinpath("downloads")
    UNZIP_LOCATION = Path(__file__).parent.parent.joinpath("unzipped")
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
        self.all_commands = list()

    @property
    def version(self):
        return self.versions[0].version if len(self.versions) > 0 else ""

    @property
    def __path(self):
        return Path.joinpath(
            self.DOWNLOAD_LOCATION,
            f"{self.publisher.publisher_name}-{self.extension_name}-{self.version}.vsix",
        )

    @property
    def commands(self):
        return self.all_commands

    def get_vsix_download_url(self):
        """Returns the download url for the vsix file"""
        return f"https://marketplace.visualstudio.com/_apis/public/gallery/publishers/{self.publisher.publisher_name}/vsextensions/{self.extension_name}/{self.version}/vspackage"

    async def download(self):
        """Downloads the vsix file"""
        logger.info(
            "Downloading %s by %s ... into %s",
            self.extension_name,
            self.publisher.publisher_name,
            self.DOWNLOAD_LOCATION,
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
            logger.error(
                "Failed to download %s, will retry after 10 sec", self.extension_name
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
                logger.error(
                    "Failed to download %s after retrying", self.extension_name
                )
                logger.error("skipping... extension %s", self.extension_name)
                logger.error(e, exc_info=True)
                return self

        if response.status_code == 200:
            async with aiofiles.open(extension_file, "wb") as file:
                await file.write(response.content)
            self.downloaded = True
        else:
            # TODO: (shubham) store in a ledger json file that this extension failed to download
            logger.error("Failed to download %s", self.extension_name)
        return self

    async def pull_commands(self):
        """Pulls the commands from the extension package.json"""
        logger.info("Pulling commands for %s", self.extension_name)
        extension_dir = Path.joinpath(
            self.UNZIP_LOCATION,
            f"{self.publisher.publisher_name}-{self.extension_name}-{self.version}",
        )
        package_json = Path.joinpath(extension_dir, "extension", "package.json")
        if not package_json.exists():
            logger.warn(
                f"Package.json does not exist for {self.extension_name}, skipping..."
            )
            return self

        async with aiofiles.open(package_json, "r") as file:
            data = json.loads(await file.read())
            if "contributes" in data:
                contributes = data["contributes"]
                if "commands" in contributes:
                    commands = contributes["commands"]
                    for command in commands:
                        self.all_commands.append(command)

    async def install(self):
        """Installs the extension"""
        logger.info(
            "Installing extension %s by %s",
            self.extension_name,
            self.publisher.publisher_name,
        )
        subp = await asyncio.create_subprocess_shell(
            f"code --install-extension {self.__path}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                subp.communicate(), timeout=self.TIMEOUT
            )
            if stderr is None:
                logger.info("Extension installed successfully")
                logger.info("Output: %s", stdout)
            else:
                logger.error("Error installing extension")
                logger.error(stderr)
        except Exception as e:
            logger.error("Exception installing extension")
            logger.error(e, exc_info=True)

    async def uninstall(self):
        """Uninstalls the extension"""
        logger.info(
            "Uninstalling extension %s by %s",
            self.extension_name,
            self.publisher.publisher_name,
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
                logger.info("Extension uninstalled successfully")
                logger.info("Output: %s", stdout)
            else:
                logger.error("Error uninstalling extension")
                logger.error(stderr)
        except Exception as e:
            logger.error("Exception uninstalling extension")
            logger.error(e, exc_info=True)

    async def unzip(self):
        """Unzips the vsix file"""
        logger.info("Unzipping extension... %s", self.extension_name)
        extension_dir = Path.joinpath(
            self.UNZIP_LOCATION,
            f"{self.publisher.publisher_name}-{self.extension_name}-{self.version}",
        )

        if not extension_dir.exists():
            extension_dir.mkdir(parents=True, exist_ok=True)

        try:
            with ZipFile(self.__path, "r") as zip_ref:
                zip_ref.extractall(extension_dir)
        except Exception as e:
            logger.error("Failed to unzip %s", self.extension_name)
            logger.error(e, exc_info=True)

        logger.info(
            "Unzipped extension... %s into %s", self.extension_name, extension_dir
        )
        return extension_dir

    async def cleanup(self):
        """Cleans up the unzipped directory"""
        logger.info("Cleaning up... %s", self.extension_name)
        extension_dir = Path.joinpath(
            self.UNZIP_LOCATION,
            f"{self.publisher.publisher_name}-{self.extension_name}-{self.version}",
        )
        shutil.rmtree(extension_dir)
        logger.info("Cleaned up... %s", self.extension_name)

    def __str__(self):
        return f"Extension: {self.extension_name} by {self.publisher.publisher_name}"
