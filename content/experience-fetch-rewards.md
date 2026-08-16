# Rushil Shah at Fetch Rewards — Backend Engineer (November 2023 to February 2024)

Rushil Shah worked at Fetch Rewards as a Backend Engineer from November 2023 to February 2024,
between Procure Networks and Tesla. The work was Go (Golang) backend engineering at consumer
scale, on AWS.

## Receipt-scanning microservices at scale

Fetch Rewards scans millions of user receipts. Rushil worked on scaling that pipeline, building
microservices and processing stages in Go that handle validation, item-expiry checks, and data
normalization, then land the results in a Snowflake data lake. Splitting the stages into separate
services let each one scale independently with its own load profile.

## 314 GB migration — CPU utilization from 95% to 32%

The headline result from Rushil's time at Fetch Rewards: he managed the migration of 314 GB of
data out of AWS ElastiCache into a more compact representation and into DynamoDB. CPU utilization
dropped from 95% to 32%.

He ran the migration safely rather than as a big-bang cutover, using feature flags to shift
traffic incrementally and fallback paths so reads could still be served from the old store if the
new one missed. A 95% CPU system has no headroom for a failed migration, so the incremental
approach was the point.

## Legacy modernization and observability

Rushil upgraded legacy endpoints into microservices and optimized data flow with AWS Lambda
updates. He also improved monitoring and operational visibility using Grafana and AWS Elastic
Beanstalk, which made the system easier to reason about in production.
