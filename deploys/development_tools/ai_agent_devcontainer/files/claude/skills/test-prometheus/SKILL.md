---
name: test-prometheus
description: Use when writing, changing, or debugging Prometheus alerting or recording rules, PrometheusRule manifests, or PromQL expressions; when alerts fire too early, too late, or not at all; or when validating rule syntax and alert behavior with promtool before deploying.
---

# Testing Prometheus rules

promtool from the prom/prometheus image (or a local promtool binary) validates rules in two layers:

1. `promtool check rules` parses the rule files and catches syntax and lint errors.
2. `promtool test rules` evaluates the rules against synthetic series and asserts which alerts fire at chosen times.

## Layer 1: syntax check

```bash
promtool check rules <file>.yml
```

With only Docker available, mount the directory and override the entrypoint:

```bash
docker run --rm -v "$PWD":/w --entrypoint promtool prom/prometheus check rules /w/<file>.yml
```

`check rules` accepts multiple rule files and reads from stdin when none are given. It expects a plain rules file whose top level is `groups:`. If the rules live in a Kubernetes PrometheusRule, strip the apiVersion/kind/metadata wrapper and pass only the `spec.groups` content. It validates parsing and lint, not PromQL evaluation semantics.

## Layer 2: behavioral test

```bash
promtool test rules test.yml
```

```bash
docker run --rm -v "$PWD":/w --entrypoint promtool prom/prometheus test rules /w/test.yml
```

The test file lists the rule files under `rule_files` (paths are relative to the test file), sets an `evaluation_interval`, and declares test groups with `input_series` (synthetic samples) and `alert_rule_test` assertions.

### Example: alert after a duration on a status change

`managedresource_status` is a gauge (value 1) labelled `managedresource`, `namespace`, `status`. The series is absent while the resource is healthy and present while it is not. This rule fires once the resource has been non-Ready for 5 minutes even if the status label changed in between, and labels the alert with the current status:

`rules.yml`:

```yaml
groups:
  - name: managedresource
    rules:
      - alert: ManagedResourceNotReady
        expr: max by (managedresource, namespace, status) (managedresource_status) and on (managedresource, namespace) (count_over_time(managedresource_status[5m]) >= 5)
        labels:
          severity: warning
        annotations:
          summary: "ManagedResource {{ $labels.managedresource }} in {{ $labels.namespace }} has status {{ $labels.status }}"
```

`test.yml`:

```yaml
rule_files:
  - rules.yml

evaluation_interval: 1m

tests:
  - name: fires after 5m of a changed status
    interval: 1m
    input_series:
      - series: 'managedresource_status{managedresource="app", namespace="default", status="TemplateError"}'
        values: '1x5 _x11'
      - series: 'managedresource_status{managedresource="app", namespace="default", status="ApplyError"}'
        values: '_x5 1x11'
    alert_rule_test:
      - eval_time: 2m
        alertname: ManagedResourceNotReady
        exp_alerts: []
      - eval_time: 12m
        alertname: ManagedResourceNotReady
        exp_alerts:
          - exp_labels:
              severity: warning
              managedresource: app
              namespace: default
              status: ApplyError
            exp_annotations:
              summary: "ManagedResource app in default has status ApplyError"

  - name: recovers when the series disappears
    interval: 1m
    input_series:
      - series: 'managedresource_status{managedresource="app", namespace="default", status="ApplyError"}'
        values: '1x20 _x10'
    alert_rule_test:
      - eval_time: 30m
        alertname: ManagedResourceNotReady
        exp_alerts: []
```

`values` uses expanding notation: `axn` repeats `a` n+1 times, `a+bxn` increments by `b`, `_` marks a missing sample and `stale` a stale sample. The first case feeds TemplateError from 0m to 5m then ApplyError, and asserts nothing at 2m (not long enough) and a firing alert at 12m labelled ApplyError. The second feeds 20 minutes of ApplyError then nothing, and asserts the alert is gone at 30m.

## Pitfall: duplicate series in a status-change join

A join that reads the current status with an arithmetic/group operator fails the moment the lookback contains both the old and the new status series:

```promql
count_over_time(managedresource_status[5m]) * on (managedresource, namespace) group_left(status) managedresource_status
```

`group_left` requires the right-hand side to be unique on the matching labels. During a status change both `status="TemplateError"` and `status="ApplyError"` exist in the lookback, so promtool fails with `found duplicate series ... on the right hand-side ... matching labels must be unique`.

Use a set operator instead, which has no uniqueness requirement:

```promql
max by (managedresource, namespace, status) (managedresource_status) and on (managedresource, namespace) (count_over_time(managedresource_status[5m]) >= 5)
```

Do not write `>= bool 5` here. `and` keeps a left-hand element whenever a matching right-hand element exists, ignoring the right-hand value. The `bool` modifier returns 0 or 1 for every series in the lookback instead of filtering, so the duration threshold would be silently ignored. Use a plain comparison (`>= 5`) so `count_over_time` is filtered before the `and`.

## What promtool does not test

`promtool test rules` validates parse and evaluation semantics against the synthetic series only. It does not test the live scrape interval, staleness handling, or Alertmanager routing and notification. A green run does not prove the rule behaves correctly under real scrape conditions.

## When to use

This skill loads when writing, changing, or debugging Prometheus alerting and recording rules.
