from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class TestType(Enum):
    BENIGN = "benign"
    MALICIOUS = "malicious"

@dataclass
class Test:
    id: str
    name: str
    test_type: TestType
    category: str
    command: str
    container_image: str = "ubuntu:latest"

@dataclass
class TestResult:
    test: Test
    executed_at: datetime
    duration_ms: float
    events_detected: list
    outcome: str = None
    performance_stats: dict = None
    falco_drops: float = 0.0
    tetragon_drops: float = 0.0

@dataclass
class SecurityEvent:
    source: str
    timestamp: datetime
    test_id: str
    rule_name: str
    raw_event: dict