import boto3
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def create_ami(instance_id, image_name, region, profile_name):
    session = boto3.Session(region_name=region, profile_name=profile_name)
    ec2_client = session.client('ec2')

    # Add InstanceId and autoexpiry tags
    tags = [
        {'Key': 'InstanceId', 'Value': instance_id},
        {'Key': 'autoexpiry', 'Value': 'true'}
    ]

    try:
        # Check if an AMI with the same name already exists
        existing_amis = ec2_client.describe_images(
            Filters=[
                {'Name': 'name', 'Values': [image_name]},
                {'Name': 'state', 'Values': ['available', 'pending']}
            ]
        )['Images']

        if existing_amis:
            print(f"AMI '{image_name}' already exists.")
            raise Exception(f"AMI already exists with ID: {existing_amis[0]['ImageId']}")

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
        raise e  # Raise the exception to capture and include it in the email


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

def send_email(subject, message, from_email, to_email, smtp_server, smtp_port, smtp_username, smtp_password):
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = ', '.join(to_email)
    msg['Subject'] = subject

    # Create the HTML message part
    html_message = MIMEText(message, 'html')
    msg.attach(html_message)

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(from_email, to_email, msg.as_string())
        server.quit()
        print("Email sent successfully.")
    except Exception as e:
        print("Failed to send email:", str(e))

def backup_and_delete_amis(instance_dict, profile_name, retention_days, email_settings):
    email_subject = "AMI Backup and Deletion Report"
    email_body = "<html><body>"
    overall_status = "Passed"  # Initialize overall status

    for region, instances in instance_dict.items():
        region_status = "Passed"  # Initialize region status
        email_body += f"<p>Region: {region}</p>"
        email_body += "<table border='1' cellspacing='0' cellpadding='5' style='border-collapse: collapse;'>"
        email_body += "<tr><th>Instance Name</th><th>Instance ID</th><th>Status</th><th>Exception Message</th></tr>"
        for instance_id in instances:
            try:
                session = boto3.Session(region_name=region, profile_name=profile_name)
                ec2_resource = session.resource('ec2')
                instance = ec2_resource.Instance(instance_id)
                instance_name = [tag['Value'] for tag in instance.tags if tag['Key'] == 'Name'][0]
                today_str = datetime.now().strftime('%Y-%m-%d')
                today_image_name = f"{instance_name}_{instance_id}_{today_str}"
                image_id = create_ami(instance_id, today_image_name, region, profile_name)

                status = ""
                exception_message = ""

                if image_id:
                    status = "<span style='color: green;'>Success</span>"
                    exception_message = f"AMI ID: {image_id}"
                    print(f"Created AMI {today_image_name} (ID: {image_id}) for instance {instance_id}")
                    delete_old_amis([instance_id], region, profile_name, retention_days)
                else:
                    status = "<span style='color: red;'>Failed</span>"
                    region_status = "Failed"  # Update region status to Failed
                    print(f"Failed to create AMI for instance {instance_id}")

                email_body += f"<tr><td>{instance_name}</td><td>{instance_id}</td><td>{status}</td><td>{exception_message}</td></tr>"
            except Exception as e:
                status = "<span style='color: red;'>Error</span>"
                region_status = "Failed"  # Update region status to Failed
                exception_message = f"<span style='color: red;'>{str(e)}</span>"
                error_message = f"Failed to process instance {instance_id}: {str(e)}"
                print(error_message)
                email_body += f"<tr><td>{instance_name}</td><td>{instance_id}</td><td>{status}</td><td>{exception_message}</td></tr>"

        email_body += "</table><br/>"

        # Update overall status based on the region status
        if region_status == "Failed":
            overall_status = "Failed"

    # Add overall status at the top with appropriate color
    overall_status_color = "red" if overall_status == "Failed" else "green"
    email_body = f"<p>Overall Status: <span style='color: {overall_status_color};'>{overall_status}</span></p>" + email_body
    email_body += "</body></html>"
    
    send_email(
        subject=email_subject,
        message=email_body,
        from_email=email_settings['from_email'],
        to_email=email_settings['to_email'],
        smtp_server=email_settings['smtp_server'],
        smtp_port=email_settings['smtp_port'],
        smtp_username=email_settings['smtp_username'],
        smtp_password=email_settings['smtp_password']
    )

# Specify your email settings
email_settings = {
    'from_email': '*************',
    'to_email': ['*********************'],
    'smtp_server': '*********',
    'smtp_port': ***,
    'smtp_username': '**********************',
    'smtp_password': '*********************************************'
}

# def backup_and_delete_amis(instance_dict, profile_name, retention_days):
#     for region, instances in instance_dict.items():
        

# Specify your instance IDs, regions, profile name, and retention period (in days) here
instance_dict = {
    'ap-south-1': ['************','i-0cighuhfhkvdhlkfhvd']
    # 'us-west-2' : ['i-58vjjkhlky789']
}

profile_name = 'Stage'
retention_days = 3

backup_and_delete_amis(instance_dict, profile_name, retention_days, email_settings)
