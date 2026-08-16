# Rushil Shah at Shipmnts — Software Developer (December 2020 to June 2021)

Rushil Shah worked at Shipmnts, a logistics technology company, from December 2020 to June 2021.
The domain was live shipping-container tracking, and the work was heavily queue- and
scheduler-oriented: Redis, TypeScript/Node, React, Ruby on Rails, and AWS SES.

## Live container tracking

Rushil implemented a queue-based backend service that delivers live tracking data for containers
in transit, built on a subscription-based architecture so clients receive updates as they happen
rather than polling for them.

## Adaptive polling — 50% less API and resource consumption

Container positions come from external carrier APIs. Rushil programmed cron jobs to asynchronously
fetch and update that data on a schedule and store it in a NoSQL database. The clever part: the
polling interval is adjusted at runtime based on previous tracking data, so containers that are
moving predictably get polled less often. This cut API and resource consumption by 50%.

## Redis-backed distributed queues — 30% performance improvement

Rushil formulated a Redis-backed queue architecture that delegates large asynchronous tasks across
several queues, making the service distributed and improving performance and scalability by
about 30%.

## Email notification system

Rushil developed an email notification system letting clients send emails with subject, content,
and attachments pre-filled by the system. He then built an asynchronous job-processing service
that dynamically parses values from user data and dispatches the emails through AWS Simple Email
Service (SES). Email templates were stored as strings in the database rather than in code, so
they could be changed without a deploy.

## Gmail plugin

Rushil developed a Gmail plugin that lets users upload documents and kick off cloud processing
jobs on those files without leaving their Gmail inbox. He integrated Google scope rules to access
email metadata — attachments, subject, content, and labels — and send it onward via HTTP request.
