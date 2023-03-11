from typing import AnyStr

from src.vsextension.publisher import Publisher
from src.vsextension.versions import Version


class Extension:
    """Represents an extension"""
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

    def get_vsix_download_url(self):
        """Returns the download url for the vsix file"""
        return f"https://marketplace.visualstudio.com/_apis/public/gallery/publishers/{self.publisher.publisher_name}/vsextensions/{self.extension_name}/{self.version}/vspackage"

    def download(self):
        """Downloads the vsix file"""
        # TODO: (Shubham) Download the vsix file and save it at some location
        pass

    def __str__(self):
        return f"Extension: {self.extension_name} by {self.publisher.publisher_name}"
