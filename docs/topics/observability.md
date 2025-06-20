# Observability

> Measurement is the first step that leads to control and eventually to improvement. If you can't measure something, you can't understand it. If you can't understand it, you can't control it. If you can't control it, you can't improve it.
>
> &mdash; H. James Harrington

REST framework doesn't ship with built-in observability features, but there are many widely-used tools, standards and third party packages to choose from that work well with it. If your needs are simple, you can also implement your own.

## Custom request logging

You can implement a custom middleware that logs relevant information about handled API requests and responses using Python's builtin `logging` module.

```python
import logging
import time

logger = logging.getLogger('your_app.requests')

def request_logging_middleware(get_response):
    def middleware(request):
        start_time = time.time()
        response = get_response(request)
        duration = time.time() - start_time
        logger.info(f'{request.method} {request.path} - {response.status_code} {response.reason_phrase} - {int(duration*1000)}ms')
        return response
    return middleware
```

Then, add the middleware to your Django settings.

```python
MIDDLEWARE = [
    'your_app.middleware.request_logging_middleware',
    # ... other middleware
]
```

## Prometheus

[Prometheus](https://prometheus.io/) is an open-source monitoring system that collects metrics by scraping HTTP endpoints exposed by applications. It stores the data in a time series database and supports flexible querying and alerting.

For a REST framework project, Prometheus can be used to track metrics such as request counts, response codes, error rates, and latency. The [django-prometheus](https://pypi.org/project/django-prometheus/) package adds the necessary instrumentation and exposes a `/metrics` endpoint that Prometheus can scrape. You can also add your own application-specific metrics.

Prometheus can be paired with [Grafana](https://grafana.com/) to visualize metrics with interactive charts and dashboards.

## OpenTelemetry

[OpenTelemetry](https://opentelemetry.io/) is an open-source framework for collecting distributed traces and metrics from applications. It provides a vendor-neutral standard for instrumenting code and exporting telemetry data.

In Django applications, OpenTelemetry can be used to trace requests through views, middleware, and database operations. The [opentelemetry-instrumentation-django](https://pypi.org/project/opentelemetry-instrumentation-django/) package automatically instruments Django and integrates with the wider OpenTelemetry ecosystem.

The collected data can be exported to and visualized with any tool that supports OpenTelemetry, such as:

- Jaeger
- Grafana Tempo
- Datadog
- Elastic APM

## Other third party packages

### Apitally

[Apitally](https://apitally.io/) is a simple API monitoring, analytics, and request logging tool with an integration for Django REST framework. It provides intuitive dashboards with metrics and insights into API requests, errors, performance and consumers.

The [apitally](https://pypi.org/project/apitally/) package integrates with Django applications through middleware, which automatically captures metrics for API requests and responses, and synchronizes with Apitally in the background. See DRF-specific setup guide [here](https://docs.apitally.io/frameworks/django-rest-framework).

### django-health-check

[django-health-check](https://pypi.org/project/django-health-check/) provides a set of health check endpoints for Django applications. It allows you to monitor the status of various application components including database connections, cache backends, and custom services.

The library is helpful for production deployments as it enables load balancers, orchestration systems, and monitoring tools to determine application health. It supports both simple health checks and detailed status reporting for different application components.

### django-silk

[django-silk](https://pypi.org/project/django-silk/) is a profiling tool designed specifically for Django applications. It provides detailed insights into request performance, database queries, and custom code blocks or functions through context managers and decorators.

The package offers a web-based interface for analyzing requests, database queries, and profiling your code. It's particularly useful during development to identify performance bottlenecks before they reach production.

### Sentry

[Sentry](https://sentry.io/) is an error monitoring platform that provides real-time error tracking and performance monitoring for applications. It automatically captures exceptions, tracks performance issues, and provides detailed context to help debug problems in production.

For Django REST framework applications, Sentry can monitor API errors, slow endpoints, and database query performance. The [sentry-sdk](https://pypi.org/project/sentry-sdk/) package provides automatic instrumentation for Django views, middleware, and database operations.
