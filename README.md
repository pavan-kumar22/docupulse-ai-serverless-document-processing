# DocuPulse – AI-Powered Serverless Document Processing Pipeline

DocuPulse is an event-driven, serverless document processing system built on AWS.

When a PDF invoice is uploaded to Amazon S3, an AWS Lambda function automatically extracts invoice data using Amazon Bedrock (Nova Lite Converse API), validates the response, stores structured data in DynamoDB, publishes CloudWatch metrics, sends notifications through Amazon SNS, and forwards the processed document to Amazon SQS.

---

## Architecture

```
Amazon S3
     │
     ▼
AWS Lambda
     │
     ├── Validate Document
     ├── Extract PDF Text
     ├── Amazon Bedrock (Nova Lite)
     ├── Validate JSON
     ├── DynamoDB
     ├── CloudWatch Metrics
     ├── SNS Notification
     └── SQS Queue
```

---

## AWS Services Used

- Amazon S3
- AWS Lambda
- Amazon Bedrock (Converse API)
- Amazon DynamoDB
- Amazon SNS
- Amazon SQS
- Amazon CloudWatch
- AWS Systems Manager Parameter Store
- AWS Secrets Manager
- AWS IAM
- AWS CloudTrail

---

## Features

- Fully serverless architecture
- Automatic PDF processing
- AI-powered invoice extraction
- JSON validation
- DynamoDB storage
- CloudWatch custom metrics
- CloudWatch dashboard
- SNS email notifications
- SQS integration
- Dead Letter Queue (DLQ)
- Structured JSON logging
- Secrets stored securely using AWS Secrets Manager
- Configuration managed through AWS Systems Manager Parameter Store

---

## Project Structure

```
DOCUPULSE/
│
├── architecture/
├── docs/
├── lambda/
│   └── lambda_function.py
├── sample-documents/
├── tests/
├── README.md
├── requirements.txt
└── .gitignore
```

---

## Processing Flow

1. Upload PDF invoice to Amazon S3.
2. Lambda is triggered automatically.
3. PDF text is extracted.
4. Amazon Bedrock extracts invoice fields.
5. JSON response is validated.
6. Data is stored in DynamoDB.
7. CloudWatch custom metrics are published.
8. Notification is sent using SNS.
9. Processed document metadata is sent to SQS.
10. Errors are redirected to the Dead Letter Queue.

---

## Sample Extracted JSON

```json
{
  "invoice_number": "INV-1001",
  "vendor_name": "ABC Pvt Ltd",
  "invoice_date": "2026-07-20",
  "currency": "INR",
  "subtotal": "10000",
  "tax": "1800",
  "total_amount": "11800"
}
```

---

## Security

- IAM Least Privilege
- Secrets Manager
- Parameter Store
- CloudTrail Auditing
- CloudWatch Monitoring
- Dead Letter Queue for failed processing

---

## Future Improvements

- OCR using Amazon Textract
- Multi-page invoice support
- Invoice confidence score
- Human approval workflow
- Step Functions orchestration
- EventBridge Scheduler
- API Gateway integration
- Cost optimization dashboard

---

## Author

**S Pavan Kumar**

Computer Science Engineering Student

Cloud • DevOps • Site Reliability Engineering • AWS • AI