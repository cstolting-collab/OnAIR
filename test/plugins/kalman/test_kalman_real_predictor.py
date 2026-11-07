"""Exercise missing telemetry with real simdkalman in a fresh interpreter.

The repository conftest replaces simdkalman with a mock in the pytest process.
The subprocess deliberately avoids that replacement without changing conftest.
These cases target PR #207's ingestion policy and preserve its predictor formula.
"""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

WORKER = """
import contextlib
import copy
import io
import json
import sys

import numpy as np
import simdkalman
from onair.services.service_manager import ServiceManager
from plugins.kalman.kalman_plugin import Plugin

assert isinstance(simdkalman.__file__, str), 'real simdkalman is required'
case = json.load(sys.stdin)
ServiceManager({})
p = Plugin('unequal-history-regression', case['headers'], window_size=5)
assert isinstance(p.kf, simdkalman.KalmanFilter)
with contextlib.redirect_stdout(io.StringIO()):
    for row in case['rows']:
        p.update(row)
before = copy.deepcopy(p.frames)
actual = p._generate_residuals()
reasoning = p.render_reasoning()
assert p.frames == before, 'rendering must not change retained histories'

# Reference: independent scalar calls to the dependency, retaining PR207's
# existing default-prior formula. PR205's numerical change is a separate scope.
reference = []
for history in before:
    if len(history) < 3:
        reference.append(0.0)
        continue
    kf = simdkalman.KalmanFilter(
        state_transition=[[1, 1], [0, 1]],
        process_noise=np.diag([0.1, 0.1]),
        observation_model=np.array([[1, 0]]),
        observation_noise=1.0,
    )
    predicted = kf.predict([history[1:-1]], 1).observations.mean[0, 0]
    reference.append(float(abs(predicted - history[-1])))
print(json.dumps({
    'lengths': list(map(len, before)),
    'residuals': actual.tolist(),
    'reference': reference,
    'reasoning': reasoning,
    'simdkalman_file': simdkalman.__file__,
    'plugin_file': sys.modules[Plugin.__module__].__file__,
}))
"""


@pytest.mark.parametrize(
    "headers, rows, lengths, expected_reasoning",
    [
        pytest.param(
            ["TIME", "SIGNAL"],
            [[1, "-"], [2, "-"], [3, "-"]],
            [3, 0],
            [],
            id="missing-second",
        ),
        pytest.param(
            ["TIME", "SIGNAL"],
            [["-", 10], ["-", 10], ["-", 100]],
            [0, 3],
            ["SIGNAL"],
            id="missing-first",
        ),
        pytest.param(
            ["TIME", "SIGNAL"],
            [[1, "-"], [2, 10], [3, 100]],
            [3, 2],
            [],
            id="short-second",
        ),
        pytest.param(
            ["TIME", "SIGNAL"],
            [[1, "-"], [2, "-"], [3, 10], [4, 11], [5, 100]],
            [5, 3],
            ["SIGNAL"],
            id="unequal-ready",
        ),
        pytest.param(
            ["TIME", "B", "C", "D"],
            [
                [1, "-", 10, "-"],
                [2, "-", 10, "-"],
                [3, 10, 10, 20],
                [4, 10, 10, 20],
                [5, 100, 100, 200],
            ],
            [5, 3, 5, 3],
            ["B", "C", "D"],
            id="interleaved-batches",
        ),
        pytest.param(
            ["TIME", "SIGNAL"], [["-", "-"]] * 3, [0, 0], [], id="all-invalid"
        ),
        pytest.param(
            ["TIME", "SIGNAL"],
            [[1, 10], [2, 11], [3, 100]],
            [3, 3],
            ["SIGNAL"],
            id="aligned-control",
        ),
        pytest.param(
            ["TIME", "SIGNAL"], [[1, 10], [2, 11]], [2, 2], [], id="warmup-control"
        ),
        pytest.param(
            ["TIME", "SIGNAL"],
            [[10**309, 10], [10**309, 10], [10**309, 100]],
            [0, 3],
            ["SIGNAL"],
            id="overflow-first",
        ),
        pytest.param(
            ["TIME", "SIGNAL"],
            [[1, 10], [2, 10], [3, -(10**309)], [4, 100]],
            [4, 3],
            ["SIGNAL"],
            id="overflow-between-valid-readings",
        ),
    ],
)
def test_real_predictor_with_missing_samples(
    headers, rows, lengths, expected_reasoning
):
    """Keep each residual at its header position and evaluate every ready channel."""
    root = Path(__file__).resolve().parents[3]
    completed = subprocess.run(
        [sys.executable, "-c", WORKER],
        cwd=root,
        input=json.dumps({"headers": headers, "rows": rows}),
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    result = json.loads(completed.stdout)
    assert result["lengths"] == lengths
    assert len(result["residuals"]) == len(headers)
    np.testing.assert_allclose(
        result["residuals"], result["reference"], rtol=1e-12, atol=1e-12
    )
    assert result["reasoning"] == expected_reasoning
    assert (
        Path(result["plugin_file"]).resolve()
        == (root / "plugins/kalman/kalman_plugin.py").resolve()
    )
