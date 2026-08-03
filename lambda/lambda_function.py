import json
import os
import boto3
from botocore.exceptions import ClientError
from pypdf import PdfReader
from io import BytesIO
from datetime import datetime
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
secrets = boto3.client("secretsmanager")

def get_secret(secret_name):
    response = secrets.get_secret_value(
        SecretId=secret_name
    )
    return json.loads(response["SecretString"])

config = get_secret("DocuPulse/Config")
QUEUE_URL = config["QUEUE_URL"]
SNS_TOPIC_ARN = config["SNS_TOPIC_ARN"]
MODEL_ID = config["MODEL_ID"]

def log_event(level, request_id, step, status, message, **kwargs):
    log = {
        "timestamp": datetime.utcnow().isoformat(),
        "level": level,
        "service": "DocuPulse",
        "request_id": request_id,
        "step": step,
        "status": status,
        "message": message
    }

    log.update(kwargs)
    logger.info(json.dumps(log))
sns = boto3.client("sns")
sqs = boto3.client("sqs")

def send_to_queue(document: dict):
    if not QUEUE_URL:
        print("QUEUE_URL not configured. Skipping SQS.")
        return
    try:
        sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps(document)
        )
        logger.info("Document sent to SQS.")
    except ClientError as e:
        print("SQS Error")
        raise
DLQ_URL = os.environ["DLQ_URL"]

def send_to_dlq(document, error):

    sqs.send_message(
        QueueUrl=DLQ_URL,
        MessageBody=json.dumps({
            "document": document,
            "error": str(error)
        })
    )
    logger.info("Document sent to DLQ.")

def send_notification(document):

    try:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject="DocuPulse Invoice Processed",
            Message=json.dumps(document, indent=4)
        )
        logger.info("SNS notification sent.")
    except ClientError:
        print("SNS Error")
        raise
ssm = boto3.client("ssm")

def get_parameter(name):
    response = ssm.get_parameter(Name=name)
    return response["Parameter"]["Value"]

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".txt"
}

def validate_file_extension(file_name: str):
    extension = os.path.splitext(file_name)[1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {extension}"
        )
    logger.info("File extension validated.")
MAX_FILE_SIZE = 10 * 1024 * 1024

def validate_file_size(file_bytes):
    if len(file_bytes) > MAX_FILE_SIZE:
        raise ValueError(
            "Document exceeds 10 MB limit."
        )
    print("File size validated.")

def validate_document(file_bytes):
    if len(file_bytes) == 0:
        raise ValueError(
            "Document is empty."
        )
    print("Document is not empty.")
bedrock = boto3.client("bedrock-runtime")

def validate_document_text(document_text: str):
    if not document_text.strip():
        raise ValueError(
            "No readable text found."
        )
    print("Document text validated.")

TABLE_NAME = get_parameter("/DocuPulse/TABLE_NAME")
dynamodb = boto3.resource("dynamodb")

def save_to_dynamodb(document, request_id, bucket_name, file_name):
    table = dynamodb.Table(TABLE_NAME)
    document["bucket"] = bucket_name
    document["key"] = file_name
    document["processed_at"] = datetime.utcnow().isoformat()
    document["request_id"] = request_id
    try:

        table.put_item(
            Item=document
        )
        log_event(
            "INFO",
            request_id,
            "DynamoDB",
            "SUCCESS",
            "Document stored.",
            bucket=bucket_name,
            key=file_name
        )
    except ClientError:
        print("DynamoDB Error")
        raise

def extract_text_from_document(file_bytes):

    try:
        pdf = PdfReader(BytesIO(file_bytes))
        text = ""
        for page in pdf.pages:
            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"
        print("PDF text extracted successfully.")
        return text
    except Exception as e:
        print("PDF Extraction Error")
        raise

def validate_json(response_text: str):

    try:
        cleaned = response_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned.replace("```json", "", 1)
        if cleaned.startswith("```"):
            cleaned = cleaned.replace("```", "", 1)
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON returned from AI: {e}")

def invoke_bedrock(prompt: str):
    """
    Invoke Amazon Bedrock Converse API
    and return extracted invoice JSON.
    """

    try:
        print("Connecting to Amazon Bedrock...")
        response = bedrock.converse(
            modelId=MODEL_ID,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            inferenceConfig={
                "temperature": 0,
                "maxTokens": 512,
                "topP": 0.9
            }
        )
        return response["output"]["message"]["content"][0]["text"]
    except ClientError as e:
        print(f"Bedrock Error: {e}")
        raise

def build_prompt(document_text: str):
    prompt = f"""
You are an invoice extraction AI.
Extract the following fields from the document.
Return ONLY valid JSON.
{{
    "invoice_number":"",
    "vendor_name":"",
    "invoice_date":"",
    "currency":"",
    "subtotal":"",
    "tax":"",
    "total_amount":""
}}
Document:
{document_text}
"""
    return prompt
cloudwatch = boto3.client("cloudwatch")

def publish_metric():

    cloudwatch.put_metric_data(
        Namespace="DocuPulse",
        MetricData=[
            {
                "MetricName": "DocumentsProcessed",
                "Value": 1,
                "Unit": "Count"
            }
        ]
    )
    logger.info("Custom metric published.")

def lambda_handler(event, context):
    request_id = context.aws_request_id
    bucket_name = "unknown"
    file_name = "unknown"
    try:
        if "Records" in event:
            record = event["Records"][0]
            bucket_name = record["s3"]["bucket"]["name"]
            file_name = record["s3"]["object"]["key"]
        else:
            bucket_name = DEFAULT_BUCKET
            file_name = "input/invoice.pdf"
        print(f"Bucket: {bucket_name}")
        print(f"Key: {file_name}")
        s3 = boto3.client("s3")
        response = s3.get_object(
            Bucket=bucket_name,
            Key=file_name
        )

        file_bytes = response["Body"].read()
        validate_file_extension(file_name)
        validate_file_size(file_bytes)
        validate_document(file_bytes)
        document_text = extract_text_from_document(file_bytes)
        validate_document_text(document_text)
        prompt = build_prompt(document_text)
        print(f"Using Model: {MODEL_ID}")
    
        ai_response = invoke_bedrock(prompt)
        log_event(
            "INFO",
            request_id,
            "Bedrock",
            "SUCCESS",
            "Invoice extracted successfully.",
            bucket=bucket_name,
            key=file_name
        )
        print(ai_response)

        parsed_json = validate_json(ai_response)
        save_to_dynamodb(
            parsed_json,
            request_id,
            bucket_name,
            file_name
        ) 
        
        publish_metric()
        send_to_queue(parsed_json)
        send_notification(parsed_json)
        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "status": "SUCCESS",
                    "response": ai_response
                }
            )
        }
    except ClientError as e:
        logger.exception("AWS Client Error")
        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "status": "FAILED",
                    "error": str(e)
                }
            )
        }
    except Exception as e:
        print("=" * 60)
        print("PROCESSING FAILED")
        print("=" * 60)
        log_event(
            "ERROR",
            request_id,
            "Lambda",
            "FAILED",
            str(e)
        )
        print(f"Error: {str(e)}")
        send_to_dlq(
            {
                "bucket": bucket_name,
                "key": file_name
            },
            e
        )
        raise  