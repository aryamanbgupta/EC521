import os
import zipfile
import shutil
import asyncio
import aiofiles

async def find_keywords_in_files(directory, output_file_name):
    keywords = ["ws", "wss", "openExternal"]
    websocket_found = False
    openExternal_found = False
    
    async def read_lines(file_path):
        async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
            return await f.readlines()

    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                lines = await read_lines(file_path)
                async with aiofiles.open(output_file_name, "a") as output_file:
                    for line_num, line in enumerate(lines, start=1):
                        for keyword in keywords:
                            if keyword in line:
                                await output_file.write(
                                    f"Keyword '{keyword}' found in file '{file}' "
                                    f"(path: {file_path}) at line {line_num}.\n"
                                )
                                if keyword in ["ws", "wss"]:
                                    websocket_found = True
                                else:
                                    openExternal_found = True
            except UnicodeDecodeError:
                async with aiofiles.open(output_file_name, "a") as output_file:
                    await output_file.write(f"Could not read file: {file_path}\n")
    return (websocket_found and openExternal_found)

async def process_vsix(item, directory, index, total):
    vsix_path = os.path.join(directory, item)
    zip_path = vsix_path.replace(".vsix", ".zip")
    os.rename(vsix_path, zip_path)

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        unzip_dir = zip_path.replace(".zip", "")
        zip_ref.extractall(unzip_dir)

    output_file_name = f"{item}_output.txt"
    intresting_file = await find_keywords_in_files(unzip_dir, output_file_name)

    shutil.rmtree(unzip_dir)
    os.rename(zip_path, vsix_path)

    if intresting_file:
        print(f"[PROGRESS] [Interesting File] ********* Processed {index + 1}/{total} .vsix files: {item}")
    else:
        print(f"[PROGRESS] Processed {index + 1}/{total} .vsix files: {item}")

async def main():
    directory = "./downloads"

    tasks = []
    vsix_files = [item for item in os.listdir(directory) if item.endswith(".vsix")]
    total_vsix_files = len(vsix_files)

    for index, item in enumerate(vsix_files):
        tasks.append(process_vsix(item, directory, index, total_vsix_files))

    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
