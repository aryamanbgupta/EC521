import os
import zipfile
import json
import re
import pandas as pd

def unzip_vsix(files, download_dir, unzipped_dir):
    for file in files:
        if file.endswith('.vsix'):
            with zipfile.ZipFile(os.path.join(download_dir, file), 'r') as zip_ref:
                print("Unipping=",file)
                zip_ref.extractall(path=os.path.join(unzipped_dir, file[:-5]))
        else:
            continue


def semgrep_check(directories, check_dir, report_dir):
    for dir in directories:
        # cmd = f'semgrep --config=auto {os.path.join(check_dir, dir)} --output {os.path.join(report_dir, dir)}.json --json'
        # os.chdir(os.path.join(check_dir, dir))
        cmd = f'semgrep --config=auto {os.path.join(check_dir, dir)} --junit-xml >> {os.path.join(report_dir, dir)}.txt'

        print(cmd)
        os.system(cmd)


def snyk_check(directories, check_dir, report_dir):
    for dir in directories:
        cmd = f'snyk test {os.path.join(check_dir, dir)} --all-projects --json-file-output={os.path.join(report_dir, dir)}.txt'
        # cmd = f'snyk test {os.path.join(check_dir, dir)} --all-projects >> {os.path.join(report_dir, dir)}.txt'
        print(cmd)
        os.system(cmd)


# Searches json files
def json_search(report_semgrep_dir,report_snyk_dir, keyword = 'path traversal'):
    data1 = []
    for filename in os.listdir(report_semgrep_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(report_semgrep_dir, filename)
            with open(file_path, 'r') as f:
                json_data = json.load(f)
            json_str = json.dumps(json_data)
            match = bool(re.search(keyword, json_str))
            data1.append({'filename': filename, 'Semgrep contains_keyword': match})

    df1 = pd.DataFrame(data1)
 
    data2 = []
    for filename in os.listdir(report_snyk_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(report_snyk_dir, filename)
            with open(file_path, 'r') as f:
                json_data = json.load(f)
            json_str = json.dumps(json_data)
            match = bool(re.search(keyword, json_str))
            data2.append({'filename': filename, 'Snyk contains_keyword': match})
            print(data2)
    df2 = pd.DataFrame(data2)
    
    df_combined = pd.merge(df1,df2, on='filename', how='left', indicator=True)
    df_combined = df_combined.drop('_merge', axis=1)

    df_combined.to_csv("compare.csv")
    df_combined.to_html('compare.html')
    print(df_combined)



# Searches txt files
def txt_search(report_semgrep_dir,report_snyk_dir, keyword = 'path traversal'):
    data1 = []
    for filename in os.listdir(report_semgrep_dir):
        if filename.endswith('.txt'):
            file_path = os.path.join(report_semgrep_dir, filename)
            with open(file_path, 'r') as f:
                txt_data = f.read()
            match = bool(re.search(keyword, txt_data))
            data1.append({'filename': filename, 'Semgrep PathTraversal': match})
    df1 = pd.DataFrame(data1)
    
    data2 = []
    for filename in os.listdir(report_snyk_dir):
        if filename.endswith('.txt'):
            file_path = os.path.join(report_snyk_dir, filename)
            with open(file_path, 'r') as f:
                txt_data = f.read()
            match = bool(re.search(keyword, txt_data))
            data2.append({'filename': filename, 'Snyk PathTraversal': match})

    df2 = pd.DataFrame(data2)

    df_combined = pd.merge(df1,df2, on='filename', how='left', indicator=True)
    df_combined = df_combined.drop('_merge', axis=1)
    
    df_combined['filename'] = df_combined['filename'].str.lower()
    df_combined = df_combined.sort_values(by=['filename']).reset_index(drop=True)
    df_combined = df_combined.fillna(False)

    df_combined.to_csv("compare.csv")
    # df_combined.to_json('compare.json', orient='records')
    df_combined.to_html('compare.html')
    
    print(df_combined)


def main():
    # Folder for downloaded extensions
    parent_dir = '/Users/zta/Docs/EC521/EC521/src/downloads'
    # Folder for unzipped extensions
    check_dir = '/Users/zta/Docs/EC521/EC521/src/unzipped_200/'
    # Folders to put reports
    report_semgrep_dir = '/Users/zta/Docs/EC521/EC521/src/scan_results_semgrep_200/'
    report_snyk_dir = '/Users/zta/Docs/EC521/EC521/src/scan_results_snyk_200_json/'

    # Get files and directories
    files = next(os.walk(parent_dir))[2]
    directories = next(os.walk(check_dir))[1]

    # Function calls:
    # unzip_vsix(files, parent_dir, check_dir)
    # semgrep_check(directories, check_dir, report_semgrep_dir)
    # snyk_check(directories, check_dir, report_snyk_dir)
    # json_search(report_semgrep_dir,report_snyk_dir)
    # txt_search(report_semgrep_dir,report_snyk_dir, keyword = 'Directory')
    txt_search(report_semgrep_dir,report_snyk_dir)
    # json_search(report_semgrep_dir,report_snyk_dir, keyword = 'slip')

if __name__ == "__main__":
    main()


