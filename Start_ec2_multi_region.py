import boto3
session = boto3.Session(profile_name='PS')
def start_ec2 (instances,region):
    try:
        ec2 = session.client('ec2', region_name=region)
        for id in instances:
            rsp = ec2.describe_instances(InstanceIds = [id])
            for pythonins in rsp['Reservations']:
                for printout in pythonins['Instances']:
                    for printname in printout['Tags']:
                        if printname['Key'] == 'Name':
                            server=(printname['Value'])

                    if (printout['State']['Name'] == 'stopped'):
                        print(f'{server} is stopped')
                        print(f'starting {server}....')
                        ec2.start_instances(InstanceIds=[id])
                    else:
                        print(f'{server}  is already running')
        
    except Exception as e:
        print(e)

mumbai = 'ap-south-1'
ohio = 'us-east-2'
oregon =  'us-west-2'

print ("............Mumbai...........")
mumbai_instances = ['i-0725fa47f5b1efe73']
start_ec2(mumbai_instances,mumbai)

print ("................Ohio...........")
ohio_instances =[]
start_ec2(ohio_instances,ohio)

print ("..............Oregon..............")
oregon_instnaces=[]
start_ec2(oregon_instnaces,oregon)

