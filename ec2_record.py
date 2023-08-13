
# Importing the module needed for work.
import boto3
import csv
from botocore.exceptions import ClientError
import json
from config import REPORT_NAME, AWS_REGION, BUCKET_NAME, OBJECT_NAME, ALARMNAME, NAMESPACE, METRICNAME, logger

"""
from config import *  
This method will also work, but it is not recommended. It makes it harder to track the origin of variables. 
It's best to be selective about the variables you import from other modules and avoid using wildcards if possible.
""" 
SNS_CLIENT = boto3.client('sns')

def list_all_instances(region_name=AWS_REGION):
    """
    Retrieves a list of stopped instances in the specified REGION and returns a list of dictionaries
    containing information about each instance.

    Args:
        AWS_REGION (str): The name of the AWS REGION to retrieve instances from.

    Returns:
        list: A list of dictionaries, where each dictionary contains information about a single instance. Each
            dictionary has the following keys:
            - image_id (str): The ID of the AMI used to launch the instance.
            - instance_id (str): The ID of the instance.
            - instance_type (str): The instance type (e.g. "t2.micro").
            - private_dns_name (str): The private DNS hostname of the instance, if it has one.
            - private_ip_address (str): The private IP address of the instance.
            - public_dns_name (str): The public DNS hostname of the instance, if it has one.
            - public_ip_address (str): The public IP address of the instance.
            - subnet_id (str): The ID of the subnet the instance is running in.
            - vpc_id (str): The ID of the VPC the instance is running in.
            - placement (str): The availability zone the instance is running in.
            - tags (dict): A dictionary of the instance's tags, where the keys are the tag names and the values
                are the tag values.
                
    Raises:
        botocore.exceptions.BotoCoreError: If there was an error communicating with the EC2 service.
    """
    # Opening the connection to AWS EC2 service in my choosen REGION.
    ec2 = boto3.client('ec2', region_name=AWS_REGION)
    instances = []    # THIS EMPTY LIST WILL LATER RECEIVED THE LIST OF DICTIONNARIES OF DATA.
    try:
        # Retrieve all instances in the REGION with status "stopped"
        response = ec2.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['stopped']}])   
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                # Create a dictionary of instance data
                instance_data = {
                    "image_id": instance['ImageId'],
                    "instance_id": instance['InstanceId'],
                    "instance_type": instance['InstanceType'],
                    "private_dns_name": instance.get('PrivateDnsName', ''),
                    "private_ip_address": instance.get('PrivateIpAddress', ''),
                    "public_dns_name": instance.get('PublicDnsName', ''),
                    "public_ip_address": instance.get('PublicIpAddress', ''),
                    "subnet_id": instance['SubnetId'],
                    "vpc_id": instance['VpcId'],
                    "placement": instance['Placement']['AvailabilityZone'],
                    "tags": {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])},
                }
                instances.append(instance_data)                
    except Exception as e:
        logger.exception(f"Error retrieving instances in REGION {region_name}: {e}")
       
    return instances
    
def generate_csv_report(data_retrieved): 
    """Generates a CSV report from the given data.

    Args:
        data_retieved (list): A list of dictionaries containing data to include in the report. Each dictionary
        should have keys that correspond to the fieldnames of the CSV report.
            
    Returns:
        bool: True if report generated successfully, False otherwise.
        
    Raises:
        TypeError: If data_retrieved is not a list of dictionaries.
    """    
    
    # Data validation
    # checking whether the data_retrieved argument is a list of dictionaries.
    # first check if data_retrieved is a list 'isinstance(data_retrieved, list)'
    # then check if element of the data_retrieved is a dictionary isinstance(d, dict) for d in data_retrieved
    # After, using the all() will allow to check for every single element in data_retrived.
    # Finally, using the if, not, or, not, to create a negative condition that will raise the TypeError.
    # in other word, "if isinstance(data_retrieved, list) and all(isinstance(d, dict) for d in data_retrieved)"
    # is the "True comdition" for our used case.
    
    if not isinstance(data_retrieved, list) or not all(isinstance(d, dict) for d in data_retrieved):     
        # This type of input validation is important to ensure that the function is called    
        # with the correct arguments, and can help to prevent errors caused by unexpected input types.                                               
        raise TypeError("data_retrieved must be a list of dictionaries")                                 
    try:
        with open(REPORT_NAME, 'w', newline= '') as file: 
            fieldnames = ['key', 'value']
            write = csv.DictWriter(file, fieldnames=fieldnames)
            # Write the header row
            write.writeheader()
            # Write the rows with key and value separated
            for element in data_retrieved:
                for key, value in element.items():
                    write.writerow({'key': key, 'value': value})
    except TypeError as error:
        logger.error(f"If data_retrieved is not a list of dictionaries: {error}")
        return False
    return True

