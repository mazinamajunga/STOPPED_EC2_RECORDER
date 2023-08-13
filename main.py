
from ec2_record import list_all_instances, generate_csv_report, upload_file_to_s3, cloudwatch_alarm, \
                       create_topic, subscribe_to_topic, publish_to_topic
from config import REPORT_NAME, AWS_REGION, BUCKET_NAME, OBJECT_NAME, ALARMNAME, NAMESPACE, METRICNAME, \
                   MY_PROTOCOL, MY_ENDPOINT, logger               
"""
from config import *  
This method will also work, but it is not recommended. It makes it harder to track the origin of variables. 
It's best to be selective about the variables you import from other modules and avoid using wildcards if possible.
"""                           


def main():
    # STORE THE DATA IN A VARIABLE
    instances = list_all_instances(region_name=AWS_REGION)                               
    # Confirming that the list has been store
    logger.info(f"our list is: {instances} has been store successfully")   
    # #######print(instances)#################
    # PASSING THE RETRIEVED DATA TO THE generated_csv_report()
    fr_generated = generate_csv_report(instances)
    print(fr_generated)
    # Checking if the report is successfully generated
    logger.info(f"the report {REPORT_NAME} has been generated successfully")           
    # Uploading the report to S3 bucket
    # uploading = upload_file_to_s3(REPORT_NAME, BUCKET_NAME, OBJECT_NAME)
    upload_file_to_s3(REPORT_NAME, BUCKET_NAME, OBJECT_NAME)
    # Confirming that the report has been uploaded to S3
    logger.info(f"the report {OBJECT_NAME} has been uploaded successfully")
    # Creating the CloudWatch alarm
    # alarm = cloudwatch_alarm(ALARMNAME, METRICNAME, NAMESPACE)
    cloudwatch_alarm(ALARMNAME, METRICNAME, NAMESPACE)  
    logger.info("create alarm %s to track metric %s in %s.", ALARMNAME, METRICNAME, NAMESPACE)
    # Creating the sns topic
    topic_name = 'sns_s3_upload_topic'
    topic = create_topic(topic_name)
    responses = []
    for protocol, endpoint in zip(MY_PROTOCOL, MY_ENDPOINT):                      # Iterating over the two lists MY_PROTOCOL and MY_ENDPOINT in parallel using the built-in zip() function.
        response = subscribe_to_topic(topic['TopicArn'], protocol, endpoint)      # On each iteration of the loop, the protocol variable is set to the next value 
        responses.append(response)                                                # in the MY_PROTOCOL list, and the endpoint variable is set to the next value in the MY_ENDPOINT list.
    my_messages = publish_to_topic(topic['TopicArn'], protocol, endpoint, "Hello from AWS", "Please check your AWS Account",
                     "Please check your AWS Account. This is an SMS message", "Please check your AWS Account to know more. This is an email message")
    print(my_messages)  
    
    
if __name__ == '__main__':   
    main()