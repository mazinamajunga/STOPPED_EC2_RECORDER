
import logging 

REPORT_NAME = 'ec2_report_list_dict.csv'
AWS_REGION = 'us-east-1'
BUCKET_NAME = 'mynewestfirstbucket'
OBJECT_NAME = 'instance_report.csv'
ALARMNAME = 's3_upload_alarm'
NAMESPACE = 'AWS/S3'
METRICNAME = 'NumberOfObjects'
MY_PROTOCOL = ["email", "sms"]
MY_ENDPOINT = ["patrickstephane@gmail.com", "+15105751778"]


# Get the logger with the name of the current module (__name__)
logger = logging.getLogger(__name__)

# Setting up the threshold for this logger to "logging.DEBUG"
# Logging messages which are less severe than "logging.DEBUG" will be ignored.
logger.setLevel(logging.DEBUG)

# Formatting the log records
FORMAT = logging.Formatter('%(filename)s - %(asctime)s - %(levelname)s - %(message)s')

# Create a FileHandler that writes to a file named 'ec2_manual_record.log'
file_handler = logging.FileHandler('ec2_manual_record.log')
file_handler.setFormatter(FORMAT)

# Add the FileHandler to the logger
logger.addHandler(file_handler)