# Copyright Amazon.com Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.

from typing import Any, Dict, Optional
from unittest.mock import Mock

import pytest

import braket.ir as ir
from braket.annealing import Problem, ProblemType
from braket.circuits import Circuit, FreeParameter
from braket.device_schema import DeviceCapabilities
from braket.devices import LocalSimulator, local_simulator
from braket.ir.openqasm import Program
from braket.simulator import BraketSimulator
from braket.task_result import AnnealingTaskResult, GateModelTaskResult
from braket.tasks import AnnealingQuantumTaskResult, GateModelQuantumTaskResult

GATE_MODEL_RESULT = GateModelTaskResult(
    **{
        "measurements": [[0, 0], [0, 0], [0, 0], [1, 1]],
        "measuredQubits": [0, 1],
        "taskMetadata": {
            "braketSchemaHeader": {"name": "braket.task_result.task_metadata", "version": "1"},
            "id": "task_arn",
            "shots": 100,
            "deviceId": "default",
        },
        "additionalMetadata": {
            "action": {
                "braketSchemaHeader": {"name": "braket.ir.jaqcd.program", "version": "1"},
                "instructions": [{"control": 0, "target": 1, "type": "cnot"}],
            },
        },
    }
)

ANNEALING_RESULT = AnnealingTaskResult(
    **{
        "solutions": [[-1, -1, -1, -1], [1, -1, 1, 1], [1, -1, -1, 1]],
        "solutionCounts": [3, 2, 4],
        "values": [0.0, 1.0, 2.0],
        "variableCount": 4,
        "taskMetadata": {
            "id": "task_arn",
            "shots": 100,
            "deviceId": "device_id",
        },
        "additionalMetadata": {
            "action": {
                "type": "ISING",
                "linear": {"0": 0.3333, "1": -0.333, "4": -0.333, "5": 0.333},
                "quadratic": {"0,4": 0.667, "0,5": -1.0, "1,4": 0.667, "1,5": 0.667},
            },
            "dwaveMetadata": {
                "activeVariables": [0],
                "timing": {
                    "qpuSamplingTime": 100,
                    "qpuAnnealTimePerSample": 20,
                    "qpuAccessTime": 10917,
                    "qpuAccessOverheadTime": 3382,
                    "qpuReadoutTimePerSample": 274,
                    "qpuProgrammingTime": 9342,
                    "qpuDelayTimePerSample": 21,
                    "postProcessingOverheadTime": 117,
                    "totalPostProcessingTime": 117,
                    "totalRealTime": 10917,
                    "runTimeChip": 1575,
                    "annealTimePerRun": 20,
                    "readoutTimePerRun": 274,
                },
            },
        },
    }
)


