# Rushil Shah at InfluxData — Engineering Intern (June 2022 to August 2022)

Rushil Shah interned at InfluxData in the summer of 2022, between June and August. This is the
role where he worked in Elixir, and it is a good story to ask him about — it was a testing
infrastructure problem, not a feature problem.

## The problem

InfluxData used AWS Marketplace for user subscriptions, and AWS Marketplace is responsible for
onboarding roughly 70% of the company's user base. But testing anything that touched subscription
onboarding meant making real calls against AWS Marketplace — slow, and it burned API quota. The
team needed a way to test the integration locally without the AWS dependency.

## What Rushil built

Rushil created a local simulator of AWS Marketplace, written in Elixir with the Phoenix
framework — a functional language and stack he picked up for the project. The simulator stands in
for Marketplace during testing of the onboarding flow that serves 70% of InfluxData's users.

To make it faithful, he had to reproduce the surrounding messaging infrastructure locally as well:

- A queuing and notification service that sends user-registration messages to local queues during
  the subscription process.
- An architecture that dispatches notifications dynamically and polls the local queues at regular
  intervals — effectively duplicating AWS SNS and SQS behavior on a developer machine. The local
  queue environment ran on ElasticMQ inside a Docker container.

## The result

Rushil collaborated with the internal team to test user onboarding with no AWS Marketplace
dependency at all, making that testing process about 40% faster.
