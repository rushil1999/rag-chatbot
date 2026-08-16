# Rushil Shah at Procure Networks — Software Developer (September 2022 to November 2023)

Rushil Shah worked at Procure Networks from September 2022 to November 2023, overlapping with and
following his master's degree at San Jose State University. The role was full-stack, centered on
asset management and search: Kafka, MongoDB, Elasticsearch, GraphQL, and React with TypeScript.

## Sorting NoSQL documents by exterior fields, using Kafka

The core problem: sorting a MongoDB document collection by fields that live on *other* documents
(exterior fields) — something NoSQL stores do not do natively. Rushil solved it with an
event-driven approach. Kafka emits an event whenever any field on a document changes, and a
Node.js consumer service (communicating over gRPC in a microservice architecture) watches that
stream and propagates the update to every document where that field is used as an exterior sort
key. The denormalized sort keys stay current without expensive joins at query time.

## Centralized multi-vendor asset platform

Rushil helped build the system that lets users store, access, and share assets sourced from many
different vendors in one centralized database, along with the management and order-request
services layered on top of those items.

## Lookup aggregator — 20-25% latency reduction

Rushil achieved a 20-25% reduction in search latency by creating a lookup aggregator service. It
maintains a MongoDB cache of frequently accessed data, refreshed on a schedule by cron jobs
running GraphQL queries. Search reads hit the cache instead of fanning out across the inventory.
On the client side he used React with TypeScript and custom hooks to consume it.

## Vendor data normalization pipelines

Products arriving from different vendors used incompatible schemas. Rushil engineered data
pipelines that normalize them into a single standard mapping and index the result into an inverted
Elasticsearch index, making search and access consistent and fast across the whole catalog.

## Scheduled reminders

Rushil added a reminder feature giving users scheduled reminders about their asset items,
implemented with a polling service and scheduled jobs persisted in the database.
