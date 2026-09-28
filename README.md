# FinSightX

## Distributed Financial Intelligence, Risk & Fraud Detection Platform

FinSightX is an end-to-end financial intelligence platform demonstrating **microservices, distributed systems, event-driven architecture, real-time fraud detection, machine learning, MLOps, data engineering, data warehousing, business intelligence, security, monitoring, Docker and Kubernetes-ready infrastructure**.

The platform is designed as a local-first system, allowing the complete architecture to run without depending on paid cloud services.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Application Services](#application-services)
- [Transaction Flow](#transaction-flow)
- [Fraud Detection](#fraud-detection)
- [Machine Learning](#machine-learning)
- [MLOps and MLflow](#mlops-and-mlflow)
- [Kafka Event Architecture](#kafka-event-architecture)
- [Data Lake and Spark](#data-lake-and-spark)
- [Data Warehouse](#data-warehouse)
- [Power BI](#power-bi)
- [Security and Reliability](#security-and-reliability)
- [Monitoring](#monitoring)
- [Docker Deployment](#docker-deployment)
- [Kubernetes and Infrastructure](#kubernetes-and-infrastructure)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Local Setup](#local-setup)
- [Service URLs](#service-urls)
- [Verified End-to-End Flow](#verified-end-to-end-flow)
- [Engineering Highlights](#engineering-highlights)
- [Future Enhancements](#future-enhancements)
- [Author](#author)

---

# Overview

FinSightX separates financial transaction processing into independently deployable services.

The high-level flow is:

```text
React Frontend
      |
      v
API Gateway
      |
      +--------------------+
      |                    |
      v                    v
Customer Service     Transaction Service
                           |
                           v
                         Kafka
                           |
                           v
                   Fraud Detection
                     |          |
                     v          v
                   Redis     ML Service
                  Velocity       |
                     |       Random Forest
                     +----------+
                           |
                           v
                       PostgreSQL
                           |
                           v
                    fraud.assessed
```

The data engineering path runs in parallel:

```text
Kafka
  |
  v
Spark Structured Streaming
  |
  +----> MinIO Raw Data
  |
  +----> MinIO Processed Data
                  |
                  v
             Warehouse ETL
                  |
                  v
          PostgreSQL Analytics
                  |
                  v
               Power BI
```

---

# Key Features

## 1. Microservices

Current services include:

- API Gateway
- Auth Service
- Customer Service
- Transaction Service
- Fraud Detection Service
- Notification Service
- Audit Service
- Analytics Service
- ML Service

Each service has a focused responsibility and communicates with other components through APIs or events.

## 2. Event-Driven Architecture

Apache Kafka is the event backbone.

Important topics include:

```text
transaction.created
fraud.assessed
transaction.created.DLQ
```

This decouples transaction creation from downstream fraud processing and analytics.

## 3. Real-Time Fraud Detection

Fraud assessment combines:

- Transaction amount
- Merchant category
- Transaction frequency
- Recent transaction amount
- Device information
- Location information
- Transaction status
- Rule-based scoring
- Machine-learning prediction

## 4. Redis Velocity Detection

Redis maintains short-window customer transaction statistics such as:

```text
Transaction count
Cumulative transaction amount
```

This allows the fraud service to identify unusually frequent or high-value transaction activity.

## 5. Dedicated ML Inference Service

The trained Random Forest model is deployed as its own FastAPI service.

Endpoints:

```text
GET  /health
GET  /ready
POST /api/v1/predict
```

The service returns:

```text
prediction
fraud_probability
legitimate_probability
risk_level
model_name
model_version
model_threshold
```

## 6. Spark Streaming and Data Lake

Spark Structured Streaming consumes Kafka events and writes:

```text
raw/
processed/
checkpoints/
```

to MinIO using Parquet.

## 7. Analytics Warehouse

Processed data is loaded into PostgreSQL using a dimensional model:

```text
dim_date
dim_customer
dim_merchant
dim_device
dim_location
fact_transactions
```

## 8. Power BI

Power BI connects to the PostgreSQL analytics layer for financial and fraud-risk reporting.

Current measures include:

- Total Transactions
- Total Amount
- Average Transaction Amount
- High Risk Transactions
- Assessed Transactions
- Unassessed Transactions
- High Risk Amount

---

# Architecture

```text
                         +----------------------+
                         |    React Frontend    |
                         |        :5173         |
                         +----------+-----------+
                                    |
                                    v
                         +----------------------+
                         |     API Gateway      |
                         |        :8002         |
                         +----------+-----------+
                                    |
              +---------------------+---------------------+
              |                     |                     |
              v                     v                     v
       +-------------+       +-------------+       +-------------+
       | Auth        |       | Customer    |       | Transaction |
       | Service     |       | Service     |       | Service     |
       | :8001       |       | :8009       |       | :8010       |
       +-------------+       +-------------+       +------+------+
                                                        |
                                                        v
                                                 +-------------+
                                                 |    Kafka    |
                                                 |   :29092    |
                                                 +------+------+
                                                        |
                           +----------------------------+----------------+
                           |                            |                |
                           v                            v                v
                    +-------------+             +-------------+    Other Consumers
                    | Fraud       |             | Spark       |
                    | Service     |             | Streaming   |
                    | :8004       |             +------+------+ 
                    +------+------+                    |
                           |                           v
              +------------+-----------+        +-------------+
              |                        |        |    MinIO    |
              v                        v        |   :9000     |
           +------+              +-----------+  +------+------+ 
           |Redis |              | ML Service|         |
           |:6380 |              |   :8008   |         v
           +------+              +-----+-----+  +-------------+
                                        |        | Warehouse   |
                                        v        | ETL         |
                                  Random Forest  +------+------+
                                                       |
                                                       v
                                                +-------------+
                                                | PostgreSQL  |
                                                |   :5434     |
                                                +------+------+
                                                       |
                                                       v
                                                +-------------+
                                                | Analytics   |
                                                |   :8007     |
                                                +------+------+
                                                       |
                                                       v
                                                  +----------+
                                                  | Power BI |
                                                  +----------+

Monitoring:
Services -> Prometheus -> Grafana
```

---

# Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React |
| APIs | FastAPI, REST |
| Language | Python |
| Authentication | JWT |
| Event Streaming | Apache Kafka |
| Cache / Velocity | Redis |
| Database | PostgreSQL 18 |
| Vector Support | pgvector |
| Streaming | Apache Spark Structured Streaming |
| Data Lake | MinIO |
| Data Format | Parquet |
| ML | Scikit-learn |
| Model | Random Forest |
| Data Processing | Pandas, NumPy, PyArrow |
| Model Serialization | Joblib |
| MLOps | MLflow |
| BI | Power BI |
| Containers | Docker, Docker Compose |
| Kubernetes | Kubernetes, kind |
| Package Management | Helm |
| IaC | Terraform |
| Monitoring | Prometheus, Grafana |
| Testing | Pytest |
| CI/CD | GitHub Actions |

---

# Application Services

## API Gateway

Provides a common entry point for frontend/API clients and separates external access from internal service communication.

## Auth Service

Handles authentication and JWT-based access control.

## Customer Service

Manages customer information and customer-related operations.

## Transaction Service

Creates transactions, persists them in PostgreSQL and publishes `transaction.created` events to Kafka.

## Fraud Detection Service

Consumes transaction events and performs:

1. Redis velocity calculation
2. Rule-based risk assessment
3. ML inference
4. Fraud assessment persistence
5. `fraud.assessed` event publication
6. Idempotency handling

## Notification Service

Provides the service boundary for downstream notification processing.

## Audit Service

Provides an independent service boundary for audit-related records and events.

## Analytics Service

Exposes analytics APIs and provides the lake-to-warehouse ETL trigger.

## ML Service

Loads the trained fraud model and provides real-time inference through FastAPI.

---

# Transaction Flow

A transaction follows this path:

```text
Client
  |
  v
Transaction Service
  |
  +--> PostgreSQL
  |
  +--> Kafka: transaction.created
                |
                v
          Fraud Service
                |
        +-------+-------+
        |       |       |
        v       v       v
      Redis   Rules   ML Service
        |       |       |
        +-------+-------+
                |
                v
         Fraud Assessment
                |
        +-------+-------+
        |               |
        v               v
    PostgreSQL     Kafka: fraud.assessed
```

The processing is asynchronous after the transaction event is published.

---

# Fraud Detection

## Rule-Based Detection

Current rules include signals for:

- Very high transaction amount
- High transaction amount
- High-risk categories such as gambling, crypto and money transfer
- Missing device
- Missing location
- High transaction frequency
- High cumulative transaction amount

The rule engine produces:

```text
risk_level
risk_score
reasons
```

## Machine Learning Detection

The ML service receives engineered transaction features including:

```text
amount
amount_band_code
is_high_risk_merchant_category
has_device
has_location
customer_is_active
is_inr
is_pending
transaction_hour
transaction_day_of_week
is_weekend
is_night_transaction
transaction_velocity
recent_transaction_amount
high_velocity_amount
merchant_category
currency
transaction_status
```

The final Kafka fraud event stores both rule-based and ML results.

Example:

```json
{
  "rule_based": {
    "risk_level": "HIGH",
    "risk_score": 100
  },
  "machine_learning": {
    "model_name": "fraud_random_forest",
    "model_version": "7D",
    "prediction": "FRAUD",
    "fraud_probability": 0.928296,
    "legitimate_probability": 0.071704,
    "risk_level": "HIGH",
    "threshold": 0.5
  }
}
```

The probability is a model output from the current synthetic-data experiment and is not a real-world fraud probability.

---

# Machine Learning

## Feature Engineering

The feature builder derives transaction features such as:

```text
amount_log
amount_band_code
transaction_hour
transaction_day_of_week
is_weekend
is_night_transaction
is_high_risk_merchant_category
has_device
has_location
customer_is_active
is_inr
is_pending
```

Real-time velocity features are supplied by Redis during inference.

## Model

Current model:

```text
RandomForestClassifier
```

Training configuration:

```text
300 trees
random_state = 42
class_weight = balanced
max_features = sqrt
min_samples_leaf = 2
```

The current synthetic dataset contains:

```text
10,000 rows
9,793 legitimate
207 fraud
Fraud rate: 2.07%
```

## Evaluation

Current synthetic test results:

```text
Accuracy   : 0.9947
Precision  : 0.7949
Recall     : 1.0000
F1 Score   : 0.8857
ROC-AUC    : 0.9998
```

Confusion matrix:

```text
[[1461    8]
 [   0   31]]
```

These metrics are a synthetic-data baseline. The unusually high performance is influenced by the way the synthetic labels were generated from patterns overlapping with the model features, so these numbers should not be presented as production fraud-detection performance.

---

# MLOps and MLflow

MLflow is used for experiment tracking and model-related artifacts.

The training workflow records information such as:

- Parameters
- Metrics
- Model artifact
- Model signature
- Input example
- Experiment information

The ML service uses:

```text
MODEL_PATH
MODEL_VERSION
```

so inference results can be associated with a deployed model version.

Local MLflow artifacts/databases are excluded from Git.

---

# Kafka Event Architecture

Important events:

```text
transaction.created
fraud.assessed
transaction.created.DLQ
```

Example:

```text
Transaction Service
       |
       v
transaction.created
       |
       +----> Fraud Service
       |
       +----> Spark Streaming

Fraud Service
       |
       v
fraud.assessed
```

## Idempotency

The fraud service uses a Redis idempotency key:

```text
fraud:processed:{event_id}
```

to prevent successful events from being processed repeatedly.

## Retry and DLQ

Failed event processing can be retried. Events that exceed the retry limit can be sent to:

```text
transaction.created.DLQ
```

---

# Data Lake and Spark

Spark Structured Streaming reads transaction events from Kafka.

The MinIO bucket is:

```text
finsightx-data
```

Data is organized into:

```text
raw/transactions
processed/transactions
checkpoints/transactions
checkpoints/processed_transactions
```

The processed layer performs:

- String trimming
- Currency normalization
- Category normalization
- Amount null handling
- Date extraction
- Amount bands
- Data-quality classification
- Processing-layer tagging

Processed data is partitioned by:

```text
year/month/day
```

---

# Data Warehouse

The warehouse ETL flow is:

```text
MinIO processed Parquet
        |
        v
Spark warehouse loader
        |
        v
analytics.stg_processed_transactions
        |
        v
Dimension loading
        |
        v
fact_transactions
```

Star schema:

```text
                  dim_customer
                       |
                       |
dim_date ---- fact_transactions ---- dim_merchant
                       |
                       |
                  dim_device
                       |
                       |
                  dim_location
```

Current verified local warehouse counts:

```text
dim_date          : 2
dim_customer      : 1
dim_merchant      : 8
dim_device        : 8
dim_location      : 1
fact_transactions : 23
```

---

# Power BI

Dashboard:

```text
FinSightX — Financial Risk & Fraud Analytics
```

Current measures:

```text
Total Transactions
Total Amount
Average Transaction Amount
High Risk Transactions
Assessed Transactions
Unassessed Transactions
High Risk Amount
```

Risk categories used for reporting include:

```text
HIGH
MEDIUM
LOW
NOT_ASSESSED
```

Power BI connects to the PostgreSQL analytics database.

---

# Security and Reliability

Security/reliability is handled across multiple layers.

## JWT

JWT-based authentication is used for API/service access.

## Environment Variables

Sensitive configuration is stored through environment variables.

Only `.env.example` is committed. Real `.env` files are ignored.

## Redis

Redis provides fast operational state for:

- Velocity tracking
- Idempotency

## PostgreSQL

PostgreSQL provides durable storage for transaction, fraud and analytical data.

## Kafka

Kafka decouples producers and consumers and supports asynchronous event processing.

## Health and Readiness

The ML service exposes:

```text
/health
/ready
```

`/ready` verifies that the fraud model has been loaded successfully.

---

# Monitoring

The monitoring architecture is:

```text
Application Services
        |
        v
     Metrics
        |
        v
   Prometheus
        |
        v
     Grafana
```

The FastAPI platform exposes metrics through:

```text
/metrics
```

Prometheus and Grafana are included in the local infrastructure.

---

# Docker Deployment

Start the complete stack:

```powershell
docker compose up -d
```

Build and start:

```powershell
docker compose up -d --build
```

Check:

```powershell
docker compose ps
```

Stop:

```powershell
docker compose down
```

The current local stack includes PostgreSQL, Redis, Kafka, MinIO, Spark and the application microservices.

---

# Kubernetes and Infrastructure

The repository contains:

```text
infrastructure/
├── docker/
├── kubernetes/
├── helm/
└── terraform/
```

The Kubernetes layer is intended for cloud-native deployment concepts such as:

- Deployments
- Services
- ConfigMaps
- Secrets
- Health probes
- Scaling

Local Kubernetes development can use:

```text
kind
kubectl
Helm
```

Terraform is included for Infrastructure-as-Code workflows.

The current development approach remains local-first and does not require paid cloud infrastructure.

---

# Testing

The repository contains:

```text
tests/
├── unit/
├── integration/
├── load/
└── security/
```

Testing targets include:

- REST APIs
- Fraud rules
- ML inference
- Database operations
- Kafka event processing
- Integration flows
- Security behavior
- Reliability scenarios

A verified end-to-end ML flow has demonstrated:

```text
Transaction Service
       |
       v
Kafka
       |
       v
Fraud Service
       |
       +--> Redis velocity
       |
       +--> Rule assessment
       |
       +--> ML Service
                |
                v
          Random Forest
                |
                v
          PostgreSQL
                |
                v
          fraud.assessed
```

---

# Project Structure

```text
FinSightX/
│
├── .github/
│   └── workflows/
│
├── services/
│   ├── api-gateway/
│   ├── auth-service/
│   ├── customer-service/
│   ├── transaction-service/
│   ├── fraud-service/
│   ├── notification-service/
│   ├── audit-service/
│   ├── analytics-service/
│   └── ml-service/
│
├── streaming/
│   ├── kafka/
│   └── spark/
│
├── ml/
│   ├── training/
│   ├── features/
│   ├── experiments/
│   └── models/
│
├── data/
│   ├── lake/
│   ├── warehouse/
│   └── schemas/
│
├── frontend/
│   └── react-app/
│
├── infrastructure/
│   ├── docker/
│   ├── kubernetes/
│   ├── helm/
│   └── terraform/
│
├── monitoring/
│   ├── prometheus/
│   └── grafana/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── load/
│   └── security/
│
├── docs/
│   ├── architecture/
│   ├── system-design/
│   ├── api/
│   └── diagrams/
│
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

# Local Setup

## Prerequisites

Install:

- Python 3.11+
- Node.js
- Docker Desktop
- Git
- PostgreSQL client
- Power BI Desktop
- kind
- kubectl
- Helm
- Terraform

## 1. Clone

```powershell
git clone <YOUR_GITHUB_REPOSITORY>
cd FinSightX
```

## 2. Python Environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 3. Environment

Copy:

```text
.env.example
```

to:

```text
.env
```

Configure local credentials and service settings.

Do not commit `.env`.

## 4. Start Docker

```powershell
docker compose up -d --build
```

Verify:

```powershell
docker compose ps
```

## 5. Verify ML Service

```powershell
Invoke-RestMethod `
  -Uri http://localhost:8008/health `
  -Method GET
```

```powershell
Invoke-RestMethod `
  -Uri http://localhost:8008/ready `
  -Method GET
```

Expected model:

```text
fraud_random_forest
```

Current deployed local model version:

```text
7D
```

## 6. Create a Transaction

```powershell
$body = @{
    customer_id = "<CUSTOMER_UUID>"
    amount = 75000
    currency = "INR"
    merchant_name = "FinSight ML Test Merchant"
    merchant_category = "Crypto"
    location = "Chennai"
    device_id = "device-ml-test-001"
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri http://localhost:8010/api/v1/transactions `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```

## 7. Inspect Fraud Processing

```powershell
docker logs --tail 100 finsightx-fraud-service
```

Look for:

```text
VELOCITY
RULE ASSESSMENT
Calling ML service
ML prediction received
FRAUD ASSESSMENT STORED
FRAUD EVENT PUBLISHED
EVENT PROCESSED SUCCESSFULLY
```

## 8. Inspect Kafka

```powershell
docker exec finsightx-kafka /opt/kafka/bin/kafka-console-consumer.sh `
  --bootstrap-server localhost:9092 `
  --topic fraud.assessed `
  --from-beginning `
  --max-messages 10
```

## 9. Run Warehouse ETL

```powershell
docker exec finsightx-spark `
  /opt/spark/bin/spark-submit `
  --master local[*] `
  /opt/finsightx/app/lake_to_warehouse.py
```

Or trigger through Analytics Service:

```powershell
Invoke-RestMethod `
  -Uri http://localhost:8007/api/v1/etl/lake/run `
  -Method POST
```

---

# Service URLs

| Service | URL |
|---|---|
| API Gateway | http://localhost:8002 |
| Customer Service | http://localhost:8009 |
| Transaction Service | http://localhost:8010 |
| Fraud Service | http://localhost:8004 |
| Notification Service | http://localhost:8005 |
| Audit Service | http://localhost:8006 |
| Analytics Service | http://localhost:8007 |
| ML Service | http://localhost:8008 |
| PostgreSQL | localhost:5434 |
| Redis | localhost:6380 |
| Kafka | localhost:29092 |
| MinIO API | http://localhost:9000 |
| MinIO Console | http://localhost:9001 |

---

# Verified End-to-End Flow

A verified ML transaction used:

```text
Amount            : ₹75,000
Currency          : INR
Merchant          : FinSight ML Test Merchant
Category          : Crypto
Location          : Chennai
Status            : PENDING
```

The Fraud Service successfully performed:

```text
Kafka event received
        ↓
Redis velocity calculated
        ↓
Rule assessment
        ↓
ML Service HTTP call
        ↓
Random Forest prediction
        ↓
PostgreSQL persistence
        ↓
fraud.assessed publication
        ↓
Idempotency marker
```

Verified result:

```text
Rule risk level       : HIGH
Rule risk score       : 100
ML prediction         : FRAUD
ML fraud probability  : 92.83%
ML risk level         : HIGH
Model version         : 7D
```

The same event was verified in the `fraud.assessed` Kafka topic as event version `2.0`.

Again, the 92.83% value is a model output from the current synthetic-data experiment, not a real-world fraud probability.

---

# Engineering Highlights

FinSightX demonstrates:

- Distributed system design
- Microservice architecture
- Event-driven architecture
- REST API development
- Kafka-based asynchronous communication
- Redis-based real-time velocity detection
- Rule-based fraud detection
- Machine-learning fraud detection
- Dedicated ML inference service
- Feature engineering
- Random Forest classification
- MLflow experiment tracking
- Spark Structured Streaming
- MinIO/S3-compatible data lake
- Parquet processing
- Data-quality processing
- PostgreSQL analytical warehouse
- Star-schema modeling
- ETL pipelines
- Power BI business analytics
- JWT security
- Idempotent event processing
- Retry and DLQ concepts
- Docker multi-container deployment
- Kubernetes-ready infrastructure
- Helm
- Terraform
- Prometheus
- Grafana
- Testing structure
- CI/CD-ready repository

---

# Future Enhancements

Planned/possible extensions:

- Production model registry and promotion
- Automated model retraining
- Model drift monitoring
- Real-time feature store
- Better online/offline feature consistency
- Transactional outbox pattern
- Kafka Schema Registry
- Stronger event contracts
- More advanced rule/ML score combination
- Model explainability
- Kubernetes deployment with Helm
- Horizontal Pod Autoscaling
- Kubernetes secrets management
- Full GitHub Actions CI/CD
- Distributed load testing
- Advanced notification channels
- Additional Power BI dashboards
- Cloud deployment
- Data quality monitoring
- Advanced observability

These are extension points rather than requirements for the current local implementation.

---

# Author

**Suriya MG**

B.Tech Computer Science and Engineering  
Vellore Institute of Technology

---

# Project Summary

FinSightX combines:

**Microservices + Distributed Systems + Event-Driven Architecture + Real-Time Fraud Detection + Machine Learning + MLOps + Data Engineering + Data Warehousing + Business Intelligence + Security + Docker + Kubernetes + Monitoring**

into one end-to-end financial technology platform.

The project demonstrates not only how to build a fraud detection model, but how to integrate that model into a larger distributed system:

```text
Transactions
    ↓
Kafka Events
    ↓
Real-Time Processing
    ↓
Redis Velocity + Rules
    ↓
Machine Learning
    ↓
Fraud Assessment
    ↓
PostgreSQL
    ↓
MinIO Data Lake
    ↓
Spark ETL
    ↓
Data Warehouse
    ↓
Power BI
```

The result is a complete software engineering, data engineering and AI/ML platform rather than an isolated machine-learning project.
