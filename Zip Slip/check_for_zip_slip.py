import os
import zipfile
import shutil
import asyncio
import json

async def find_keywords_in_files(directory):
    package_json_path = os.path.join(directory, 'extension/package.json')
    
    if not os.path.exists(package_json_path):
        return False

    with open(package_json_path, "r", encoding="utf-8") as f:
        package_json = json.load(f)

    dependencies = package_json.get('dependencies', {})

    # Keywords to search for
    required_keywords = ["axios", "express", "multer"]
    optional_keywords = ["jszip", "adm-zip", "unzipper"]

    # Check if required keywords are present
    if not all(keyword in dependencies for keyword in required_keywords):
        return False

    # Check if any of the optional keywords are present
    if not any(keyword in dependencies for keyword in optional_keywords):
        return False

    return True

async def process_vsix(item, directory, index, total):
    vsix_path = os.path.join(directory, item)
    zip_path = vsix_path.replace(".vsix", ".zip")
    os.rename(vsix_path, zip_path)

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        unzip_dir = zip_path.replace(".zip", "")
        zip_ref.extractall(unzip_dir)

    interesting_file = await find_keywords_in_files(unzip_dir)

    shutil.rmtree(unzip_dir)
    os.rename(zip_path, vsix_path)

    if interesting_file:
        print(f"[PROGRESS] [Interesting File] ********* Processed {index + 1}/{total} .vsix files: {item}")
    else:
        print(f"[PROGRESS] Processed {index + 1}/{total} .vsix files: {item}")

async def main():
    directory = "/Users/prateek/Downloads/extensions"

    tasks = []
    vsix_files = [item for item in os.listdir(directory) if item.endswith(".vsix")]
    total_vsix_files = len(vsix_files)

    for index, item in enumerate(vsix_files):
        tasks.append(process_vsix(item, directory, index, total_vsix_files))

    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
