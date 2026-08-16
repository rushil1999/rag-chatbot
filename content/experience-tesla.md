# Rushil Shah at Tesla — Software Development Engineer (February 2024 to present)

Tesla is Rushil Shah's current employer. He joined in February 2024 as a Software Development
Engineer and works primarily in Go (Golang) on backend services, with Elasticsearch, RabbitMQ,
and SQL databases.

Rushil is on the Sales Management Platform team, which builds the internal CRM that Tesla
Advisors use day to day. That context explains the shape of his work there: the users are
Tesla's own sales staff, so the wins are measured in advisor time saved and system reliability.

## Autosweep — configurable data retention

Rushil designed and built Autosweep, a service that clears out stale data according to business
retention rules. It saved Tesla Advisors roughly 33% of their time. He implemented it with
goroutines and scheduled cron jobs so sweeps run concurrently in the background.

The design decision he is proudest of here: the retention rules are driven by SQL queries stored
as configuration rather than compiled into the service. That means the business can change what
gets swept and when without waiting on a production release. This is a good example of how Rushil
thinks about operational cost, not just shipping the feature.

## Real-time email notification pipeline

Rushil engineered a real-time email notification feature at Tesla. Cron jobs poll data sources at
regular intervals, and matching events are asynchronously published as email payloads onto
RabbitMQ queues for downstream delivery. Doing the handoff asynchronously through a message queue
keeps the polling path fast and decouples notification delivery from detection.

## 40% reduction in Elasticsearch write errors

Tesla's services were hitting version-conflict errors when writing documents concurrently to
Elasticsearch. Rushil cut those write errors by 40% by building a retry mechanism with proper
error handling, randomized jitter to avoid thundering-herd retry storms, and asynchronous
execution using goroutines. The jitter detail matters — naive retries would have synchronized and
made the conflicts worse.

## Database transactions in request context — 20% CPU improvement

Services were opening a new database transaction for every individual database call within a
single request. Rushil changed this by storing the transaction in the request context using Go's
`context` package, so all database work in a request shares one transaction. This improved CPU
consumption by about 20% and substantially reduced load on the database.
