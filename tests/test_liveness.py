from process_as_code.validate import validate_process


def _process(steps, start="start"):
    return {
        "version": "0.2",
        "process": {"id": "liveness", "name": "Liveness", "start": start},
        "steps": steps,
    }


def _step(step_id, step_type="task", transitions=None):
    step = {"id": step_id, "name": step_id.replace("_", " ").title(), "type": step_type}
    if transitions is not None:
        step["transitions"] = [{"to": target} for target in transitions]
    return step


def test_terminating_retry_loop_is_not_reported_as_trapped():
    data = _process(
        [
            _step("start", transitions=["gate"]),
            _step("gate", "decision", ["retry", "done"]),
            _step("retry", transitions=["gate"]),
            _step("done", "end"),
        ]
    )

    result = validate_process(data)

    assert result.ok
    assert result.warnings == []


def test_reachable_trapped_cycle_is_distinct_from_unreachable_terminal():
    data = _process(
        [
            _step("start", transitions=["retry_a"]),
            _step("retry_a", transitions=["retry_b"]),
            _step("retry_b", transitions=["retry_a"]),
            _step("unused_end", "end"),
        ]
    )

    result = validate_process(data)

    assert result.ok
    assert "step 'unused_end' is unreachable from process start" in result.warnings
    assert "process has no reachable terminal step" in result.warnings
    assert "reachable step 'start' has no path to a terminal step" in result.warnings
    assert "reachable step 'retry_a' has no path to a terminal step" in result.warnings
    assert "reachable step 'retry_b' has no path to a terminal step" in result.warnings
    assert "trapped cycle component has no path to a terminal step: retry_a, retry_b" in result.warnings


def test_end_step_with_outgoing_transition_is_error():
    data = _process(
        [
            _step("start", "end", ["after"]),
            _step("after", "end"),
        ]
    )

    result = validate_process(data)

    assert not result.ok
    assert "end step 'start' must not declare outgoing transitions" in result.errors


def test_reachable_non_end_without_outgoing_transition_is_implicit_terminal_warning():
    result = validate_process(_process([_step("start")]))

    assert result.ok
    assert result.warnings == ["non-end step 'start' is an implicit terminal with no outgoing transition"]


def test_decision_with_only_one_branch_warns():
    data = _process(
        [
            _step("start", "decision", ["done"]),
            _step("done", "end"),
        ]
    )

    result = validate_process(data)

    assert result.ok
    assert "decision step 'start' has fewer than two outgoing branches" in result.warnings


def test_parallel_one_in_one_out_warns_but_split_and_join_do_not():
    weak = _process(
        [
            _step("start", transitions=["parallel"]),
            _step("parallel", "parallel", ["done"]),
            _step("done", "end"),
        ]
    )
    weak_result = validate_process(weak)
    assert "parallel step 'parallel' has neither multiple incoming nor multiple outgoing flows" in weak_result.warnings

    valid = _process(
        [
            _step("start", transitions=["split"]),
            _step("split", "parallel", ["left", "right"]),
            _step("left", transitions=["join"]),
            _step("right", transitions=["join"]),
            _step("join", "parallel", ["done"]),
            _step("done", "end"),
        ]
    )
    valid_result = validate_process(valid)
    assert valid_result.ok
    assert not [warning for warning in valid_result.warnings if "parallel step" in warning]
