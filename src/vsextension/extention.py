import json
import shutil
from pathlib import Path
from typing import AnyStr
import asyncio
from zipfile import ZipFile

import aiofiles
from httpx import AsyncClient

from src.utils.utils import get_random_user_agents
from src.vsextension.Command import Command
from src.vsextension.editor_context import EditorContext
from src.vsextension.keybinding import KeyBinding
from src.vsextension.palette import CommandPalette
from src.vsextension.publisher import Publisher
from src.vsextension.versions import Version
from src.utils.logman import logger
from src import KEY


EXTENSION = {
    "path_traversal_attack": {
        "downloads": "downloads",
        "unzipped": "unzipped",
    },
    "zip_slip_attack": {
        "downloads": "downloads_zip",
        "unzipped": "unzipped_zip",
    },
}

DOWNLOADS = EXTENSION[KEY]["downloads"]
UNZIPPED = EXTENSION[KEY]["unzipped"]


class Extension:
    """Represents an extension"""

    DOWNLOAD_LOCATION = Path(__file__).parent.parent.joinpath(DOWNLOADS)
    UNZIP_LOCATION = Path(__file__).parent.parent.joinpath(UNZIPPED)
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
        self._all_commands = dict()
        self._activation_events = list()
        self.tested = False

    @property
    def version(self):
        return self.versions[0].version if len(self.versions) > 0 else ""

    @version.setter
    def version(self, value):
        self.versions = Version(value, "")

    @property
    def __path(self):
        return Path.joinpath(
            self.DOWNLOAD_LOCATION,
            f"{self.publisher.publisher_name}-{self.extension_name}-{self.version}.vsix",
        )

    @property
    def commands(self):
        return self._all_commands

    @property
    def activation_events(self):
        return self._activation_events

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

        response = None
        try:
            response = await self.client.get(
                self.get_vsix_download_url(),
                headers={
                    "User-Agent": get_random_user_agents(),
                    "Accept": "application/octet-stream",
                },
            )

        except Exception as e:
            if response and response.status_code != 200:
                logger.error(
                    "Failed to download %s, will retry after 10 sec", self.extension_name
                )

                # sleep for 10 seconds and try again
                await asyncio.sleep(10)
                try:
                    response = await self.client.get(
                        self.get_vsix_download_url(),
                        headers={
                            "User-Agent": get_random_user_agents(),
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

        if response and response.status_code == 200:
            async with aiofiles.open(extension_file, "wb") as file:
                await file.write(response.content)
            self.downloaded = True
        else:
            # TODO: (shubham) store in a ledger json file that this extension failed to download
            logger.error("Failed to download %s", self.extension_name)
        return self

    @staticmethod
    async def _insert_nls_data(nls_data, package_data):
        """Replace values in package.json with nls data"""

        logger.info("Compiling package.json with nls data")

        for key, value in nls_data.items():
            new_key = "%" + key + "%"
            package_data_str = json.dumps(package_data)
            package_data_str = package_data_str.replace(new_key, value)
            package_data = json.loads(package_data_str)

        return package_data

    async def pull_activation_events(self, package_data):
        """Pull activation events from package.json"""

        logger.info("Pulling activation events from package.json")
        if "activationEvents" in package_data:
            self._activation_events = package_data["activationEvents"]
        logger.info("Activation events: %s", self._activation_events)

    async def _parse_package_json(self, package_data: dict):
        """Parse package json and fill _all_commands dictionary"""

        await self.pull_activation_events(package_data)

        if "contributes" not in package_data:
            logger.warn("No contributes found in package.json, skipping...")
            return

        logger.info("Parsing package.json for commands")
        contributes = package_data["contributes"]

        if "commands" in contributes:
            for command in contributes["commands"]:
                if "command" in command:
                    self._all_commands[command["command"]] = Command(
                        command["command"], command["title"], "" if "category" not in command else command["category"])

        if "menus" in contributes:
            if "editor/context" in contributes["menus"]:
                for context in contributes["menus"]["editor/context"]:
                    self._all_commands.get(context["command"]).all_type_commands["editorContext"].append(
                        EditorContext(context["command"], self._all_commands.get(context["command"]).title)
                    )

            if "commandPalette" in contributes["menus"]:
                for command in contributes["menus"]["commandPalette"]:
                    self._all_commands.get(command["command"]).all_type_commands["commandPalette"].append(
                        CommandPalette(command["command"], "" if "when" not in command else command["when"])
                    )

        if "keybindings" in contributes:
            for keybinding in contributes["keybindings"]:
                self._all_commands.get(keybinding["command"]).all_type_commands["keyBinding"].append(
                    KeyBinding(keybinding["command"], keybinding["key"], keybinding["when"], keybinding.get("mac", None))
                )

        logger.info("Finished parsing package.json for commands")
        logger.info("All commands: %s", self._all_commands)

        ####################################
        # Just for previewing the commands #
        ####################################

        # for key, command in self._all_commands.items():
        #     for cmd, value in command.all_type_commands.items():
        #         if len(value) > 0:
        #             logger.info("Type: %s", cmd)
        #             logger.info("Commands: %s", ", ".join([str(cc) for cc in value]))

    async def pull_commands(self):
        """Pulls the commands from the extension package.json"""
        logger.info("Pulling commands for %s", self.extension_name)
        extension_dir = Path.joinpath(
            self.UNZIP_LOCATION,
            f"{self.publisher.publisher_name}-{self.extension_name}-{self.version}",
        )
        package_json = Path.joinpath(extension_dir, "extension", "package.json")
        package_nls_json = Path.joinpath(extension_dir, "extension", "package.nls.json")

        if not package_json.exists():
            logger.warn(
                f"Package.json does not exist for {self.extension_name}, skipping..."
            )
            return self

        if not package_nls_json.exists():
            logger.info(
                f"Package.nls.json does not exist for {self.extension_name}, interesting..."
            )

        async with aiofiles.open(package_json, "r") as file:
            nls_data = None
            if package_nls_json.exists():
                logger.info(
                    f"Package.nls.json exist for {self.extension_name}, interesting..."
                )
                async with aiofiles.open(package_nls_json, "r") as nls_file:
                    nls_data = json.loads(await nls_file.read())

            data = json.loads(await file.read())

            if nls_data is not None:
                data = await self._insert_nls_data(nls_data, data)

        await self._parse_package_json(data)

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

    def to_json(self):
        """Get the json representation of the extension objects"""
        return {
            "extensionId": self.extension_id,
            "extensionName": self.extension_name,
            "publisherName": self.publisher.publisher_name,
            "publisherId": self.publisher.publisher_id,
            "publishedDate": self.published_date,
            "lastUpdated": self.last_updated,
            "shortDescription": self.short_description,
            "versions": [version.to_json() for version in self.versions],
            "downloaded": self.downloaded,
            "tested": self.tested,
        }

    @classmethod
    def from_json(cls, data):
        """Create an extension object from json"""
        new_object = cls(
            Publisher(data["publisherId"], data["publisherName"]),
            data["extensionId"],
            data["extensionName"],
            data["publishedDate"],
            data["lastUpdated"],
            data["shortDescription"],
            data["versions"]
        )
        new_object.downloaded = data["downloaded"]
        if "tested" in data:
            new_object.tested = data["tested"]
        return new_object
