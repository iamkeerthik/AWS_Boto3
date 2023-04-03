import boto3
import pandas as pd

# Set the profile name for your AWS credentials
profile_name = 'stage'

# Set the regions to check
regions = ['ap-south-1', 'us-east-1']

# Initialize a session object with the specified profile
session = boto3.Session(profile_name=profile_name)

# Create empty lists to store bucket information
bucket_names = []
bucket_sizes = []
bucket_locations = []
bucket_creation_dates = []
bucket_lifecycle_policies = []

# Loop through each region to retrieve the information we need
for region in regions:
    try:
        # Initialize a client object for the S3 service in the specified region
        s3 = session.client('s3', region_name=region)
        
        # Retrieve a list of all S3 buckets in the region
        buckets = s3.list_buckets()

        # Loop through each bucket to retrieve its information
        for bucket in buckets['Buckets']:
            try:
                bucket_name = bucket['Name']
                bucket_names.append(bucket_name)

                # Retrieve the bucket size
                try:
                    response = s3.list_objects_v2(Bucket=bucket_name)
                    bucket_size = sum([obj['Size'] for obj in response['Contents']])
                    if bucket_size > 1099511627776:
                        bucket_size = f'{bucket_size/1099511627776:.2f} TB'
                    elif bucket_size > 1073741824:
                        bucket_size = f'{bucket_size/1073741824:.2f} GB'
                    elif bucket_size > 1048576:
                        bucket_size = f'{bucket_size/1048576:.2f} MB'
                    elif bucket_size > 1024:
                        bucket_size = f'{bucket_size/1024:.2f} KB'
                    else:
                        bucket_size = f'{bucket_size} B'
                except:
                    bucket_size = 'N/A'
                bucket_sizes.append(bucket_size)

                # Retrieve the bucket location
                try:
                    response = s3.get_bucket_location(Bucket=bucket_name)
                    bucket_location = response['LocationConstraint']
                    if bucket_location is None:
                        bucket_location = 'us-east-1'
                except:
                    bucket_location = 'N/A'
                bucket_locations.append(bucket_location)

                # Retrieve the bucket creation date
                try:
                    bucket_creation_date = bucket['CreationDate'].strftime('%Y-%m-%d %H:%M:%S %Z')
                except:
                    bucket_creation_date = 'N/A'
                bucket_creation_dates.append(bucket_creation_date)

                # Retrieve the bucket lifecycle policy
                try:
                    response = s3.get_bucket_lifecycle_configuration(Bucket=bucket_name)
                    bucket_lifecycle_policy = response['Rules']
                except:
                    bucket_lifecycle_policy = 'N/A'
                bucket_lifecycle_policies.append(bucket_lifecycle_policy)

            except:
                pass

    except:
        pass

# Create a Pandas DataFrame to store the bucket information
df = pd.DataFrame({'Bucket Name': bucket_names,
                   'Bucket Size': bucket_sizes,
                   'Bucket Location': bucket_locations,
                   'Bucket Creation Date': bucket_creation_dates,
                   'Bucket Lifecycle Policy': bucket_lifecycle_policies})

# Export the DataFrame to an Excel file
df.to_excel('s3_buckets_info.xlsx', index=False)
