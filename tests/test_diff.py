from process_as_code.diff import semantic_diff


def test_semantic_diff_reports_changed_steps():
    old = {"process": {"id": "p", "name": "P"}, "steps": [{"id": "a", "name": "Old"}]}
    new = {"process": {"id": "p", "name": "P"}, "steps": [{"id": "a", "name": "New"}, {"id": "b", "name": "B"}]}
    result = semantic_diff(old, new)
    assert result["sections"]["steps"]["added"] == ["b"]
    assert result["sections"]["steps"]["changed"]["a"]["name"] == {"old": "Old", "new": "New"}
