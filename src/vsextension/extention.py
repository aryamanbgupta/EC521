from pathlib import Path
from typing import AnyStr
import requests

from src.vsextension.publisher import Publisher
from src.vsextension.versions import Version


class Extension:
    """Represents an extension"""

    DOWNLOAD_LOCATION = Path(__file__).parent.parent.joinpath("downloads")

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

    @property
    def version(self):
        return self.versions[0].version if len(self.versions) > 0 else ""

    def get_vsix_download_url(self):
        """Returns the download url for the vsix file"""
        return f"https://marketplace.visualstudio.com/_apis/public/gallery/publishers/{self.publisher.publisher_name}/vsextensions/{self.extension_name}/{self.version}/vspackage"

    def download(self):
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

        response = requests.get(
            self.get_vsix_download_url(),
            stream=True,
            headers={
                "Accept": "application/octet-stream",
                "User-Agent": "",  # TODO: (Shubham) Add user agents randomly, also think about rate limiting
            },
        )
        with open(extension_file, "wb") as file:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    file.write(chunk)
        return extension_file

    def __str__(self):
        return f"Extension: {self.extension_name} by {self.publisher.publisher_name}"
