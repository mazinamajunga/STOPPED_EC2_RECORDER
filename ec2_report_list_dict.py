# Importing the module needed for work.
import boto3
import logging
import csv
from botocore.exceptions import ClientError
import json

# Setting up the logger
logger = logging.getLogger(__name__)
# Setting up the threshold for this logger to "logging.DEBUG"
# Logging messages which are less severe than "logging.DEBUG" will be ignored.
logger.setLevel(logging.DEBUG)
# Formatting the logs records
FORMAT = logging.Formatter('%(filename)s - %(asctime)s - %(levelname)s - %(message)s')
# Create a FileHandler that writes to a file named 'ec2_manual_record.log'
fh = logging.FileHandler('ec2_manual_record.log')
# Setting up FORMAT for a logging handler object called fh.
fh.setFormatter(FORMAT)
# Add the FileHandler to the logger
logger.addHandler(fh)


REPORT_NAME = 'ec2_report_list_dict.csv'
AWS_REGION = 'us-east-1'
BUCKET_NAME = 'mynewestfirstbucket'
OBJECT_NAME = 'instance_report.csv'         # THE ACTUAL NAME OF THE FILE ONCE IN THE S3 BUCKET
ALARMNAME = 's3_upload_alarm'
NAMESPACE = 'AWS/S3'
METRICNAME = 'NumberOfObjects'
MY_PROTOCOL = ["email", "sms"]
MY_ENDPOINT = ["patrickstephane@gmail.com", "+15105751778"] 
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

def format_tags(tags_dict):
    formatted_tags = []
    for key, value in tags_dict.items():
        formatted_tags.append(f"{key}: {value!r}")  # !r adds quotes around the value
    return ", ".join(formatted_tags)

def format_instance_data(instance_data):
    tags_str = format_tags(instance_data['tags'])
    formatted_str = (
        f"Image ID: {instance_data['image_id']}\n"
        f"Instance ID: {instance_data['instance_id']}\n"
        f"Instance Type: {instance_data['instance_type']}\n"
        f"Private DNS Name: {instance_data['private_dns_name']}\n"
        f"Private IP Address: {instance_data['private_ip_address']}\n"
        f"Public DNS Name: {instance_data['public_dns_name']}\n"
        f"Public IP Address: {instance_data['public_ip_address']}\n"
        f"Subnet ID: {instance_data['subnet_id']}\n"
        f"VPC ID: {instance_data['vpc_id']}\n"
        f"Placement: {instance_data['placement']}\n"
        f"Tags: {tags_str}\n"
    )
    return formatted_str

# def format_instance_data(instance_data):
#     tags_str = ", ".join([f"{key}: {value}" for key, value in instance_data['tags'].items()])  
#     formatted_str = (
#         f"Image ID: {instance_data['image_id']}\n"
#         f"Instance ID: {instance_data['instance_id']}\n"
#         f"Instance Type: {instance_data['instance_type']}\n"
#         f"Private DNS Name: {instance_data['private_dns_name']}\n"
#         f"Private IP Address: {instance_data['private_ip_address']}\n"
#         f"Public DNS Name: {instance_data['public_dns_name']}\n"
#         f"Public IP Address: {instance_data['public_ip_address']}\n"
#         f"Subnet ID: {instance_data['subnet_id']}\n"
#         f"VPC ID: {instance_data['vpc_id']}\n"
#         f"Placement: {instance_data['placement']}\n"
#         f"Tags: {tags_str}\n"
#     )
#     return formatted_str

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
    
def publish_to_topic(topic_arn, subject, default_message, sms_message, email_message): 
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
        
if __name__ == '__main__':     # ENTRYPOINT OF THE CODE
    # STORE THE DATA IN A VARIABLE
    instances = list_all_instances("us-east-1")                                # (region_name=AWS_REGION)    
    for instance_data in instances:
        formatted_instance_data = format_instance_data(instance_data)
        print(formatted_instance_data)                  
        
        
                 
    # # Confirming that the list has been store
    logger.info(f"our list is: {formatted_instance_data} has been store successfully")   
    # # PASSING THE RETRIEVED DATA TO THE generated_csv_report()
    # fr_generated = generate_csv_report(instances)
    # print(fr_generated)
    # # Checking if the report is successfully generated
    # logger.info(f"the report {REPORT_NAME} has been generated successfully")           
    # # Uploading the report to S3 bucket
    # uploading = upload_file_to_s3(REPORT_NAME, BUCKET_NAME, OBJECT_NAME)
    # # Confirming that the report has been uploaded to S3
    # logger.info(f"the report {OBJECT_NAME} has been uploaded successfully")
    # # Creating the CloudWatch alarm
    # alarm = cloudwatch_alarm(ALARMNAME, METRICNAME, NAMESPACE) 
    # logger.info("create alarm %s to track metric %s in %s.", ALARMNAME, METRICNAME, NAMESPACE)
    # # Creating the sns topic
    # topic_name = 'sns_s3_upload_topic'
    # topic = create_topic(topic_name)
    # responses = []
    # for protocol, endpoint in zip(MY_PROTOCOL, MY_ENDPOINT):                      # Iterating over the two lists MY_PROTOCOL and MY_ENDPOINT in parallel using the built-in zip() function.
    #     response = subscribe_to_topic(topic['TopicArn'], protocol, endpoint)      # On each iteration of the loop, the protocol variable is set to the next value 
    #     responses.append(response)                                                # in the MY_PROTOCOL list, and the endpoint variable is set to the next value in the MY_ENDPOINT list.
    # my_messages = publish_to_topic(topic['TopicArn'], "Hello from AWS", "Please check your AWS Account",
    #                  "Please check your AWS Account. This is an SMS message", "Please check your AWS Account to know more. This is an email message")
    # print(my_messages)  
  

        
############################################
#############################################
###
###  THIS CODE HAS BEEN REFACTOR IN TROUBLESHOOT\EXPERIMENT
###
#################################################################   
###############################################################





