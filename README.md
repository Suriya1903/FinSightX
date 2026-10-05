# FinSightX

## Distributed Financial Intelligence, Risk & Fraud Detection Platform

FinSightX is an end-to-end financial intelligence, risk, and fraud detection platform designed to demonstrate how a modern distributed fintech system can be built from the ground up.

The project combines:

**Microservices + Distributed Systems + Event-Driven Architecture + Real-Time Fraud Detection + Machine Learning + MLOps + Data Engineering + Data Warehousing + Business Intelligence + Security + Docker + Kubernetes + Observability + Helm + Terraform + CI/CD**

Unlike an isolated machine-learning project, FinSightX demonstrates how a fraud model can be integrated into a complete production-style platform: transactions enter through APIs, events move through Kafka, fraud is evaluated using Redis and ML, results are persisted, streaming data is processed with Spark, analytics are loaded into a warehouse, Power BI visualizes business intelligence, and the platform is monitored using Prometheus and Grafana.

The platform is intentionally **local-first**. The complete development environment can be run on a Windows machine using Docker Desktop and a local Kubernetes `kind` cluster without requiring paid cloud infrastructure.

---

## Table of Contents

- [1. Project Overview](#1-project-overview)
- [2. What Has Been Implemented](#2-what-has-been-implemented)
- [3. High-Level Architecture](#3-high-level-architecture)
- [4. Technology Stack](#4-technology-stack)
- [5. Microservices](#5-microservices)
- [6. End-to-End Transaction Flow](#6-end-to-end-transaction-flow)
- [7. Authentication and Security](#7-authentication-and-security)
- [8. Kafka and Event-Driven Architecture](#8-kafka-and-event-driven-architecture)
- [9. Redis Velocity and Idempotency](#9-redis-velocity-and-idempotency)
- [10. Fraud Detection Engine](#10-fraud-detection-engine)
- [11. Machine Learning Pipeline](#11-machine-learning-pipeline)
- [12. ML Inference Service](#12-ml-inference-service)
- [13. MLOps and MLflow](#13-mlops-and-mlflow)
- [14. Spark Structured Streaming](#14-spark-structured-streaming)
- [15. MinIO Data Lake](#15-minio-data-lake)
- [16. PostgreSQL Analytics Warehouse](#16-postgresql-analytics-warehouse)
- [17. Power BI](#17-power-bi)
- [18. Observability](#18-observability)
- [19. Docker Deployment](#19-docker-deployment)
- [20. Kubernetes Deployment](#20-kubernetes-deployment)
- [21. Helm](#21-helm)
- [22. Terraform and Infrastructure](#22-terraform-and-infrastructure)
- [23. Testing and Verification](#23-testing-and-verification)
- [24. Project Structure](#24-project-structure)
- [25. Local Docker Setup](#25-local-docker-setup)
- [26. Kubernetes Setup](#26-kubernetes-setup)
- [27. Useful Verification Commands](#27-useful-verification-commands)
- [28. Current Verified Results](#28-current-verified-results)
- [29. Engineering Highlights](#29-engineering-highlights)
- [30. Future Enhancements](#30-future-enhancements)
- [31. Author](#31-author)

---

# 1. Project Overview

FinSightX separates financial transaction processing into independently deployable services.

The primary business flow is:

```text
React Frontend
      |
      v
API Gateway
      |
      +--------------------+
      |                    |
      v                    v
 Auth Service        Customer Service
                           |
                           v
                   Transaction Service
                           |
                           v
                         Kafka
                           |
              +------------+-------------+
              |            |             |
              v            v             v
        Fraud Service   Spark       Other Consumers
              |
       +------+------+
       |             |
       v             v
     Redis       ML Service
   Velocity      Random Forest
       |             |
       +------+------+
              |
              v
       Fraud Assessment
              |
       +------+------+
       |             |
       v             v
   PostgreSQL     Kafka
              fraud.assessed
```

The analytics/data-engineering path runs in parallel:

```text
Kafka
  |
  v
Spark Structured Streaming
  |
  +----------------------+
  |                      |
  v                      v
MinIO Raw           MinIO Processed
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

The observability path is:

```text
API Gateway / Fraud Service
          |
          v
     Prometheus
          |
          v
       Grafana
```

---

# 2. What Has Been Implemented

The current implementation has progressed significantly beyond the original application prototype.

## Core platform

- API Gateway
- Authentication service
- Customer service
- Transaction service
- Fraud detection service
- Notification service
- Audit service
- Analytics service
- Dedicated ML inference service
- React frontend structure
- PostgreSQL
- Redis
- Apache Kafka
- Spark Structured Streaming
- MinIO
- Power BI analytics
- Prometheus
- Grafana

## Security

- JWT-based authentication
- Role-based access control concepts
- ADMIN and USER roles
- Protected gateway routes
- Environment-based secrets/configuration
- `.env` excluded from Git
- Password hashing
- Authentication verification through the gateway

## Fraud detection

- Rule-based risk scoring
- Redis transaction velocity tracking
- Idempotent Kafka event processing
- Machine-learning inference
- Rule + ML fraud assessment persistence
- `fraud.assessed` event publishing
- Retry/DLQ architecture

## Machine learning

- Feature engineering pipeline
- Synthetic fraud dataset
- Random Forest model
- Imbalanced-class handling
- Model evaluation
- Model serialization with Joblib
- Dedicated FastAPI ML inference service
- Model versioning
- MLflow experiment tracking

## Data engineering

- Kafka to Spark Structured Streaming
- Raw Parquet data in MinIO
- Processed Parquet data in MinIO
- Data-quality transformations
- Date partitioning
- Warehouse ETL
- PostgreSQL dimensional warehouse

## Business intelligence

- PostgreSQL analytics layer
- Star schema
- Power BI dashboard
- Fraud/risk measures
- High-risk transaction analytics

## Cloud-native infrastructure

- Docker
- Docker Compose
- Kubernetes manifests
- Local `kind` Kubernetes cluster
- Helm chart
- Kubernetes Services
- Kubernetes Deployments
- ConfigMaps
- Secrets
- Persistent Volumes
- Health/readiness endpoints
- Prometheus and Grafana deployed in Kubernetes

## Observability

- Prometheus instrumentation
- API Gateway request counters
- API Gateway request latency histograms
- Fraud event counters
- Fraud assessment counters
- ML prediction counters
- Processing failure counters
- Fraud processing latency
- Grafana dashboards
- Kubernetes service monitoring

## Deployment verification

The complete Kubernetes deployment has been successfully brought up with all core deployments running.

The Helm chart has also been successfully used to manage/adopt the Kubernetes resources.

---

# 3. High-Level Architecture

```text
                           +----------------------+
                           |    React Frontend    |
                           +----------+-----------+
                                      |
                                      v
                           +----------------------+
                           |     API Gateway      |
                           |        :8000         |
                           +----------+-----------+
                                      |
                 +--------------------+--------------------+
                 |                    |                    |
                 v                    v                    v
          +-------------+      +-------------+      +-------------+
          |    Auth     |      |  Customer   |      | Transaction |
          |   Service   |      |   Service   |      |   Service   |
          +-------------+      +-------------+      +------+------+
                                                           |
                                                           v
                                                    +-------------+
                                                    |    Kafka    |
                                                    |    :9092    |
                                                    +------+------+
                                                           |
                     +----------------------+--------------+----------------+
                     |                      |                               |
                     v                      v                               v
              +-------------+       +-------------+                 +-------------+
              |    Fraud    |       |    Spark    |                 |   Other     |
              |   Service   |       |  Streaming  |                 | Consumers   |
              +------+------+       +------+------+                 +-------------+
                     |                     |
              +------+-------+             |
              |              |             v
              v              v         +---------+
           +------+      +-------+     |  MinIO  |
           |Redis |      |  ML   |     +----+----+
           |      |      |Service|          |
           +------+      +---+---+          v
                              |       +-------------+
                              v       | Warehouse   |
                       Random Forest  |    ETL      |
                                      +------+------+
                                             |
                                             v
                                      +-------------+
                                      | PostgreSQL  |
                                      | Analytics   |
                                      +------+------+
                                             |
                                             v
                                      +-------------+
                                      |  Power BI   |
                                      +-------------+

Observability:

+-------------------+       +-------------+       +-------------+
| Gateway/Fraud     | ----> | Prometheus  | ----> |   Grafana   |
| /metrics          |       |    :9090    |       |    :3000    |
+-------------------+       +-------------+       +-------------+
```

---

# 4. Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React |
| Backend APIs | FastAPI |
| Language | Python |
| Authentication | JWT |
| Authorization | Role-based access control |
| Event Streaming | Apache Kafka |
| Cache / Operational State | Redis |
| Database | PostgreSQL 18 |
| Vector Extension | pgvector |
| Streaming | Apache Spark Structured Streaming |
| Data Lake | MinIO |
| Data Format | Parquet |
| Data Processing | Pandas, NumPy, PyArrow |
| ML | Scikit-learn |
| ML Model | Random Forest |
| Model Serialization | Joblib |
| MLOps | MLflow |
| BI | Microsoft Power BI |
| Containers | Docker |
| Local Orchestration | Docker Compose |
| Kubernetes | Kubernetes + kind |
| Package Management | Helm |
| Infrastructure as Code | Terraform |
| Metrics | Prometheus |
| Dashboards | Grafana |
| Testing | Pytest |
| CI/CD | GitHub Actions |
| Version Control | Git / GitHub |

---

# 5. Microservices

## API Gateway

The API Gateway is the external entry point to the platform.

Responsibilities:

- Central API entry point
- Request routing
- JWT authentication
- Authorization/RBAC
- HTTP metrics
- Health endpoint
- Service-to-service forwarding

Important endpoints include:

```text
/health
/metrics
/api/v1/...
```

---

## Auth Service

Responsible for:

- User registration
- Authentication
- Password hashing
- JWT token generation
- User roles

Example roles:

```text
ADMIN
USER
```

---

## Customer Service

Responsible for:

- Customer creation
- Customer retrieval
- Customer status
- Customer-related data

---

## Transaction Service

Responsible for:

1. Receiving transaction requests
2. Validating transaction data
3. Persisting transactions
4. Publishing `transaction.created`
5. Returning the transaction response

---

## Fraud Service

The Fraud Service is one of the main components of the platform.

Processing sequence:

```text
Kafka event
     |
     v
Redis velocity
     |
     v
Rule-based assessment
     |
     v
ML Service
     |
     v
Combined fraud assessment
     |
     v
PostgreSQL
     |
     v
fraud.assessed
```

It also handles:

- Idempotency
- Retries
- DLQ behavior
- Prometheus metrics
- Fraud persistence
- ML integration

---

## Notification Service

Consumes fraud-related events and provides the service boundary for high-risk notification processing.

A verified high-risk transaction generated a high-risk alert record.

---

## Audit Service

Provides an independent audit boundary for recording important platform actions.

A verified gateway transaction generated an audit record containing information such as:

```text
gateway user
role
action
resource
status
```

---

## Analytics Service

Responsible for:

- Analytics APIs
- Lake-to-warehouse ETL trigger
- Analytics integration

---

## ML Service

A dedicated FastAPI inference service.

Responsibilities:

- Load the trained Random Forest model
- Validate inference input
- Generate fraud probability
- Generate prediction
- Generate risk level
- Expose health/readiness endpoints

Endpoints:

```text
GET  /health
GET  /ready
POST /api/v1/predict
```

---

# 6. End-to-End Transaction Flow

A typical transaction moves through the system as follows:

```text
1. Client
      |
      v
2. API Gateway
      |
      v
3. Transaction Service
      |
      +----> PostgreSQL
      |
      +----> Kafka
               |
               | transaction.created
               v
4. Fraud Service
      |
      +----> Redis velocity
      |
      +----> Rule engine
      |
      +----> ML Service
               |
               v
          Random Forest
               |
               v
5. Fraud Assessment
      |
      +----> PostgreSQL
      |
      +----> Kafka
               |
               | fraud.assessed
               +----> Notification Service
               |
               +----> Audit/other consumers

Parallel data path:

Kafka
  |
  v
Spark
  |
  v
MinIO
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

The transaction-to-fraud path is asynchronous after the transaction event is published.

---

# 7. Authentication and Security

Security is implemented as a platform concern rather than an isolated feature.

## JWT Authentication

The authentication flow is:

```text
Login
  |
  v
Auth Service
  |
  v
JWT
  |
  v
Client
  |
  v
API Gateway
  |
  v
Token validation
  |
  v
Authorized service operation
```

## RBAC

Role-based access is used to distinguish privileged and normal users.

Example:

```text
ADMIN
USER
```

Administrative gateway access was verified using an ADMIN account.

## Password Security

Passwords are stored using secure password hashing rather than plain text.

## Environment Configuration

Sensitive values are configured through environment variables.

The repository commits configuration templates rather than real secrets.

```text
.env.example   -> committed
.env           -> ignored
```

## Kubernetes Secrets

Kubernetes deployment includes Secret resources for sensitive configuration such as database/JWT/MinIO credentials.

For production, external secret management should be used instead of static development secrets.

---

# 8. Kafka and Event-Driven Architecture

Kafka acts as the event backbone.

Important topics:

```text
transaction.created
fraud.assessed
transaction.created.DLQ
```

## Transaction Event

```text
Transaction Service
       |
       v
transaction.created
       |
       +----> Fraud Service
       |
       +----> Spark Streaming
       |
       +----> Other consumers
```

## Fraud Event

```text
Fraud Service
      |
      v
fraud.assessed
      |
      +----> Notification
      |
      +----> Audit/other consumers
```

This architecture prevents the Transaction Service from waiting synchronously for every downstream operation.

---

## Event Versioning

Fraud events currently use versioned event payloads. A verified fraud event was published as event version:

```text
2.0
```

This establishes a foundation for stronger event-contract management in future versions.

---

## Idempotency

Fraud processing uses an event-specific Redis idempotency key:

```text
fraud:processed:{event_id}
```

If a previously successful event is delivered again, the service can detect that it has already been processed.

---

## Retry and DLQ

Failures can be retried.

Events that exceed retry limits can be routed to:

```text
transaction.created.DLQ
```

This prevents a poison event from continuously blocking normal processing.

---

# 9. Redis Velocity and Idempotency

Redis is used for fast operational state.

For fraud detection, Redis maintains short-window transaction statistics such as:

```text
transaction count
cumulative transaction amount
recent transaction amount
```

Example:

```text
Customer
   |
   +--> Transaction 1: ₹20,000
   +--> Transaction 2: ₹25,000
   +--> Transaction 3: ₹75,000
                |
                v
        High transaction velocity
                |
                v
          Fraud signal
```

Redis is also used for event idempotency.

This gives Redis two important roles:

1. Real-time fraud features
2. Reliable event-processing state

---

# 10. Fraud Detection Engine

FinSightX combines deterministic rules with machine learning.

## Rule-Based Detection

Signals include:

- Very high transaction amount
- High transaction amount
- High-risk merchant categories
- Gambling
- Crypto
- Money transfer
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

Example:

```text
Amount            : ₹75,000
Category          : Crypto
Location          : Chennai
Velocity          : High

Rule Risk Level   : HIGH
Rule Risk Score   : 100
```

---

## Machine Learning Detection

The ML model independently evaluates engineered transaction features.

The final fraud assessment stores both rule-based and ML information.

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
    "fraud_probability": 0.896390,
    "legitimate_probability": 0.103610,
    "risk_level": "HIGH",
    "threshold": 0.5
  }
}
```

The exact probability changes depending on the transaction features.

**Important:** the current model is trained on synthetic data. Its probability must not be interpreted as a real-world calibrated fraud probability.

---

# 11. Machine Learning Pipeline

## Feature Engineering

The feature builder reads warehouse data and creates model-ready features.

Important features include:

```text
amount
amount_log
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

Real-time velocity features are obtained from Redis during fraud inference.

---

## Training Dataset

The current synthetic training dataset contains:

```text
Total rows     : 10,000
Legitimate     : 9,793
Fraud          : 207
Fraud rate     : 2.07%
```

---

## Model

Current model:

```text
RandomForestClassifier
```

Training configuration:

```text
n_estimators     = 300
random_state     = 42
class_weight     = balanced
max_features     = sqrt
min_samples_leaf = 2
```

The model is serialized with Joblib:

```text
ml/models/fraud_random_forest.joblib
```

---

## Validation Results

Current synthetic validation results:

```text
Precision : 0.8667
Recall    : 0.8387
F1 Score  : 0.8525
ROC-AUC   : 0.9974
```

---

## Test Results

Current synthetic test results:

```text
Accuracy  : 0.9947
Precision : 0.7949
Recall    : 1.0000
F1 Score  : 0.8857
ROC-AUC   : 0.9998
```

Confusion matrix:

```text
[[1461    8]
 [   0   31]]
```

The high ROC-AUC is not evidence of production-level fraud detection performance. The synthetic labels were generated using patterns that overlap with the model features, which can make the classification problem artificially easy.

---

## Feature Importance

Important model features include:

```text
amount                     25.23%
recent_transaction_amount  16.64%
transaction_velocity       13.04%
amount_band_code            12.23%
high_velocity_amount         9.79%
high-risk merchant category  6.66%
night                        4.32%
transaction_hour             3.99%
```

This gives an interpretable view of which engineered signals influenced the model most strongly in the current experiment.

---

# 12. ML Inference Service

The model is not embedded directly into the Transaction Service.

Instead:

```text
Fraud Service
     |
     | HTTP
     v
ML Service
     |
     v
Random Forest
     |
     v
Prediction
```

This separation makes it possible to:

- Deploy the model independently
- Version the model
- Scale ML inference separately
- Replace the model without changing transaction processing
- Add model monitoring later
- Support multiple model versions

Example endpoint:

```text
POST /api/v1/predict
```

Example response:

```json
{
  "model_name": "fraud_random_forest",
  "model_version": "7D",
  "prediction": "FRAUD",
  "fraud_probability": 0.9576919434179314,
  "legitimate_probability": 0.04230805658206862,
  "risk_level": "HIGH",
  "model_threshold": 0.5
}
```

The deployed local model version used during verification was:

```text
7D
```

---

# 13. MLOps and MLflow

MLflow is used for experiment tracking.

The training workflow records:

- Parameters
- Metrics
- Model artifact
- Model signature
- Input example
- Experiment information

The local MLflow tracking store uses SQLite.

Example:

```text
ml/experiments/mlflow.db
```

The training code configures MLflow with a SQLite tracking URI and logs the trained scikit-learn model.

A local MLflow UI can be started with:

```powershell
mlflow ui `
  --backend-store-uri "sqlite:///D:/FinSightX/ml/experiments/mlflow.db" `
  --host 127.0.0.1 `
  --port 5000
```

Local MLflow databases and experiment artifacts are excluded from Git where appropriate.

---

# 14. Spark Structured Streaming

Spark consumes Kafka transaction events.

The streaming architecture is:

```text
Kafka
  |
  v
Spark Structured Streaming
  |
  +----> Raw Parquet
  |
  +----> Processed Parquet
```

Spark performs transformations including:

- String trimming
- Currency normalization
- Merchant-category normalization
- Amount null handling
- Date extraction
- Amount bands
- Data-quality classification
- Processing-layer tagging

Processed data is partitioned using:

```text
year/month/day
```

---

# 15. MinIO Data Lake

MinIO provides S3-compatible local object storage.

Bucket:

```text
finsightx-data
```

The data layout includes:

```text
raw/
processed/
checkpoints/
```

Important paths include:

```text
raw/transactions

processed/transactions

checkpoints/transactions

checkpoints/processed_transactions
```

Parquet is used because it is columnar and suitable for analytical workloads.

---

# 16. PostgreSQL Analytics Warehouse

The lake-to-warehouse flow is:

```text
MinIO Processed Parquet
          |
          v
Spark Warehouse Loader
          |
          v
analytics.stg_processed_transactions
          |
          v
Dimension Loading
          |
          v
fact_transactions
```

The warehouse uses a star schema.

```text
                     dim_customer
                          |
                          |
dim_date -------- fact_transactions -------- dim_merchant
                          |
                          |
                     dim_device
                          |
                          |
                    dim_location
```

Tables:

```text
analytics.dim_date
analytics.dim_customer
analytics.dim_merchant
analytics.dim_device
analytics.dim_location
analytics.fact_transactions
```

Verified local warehouse counts during implementation:

```text
dim_date          : 2
dim_customer      : 1
dim_merchant      : 8
dim_device        : 8
dim_location      : 1
fact_transactions : 23
```

These counts are verification snapshots and will change as new transactions are processed.

---

# 17. Power BI

Power BI connects to the PostgreSQL analytics layer.

Dashboard:

```text
FinSightX — Financial Risk & Fraud Analytics
```

Page:

```text
Risk Dashboard
```

Current measures include:

```text
Total Transactions
Total Amount
Average Transaction Amount
High Risk Transactions
Assessed Transactions
Unassessed Transactions
High Risk Amount
```

A reporting column is also used to normalize risk display:

```text
HIGH
MEDIUM
LOW
NOT_ASSESSED
```

A verified dashboard scenario filtered transactions by date, merchant, and HIGH risk to validate that the warehouse and reporting layer were returning the expected fraud-risk results.

---

# 18. Observability

Observability was implemented after the initial application and data-engineering phases.

The current monitoring architecture is:

```text
API Gateway       Fraud Service
      |                 |
      | /metrics       | /metrics
      +--------+--------+
               |
               v
          Prometheus
               |
               v
            Grafana
```

## Prometheus

Prometheus is configured to scrape:

```text
Prometheus
API Gateway
Fraud Service
```

All configured application targets were verified as `UP`.

---

## API Gateway Metrics

The gateway records:

```text
finsightx_http_requests_total

finsightx_http_request_duration_seconds
```

Labels include:

```text
method
path
status_code
```

This allows request rates, status codes, and latency to be analyzed.

---

## Fraud Service Metrics

Fraud metrics include:

```text
finsightx_fraud_events_processed_total

finsightx_fraud_assessments_total

finsightx_ml_predictions_total

finsightx_fraud_processing_failures_total

finsightx_ml_prediction_failures_total

finsightx_fraud_processing_duration_seconds
```

Examples:

```text
Fraud events processed
Fraud assessments by risk level
ML predictions
ML predictions by risk level
Fraud processing failures
ML prediction failures
Fraud processing latency
```

---

## Verified Observability Transaction

A dedicated observability transaction was processed successfully.

Example:

```text
Transaction ID : 0ccfbe22-4021-4a6c-bb09-6ab15ac961bb
Amount         : ₹75,000
Currency       : INR
Merchant       : FinSightX Observability Test
Category       : Crypto
Location       : Chennai
Device         : observability-test-device-001
Status         : PENDING
```

Observed processing:

```text
Kafka event received
        ↓
Redis velocity
        ↓
Rule assessment
        ↓
ML prediction
        ↓
Fraud persistence
        ↓
fraud.assessed
        ↓
Idempotency
```

Verified metrics included:

```text
fraud events processed       : 1 success
fraud assessments            : 1 HIGH
ML predictions               : 1 FRAUD/HIGH
fraud processing failures    : 0
ML prediction failures      : 0
processing count             : 1
```

Measured processing latency for that verification event was approximately:

```text
1.207 seconds
```

This is a single local verification measurement, not a production performance benchmark.

---

## Grafana

The Grafana dashboard contains API Gateway panels such as:

- Requests by API Endpoint
- HTTP Requests by Status Code
- API Gateway P95 Latency
- HTTP Request Rate
- API Gateway Status

Fraud/ML observability panels were added for:

1. Fraud Events Processed
2. Fraud Assessments by Risk Level
3. ML Predictions
4. ML Predictions by Risk Level
5. Fraud Processing Failures
6. ML Prediction Failures
7. Fraud Processing Latency / P95
8. Fraud Service Status

---

# 19. Docker Deployment

Docker is used for local multi-service deployment.

Build and start:

```powershell
docker compose up -d --build
```

Check:

```powershell
docker compose ps
```

View logs:

```powershell
docker compose logs --tail 100
```

Stop:

```powershell
docker compose down
```

The local Docker architecture includes application services and infrastructure such as:

```text
PostgreSQL
Redis
Kafka
MinIO
Spark
FastAPI services
```

---

# 20. Kubernetes Deployment

The project has progressed from being merely Kubernetes-ready to having the core platform deployed and verified on a local Kubernetes cluster.

## Local Cluster

The cluster is created with:

```text
kind
```

Current cluster:

```text
finsightx
```

Namespace:

```text
finsightx
```

Control-plane node:

```text
finsightx-control-plane
```

---

## Kubernetes Components

The namespace currently contains deployments for:

```text
api-gateway
auth-service
customer-service
transaction-service
fraud-service
notification-service
audit-service
ml-service
kafka
minio
postgres
redis
prometheus
grafana
```

The core deployments were verified as:

```text
1/1 Running
```

during the implementation milestone.

---

## Kubernetes Services

Important service ports:

```text
api-gateway            8000
auth-service           8001
fraud-service          8004
notification-service   8005
audit-service          8006
ml-service             8008
customer-service       8009
transaction-service    8010
kafka                  9092
minio                  9000 / 9001
postgres               5432
redis                  6379
prometheus             9090
grafana                3000
```

The API Gateway also has a Kubernetes NodePort:

```text
30080
```

For the local kind environment, port-forwarding is the preferred and verified access method.

---

## Persistent Storage

Persistent volumes currently used include:

```text
minio-pvc      10Gi
postgres-pvc    5Gi
```

Some development infrastructure such as Redis, Kafka, Prometheus and Grafana uses ephemeral storage in the current local setup.

---

# 21. Helm

FinSightX now includes a Helm chart:

```text
infrastructure/helm/finsightx
```

The chart contains:

```text
Chart.yaml
values.yaml
templates/
_helpers.tpl
.helmignore
```

The chart defines configuration for:

- Application images
- PostgreSQL
- Redis
- Kafka
- MinIO
- JWT configuration
- ML configuration
- Services
- Replicas
- Resources
- Storage
- Monitoring
- Secrets

Validate the chart:

```powershell
helm lint .\infrastructure\helm\finsightx
```

The chart passed Helm linting.

---

## Helm Deployment

The platform was successfully adopted/upgraded through Helm:

```powershell
helm upgrade --install finsightx .\infrastructure\helm\finsightx `
    --namespace finsightx `
    --force-conflicts
```

Result:

```text
Release "finsightx" has been upgraded.
STATUS: deployed
REVISION: 2
```

This means Kubernetes resources are now managed as part of the FinSightX Helm release rather than existing only as manually applied manifests.

---

# 22. Terraform and Infrastructure

Terraform is included under:

```text
infrastructure/terraform
```

The purpose is to demonstrate Infrastructure-as-Code concepts and provide a path toward cloud infrastructure.

The current project intentionally remains local-first.

The architecture is designed so that infrastructure components can later be mapped to cloud equivalents.

---

# 23. Testing and Verification

The repository contains:

```text
tests/
├── unit/
├── integration/
├── load/
└── security/
```

Testing areas include:

- REST APIs
- Authentication
- Authorization
- Fraud rules
- ML inference
- Database operations
- Kafka events
- Redis state
- End-to-end processing
- Integration flows
- Security behavior
- Observability

---

## Verified End-to-End ML Flow

A complete transaction was successfully verified through:

```text
Transaction
    |
    v
Kafka
    |
    v
Fraud Service
    |
    +----> Redis velocity
    |
    +----> Rule engine
    |
    +----> ML Service
              |
              v
        Random Forest
              |
              v
        Fraud Assessment
              |
              v
          PostgreSQL
              |
              v
        fraud.assessed
```

---

## Verified Authentication and RBAC Flow

The gateway authentication path was verified using an ADMIN account.

The platform successfully demonstrated:

```text
Login
  ↓
JWT generation
  ↓
Gateway authentication
  ↓
Role verification
  ↓
Authorized operation
```

---

## Verified Notification Flow

A high-risk transaction produced a high-risk notification record.

Example notification classification:

```text
HIGH_RISK_ALERT
URGENT
HIGH
```

---

## Verified Audit Flow

A gateway transaction generated an audit record containing:

```text
gateway user
ADMIN role
CREATE_TRANSACTION
SUCCESS
```

---

## Verified Kafka Consumer Health

The notification consumer was checked and its consumer-group lag reached:

```text
0
```

after successful processing.

---

# 24. Project Structure

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
│   │   └── finsightx/
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

# 25. Local Docker Setup

## Prerequisites

Recommended tools:

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

---

## Clone

```powershell
git clone https://github.com/Suriya1903/FinSightX.git
cd FinSightX
```

---

## Python Environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## Environment

Copy:

```text
.env.example
```

to:

```text
.env
```

Configure local values as required.

Never commit real credentials.

---

## Start Docker

```powershell
docker compose up -d --build
```

Check:

```powershell
docker compose ps
```

---

## Verify ML Service

```powershell
Invoke-RestMethod `
  -Uri http://localhost:8008/health `
  -Method GET
```

Then:

```powershell
Invoke-RestMethod `
  -Uri http://localhost:8008/ready `
  -Method GET
```

The readiness response verifies that the model has been loaded.

---

## Test ML Prediction

Example request:

```powershell
$body = @{
    amount = 75000
    amount_band_code = 3
    is_high_risk_merchant_category = 1
    has_device = 1
    has_location = 1
    customer_is_active = 1
    is_inr = 1
    is_pending = 1
    transaction_hour = 22
    transaction_day_of_week = 2
    is_weekend = 0
    is_night_transaction = 1
    transaction_velocity = 1
    recent_transaction_amount = 75000
    high_velocity_amount = 75000
    merchant_category = "Crypto"
    currency = "INR"
    transaction_status = "PENDING"
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri http://localhost:8008/api/v1/predict `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```

---

# 26. Kubernetes Setup

## Create Cluster

```powershell
kind create cluster --name finsightx
```

Verify:

```powershell
kubectl cluster-info --context kind-finsightx
```

---

## Create Namespace

```powershell
kubectl create namespace finsightx
```

---

## Verify Namespace

```powershell
kubectl get pods -n finsightx
kubectl get svc -n finsightx
kubectl get deployments -n finsightx
```

---

## Helm

From the repository root:

```powershell
helm lint .\infrastructure\helm\finsightx
```

Install/upgrade:

```powershell
helm upgrade --install finsightx .\infrastructure\helm\finsightx `
    --namespace finsightx `
    --force-conflicts
```

Verify:

```powershell
helm list -n finsightx
```

---

## Port Forwarding

### API Gateway

```powershell
kubectl port-forward service/api-gateway 8000:8000 -n finsightx
```

### Prometheus

```powershell
kubectl port-forward service/prometheus 9090:9090 -n finsightx
```

### Grafana

```powershell
kubectl port-forward service/grafana 3000:3000 -n finsightx
```

Use:

```text
127.0.0.1
```

for local access when port-forwarding.

---

# 27. Useful Verification Commands

## Kubernetes

```powershell
kubectl get pods -n finsightx
```

```powershell
kubectl get deployments -n finsightx
```

```powershell
kubectl get services -n finsightx
```

```powershell
kubectl get pvc -n finsightx
```

```powershell
kubectl get events -n finsightx --sort-by=.lastTimestamp
```

---

## Logs

Gateway:

```powershell
kubectl logs deployment/api-gateway -n finsightx --tail=100
```

Fraud:

```powershell
kubectl logs deployment/fraud-service -n finsightx --tail=100
```

ML:

```powershell
kubectl logs deployment/ml-service -n finsightx --tail=100
```

---

## Prometheus

After port-forwarding:

```text
http://127.0.0.1:9090
```

Example PromQL:

```promql
finsightx_fraud_events_processed_total
```

```promql
finsightx_fraud_assessments_total
```

```promql
finsightx_ml_predictions_total
```

```promql
finsightx_fraud_processing_failures_total
```

Average fraud processing duration:

```promql
rate(finsightx_fraud_processing_duration_seconds_sum[5m])
/
rate(finsightx_fraud_processing_duration_seconds_count[5m])
```

---

## Grafana

After port-forwarding:

```text
http://127.0.0.1:3000
```

The Grafana dashboard can be used to observe:

```text
API traffic
HTTP status codes
API latency
Fraud events
Fraud risk levels
ML predictions
ML risk levels
Processing failures
Fraud latency
Service health
```

---

# 28. Current Verified Results

The following major flows have been verified during development.

## 1. Real-Time Fraud Detection

A high-value Crypto transaction was processed through:

```text
Kafka
  ↓
Fraud Service
  ↓
Redis
  ↓
Rule Engine
  ↓
ML Service
  ↓
PostgreSQL
  ↓
fraud.assessed
```

---

## 2. Machine Learning

The Random Forest model was trained and deployed successfully.

Verified:

```text
Training
   ↓
Model artifact
   ↓
ML Service
   ↓
HTTP inference
   ↓
Fraud Service
```

---

## 3. Spark + MinIO

Verified:

```text
Kafka
  ↓
Spark Structured Streaming
  ↓
MinIO raw
  ↓
MinIO processed
```

with Parquet output and checkpoints.

---

## 4. Warehouse

Verified:

```text
MinIO processed Parquet
  ↓
Spark ETL
  ↓
PostgreSQL analytics
```

---

## 5. Power BI

Verified:

```text
PostgreSQL analytics
  ↓
Power BI
  ↓
Risk Dashboard
```

---

## 6. Authentication and RBAC

Verified:

```text
Login
  ↓
JWT
  ↓
API Gateway
  ↓
ADMIN authorization
  ↓
Successful operation
```

---

## 7. Notification and Audit

Verified:

```text
fraud.assessed
   |
   +----> Notification
   |
   +----> Audit
```

A high-risk notification and a successful administrative audit record were observed.

---

## 8. Observability

Verified:

```text
Gateway/Fraud
    ↓
/metrics
    ↓
Prometheus
    ↓
Grafana
```

Metrics for successful fraud processing, ML predictions, risk levels, failures, and processing latency were observed.

---

## 9. Kubernetes

Verified local cluster:

```text
kind cluster : finsightx
namespace    : finsightx
```

Core deployments were running successfully.

---

## 10. Helm

Verified:

```text
helm lint          -> passed
helm upgrade/install -> deployed
release status     -> deployed
```

The Helm release is:

```text
finsightx
```

---

# 29. Engineering Highlights

FinSightX demonstrates:

- Distributed system design
- Microservice architecture
- Event-driven architecture
- REST API development
- API Gateway pattern
- JWT authentication
- RBAC
- Kafka-based asynchronous communication
- Redis-based real-time velocity detection
- Redis idempotency
- Rule-based fraud detection
- Machine-learning fraud detection
- Dedicated ML inference service
- Feature engineering
- Random Forest classification
- Synthetic-data evaluation
- MLflow experiment tracking
- Spark Structured Streaming
- MinIO/S3-compatible data lake
- Parquet processing
- Data-quality processing
- PostgreSQL analytical warehouse
- Star-schema modeling
- ETL pipelines
- Power BI business analytics
- Notification processing
- Audit logging
- Retry and DLQ concepts
- Prometheus instrumentation
- Grafana dashboards
- Docker multi-container deployment
- Kubernetes deployment
- kind local cluster
- Helm packaging and release management
- Terraform/IaC structure
- Persistent Kubernetes storage
- Health/readiness checks
- End-to-end integration verification
- Git/GitHub version control
- CI/CD-ready repository

---

# 30. Future Enhancements

The current platform is a strong local implementation, but several production-grade extensions remain possible.

## ML / MLOps

- Production model registry and promotion
- Automated model retraining
- Model drift monitoring
- Model explainability
- Better model calibration
- Real-world fraud datasets
- Real-time feature store
- Stronger online/offline feature consistency
- Automated model validation

## Event Architecture

- Transactional outbox pattern
- Kafka Schema Registry
- Stronger event contracts
- More advanced event versioning
- Exactly-once processing where appropriate

## Fraud Engine

- More advanced rule/ML score combination
- Explainable fraud reasons
- Customer behavior baselines
- Geographic anomaly detection
- Device fingerprinting
- Cross-customer risk signals

## Kubernetes

- Horizontal Pod Autoscaling
- Production-grade ingress
- Network policies
- Resource limits tuning
- Kubernetes secrets management
- Multi-node production cluster
- Rolling deployment strategies

## Observability

- More service metrics
- Distributed tracing
- Centralized logging
- Alertmanager
- SLO/SLA dashboards
- Error-budget monitoring

## CI/CD

- Automated image builds
- Automated tests in GitHub Actions
- Container vulnerability scanning
- Helm deployment pipelines
- Automated Kubernetes deployment
- Environment promotion

## Data Engineering

- Advanced data-quality monitoring
- Data lineage
- Schema evolution
- More warehouse dimensions
- Incremental ETL improvements
- Larger-scale analytics

## Cloud

The platform can later be mapped to cloud services such as:

```text
Managed Kubernetes
Managed Kafka
Object Storage
Managed PostgreSQL
Managed Redis
Cloud Monitoring
Cloud ML services
```

The current implementation deliberately avoids requiring paid cloud services.

---

# 31. Author

**Suriya MG**

B.Tech Computer Science and Engineering  
Vellore Institute of Technology

GitHub:

```text
https://github.com/Suriya1903/FinSightX
```

---

# Final Project Summary

FinSightX brings together a complete financial technology architecture:

```text
                         FIN SIGHT X
                              |
        +---------------------+---------------------+
        |                     |                     |
        v                     v                     v
   Microservices         Event Streaming        Security
        |                     |                     |
        v                     v                     v
   FastAPI APIs            Kafka                JWT/RBAC
        |                     |
        +----------+----------+
                   |
                   v
            Fraud Detection
             /           \
            v             v
         Redis           Rules
            \             /
             \           /
              v         v
                 ML
                  |
                  v
             Random Forest
                  |
                  v
           Fraud Assessment
                  |
                  v
             PostgreSQL
                  |
        +---------+---------+
        |                   |
        v                   v
   Analytics Warehouse    Operational Data
        |
        v
      Power BI

Parallel data engineering:

Kafka
  ↓
Spark
  ↓
MinIO
  ↓
Warehouse ETL
  ↓
PostgreSQL
  ↓
Power BI

Platform engineering:

Docker
  ↓
kind Kubernetes
  ↓
Helm
  ↓
Prometheus
  ↓
Grafana
```

The project therefore demonstrates much more than a fraud-detection model.

It demonstrates how to design, build, integrate, deploy, monitor, and analyze a distributed AI-powered financial platform using modern software engineering, data engineering, machine learning, security, and cloud-native technologies.

---

## Project Status

**Current status: Core implementation completed and locally verified across application, ML, streaming, warehouse, BI, security, observability, Kubernetes, and Helm layers.**

The repository is maintained as a local-first engineering project and is structured for further CI/CD and cloud deployment enhancements.
