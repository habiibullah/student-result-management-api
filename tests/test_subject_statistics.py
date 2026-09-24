from app.services.result_service import calculate_subject_statistics


def test_subject_average_and_positions_exclude_incomplete_results():
    results = {
        1: {
            "subjects": [
                {"subject_id": 10, "total": 80.0},
            ],
        },
        2: {
            "subjects": [
                {"subject_id": 10, "total": 60.0},
            ],
        },
        3: {
            "subjects": [
                {"subject_id": 10, "total": None},
            ],
        },
    }

    statistics = calculate_subject_statistics(results)

    assert statistics[10]["class_average"] == 70.0
    assert statistics[10]["positions"] == {1: 1, 2: 2}


def test_equal_subject_totals_share_position():
    results = {
        1: {"subjects": [{"subject_id": 10, "total": 90.0}]},
        2: {"subjects": [{"subject_id": 10, "total": 90.0}]},
        3: {"subjects": [{"subject_id": 10, "total": 70.0}]},
    }

    statistics = calculate_subject_statistics(results)

    assert statistics[10]["class_average"] == round(250 / 3, 2)
    assert statistics[10]["positions"] == {1: 1, 2: 1, 3: 3}


def test_subject_with_no_completed_results_has_no_average_or_positions():
    results = {
        1: {"subjects": [{"subject_id": 10, "total": None}]},
        2: {"subjects": [{"subject_id": 10, "total": None}]},
    }

    statistics = calculate_subject_statistics(results)

    assert statistics[10]["class_average"] is None
    assert statistics[10]["positions"] == {}
