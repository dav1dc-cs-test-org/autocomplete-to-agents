# ADR-0002: Zones are derived from postal bands, not a published matrix

- **Status**: accepted, with known limits
- **Date**: 2026-01-22

## Context

Every carrier publishes a zone matrix: a table mapping an origin/destination
postal pair to a billing zone. Atlas publishes a 42,000-row CSV. Borealis
publishes a PDF. Pigeon publishes nothing and answers by email.

Ingesting three incompatible matrices, keeping them fresh, and reconciling them
when they disagree is a project. We needed quotes working in two weeks.

## Decision

`rating/zones.py` maps a postal code to a coarse numeric band and computes the
zone as the distance between the origin and destination bands, clamped to 1–8.
International lanes get a floor so a cross-border move never prices as local.

This is an approximation and is documented as one.

## Consequences

- Zone resolution is symmetric and deterministic, which makes it testable and
  makes a quote reproducible from its audit row.
- We are wrong at the edges — a lane that crosses a band boundary by twenty miles
  can price a zone high or low. Measured against a sample of 500 Atlas
  invoices, we were within one zone 96% of the time and exact 71% of the time.
- Carriers re-rate at pickup, so the customer is billed the carrier's number.
  Our error shows up as quote-to-invoice variance, not as an overcharge.
- Adding a country means adding a band anchor, which takes one line and is
  guessable — and that guessability is itself a risk.

## When to revisit

When quote-to-invoice variance exceeds 2% of billed revenue in a quarter, or when
a carrier starts billing from our quote rather than re-rating. At that point this
module becomes a table lookup with a loader per carrier, and
`resolve_zone(origin, destination)` keeps its signature.
