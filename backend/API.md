# API Documentation

Base URL: `http://localhost:5001`

Interactive Swagger UI: `http://localhost:5001/docs`

---

## Endpoints

### GET /health

Lightweight health check.

**Response:**
```json
{
  "status": "ok",
  "model": "ggml-org/Clef-Flash-GGUF:Q4_K_M"
}
```

---

### POST /api/discharge

Disposition assessment — should the patient be discharged?

**Request:**
```json
{
  "report": "Fictional, de-identified emergency department narrative..."
}
```

**Response:**
```json
{
  "model": "/models/clef-flash-q4_k_m.gguf",
  "answers": {
    "discharge": {
      "type": "noul",
      "noul": 0.0118
    },
    "severity": {
      "type": "score",
      "score": 2.5954,
      "legend": {
        "0": "Minor - can be treated as outpatient",
        "1": "Moderate - needs observation or short stay",
        "2": "Serious - requires admission or intensive treatment",
        "3": "Critical - life-threatening, immediate intervention needed"
      },
      "probabilities": {
        "0": 0.0036,
        "1": 0.0346,
        "2": 0.3247,
        "3": 0.6371
      },
      "confidence": 0.5954
    },
    "risk_factors": {
      "type": "choice",
      "choice": "cardiac",
      "probabilities": {
        "cardiac": 0.9255,
        "infectious": 0.0089,
        "neurological": 0.0065,
        "none": 0.0292,
        "respiratory": 0.0189,
        "trauma": 0.0109
      },
      "confidence": 0.9107
    }
  },
  "usage": {
    "input_tokens": 522,
    "output_tokens": 0
  }
}
```

**Field descriptions:**

| Field | Type | Description |
|---|---|---|
| `discharge.noul` | float | Probability the patient should **not** be discharged (0 = discharge, 1 = admit). No `confidence` field for this type. |
| `severity.score` | float | Weighted average of severity indices (0-3). Add 1 to map to 1-4 scale. |
| `severity.probabilities` | object | Probability distribution over the 4 severity levels. |
| `severity.confidence` | float | Model confidence in the severity prediction (0-1). |
| `risk_factors.choice` | string | Most likely risk factor category. |
| `risk_factors.probabilities` | object | Probability distribution over risk factor categories. |
| `risk_factors.confidence` | float | Model confidence in the risk factor prediction (0-1). |

---

### POST /api/priority

ESI-oriented triage estimate.

**Request:**
```json
{
  "report": "Fictional, de-identified emergency department narrative..."
}
```

**Response:**
```json
{
  "model": "/models/clef-flash-q4_k_m.gguf",
  "answers": {
    "priority": {
      "type": "score",
      "score": 1.8504,
      "legend": {
        "0": "1 - ESI-1: immediate life-saving intervention required",
        "1": "2 - ESI-2: high risk, severe pain, or severe distress",
        "2": "3 - ESI-3: stable; multiple resources expected",
        "3": "4 - ESI-4: stable; one resource expected",
        "4": "5 - ESI-5: stable; no resources expected"
      },
      "probabilities": {
        "0": 0.0618,
        "1": 0.2682,
        "2": 0.4671,
        "3": 0.1637,
        "4": 0.0392
      },
      "confidence": 0.4717
    },
    "triage_category": {
      "type": "choice",
      "choice": "esi_3",
      "probabilities": {
        "esi_1": 0.0411,
        "esi_2": 0.2301,
        "esi_3": 0.4189,
        "esi_4": 0.2710,
        "esi_5": 0.0389
      },
      "confidence": 0.2737
    },
    "resource_needs": {
      "type": "choice",
      "choice": "moderate",
      "probabilities": {
        "critical": 0.0162,
        "extensive": 0.0466,
        "minimal": 0.0668,
        "moderate": 0.8420,
        "none": 0.0283
      },
      "confidence": 0.8025
    }
  },
  "usage": {
    "input_tokens": 522,
    "output_tokens": 0
  }
}
```

**Field descriptions:**

| Field | Type | Description |
|---|---|---|
| `priority.score` | float | Weighted average of ESI indices (0-4). Add 1 to map to ESI 1-5. |
| `priority.probabilities` | object | Probability distribution over the 5 ESI levels. |
| `priority.confidence` | float | Model confidence in the priority prediction (0-1). |
| `triage_category.choice` | string | Most likely ESI category (`esi_1` through `esi_5`). |
| `triage_category.probabilities` | object | Probability distribution over ESI categories. |
| `triage_category.confidence` | float | Model confidence in the triage category (0-1). |
| `resource_needs.choice` | string | Most likely resource level (`none`, `minimal`, `moderate`, `extensive`, `critical`). |
| `resource_needs.probabilities` | object | Probability distribution over resource levels. |
| `resource_needs.confidence` | float | Model confidence in the resource prediction (0-1). |

---

### GET /api/examples/search

Search example files by keyword (case-insensitive, recursive).

**Query parameters:**
- `q` (string, required) — keyword to search for.

**Response:**
```json
{
  "results": [
    {
      "file": "cases/case_001_p1_senior_expressive_stemi.txt",
      "context": "Patient: 32-year-old male Chief Complaint: Chest pain for 1 hour..."
    }
  ]
}
```

---

### GET /api/examples/file

Get the full content of an example file.

**Query parameters:**
- `path` (string, required) — relative path to the file (e.g., `cases/case_001.txt`).

**Response:**
```json
{
  "content": "Patient: 32-year-old male\nChief Complaint: Chest pain for 1 hour\n..."
}
```

---

## Error codes

| Code | Meaning |
|---|---|
| 422 | Invalid request (missing or invalid `report` field). |
| 502 | Inference service error or unavailable. |
| 504 | Inference service timed out. |
| 404 | Example file not found. |

---

## Notes

- The `score` field for `priority` and `severity` is a weighted average of the indices in `legend`, not a direct ESI/severity level. Add 1 to convert to the 1-based scale.
- `probabilities` and `confidence` are independent outputs from the model. `probabilities` shows the distribution across categories; `confidence` is a single certainty value.
- The `noul` type (discharge) does not return a `confidence` field. Use `Math.abs(noul - 0.5) * 2` as an implicit confidence proxy.
