import boto3
session = boto3.Session(profile_name='Test')
# Boto Connection
asg = session.client('autoscaling','ap-south-1')
def scaleup(asg_name, min, desired, max):
  response = asg.update_auto_scaling_group(AutoScalingGroupName=asg_name,MinSize=min,DesiredCapacity=desired,MaxSize=max)
  print(response)

Loki='autoscale group name'
# Dev=
# Stage=
# Stage-multilane=
print("....Loki...")
scaleup(Loki,1,1,1)
