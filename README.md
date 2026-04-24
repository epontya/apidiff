# apidiff

Detects breaking changes between two OpenAPI spec versions and outputs a structured diff report.

---

## Installation

```bash
pip install apidiff
```

Or install from source:

```bash
git clone https://github.com/yourname/apidiff.git
cd apidiff && pip install -e .
```

---

## Usage

Compare two OpenAPI spec files and print a structured diff report:

```bash
apidiff old_spec.yaml new_spec.yaml
```

Output to JSON:

```bash
apidiff old_spec.yaml new_spec.yaml --format json --output report.json
```

Use as a library:

```python
from apidiff import compare

report = compare("old_spec.yaml", "new_spec.yaml")

for change in report.breaking_changes:
    print(f"[BREAKING] {change.description}")
```

### Example Output

```
[BREAKING] DELETE /users/{id} - endpoint removed
[BREAKING] POST /orders - required field 'customer_id' added to request body
[WARNING]  GET /products - response field 'price' type changed from integer to string
```

---

## Features

- Detects removed endpoints, changed methods, and modified request/response schemas
- Distinguishes breaking changes from non-breaking modifications
- Supports JSON and YAML OpenAPI specs (v3.0+)
- Outputs reports as plain text, JSON, or Markdown

---

## License

This project is licensed under the [MIT License](LICENSE).