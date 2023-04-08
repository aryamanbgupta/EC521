from typing import List, Dict, AnyStr
import json
from httpx import AsyncClient

from src.utils.utils import get_random_user_agents
from src.vsextension.extention import Extension
from src.vsextension.publisher import Publisher


class VSExtensionPuller:
    """Pulls extensions from the marketplace"""

    client = AsyncClient()
    url = "https://marketplace.visualstudio.com/_apis/public/gallery/extensionquery"
    payload = json.dumps(
        {
            "filters": [
                {
                    "criteria": [
                        {"filterType": 8, "value": "Microsoft.VisualStudio.Code"},
                        {"filterType": 10, "value": "%s"},
                        {"filterType": 12, "value": "37888"},
                    ],
                    "direction": 2,
                    "pageSize": 1000,
                    "pageNumber": 1,
                    "sortBy": 0,
                    "sortOrder": 0,
                    "pagingToken": None,
                }
            ]
        }
    )
    headers = {
        "User-Agent": get_random_user_agents(),
        "Accept": "application/json;api-version=7.1-preview.1;excludeUrls=true",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Content-Type": "application/json",
    }

    async def pull(self, keywords: List[AnyStr]) -> List[Extension]:
        """Pulls extensions from the marketplace"""
        extensions: List[Extension] = list()

        for keyword in (keyword for keyword in keywords):
            payload = self.payload % keyword
            response = await self.client.post(
                self.url, headers=self.headers, data=payload
            )
            extensions.extend(await self.__parse(json.loads(response.text)))

        return extensions

    async def __parse(self, response: Dict) -> List[Extension]:
        """Parses the response from the marketplace"""
        if "results" not in response:
            return []

        results = response["results"]

        if len(results) == 0:
            return []

        extensions = list()

        for extension in results[0].get("extensions", []):
            publisher = Publisher(
                extension["publisher"]["publisherId"],
                extension["publisher"]["publisherName"],
            )
            extensions.append(
                Extension(
                    publisher,
                    extension["extensionId"],
                    extension["extensionName"],
                    extension.get("publishedDate", "No Date"),
                    extension.get("lastUpdated", "No Date"),
                    extension.get("shortDescription", "No Description"),
                    extension["versions"],
                )
            )
        return extensions
