import boto3
from datetime import datetime, timedelta, timezone

def main():
    session = boto3.Session(profile_name='PS', region_name='us-east-2')
    ses_client = session.client('ses')
    iam_client = session.client('iam')
    sender_email = 'sendermail@gmail.com'

    response = iam_client.list_users()
    users = response['Users']

    rotated_users = []

    for user in users:
        username = user['UserName']
        email_address = get_user_email(iam_client, username)

        if not email_address:
            email_address = 'defaultmail@gmail.com'

        access_keys = iam_client.list_access_keys(UserName=username)['AccessKeyMetadata']

        for access_key in access_keys:
            access_key_id = access_key['AccessKeyId']
            access_key_create_date = access_key['CreateDate']

            access_key_create_date = access_key_create_date.replace(tzinfo=timezone.utc)
            key_age = (datetime.now(timezone.utc) - access_key_create_date).days

            if key_age > 90:
                # Delete the old access key
                iam_client.delete_access_key(UserName=username, AccessKeyId=access_key_id)

                # Create a new access key
                new_access_key_response = iam_client.create_access_key(UserName=username)
                new_access_key_id = new_access_key_response['AccessKey']['AccessKeyId']
                new_secret_access_key = new_access_key_response['AccessKey']['SecretAccessKey']

                # Add the username to the rotated_users list
                rotated_users.append(username)

                # Send email with the new access key details to the user's email address
                send_email(ses_client, sender_email, email_address, new_access_key_id, new_secret_access_key)

    send_rotation_summary_email(ses_client, sender_email, rotated_users, len(users))

    print('Access key rotation completed successfully.')

def get_user_email(iam_client, username):
    response = iam_client.list_user_tags(UserName=username)
    tags = response['Tags']

    for tag in tags:
        if tag['Key'] == 'email':
            return tag['Value']

    return None

def send_email(ses_client, sender_email, recipient_email, access_key_id, secret_access_key):
    subject = f"New Access Key for User: {recipient_email}"
    message = f"Hello {recipient_email},\n\nA new access key has been created for your AWS IAM user.\n\n" \
              f"Access Key ID: {access_key_id}\n" \
              f"Secret Access Key: {secret_access_key}\n\n" \
              f"Please make sure to securely store and update your credentials.\n\n"

    response = ses_client.send_email(
        Source=sender_email,
        Destination={'ToAddresses': [recipient_email]},
        Message={
            'Subject': {'Data': subject},
            'Body': {'Text': {'Data': message}}
        }
    )

    return response

def send_rotation_summary_email(ses_client, sender_email, rotated_users, total_users):
    subject = "IAM Access Key Rotation Summary"
    message = ""

    if rotated_users:
        message = f"The following IAM users' access keys have been rotated:\n\n"
        for username in rotated_users:
            message += f"- {username}\n"
    else:
        message = "No IAM user access key rotation needed for any user."

    message += f"\nTotal Users: {total_users}"

    response = ses_client.send_email(
        Source=sender_email,
        Destination={'ToAddresses': [sender_email]},
        Message={
            'Subject': {'Data': subject},
            'Body': {'Text': {'Data': message}}
        }
    )

    return response

if __name__ == '__main__':
    main()