class DummyCircuitSimulator(BraketSimulator):
    def run(
        self,
        program: ir.jaqcd.Program,
        qubits: int,
        shots: Optional[int],
        inputs: Optional[Dict[str, float]],
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        self._shots = shots
        self._qubits = qubits
        return GATE_MODEL_RESULT

    @property
    def properties(self) -> DeviceCapabilities:
        return DeviceCapabilities.parse_obj(
            {
                "service": {
                    "executionWindows": [
                        {
                            "executionDay": "Everyday",
                            "windowStartHour": "11:00",
                            "windowEndHour": "12:00",
                        }
                    ],
                    "shotsRange": [1, 10],
                },
                "action": {
                    "braket.ir.openqasm.program": {
                        "actionType": "braket.ir.openqasm.program",
                        "version": ["1"],
                    },
                    "braket.ir.jaqcd.program": {
                        "actionType": "braket.ir.jaqcd.program",
                        "version": ["1"],
                    },
                },
                "deviceParameters": {},
            }
        )


class DummyJaqcdSimulator(BraketSimulator):
    def run(
        self, program: ir.jaqcd.Program, qubits: int, shots: Optional[int], *args, **kwargs
    ) -> Dict[str, Any]:
        if not isinstance(program, ir.jaqcd.Program):
            raise TypeError("Not a Jaqcd program")
        self._shots = shots
        self._qubits = qubits
        return GATE_MODEL_RESULT

    @property
    def properties(self) -> DeviceCapabilities:
        return DeviceCapabilities.parse_obj(
            {
                "service": {
                    "executionWindows": [
                        {
                            "executionDay": "Everyday",
                            "windowStartHour": "11:00",
                            "windowEndHour": "12:00",
                        }
                    ],
                    "shotsRange": [1, 10],
                },
                "action": {
                    "braket.ir.jaqcd.program": {
                        "actionType": "braket.ir.jaqcd.program",
                        "version": ["1"],
                    },
                },
                "deviceParameters": {},
            }
        )

    def assert_shots(self, shots):
        assert self._shots == shots

    def assert_qubits(self, qubits):
        assert self._qubits == qubits


class DummyProgramSimulator(BraketSimulator):
    def run(
        self,
        openqasm_ir: Program,
        shots: int = 0,
        batch_size: int = 1,
    ) -> GateModelTaskResult:
        return GATE_MODEL_RESULT

    @property
    def properties(self) -> DeviceCapabilities:
        return DeviceCapabilities.parse_obj(
            {
                "service": {
                    "executionWindows": [
                        {
                            "executionDay": "Everyday",
                            "windowStartHour": "00:00",
                            "windowEndHour": "23:59:59",
                        }
                    ],
                    "shotsRange": [1, 10],
                },
                "action": {
                    "braket.ir.openqasm.program": {
                        "actionType": "braket.ir.openqasm.program",
                        "version": ["1"],
                    }
                },
                "deviceParameters": {},
            }
        )


class DummyAnnealingSimulator(BraketSimulator):
    def run(self, problem: ir.annealing.Problem, *args, **kwargs) -> AnnealingTaskResult:
        return ANNEALING_RESULT

    @property
    def properties(self) -> DeviceCapabilities:
        return DeviceCapabilities.parse_obj(
            {
                "service": {
                    "executionWindows": [
                        {
                            "executionDay": "Everyday",
                            "windowStartHour": "11:00",
                            "windowEndHour": "12:00",
                        }
                    ],
                    "shotsRange": [1, 10],
                },
                "action": {
                    "braket.ir.annealing.problem": {
                        "actionType": "braket.ir.annealing.problem",
                        "version": ["1"],
                    }
                },
                "deviceParameters": {},
            }
        )


mock_circuit_entry = Mock()
mock_program_entry = Mock()
mock_jaqcd_entry = Mock()
mock_circuit_entry.load.return_value = DummyCircuitSimulator
mock_program_entry.load.return_value = DummyProgramSimulator
mock_jaqcd_entry.load.return_value = DummyJaqcdSimulator
local_simulator._simulator_devices = {
    "dummy": mock_circuit_entry,
    "dummy_oq3": mock_program_entry,
    "dummy_jaqcd": mock_jaqcd_entry,
}


def test_load_from_entry_point():
    sim = LocalSimulator("dummy_oq3")
    task = sim.run(Circuit().h(0).cnot(0, 1), 10)
    assert task.result() == GateModelQuantumTaskResult.from_object(GATE_MODEL_RESULT)


def test_run_gate_model():
    dummy = DummyProgramSimulator()
    sim = LocalSimulator(dummy)
    task = sim.run(Circuit().h(0).cnot(0, 1), 10)
    assert task.result() == GateModelQuantumTaskResult.from_object(GATE_MODEL_RESULT)


def test_run_gate_model_inputs():
    dummy = DummyProgramSimulator()
    dummy.run = Mock(return_value=GATE_MODEL_RESULT)
    sim = LocalSimulator(dummy)
    circuit = Circuit().rx(0, FreeParameter("theta"))
    task = sim.run(circuit, inputs={"theta": 2}, shots=10)
    dummy.run.assert_called_with(
        Program(
            source="\n".join(
                (
                    "OPENQASM 3.0;",
                    "input float theta;",
                    "bit[1] b;",
                    "qubit[1] q;",
                    "rx(theta) q[0];",
                    "b[0] = measure q[0];",
                )
            ),
            inputs={"theta": 2},
        ),
        10,
    )
    assert task.result() == GateModelQuantumTaskResult.from_object(GATE_MODEL_RESULT)


def test_run_jaqcd_only():
    dummy = DummyJaqcdSimulator()
    sim = LocalSimulator(dummy)
    task = sim.run(Circuit().h(0).cnot(0, 1), 10)
    dummy.assert_shots(10)
    dummy.assert_qubits(2)
    assert task.result() == GateModelQuantumTaskResult.from_object(GATE_MODEL_RESULT)


def test_run_program_model():
    dummy = DummyProgramSimulator()
    sim = LocalSimulator(dummy)
    task = sim.run(
        Program(
            source="""
qubit[2] q;
bit[2] c;

h q[0];
cnot q[0], q[1];

c = measure q;
"""
        )
    )
    assert task.result() == GateModelQuantumTaskResult.from_object(GATE_MODEL_RESULT)


@pytest.mark.xfail(raises=ValueError)
def test_run_gate_model_value_error():
    dummy = DummyCircuitSimulator()
    sim = LocalSimulator(dummy)
    sim.run(Circuit().h(0).cnot(0, 1))


def test_run_annealing():
    sim = LocalSimulator(DummyAnnealingSimulator())
    task = sim.run(Problem(ProblemType.ISING))
    assert task.result() == AnnealingQuantumTaskResult.from_object(ANNEALING_RESULT)


def test_registered_backends():
    assert LocalSimulator.registered_backends() == {"dummy", "dummy_oq3", "dummy_jaqcd"}


@pytest.mark.xfail(raises=TypeError)
def test_init_invalid_backend_type():
    LocalSimulator(1234)


@pytest.mark.xfail(raises=ValueError)
def test_init_unregistered_backend():
    LocalSimulator("foo")


@pytest.mark.xfail(raises=NotImplementedError)
def test_run_unsupported_type():
    sim = LocalSimulator(DummyCircuitSimulator())
    sim.run("I'm unsupported")


@pytest.mark.xfail(raises=NotImplementedError)
def test_run_annealing_unsupported():
    sim = LocalSimulator(DummyCircuitSimulator())
    sim.run(Problem(ProblemType.ISING))


@pytest.mark.xfail(raises=NotImplementedError)
def test_run_qubit_gate_unsupported():
    sim = LocalSimulator(DummyAnnealingSimulator())
    sim.run(Circuit().h(0).cnot(0, 1), 1000)


def test_properties():
    dummy = DummyCircuitSimulator()
    sim = LocalSimulator(dummy)
    expected_properties = dummy.properties
    assert sim.properties == expected_properties
