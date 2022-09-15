import csv
import jmespath
import boto3
import itertools
import configparser
import os

# Get list of profiles
config = configparser.ConfigParser()
path = os.path.join(os.path.expanduser('~'), '.aws/credentials')
config.read(path)
profiles = config.sections()

# Get list of regions
ec2_client = boto3.client('ec2')
regions = [region['RegionName']
            for region in ec2_client.describe_regions()['Regions']]

# Get list of EC2 attributes from all profiles and regions
myData = []
for profile in profiles:
    for region in regions:
        current_session = boto3.Session(profile_name = profile, region_name = region)
        client = current_session.client('ec2')
        response = client.describe_instances()
        output = jmespath.search("Reservations[].Instances[].[NetworkInterfaces[0].OwnerId, InstanceId, InstanceType, \
            State.Name, Placement.AvailabilityZone, PrivateIpAddress, PublicIpAddress, KeyName, [Tags[?Key=='Name'].Value] [0][0]]", response)
        myData.append(output)

# Write myData to CSV file with headers
output = list(itertools.chain(*myData))
with open("ec2-inventory-latest.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(['AccountID','InstanceID','Type','State','AZ','PrivateIP','PublicIP','KeyPair','Name'])
    writer.writerows(output)
