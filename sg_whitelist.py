import boto3

# Specify the IP address to whitelist
ip_address = '<ip to whitelist>'

# Specify the AWS profile name
aws_profile = 'Stage'

# Specify the security groups with their specific regions
security_groups = [
    {
        'region': 'ap-south-1',
        'security_group_id': '<sg-group id>'
    },
    {
        'region': 'us-east-2',
        'security_group_id': '<sg-group id>'
    }
]

def whitelist_ip_address(ip, region, sg_id):
    try:
        session = boto3.Session(profile_name=aws_profile, region_name=region)
        ec2_client = session.client('ec2')
        response = ec2_client.authorize_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 80,
                    'ToPort': 80,
                    'IpRanges': [
                        {
                            'CidrIp': ip,
                            'Description': 'python-test'
                        },
                    ],
                },
            ],
        )
        print(f"Whitelisted IP {ip} in Security Group {sg_id} in region {region}")
    except Exception as e:
        print(f"Error whitelisting IP {ip} in Security Group {sg_id} in region {region}: {str(e)}")

# Whitelist IP in each security group within its specific region
for security_group in security_groups:
    region = security_group['region']
    sg_id = security_group['security_group_id']
    whitelist_ip_address(ip_address, region, sg_id)
