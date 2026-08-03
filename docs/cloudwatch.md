# CloudWatch Monitoring

DocuPulse uses Amazon CloudWatch for monitoring, logging, metrics, and alerting.

---

## Metrics

The Lambda function publishes a custom metric.

Namespace:

```
DocuPulse
```

Metric:

```
DocumentsProcessed
```

Unit:

```
Count
```

---

## Logs

Each Lambda execution produces structured JSON logs.

Example:

```json
{
  "timestamp": "2026-07-19T16:58:21",
  "level": "INFO",
  "service": "DocuPulse",
  "step": "Bedrock",
  "status": "SUCCESS",
  "message": "Invoice extracted successfully."
}
```

---

## CloudWatch Dashboard

The dashboard displays:

- Documents Processed
- Lambda Invocations
- Lambda Errors
- Lambda Duration

---

## CloudWatch Alarm

Alarm Name:

```
DocuPulseLambdaErrors
```

Condition:

```
Errors > 0
```

Action:

```
Amazon SNS Notification
```

---

## SNS Alert

Whenever a Lambda error occurs:

CloudWatch Alarm

↓

SNS Topic

↓

Email Notification

---

## Benefits

- Real-time monitoring
- Operational visibility
- Error notifications
- Historical metrics
- Centralized logging