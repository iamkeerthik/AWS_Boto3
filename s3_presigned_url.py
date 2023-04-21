import logging
import boto3
import botocore
import pyperclip
from botocore.exceptions import ClientError


def create_presigned_urls(bucket_name, object_names, expiration=600):
    # Choose AWS CLI profile, If not mentioned, it would take default
    boto3.setup_default_session(profile_name='Stage')

    # Generate presigned URLs for the S3 objects
    s3_client = boto3.client('s3', region_name="ap-south-1", config=boto3.session.Config(signature_version='s3v4'))
    presigned_urls = []
    try:
        for object_name in object_names:
            response = s3_client.generate_presigned_url('get_object',
                                                        Params={'Bucket': bucket_name,
                                                                'Key': object_name},
                                                        ExpiresIn=expiration)
            presigned_urls.append((object_name, response))
            print(f"{object_name}:\n{response}\n")

        # Concatenate all the presigned URLs into a single string with newline separators
        urls_str = "\n".join([f"{name}:\n{url}\n" for name, url in presigned_urls])

        # Copy all the presigned URLs to the clipboard
        pyperclip.copy(urls_str)
        print(f"All presigned URLs copied to clipboard")

        return presigned_urls
    except Exception as e:
        print(e)
        logging.error(e)
        return "Error"


# Example usage
bucket_name = 'bucket-temp'
object_names = ['object_1.txt', 'object_2.txt']
expiration = 3600
create_presigned_urls(bucket_name, object_names, expiration)
