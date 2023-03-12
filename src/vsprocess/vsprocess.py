import asyncio


VSCODE_PATH = (
    "/Users/shubham/Downloads/Visual\ Studio\ Code.app/Contents/MacOS/Electron"
)


class VSProcess:
    vscode_path = VSCODE_PATH

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
            print(f"Starting VSCode at '{self.vscode_path}'")
            self.__process = await asyncio.create_subprocess_shell(
                self.vscode_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE,
            )
            print(f"VSCode started with PID {self.__process.pid}")
        else:
            print("VSCode is already running")
            print(f"VSCode PID {self.__process.pid}")

    async def __stop(self):
        if self.__process is not None:
            print(f"Stopping VSCode with PID {self.__process.pid}")
            await self.__process.kill()
            self.__process = None
            print("VSCode stopped")
        else:
            print("VSCode is not running")