def upload_file_to_s3(report = REPORT_NAME, bucket = BUCKET_NAME, object = OBJECT_NAME):
    """
    Upload a file to the specified S3 bucket with the given object name.

    Args:
        file_name (str): The name of the file to upload.
        bucket (str): The name of the S3 bucket to upload the file to.
        object_name (str): The object name to give to the uploaded file.

    Returns:
        bool: True if the upload was successful, False otherwise.
    """
    
    # Upload the file to S3 bucket
    client_s3 = boto3.client('s3')
    try:
        client_s3.upload_file(report, bucket, object)
    except ClientError as error:
        logger.error(f"here is the error message: {error}")
        return False
    return True

def cloudwatch_alarm(alarmname, metricname, namespace): 
    """create a cloudwatch alarm

    Args:
        alarmname (str): name of the alarm. Defaults to ALARMNAME.
        metricname (str): name of the metric being measured. Defaults to METRICNAME.
        namespace (str): name of the name space. Defaults to NAMESPACE.

    Returns:
        True if the creation was successful, False otherwise.
    """    
    # Initializing cloudwatch client
    cloudwatch = boto3.client('cloudwatch')
    # Create alarm
    try:
        alarm = cloudwatch.put_metric_alarm(
            AlarmName=ALARMNAME,                              
            MetricName=METRICNAME,
            Namespace=NAMESPACE,
            Statistic='Sum',
            Period=86400,                 # 1 day in seconds      
            EvaluationPeriods=1,
            ComparisonOperator='GreaterThanOrEqualToThreshold',                               
            Threshold=2,
            AlarmDescription='Alarm triggered when object uploaded to s3 bucket',            
            AlarmActions=[
                'arn:aws:sns:us-east-1:390683858216:sns_s3_upload',   # used to specify the ARN of the Amazon SNS topics to which you want to send notifications when the alarm state changes.
            ],
            ActionsEnabled=True,
            DatapointsToAlarm=1,
            TreatMissingData='notBreaching',                # set to 'notBreaching' to only trigger alarm if metric data exists
            
        )
    except ClientError as error:
            logger.error(f"Because of {error}, %s couldn't be created and added to %s so it can track %s.", alarmname, namespace, metricname)
            return False
    return alarm

def create_topic(name):    
    """This function create a topic that will be used for notifying the users.

    Args:
        name (str): Name of the topic to create.
    Returns:
        str: The arn of the topic.
    """    
    try:
        topic = SNS_CLIENT.create_topic(Name=name)
        logger.info("Created topic %s with ARN %s.", name, topic['TopicArn'])
    except ClientError:
        logger.exception("Couldn't create topic %s.", name)
        raise
    else:
        return topic
    
def subscribe_to_topic(my_topic, protocol, endpoint):
    """this function allow subscription to a topic

    Args:
        topic_arn (str): the ARN of the SNS topic to publish to.
        protocol (str): the protocol to use (either "email" or "sms").
        endpoint (str): the destination address for the message (e.g. an email address or phone number).

    Returns:
        str: the arn of the subscription.
    """   
    try:
        email_subscription = SNS_CLIENT.subscribe(
        TopicArn=my_topic, Protocol=protocol, Endpoint=endpoint, ReturnSubscriptionArn=True)   # True == the response includes the ARN in all cases, even if the subscription is not yet confirmed
        logger.info("Subscribed %s %s to topic %s.", protocol, endpoint, my_topic)
    except ClientError:
        logger.exception(
            "Couldn't subscribe %s %s to topic %s.", protocol, endpoint, my_topic)
        raise
    else:
        return email_subscription
    
def publish_to_topic(topic_arn, protocol, endpoint, subject, default_message, sms_message, email_message): 
    """Publishes a multi-format message to a topic. A multi-format message takes
       different forms based on the protocol of the subscriber.

    Args:
        topic_arn (str): The topic to publish to.
        subject (str): The subject of the message.
        default_message (str): The default version of the message. This version is
                                  sent to subscribers that have protocols that are not
                                  otherwise specified in the structured message.
        sms_message (str): The version of the message sent to SMS subscribers.
        email_message (str): The version of the message sent to email subscribers.
    Returns:
        str: The ID of the message.
    """      
    message = {
        'default': default_message,
        'sms': sms_message,
        'email': email_message
    }
    # logging informations before message is published.
    logger.info(f"Publishing message to SNS topic {topic_arn} with protocol {protocol} and endpoint {endpoint}")
    # Calling the "publish method" of the "sns_client" object to pass some parameters to it.
    try:
        answer = SNS_CLIENT.publish(
            TopicArn=topic_arn, 
            Message=json.dumps(message), 
            Subject=subject, 
            MessageStructure='json'
        )
        # Logging the message ID after it has been published.
        logger.info(f'Successfully published message with ID {answer["MessageId"]}')   
    except ClientError as e:
        logger.error(f'Error publishing message: {e.answer["Error"]["Message"]}')
    message_id = answer['MessageId'] 
    return message_id      
        
    
  

        
        






      
   






