# Test Events

This directory contains sample Lambda events used for testing the DocuPulse pipeline.

## test_event_s3.json

Simulates an Amazon S3 ObjectCreated event that triggers the Lambda function.

## test_event_local.json

Simple event used to test the Lambda locally without an S3 trigger.

## Running Locally

```bash
sam build
sam local invoke DocuPulseFunction -e tests/test_event_s3.json