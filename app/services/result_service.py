from app.models.assessment import Assessment
from app.models.subject import Subject


def calculate_grade(total: float) -> str:
    if total >= 70:
        return "A"
    if total >= 60:
        return "B"
    if total >= 50:
        return "C"
    if total >= 45:
        return "D"
    if total >= 40:
        return "E"
    return "F"


def calculate_remark(average: float) -> str:
    if average >= 80:
        return "Excellent"
    if average >= 70:
        return "Very Good"
    if average >= 60:
        return "Good"
    if average >= 50:
        return "Satisfactory"
    if average >= 40:
        return "Needs Improvement"
    return "Poor"


def compute_student_term_result(
    student_id: int,
    assessments: list[Assessment],
    subjects_by_id: dict[int, Subject],
    scores_by_key: dict[tuple[int, int], float],
):
    grouped_assessments: dict[int, list[Assessment]] = {}

    for assessment in assessments:
        grouped_assessments.setdefault(
            assessment.subject_id,
            [],
        ).append(assessment)

    subject_results = []
    completed_totals = []

    for subject_id, subject_assessments in grouped_assessments.items():
        ca1 = None
        ca2 = None
        ca3 = None
        exam = None

        for assessment in subject_assessments:
            score = scores_by_key.get(
                (student_id, assessment.id)
            )

            if score is None:
                continue

            if (
                assessment.assessment_type == "CA"
                and assessment.sequence == 1
            ):
                ca1 = score

            elif (
                assessment.assessment_type == "CA"
                and assessment.sequence == 2
            ):
                ca2 = score

            elif (
                assessment.assessment_type == "CA"
                and assessment.sequence == 3
            ):
                ca3 = score

            elif assessment.assessment_type == "EXAM":
                exam = score

        is_complete = all(
            value is not None
            for value in [ca1, ca2, ca3, exam]
        )

        total = None
        grade = None
        status = "INCOMPLETE"

        if is_complete:
            total = ca1 + ca2 + ca3 + exam
            grade = calculate_grade(total)
            status = "COMPLETE"
            completed_totals.append(total)

        subject = subjects_by_id.get(subject_id)

        subject_results.append(
            {
                "subject_id": subject_id,
                "subject_name": (
                    subject.name
                    if subject is not None
                    else f"Subject {subject_id}"
                ),
                "ca1": ca1,
                "ca2": ca2,
                "ca3": ca3,
                "exam": exam,
                "total": total,
                "grade": grade,
                "status": status,
            }
        )

    number_of_subjects = len(subject_results)
    completed_subjects = len(completed_totals)

    result_status = (
        "COMPLETE"
        if (
            number_of_subjects > 0
            and completed_subjects == number_of_subjects
        )
        else "INCOMPLETE"
    )

    total_score = None
    average = None
    overall_grade = None
    remark = None

    if result_status == "COMPLETE":
        total_score = sum(completed_totals)

        average = (
            total_score / number_of_subjects
            if number_of_subjects > 0
            else None
        )

        if average is not None:
            overall_grade = calculate_grade(average)
            remark = calculate_remark(average)

    return {
        "subjects": subject_results,
        "total_score": total_score,
        "number_of_subjects": number_of_subjects,
        "completed_subjects": completed_subjects,
        "average": average,
        "overall_grade": overall_grade,
        "result_status": result_status,
        "remark": remark,
    }


def calculate_class_positions(
    student_results: dict[int, dict],
) -> dict[int, int]:
    complete_students = [
        (
            student_id,
            result["average"],
        )
        for student_id, result in student_results.items()
        if (
            result["result_status"] == "COMPLETE"
            and result["average"] is not None
        )
    ]

    complete_students.sort(
        key=lambda item: item[1],
        reverse=True,
    )

    positions: dict[int, int] = {}

    previous_average = None
    previous_position = None

    for index, (
        student_id,
        average,
    ) in enumerate(
        complete_students,
        start=1,
    ):
        if average == previous_average:
            position = previous_position
        else:
            position = index

        positions[student_id] = position

        previous_average = average
        previous_position = position

    return positions
