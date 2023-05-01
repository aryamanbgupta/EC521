# Finding Vulnerabilities in VS Code Extensions

Finding vulnerabilities in VSCode extensions is always a challenging task. This repository is a collection of resources 
that can help you find vulnerabilities in VSCode extensions. This repository is a work in progress and will be updated,
for the time being, it contains the following resources:

- Path Traversal Attack - Path traversal vulnerability, also known as directory traversal, is a type of security 
    vulnerability that allows an attacker to gain unauthorized access to files and directories outside the intended 
    scope of the application. It occurs when user input is not properly validated or sanitized, allowing an attacker 
    to manipulate file paths and access sensitive data or system files
- Zip Slip Attack : Zip Slip is a type of security vulnerability that occurs during the extraction of compressed files. 
    It arises when an attacker manipulates the file paths within a compressed archive to cause a directory traversal, 
    allowing them to overwrite files or create new files in unintended locations. Zip Slip vulnerabilities can be 
    exploited by crafting a malicious archive file that contains specially crafted file paths.

## Pre-requisites

- VSCode Installed on your machine
- Python 3.6 or above
- Create a virtual environment and install the requirements.txt file

## Steps: How To Use ?

STEP-1: Set `KEYWORDS` - Keywords to search for in the VSCode Marketplace

STEP-2: Change `KEY` - Toggle the `KEY` in `__init__.py` file in src folder to test specific vulnerability

STEP-3: Provide `VSCODE_PATH` - Path to VSCode installed on your machine

STEP-4: Set `WORKSPACE` - Path to the workspace where you want to run tests.

STEP-5: Set `NMAP_PATH` - Path to nmap installed on your machine

STEP-6: Run `python3 main.py`


## Challenges

- Downloading multiple extensions at same time, Since Microsoft does not provide API to search based on keywords.
- Microsoft also limit number of requests for any particular IP address and extension ID.
- How to get the port number from the `package.json`, `package.nls.json` files.
- How to get the port number, which is currently used by the extension. (Most extensions allocate port numbers randomly)
- Checking for path traversal in the extension using variants of URI's, headers like `User-Agents` and other parameters.
- Automating the whole process using python coroutines made it much faster which was a challenge in itself.


## Pre-requisites for automated reports

- Python 3.6 or above
- SNYK CLI
- Semgrep 1.19.0


## Steps: How To create automated reports with SNYK and Semgrep ?

STEP-1: Authenticate Snyk account via CLI with `snyk auth`

STEP-2: **Set directories**: Configure the necessary directories for your project:

- `PARENT_DIR`: The parent directory containing the folders with extensions
- `CHECK_DIR`: The directory to extract extensions
- `REPORT_SEMGREP_DIR`: The directory to save Semgrep reports
- `REPORT_SNYK_DIR`: The directory to save Snyk reports

STEP-3: Set `KEYWORD` - Choose a keyword to search the type of vulnerability in the results of the report

STEP-4: Run `python3 Checker.py` Execute the following command to run the Python script

## Steps: How to use exploits on the vulnerable extensions?

### Steps for Exploit 1 : Path traversal
STEP-1: Host the index.html and data.php on some server.

STEP-2: Open VS Code.

STEP-3: Run `HQ Live Server` on some HTML file.

STEP-4: Click on the website link for your hosted webpage.

### Steps for Exploit 2 : Zip Slip Vulnerability

STEP-1: Create payload by running `python create_zip.py` with correct parameters for `file_content` and `file_name` variable. 

STEP-2: Open VScode and install extension Zip File Explorer.

STEP-3: Extract the zip created in Step 1 in VS code.

STEP-4: This will write  a file authorized_keys in ~/.ssh folder with the `file_content` you provided.

STEP-5: Change the following setting in /etc/ssh/sshd_config file
`StrictModes no`

STEP-6: Connect from the other system using `ssh`.
