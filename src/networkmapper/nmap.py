import asyncio
from collections import defaultdict
from typing import Any, Callable, Dict, List
from xml.etree import ElementTree as ET

from src import NMAP_PATH
from src.networkmapper.exceptions import NmapError
from src.utils.utils import async_for
from src.utils.logman import logger

nmap_path = NMAP_PATH

_stdout: Callable[[], Dict[str, Dict]] = lambda: {
    "state": dict(),
    "service": dict(),
    "script": dict(),
    "scriptDict": dict(),
}


async def cleandict(badd: Dict[str, Any]) -> Dict[str, Any]:
    """Clean keys and values by removing extra spaces & tabs

    Args:
        badd (Dict[str, Any]): bad dictionary

    Returns:
        Dict[str, Any]: cleaned dictionary
    """
    cleaned: Dict[str, Any] = dict()

    async for key, value in async_for(badd.items()):
        ckey = key.strip(" \t").strip(" ")
        if isinstance(value, dict):
            cleaned[ckey] = await cleandict(value)
        elif isinstance(value, list):
            cleaned[ckey] = list()
            async for val in async_for(value):
                cleaned[ckey].append(await cleandict(val))
        else:
            cleaned[ckey] = value.strip(" \t").strip(" ")

    return cleaned


class _ScriptXMLTarget:
    ports: Dict[str, Dict] = defaultdict(_stdout)
    lpkey: str = ""

    def start(self, tag: str, attrib: Dict):
        if tag.lower() in ("port",):
            _id = attrib.get("portid", "NA")
            protocol = attrib.get("protocol", "NA")
            self.lpkey = f"{_id}/{protocol}"
        elif tag.lower() in ("state", "service", "script") and self.lpkey:
            self.ports[self.lpkey][tag.lower()].update(attrib)

    def end(self, tag: str):
        if tag.lower() in ("port",):
            self.lpkey = ""

    def close(self):
        return {
            port: val
            for port, val in self.ports.items()
            if val.get("script", None)
            or val.get("state", dict()).get("state", "").lower() == "open"
        }

    def data(self, data):
        pass


class Nmap:
    default_args = "-oX - -Pn".split(" ")

    def __init__(self, ip: str, *args, **kwargs) -> None:
        self.__parser = ET.XMLParser(target=_ScriptXMLTarget())
        self.__raw: Dict[str, Any] = dict()
        self._cmnd_args: List[str] = list(Nmap.default_args)
        self._ip = ip

        self._cmnd_args.extend(list(args))

        for key, val in kwargs.items():
            self._cmnd_args.extend([key, val])

    @property
    def raw(self):
        return self.__raw

    @property
    def open_ports(self):
        ports = list(self.__raw.keys())
        ports = [int(port.split("/")[0]) for port in ports]
        ports = [port for port in ports if port > 1024 and port not in [49155, 49152]]
        return ports

    @staticmethod
    async def fromstring(string: str) -> Dict[str, Any]:
        """Form dictionary from string based using `:`,`\\`,`=`
        and `,` as separators.

        Args:
            string (str): string data of `ssl-cert` script

        Returns:
            Dict[str, Any]: converted dictionary
        """
        sslcertdict: Dict[str, Any] = dict()

        if ":" in string:
            key, value = string.split(":", 1)
            if "=" in value:
                sslcertdict[key] = await Nmap.fromstring(value)
            elif "," in value:
                sslcertdict[key] = list()
                async for key_val in async_for(value.split(",")):
                    sslcertdict[key].append(await Nmap.fromstring(key_val))
            elif ":" in value:
                sslcertdict[key] = await Nmap.fromstring(value)
            else:
                sslcertdict[key] = value
        elif "=" in string:
            if "/" in string:
                nested_sslcert = dict()
                async for key_val in async_for(string.split("/")):
                    nested_sslcert.update(await Nmap.fromstring(key_val))
                return nested_sslcert
            else:
                key, value = string.split("=", 1)
                sslcertdict[key] = value

        return sslcertdict

    @staticmethod
    async def outputdict(data: str) -> Dict[str, Any]:
        """Process output string convert into dictionary

        Args:
            data (str): string value of output key

        Returns:
            Dict[str, Any]: clean converted dictionary
        """
        _outdict = dict()

        async for item in async_for(data.split("\n")):
            _outdict.update(await Nmap.fromstring(item))

        return await cleandict(_outdict)

    async def parse_attrib(self, attrib: Dict[str, Any]) -> Dict[str, Any]:
        """Parse attributes present for script `ssl-cert`

        Args:
            attrib (Dict[str, Any]): attributes dictionary from xml

        Returns:
            Dict[str, Any]: `ssl-cert` script data
        """
        logger.info(f"Parsing script attribute for IP: '{self._ip}'")

        if output := attrib.get("output"):
            return await Nmap.outputdict(output)
        return dict()

    async def parse(self, output: bytes) -> None:
        """Parse output returned from nmap subprocess

        Args:
            output (bytes): nmap std output
        """
        logger.info(f"Parsing output of IP: '{self._ip}'")

        try:
            self.__parser.feed(output)
        except Exception as xerr:
            logger.error(
                f"errored in feeding output of IP: '{self._ip}'\n\tError: {str(xerr)}",
                exc_info=True,
            )
            self.__raw = {"error": "unable to parse namp output"}
            return

        self.__raw = self.__parser.close()

        async for port, data in async_for(self.__raw.items()):
            logger.info(f"Processing PORT: {port}, for IP {self._ip}")
            data.update(
                {"scriptDict": await self.parse_attrib(data.get("script", dict()))}
            )

    async def scan(self, timeout: int = 120) -> None:
        """Spawn nmap subprocess and parse output

        Args:
            timeout (int, optional): timeout for suprocess. Default to 120.
        """
        logger.info(f"initiating for IP: '{self._ip}' args: {self._cmnd_args}")

        cmnd = self._cmnd_args + [f"{self._ip}"]
        subp = await asyncio.create_subprocess_exec(
            nmap_path,
            *cmnd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )

        try:
            stdout, stderr = await asyncio.wait_for(subp.communicate(), timeout=timeout)
            if stderr is None:
                await self.parse(stdout)
            else:
                raise NmapError(stderr)
        except asyncio.TimeoutError:
            logger.warn(f"timedout for IP: '{self._ip}'")
            subp.kill()
        except NmapError as nerr:
            logger.error(
                f"errored for IP: '{self._ip}'\n\tError: {str(nerr)}", exc_info=True
            )
            self.__raw = {"error": "error from nmap subprocess"}
