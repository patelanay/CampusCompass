# Backend Testing

This test suite uses only Python standard library tooling:

- `unittest` for test execution
- `trace` for coverage summary

## Run tests

```bash
./backend/.venv/bin/python -m unittest discover -s backend/tests -p "test_*.py" -v
```

## Run coverage gate (95%+)

```bash
./backend/.venv/bin/python backend/tests/run_coverage.py --fail-under 95
```

The coverage gate is evaluated on these core modules:

- `backend/main.py`
- `backend/taskbar.py`
- `backend/campus_calendar.py`
- `backend/db_helpers.py`
- `backend/uf_schedule.py`
