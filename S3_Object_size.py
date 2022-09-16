from boto3 import client
import pandas as pd
conn = client('s3')
col1 = "Folder"
col2 = "Size"
top_level_folders = dict()
df_list = []
n=0
bucket_to_search='keerthik-test'

for key in conn.list_objects(Bucket=bucket_to_search)['Contents']:

         #change this index to change folder level of s3 bucket (subfolders)
        folder = key['Key'].split('/')[0] 
        # print("Key %s in folder %s. %d bytes" % (key['Key'], folder, key['Size']))

        if folder in top_level_folders:
            top_level_folders[folder] += key['Size']
        else:
            top_level_folders[folder] = key['Size']


for folder, size in top_level_folders.items():
        def convert_bytes(size):
            for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
                if size < 1024.0:
                    return "%3.1f %s" % (size, x)
                size /= 1024.0
            return size
        
        # print(bucket_to_search)
        # print("Folder: %s, size: %s" % (folder, convert_bytes(size)))
        df_list.append(pd.DataFrame({col1:folder,col2:convert_bytes(size)},index=[n]))
        n=n+1
df = pd.concat(df_list)
         
df.to_excel(bucket_to_search+'.xlsx', sheet_name='sheet1', index=False)
