import os
from zipfile import ZipFile

def unzip_vsix(f):
    # Unzip vsix
    for i in range(len(f)):
        if f[i].endswith('.vsix'):
            with ZipFile('/Users/zta/Documents/EC521/src/downloads/' + f[i], 'r') as zObject:
                # Extracting all the members of the zip into a specific location.
                print(f[i], i)
                zObject.extractall(path='/Users/zta/Documents/EC521/src/unzipped/'+f[i][:-5])
        else:
            continue

def semgrep_check(d):
    # Check with Semgrep
    
    for j in range(len(d)):
        cmd = 'semgrep --config=auto ' + check_dir + d[j] + ' --output ' + report_dir + d[j]+'.txt --junit-xml'
        print(cmd)
        os.system(cmd)


def snyk_check(d):
    # Check with Semgrep
    
    for j in range(len(d)):
        # cmd = 'snyk code test ' + check_dir + d[j] + ' --sarif-file-output=/Users/zta/Documents/EC521/src/scan_results_snyk/'+ d[j] +'.json'
        cmd = 'snyk test ' + check_dir + d[j] + ' --all-projects >> '+ '/Users/zta/Documents/EC521/src/scan_results_snyk/' + d[j]+'.txt'
        print(cmd)
        os.system(cmd)

# Walk on folders d = floders
check_dir = '/Users/zta/Documents/EC521/src/unzipped/'
d = []
d = next(os.walk(check_dir))[1]

parent_dir = '/Users/zta/Documents/EC521/src/downloads'
# Walk on folders f = files
f = []
f = next(os.walk(parent_dir))[2]

report_dir = '/Users/zta/Documents/EC521/src/scan_results/'

# Function calls
unzip_vsix(f)
semgrep_check(d)
snyk_check(d)

