# Changelog

All notable changes to Freightline. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## Unreleased

### Added

- `freightline quote --format json` provides a stable machine-readable quote
  contract while preserving the default table output.

## [4.7.2] - 2026-08-19

### Fixed

- `POST /v1/webhooks/{carrier_code}` now verifies the HMAC over the raw request
  body instead of a re-serialised payload, which was rejecting valid Borealis
  deliveries whose JSON key order differed from ours.
- `freightline track` no longer crashes on a shipment with zero scan events.

## [4.7.1] - 2026-07-30

### Fixed

- Quote audit rows recorded the pre-surcharge total. They now record the total
  the customer was actually quoted.

## [4.7.0] - 2026-07-14

### Added

- `GET /v1/shipments` accepts `sort_by` and `direction`, validated against
  `SORTABLE_COLUMNS` and `SORT_DIRECTIONS`.
- Heavyweight handling surcharge for parcels over 30 kg.

### Changed

- **Breaking**: `Quote.total` is a string in API responses rather than a number,
  so clients stop round-tripping prices through floats. Clients parsing `total`
  as a number must parse it as a decimal string. Migration window closed
  2026-09-01.

### Security

- Admin reporting endpoints now fail closed when no admin token is configured,
  rather than serving unauthenticated.

## [4.6.0] - 2026-06-02

### Added

- Borealis Air joins the carrier panel (express and overnight).
- Canonical status vocabulary and `tracking/normalizer.py`, replacing the
  per-carrier status handling that had accumulated in the API layer.

### Internal

- `tests/test_carrier_contract.py` replaces the copy-pasted per-carrier test
  modules. Adding a carrier now produces an executable checklist.
