import pandas as pd
import os
df = pd.DataFrame()

# Parses Snyk results
parent_dir = '/Users/zta/Documents/EC521/src/scan_results_snyk/'
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
parent_dir = '/Users/zta/Documents/EC521/src/scan_results/'
# Walk on folders f = files
f = []
f = next(os.walk(parent_dir))[2]

result2 = []
for j in range(len(f)):
    with open(parent_dir + f[j],"r") as fi:
        if f[j].endswith('.txt'):
            for ln in fi:
                if ln.__contains__("failures="):
                    result2.append([f[j],ln])
                    break


 
df2 = pd.DataFrame(result2)
print(df2)

# Merges results
df3 = df2.merge(df1, how='outer', on=0)
df3 = df3.rename(columns={0: 'Name', '1_x': 'SemGrep_Failures', '1_y': 'SNYK_Issues'})

df3.to_csv('file1.csv')
print(df3)