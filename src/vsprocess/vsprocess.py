import asyncio

from src import VSCODE_PATH, WORKSPACE
from src.utils.logman import logger


class VSProcess:
    vscode_path = VSCODE_PATH
    workspace = WORKSPACE

    def __init__(self):
        self.__process = None

    @property
    def process(self):
        return self.__process

    async def start(self):
        await self.__start()

    async def kill(self):
        await self.__stop()

    async def __start(self):
        if self.__process is None:
            logger.info(f"Starting VSCode at '{self.vscode_path}'")
            self.__process = await asyncio.create_subprocess_shell(
                f"{self.vscode_path} {self.workspace}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE,
            )
            logger.info(f"VSCode started with PID {self.__process.pid}")
        else:
            logger.info("VSCode is already running")
            logger.info(f"VSCode PID {self.__process.pid}")

    async def __stop(self):
        if self.__process is not None:
            logger.info(f"Stopping VSCode with PID {self.__process.pid}")
            self.__process.kill()
            self.__process = None
            logger.info("VSCode stopped")
        else:
            logger.info("VSCode is not running")
