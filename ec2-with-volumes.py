import csv
import jmespath
import boto3
import os
import argparse

# Replace with the AWS region you want to list EC2 instances from
region = 'eu-west-1'

# Replace with the name of the AWS profile you want to use
aws_profile = 'stage'

# Get EC2 client for specified profile and region
session = boto3.Session(profile_name=aws_profile, region_name=region)
ec2_client = session.client('ec2')

# Get list of EC2 instances and their EBS volumes
response = ec2_client.describe_instances()
output = jmespath.search("Reservations[].Instances[].[NetworkInterfaces[0].OwnerId, InstanceId, InstanceType, \
            State.Name, Placement.AvailabilityZone, PrivateIpAddress, PublicIpAddress, KeyName, [Tags[?Key=='Name'].Value] [0][0], \
            BlockDeviceMappings[*].Ebs.VolumeId, BlockDeviceMappings[*].DeviceName, VpcId, LaunchTime]", response)

# Get EBS volume size for each volume ID
for instance in output:
    for i, volume_id in enumerate(instance[9]):
        volume_response = ec2_client.describe_volumes(VolumeIds=[volume_id])
        volume_size = jmespath.search("Volumes[].Size", volume_response)[0]
        instance[9][i] = volume_size

# Write output to CSV file with headers
with open(f"{aws_profile}-{region}-ec2-inventory.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(['AccountID','InstanceID','Type','State','AZ','PrivateIP','PublicIP','KeyPair','Name','VolumeSize','DeviceName', 'LaunchTime'])
    writer.writerows(output)

print("EC2 inventory complete")
