"""Made-up test data. These are NOT real FDA records or real K-numbers' contents."""

RAW_510K = [
    {"k_number": "K240001", "device_name": "Demo Pulse Oximeter", "applicant": "Acme Med",
     "product_code": "dqa", "decision_date": "20240115", "decision_description": "Substantially Equivalent",
     "clearance_type": "Traditional",
     "openfda": {"device_class": "2", "regulation_number": "870.2700",
                 "medical_specialty_description": "Anesthesiology"}},
    {"k_number": "K240001", "device_name": "Demo Pulse Oximeter (dup)", "product_code": "DQA",
     "decision_date": "20240115"},
    {"k_number": "BAD123", "device_name": "No valid number"},
    {"k_number": "k240002", "device_name": "Demo Oximeter II", "applicant": "Beta Health",
     "product_code": "DQA", "decision_date": "not-a-date", "openfda": {}},
]

SUMMARY_PAGES = [
    "510(k) Summary K240001. Submitter: Acme Med. Device: Demo Pulse Oximeter.",
    "Predicate Device: The predicate device is the Example Oximeter cleared under K201234. "
    "A reference device, K199876, was used for the sensor comparison. "
    "Intended Use: The device is intended for spot-check measurement of functional oxygen "
    "saturation (SpO2) and pulse rate in adults.",
    "Technology: Two-wavelength red and infrared light absorption through the fingertip. "
    "Energy source: two AAA alkaline batteries. Materials: patient-contacting finger pad made of "
    "medical grade silicone. Performance testing: bench testing per ISO 80601-2-61 and a "
    "clinical desaturation study.",
]


class FakeLLM:
    """Returns a canned JSON answer and records what it was asked."""

    def __init__(self, response: dict):
        self.response = response
        self.calls = []

    def complete_json(self, system, user):
        self.calls.append((system, user))
        return self.response


class FakeSession:
    """Stands in for a neo4j session; stores each Cypher call."""

    def __init__(self, result=None):
        self.calls = []
        self.result = result or []

    def run(self, query, **params):
        self.calls.append((query, params))
        return self.result
