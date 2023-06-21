import boto3

# Specify the IP address to whitelist
ip_address = '<ip to whitelist>'

# Specify the AWS profile name
aws_profile = 'Stage'

# Specify the security groups with their specific regions
security_groups = [
    {
        'region': 'ap-south-1',
        'security_group_id': '<sg-groupid>'
    },
    {
        'region': 'us-east-2',
        'security_group_id': '<sg-groupid>'
    }
]

def remove_whitelist_ip(ip, region, sg_id):
    try:
        session = boto3.Session(profile_name=aws_profile, region_name=region)
        ec2_client = session.client('ec2')
        response = ec2_client.revoke_security_group_ingress(
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
        print(f"Removed IP {ip} from the whitelist in Security Group {sg_id} in region {region}")
    except Exception as e:
        print(f"Error removing IP {ip} from the whitelist in Security Group {sg_id} in region {region}: {str(e)}")

# Remove IP from the whitelist in each security group within its specific region
for security_group in security_groups:
    region = security_group['region']
    sg_id = security_group['security_group_id']
    remove_whitelist_ip(ip_address, region, sg_id)
