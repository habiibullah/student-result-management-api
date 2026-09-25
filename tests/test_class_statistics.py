from app.services.result_service import calculate_class_statistics


def test_class_statistics_use_only_complete_results():
    results = {
        1: {
            "result_status": "COMPLETE",
            "average": 80.0,
        },
        2: {
            "result_status": "COMPLETE",
            "average": 60.0,
        },
        3: {
            "result_status": "INCOMPLETE",
            "average": None,
        },
    }

    statistics = calculate_class_statistics(results)

    assert statistics == {
        "highest_average": 80.0,
        "lowest_average": 60.0,
        "class_average": 70.0,
    }


def test_class_statistics_return_none_when_no_complete_results():
    results = {
        1: {
            "result_status": "INCOMPLETE",
            "average": None,
        },
        2: {
            "result_status": "INCOMPLETE",
            "average": None,
        },
    }

    statistics = calculate_class_statistics(results)

    assert statistics == {
        "highest_average": None,
        "lowest_average": None,
        "class_average": None,
    }


def test_class_statistics_handle_single_complete_result():
    results = {
        1: {
            "result_status": "COMPLETE",
            "average": 73.5,
        },
        2: {
            "result_status": "INCOMPLETE",
            "average": None,
        },
    }

    statistics = calculate_class_statistics(results)

    assert statistics == {
        "highest_average": 73.5,
        "lowest_average": 73.5,
        "class_average": 73.5,
    }


def test_class_statistics_round_class_average_to_two_decimal_places():
    results = {
        1: {
            "result_status": "COMPLETE",
            "average": 81.25,
        },
        2: {
            "result_status": "COMPLETE",
            "average": 70.10,
        },
        3: {
            "result_status": "COMPLETE",
            "average": 65.33,
        },
    }

    statistics = calculate_class_statistics(results)

    assert statistics["highest_average"] == 81.25
    assert statistics["lowest_average"] == 65.33
    assert statistics["class_average"] == 72.23
