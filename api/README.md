# API contracts

The machine-readable contracts of the Ostler server (`src/openostler/web/server.py`),
adopted by [ADR-0017](../decisions/adr-0017-open-standards-first.md):

| File | Standard | What it covers |
|---|---|---|
| [`openapi.yaml`](openapi.yaml) | OpenAPI 3.1.1 (schemas are JSON Schema 2020-12) | Every HTTP route: parameters, request bodies, response schemas, errors, admin gating and public-mode behaviour |
| [`asyncapi.yaml`](asyncapi.yaml) | AsyncAPI 3.0 | The `GET /events` Server-Sent Events stream. MQTT channels arrive with U5 |

The UI's Zod schemas (`ui/src/api/schemas.ts`) remain what the browser checks at runtime.
These files describe the same contract for everyone else (integrations, tooling, reviews),
and the tests keep the three in step.

## Reading the files

- **`x-ostler-access`** on each operation: `public`, or `admin` (HTTP Basic auth, the
  `adminBasic` scheme; ungated when the server has no `--admin-password`).
- **`x-ostler-public-mode`**: what the `--public` server does with the route (`open`,
  `filtered` to the synthetic sessions, `refused` with 403, `hidden` as 404, or `partial`
  for `/command`).
- **`x-ostler-query-string: refused`**: the route is matched exactly, so `?anything`
  answers 404.
- **`x-ostler-route: static`**: served from the built app's `static/` directory.
- **`components.x-ostler-wire-conventions`**: the wire rules for every Ostler API:
  - RFC 3339 UTC `Z` timestamps;
  - COVESA VSS units ([ADR-0016](../decisions/adr-0016-covesa-vss-canonical-signal-namespace.md));
  - GeoJSON (RFC 7946) positions and traces;
  - `vid` on every session (U0-A, optional).

  The existing deviations (epoch seconds in the snapshot) are listed there so they can be
  migrated.
- `asyncapi.yaml` takes its payload by `$ref` from `openapi.yaml#/components/schemas/Snapshot`,
  so there is one snapshot definition.

## Viewing them locally

No tool is needed on the device. On a development machine, any of these works:

```bash
# Swagger UI in Docker, then open http://localhost:8081
docker run --rm -p 8081:8080 -e SWAGGER_JSON=/api/openapi.yaml -v "$PWD/api:/api" swaggerapi/swagger-ui

# Redocly: preview, or lint
npx @redocly/cli preview-docs api/openapi.yaml
npx @redocly/cli lint api/openapi.yaml

# AsyncAPI Studio in the browser, or the CLI
npx @asyncapi/cli validate api/asyncapi.yaml
npx @asyncapi/cli start studio api/asyncapi.yaml
```

The Swagger UI "Try it out" button works against a local dashboard once you add your
server URL (the default `servers` entry is `http://localhost:8080`).

## Keeping them current

`tests/test_api_contracts.py` (needs the `[dev]` extra, no pack, no hardware) fails when:

- `server.py` handles a route that `openapi.yaml` lacks, or `openapi.yaml` lists a route
  the server does not have. The routes are read from the server's source: the string
  literals `_Handler` compares `self.path` with, and the path parts the `/sessions/…`
  helpers compare with;
- an operation's admin gating or query-string handling differs from the server's;
- an operation lacks `x-ostler-access`, `x-ostler-public-mode`, a success response, a 401
  (admin) or a 403 (refused in public mode);
- `openapi.yaml` fails `openapi-spec-validator`, or `asyncapi.yaml` loses its structure;
- a committed UI fixture (`ui/src/api/fixtures/*.json`) does not validate against its
  documented response schema, or a new fixture has no mapping in `FIXTURE_ROUTES`.

When you change the server:

1. Add or change the route in `openapi.yaml`, and the stream in `asyncapi.yaml`. Keep
   response objects open (`additionalProperties: true`): clients ignore unknown fields.
2. When a response shape changes, regenerate the fixtures
   (`UPDATE_UI_FIXTURES=1 pytest tests/test_ui_contract.py`), update the Zod schema,
   then the OpenAPI schema. Add a new fixture to `FIXTURE_ROUTES` in the test.
3. Bump `info.version` in both files with the platform version (`openostler.__version__`).
4. Run `pytest -q`.
