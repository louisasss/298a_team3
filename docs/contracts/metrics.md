# Metrics Contract — ParcelPost /metrics

- Subject: the GET /metrics endpoint of the ParcelPost app (Prometheus text format)
- Consumer: T3-68 (implementation)
- Ratifiers: Pragya (analysis), Louisa (agent side)
- Status: Draft — open points are marked PROPOSED and are settled by ratification

## 1. The metrics

### 1.1 Request counter — http_requests_total
Labels: method, route, status, version.
Counts every HTTP request the app serves. status is the numeric code as a
string (PROPOSED: "200", "404", "500" — queries group errors with status=~"5..").

### 1.2 Latency histogram — http_request_duration_seconds
Labels: method, route, version (plus le, added by the histogram itself).
Records each request's duration in seconds into buckets.
PROPOSED bucket edges: 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0
(+Inf is automatic). Edges near the analysis p95 threshold may be added
at ratification.

### 1.3 Build info — parcelpost_build_info
Labels: version. Value is always 1; the label carries the identity.
version is the build's version string — the commit SHA for CI-built
images — and is the same string that /version reports (T3-69).

## 2. Label rules
- route is always the route template (e.g. /shipments/{shipment_id}),
  never the raw request path.
- No label value may be unbounded: no shipment ids, no tracking codes,
  no error messages. A label is allowed only if all its possible values
  can be listed in advance.
- The label sets in section 1 are complete. Adding a label is a change
  to this contract.

## 3. Version identity and the per-version split
PROPOSED mechanism: the app stamps its own version label on all three
families (the app knows its version; T3-69 gives it the string).
Every series therefore identifies its deployable, and queries keep the
stable and canary split by filtering or grouping on version.
Fallback, for an app that cannot stamp: the platform attaches the same
version label at scrape time. The label name and meaning do not change.

## 4. The decision queries this contract must support
Error rate per version (window shown is illustrative; the
AnalysisTemplates set the real window):

    sum by (version) (rate(http_requests_total{status=~"5.."}[2m]))
    /
    sum by (version) (rate(http_requests_total[2m]))

p95 latency per version:

    histogram_quantile(0.95, sum by (version, le) (rate(http_request_duration_seconds_bucket[2m])))

Traffic per version is the second query's denominator pattern without
the division. The classifier's features (error rate, latency, traffic,
per version) are these same quantities.

## 5. Out of scope
Thresholds are not part of this contract; they belong to the
AnalysisTemplates. How the endpoint is implemented (library or
hand-wired) is T3-68's choice, with one constraint: the emitted
metric names, labels, and semantics must match this contract exactly.

## 6. Changes
After ratification, changes to this contract are made by a PR amending
this file, approved by the same ratifiers.
