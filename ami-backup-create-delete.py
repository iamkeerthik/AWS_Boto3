import boto3
from datetime import datetime, timedelta

def create_ami(instance_id, image_name, region, profile_name):
    session = boto3.Session(region_name=region, profile_name=profile_name)
    ec2_client = session.client('ec2')

    # Add InstanceId and autoexpiry tags
    tags = [
        {'Key': 'InstanceId', 'Value': instance_id},
        {'Key': 'autoexpiry', 'Value': 'true'}
    ]

    try:
        response = ec2_client.create_image(
            InstanceId=instance_id,
            Name=image_name,
            Description='Automated AMI backup',
            NoReboot=True,
            TagSpecifications=[
                {
                    'ResourceType': 'image',
                    'Tags': tags
                }
            ]
        )
        image_id = response['ImageId']
        tag_name = {'Key': 'Name', 'Value': image_name}
        ec2_client.create_tags(Resources=[image_id], Tags=[tag_name])
        return image_id
    except Exception as e:
        print(f"Failed to create AMI for instance {instance_id}: {str(e)}")
        return None

def delete_old_amis(instance_ids, region, profile_name, retention_days):
    session = boto3.Session(region_name=region, profile_name=profile_name)
    ec2_client = session.client('ec2')
    response = ec2_client.describe_images(
        Filters=[
            {'Name': 'tag:InstanceId', 'Values': instance_ids},
            {'Name': 'tag:autoexpiry', 'Values': ['true']},
            {'Name': 'state', 'Values': ['available']}
        ]
    )
    images = response['Images']

    for image in images:
        image_id = image['ImageId']
        creation_date = image['CreationDate']
        image_date = datetime.strptime(creation_date, '%Y-%m-%dT%H:%M:%S.%fZ')
        age = datetime.now() - image_date

        if age.days >= retention_days:
            snapshot_id = ''
            for mapping in image['BlockDeviceMappings']:
                if 'Ebs' in mapping and 'SnapshotId' in mapping['Ebs']:
                    snapshot_id = mapping['Ebs']['SnapshotId']
                    break

            if snapshot_id:
                try:
                    ec2_client.deregister_image(ImageId=image_id)
                    print(f"Deleted AMI {image_id} for instance IDs: {', '.join(instance_ids)} in region {region}")
                    ec2_client.delete_snapshot(SnapshotId=snapshot_id)
                    print(f"Deleted Snapshot {snapshot_id} for AMI {image_id} in region {region}")
                except Exception as e:
                    print(f"Failed to delete AMI {image_id} for instance IDs: {', '.join(instance_ids)} in region {region}: {str(e)}")
        else:
            print(f"AMI {image_id} is not eligible for deletion. It has not reached the retention period yet.")

def backup_and_delete_amis(instance_dict, profile_name, retention_days):
    for region, instances in instance_dict.items():
        for instance_id in instances:
            session = boto3.Session(region_name=region, profile_name=profile_name)
            ec2_resource = session.resource('ec2')
            instance = ec2_resource.Instance(instance_id)
            instance_name = [tag['Value'] for tag in instance.tags if tag['Key'] == 'Name'][0]
            today_str = datetime.now().strftime('%Y-%m-%d')
            today_image_name = f"{instance_name}_{instance_id}_{today_str}"
            image_id = create_ami(instance_id, today_image_name, region, profile_name)
            if image_id:
                print(f"Created AMI {today_image_name} (ID: {image_id}) for instance {instance_id}")
                delete_old_amis([instance_id], region, profile_name, retention_days)
            else:
                print(f"Failed to create AMI for instance {instance_id}")

# Specify your instance IDs, regions, profile name, and retention period (in days) here
instance_dict = {
    'ap-south-1': ['instnaceid1','instnaceid2'],
    'us-east-2': ['instnaceid1','instnaceid2']
}

profile_name = 'PS'
retention_days = 3

backup_and_delete_amis(instance_dict, profile_name, retention_days)
