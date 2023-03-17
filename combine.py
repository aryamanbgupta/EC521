import pandas as pd
import os
from IPython.display import HTML

df = pd.DataFrame()

# Parses Snyk results
parent_dir = '/Users/zta/Docs/EC521/EC521/src/scan_results_snyk/'
# Walk on folders f = files
f = []
f = next(os.walk(parent_dir))[2]

result1 = []

for i in range(len(f)):
    with open(parent_dir + f[i],"r") as fi:
        if f[i].endswith('.txt'):
            for ln in fi:
                if ln.__contains__("found "):
                    result1.append([f[i],ln])
                    break
                

df1 = pd.DataFrame(result1)
# print(df1)


# Parses Semgrep results
parent_dir = '/Users/zta/Docs/EC521/EC521/src/scan_results_semgrep/'
# Walk on folders f = files
f = []
f = next(os.walk(parent_dir))[2]

result2 = []
for j in range(len(f)):
    with open(parent_dir + f[j],"r") as fi:
        if f[j].endswith('.txt'):
            for ln in fi:
                if ln.__contains__("failures="):
                    result2.append([f[j],ln[35:48]])
                    break


 
df2 = pd.DataFrame(result2)
# print(df2)

# Merges results
df3 = df2.merge(df1, how='outer', on=0)
df3 = df3.rename(columns={0: 'Name', '1_x': 'SemGrep_Issues', '1_y': 'SNYK_Issues'})
df3['SNYK_Issues'] = df3['SNYK_Issues'].fillna(0)


df3['SNYK file'] = '<a href="./src/scan_results_snyk/' + df3['Name'] + '">' + df3['Name'] + '</a>'


df3.insert(loc = 2, column = 'Semgrep file', value = '<a href="./src/scan_results_semgrep/' + df3['Name'] + '">' + df3['Name'] + '</a>')


df3.to_html('report.html', render_links=True, escape=False)

df3.to_csv('file1.csv')
print(df3)