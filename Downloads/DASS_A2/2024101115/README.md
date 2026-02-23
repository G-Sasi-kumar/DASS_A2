# DASS Assignment 2 - Roll Number 2024101115

This submission is structured exactly in the required assignment layout:

- `whitebox/`
- `integration/`
- `blackbox/`

Repository link:
`https://github.com/G-Sasi-kumar/DASS_A2`

## Whitebox

White-box testing target: `MoneyPoly`

Run the lightweight whitebox entry point:

```bash
cd whitebox
python3 main.py
```

Run the whitebox tests:

```bash
cd whitebox
python3 -m pytest -q tests
```

## Integration

Integration target: `StreetRace Manager`

Run the integration demo entry point:

```bash
cd integration/code
python3 main.py
```

Run the integration tests:

```bash
cd integration/code
python3 -m pytest -q ../tests
```

## Blackbox

Black-box target: `QuickCart` REST API

Export the API base URL and then run the tests:

```bash
export QUICKCART_BASE_URL=http://127.0.0.1:8080
cd blackbox
python3 -m pytest -q tests
```

Optional environment variables:

- `QUICKCART_ROLL_NUMBER`
- `QUICKCART_USER_ID`

## Notes

- The hand-drawn diagram images are included in the corresponding `diagrams/` folders.
- The reports for each section are present as `report.pdf`.
- The automated test commands above assume `pytest` is installed in the active Python environment.
