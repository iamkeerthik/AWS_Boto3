import boto3
import xlsxwriter

# Replace with the AWS regions you want to list load balancers from
regions = ['ap-south-1', 'us-east-1', 'eu-west-1', 'eu-central-1']

# Replace with the name of the AWS profile you want to use
aws_profile = 'stage'

# Create a Boto3 session with the specified profile
session = boto3.Session(profile_name=aws_profile)

# Create a new Excel workbook and worksheet
workbook = xlsxwriter.Workbook('load_balancers.xlsx')
worksheet = workbook.add_worksheet()

# Write the headers for the worksheet
worksheet.write(0, 0, 'Region')
worksheet.write(0, 1, 'Load Balancer Name')
worksheet.write(0, 2, 'Type')
worksheet.write(0, 3, 'DNS Name')
worksheet.write(0, 4, 'Internal/Internet-Facing')
worksheet.write(0, 5, 'Protocol')

# Loop through each region
row = 1
for region_name in regions:
    # Create a Boto3 client for Elastic Load Balancing in the current region
    elb_client = session.client('elbv2', region_name=region_name)

    # Get all load balancers in the current region
    response = elb_client.describe_load_balancers()

    # Loop through each load balancer in the current region
    for lb in response['LoadBalancers']:
        lb_name = lb['LoadBalancerName']
        lb_type = lb['Type']
        lb_dns_name = lb['DNSName']
        lb_scheme = lb['Scheme'].upper()
        
        # Check if the load balancer is internal or internet-facing
        if lb_scheme == 'INTERNAL':
            lb_internet_facing = 'Internal'
        else:
            lb_internet_facing = 'Internet-Facing'
        
        # Check if the load balancer is a Network Load Balancer (NLB)
        if lb_type == 'network':
            lb_protocol = 'TCP'
        # Check if the load balancer is an Application Load Balancer (ALB)
        elif lb_type == 'application':
            lb_protocol = 'HTTP/HTTPS'
        
        worksheet.write(row, 0, region_name)
        worksheet.write(row, 1, lb_name)
        worksheet.write(row, 2, lb_type)
        worksheet.write(row, 3, lb_dns_name)
        worksheet.write(row, 4, lb_internet_facing)
        worksheet.write(row, 5, lb_protocol)
        
        row += 1

# Close the workbook
workbook.close()

print('Load balancers details exported to load_balancers.xlsx')
