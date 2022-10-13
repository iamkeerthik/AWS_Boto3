import boto3
import csv

session = boto3.Session(profile_name='default', region_name='us-east-1')

ec2 = session.client('ec2')
def ec2_details(id):

    result = []
    response = ec2.describe_instances(
        InstanceIds=[id]).get('Reservations')

    for item in response:
        for each in item['Instances']:
            result.append({
                'ImageId': each['ImageId'],
                'InstanceType': each['InstanceType'],
                'PublicIp': each['PublicIpAddress'],
                'PrivateIp': each['PrivateIpAddress']
            })
    #The result type will be list of dictionary.
    # print(result) [{'ImageId': 'ami-08c5e20f0xxxxxxxx', 'InstanceType': 't2.micro', 'PublicIp': '10.200.101.11', 'PrivateIp': '172.31.33.95'}]

    # Write to csv file.
    header = ['ImageId', 'InstanceType', 'PublicIp', 'PrivateIp']
    with open('ec2-details.csv', 'w') as file:
        writer = csv.DictWriter(file, fieldnames=header)
        writer.writeheader()
        writer.writerows(result)

Myec2=ec2.describe_instances()
for pythonins in Myec2['Reservations']:
 for printout in pythonins['Instances']:
  id=(printout['InstanceId'])
  ec2_details(id)
