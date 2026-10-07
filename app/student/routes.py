from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    session,
    flash,
    
)

from flask_login import login_required, current_user
from datetime import datetime, timedelta

from .. import db

from ..models import (
    Student,
    Exam,
    Question,
    ExamQuestion,
    Answer
)

import random


student = Blueprint(
    "student",
    __name__,
    url_prefix="/student"
)


def student_required():

    if not current_user.is_authenticated:
        return False

    return current_user.role == "student"


@student.route("/dashboard")
@login_required
def dashboard():

    if not student_required():
        return "Access Denied", 403

    student_profile = Student.query.filter_by(
        user_id=current_user.id
    ).first()

    if not student_profile:
        return "Student profile not found.", 404

    return render_template(
        "student/dashboard.html",
        student=student_profile
    )


@student.route("/terms")
@login_required
def terms():

    if not student_required():
        return "Access Denied", 403

    return render_template(
        "student/terms.html"
    )
    

@student.route("/start-exam", methods=["GET", "POST"])
@login_required
def start_exam():

    if not student_required():
        return "Access Denied", 403

    # Student must submit the agreement form
    if request.method == "POST":

        agreed = request.form.get("agreed")

        if agreed != "yes":

            flash(
                "You must agree to the examination instructions.",
                "danger"
            )

            return redirect(
                url_for("student.terms")
            )

    else:

        # Do not allow direct GET access to start
        return redirect(
            url_for("student.terms")
        )

    student_profile = Student.query.filter_by(
        user_id=current_user.id
    ).first()

    if not student_profile:
        return "Student profile not found.", 404


    # Check whether this student already has an exam
    existing_exam = Exam.query.filter_by(
        student_id=student_profile.id
    ).first()


    if existing_exam:

        if existing_exam.status == "completed":

            return redirect(
                url_for("student.thank_you")
            )


        if existing_exam.status == "timeout":

            return redirect(
                url_for("student.thank_you")
            )


        if existing_exam.status == "in_progress":

            session["exam_id"] = existing_exam.id

            return redirect(
                url_for("student.exam")
            )


    # Get all available questions
    questions = Question.query.all()


    if len(questions) < 50:

        return (
            "The examination is not ready. "
            "At least 50 questions are required."
        )


    # Select exactly 50 questions
    selected_questions = random.sample(
        questions,
        50
    )


    # Create exam timing
    start_time = datetime.utcnow()

    end_time = start_time + timedelta(
        minutes=30
    )


    # Create exam record
    exam = Exam(

        student_id=student_profile.id,

        start_time=start_time,

        end_time=end_time,

        status="in_progress",

        score=0

    )


    db.session.add(exam)

    db.session.flush()


    # Assign the 50 questions
    for number, question in enumerate(
        selected_questions,
        start=1
    ):

        exam_question = ExamQuestion(

            exam_id=exam.id,

            question_id=question.id,

            question_number=number

        )

        db.session.add(exam_question)


    db.session.commit()


    # Store exam ID in session
    session["exam_id"] = exam.id


    # Go to examination
    return redirect(
        url_for("student.exam")
    )
    
    
@student.route("/exam")
@login_required
def exam():

    if not student_required():
        return "Access Denied", 403

    exam_id = session.get("exam_id")

    if not exam_id:
        return redirect(
            url_for("student.dashboard")
        )

    exam = Exam.query.get(exam_id)

    if not exam:
        return "Exam not found.", 404

    # Make sure this exam belongs to the
    # currently logged-in student
    student_profile = Student.query.filter_by(
        user_id=current_user.id
    ).first()

    if exam.student_id != student_profile.id:
        return "Access Denied", 403

    # Check whether time has expired
    now = datetime.utcnow()

    if now >= exam.end_time:

        exam.status = "timeout"

        db.session.commit()

        return redirect(
            url_for("student.timeout")
        )

    # Get assigned questions
    assigned_questions = ExamQuestion.query.filter_by(
        exam_id=exam.id
    ).order_by(
        ExamQuestion.question_number
    ).all()

    if not assigned_questions:
        return "No questions assigned.", 404

    # Current question
    question_number = request.args.get(
        "question",
        default=1,
        type=int
    )

    # Prevent invalid question numbers
    if question_number < 1:
        question_number = 1

    if question_number > len(assigned_questions):
        question_number = len(assigned_questions)

    current_assignment = assigned_questions[
        question_number - 1
    ]

    question = Question.query.get(
        current_assignment.question_id
    )

    # Check if this question was already answered
    existing_answer = Answer.query.filter_by(
        exam_id=exam.id,
        question_id=question.id
    ).first()

    return render_template(
        "student/exam.html",
        exam=exam,
        question=question,
        question_number=question_number,
        total_questions=len(assigned_questions),
        existing_answer=existing_answer
    )

@student.route("/exam/answer", methods=["POST"])
@login_required
def save_answer():

    if not student_required():
        return "Access Denied", 403

    exam_id = session.get("exam_id")

    if not exam_id:
        return redirect(
            url_for("student.dashboard")
        )

    exam = Exam.query.get(exam_id)

    if not exam:
        return "Exam not found.", 404

    # Verify student
    student_profile = Student.query.filter_by(
        user_id=current_user.id
    ).first()

    if exam.student_id != student_profile.id:
        return "Access Denied", 403

    # Server-side timer validation
    now = datetime.utcnow()

    if now >= exam.end_time:

        exam.status = "timeout"

        db.session.commit()

        return redirect(
            url_for("student.timeout")
        )

    question_id = request.form.get(
        "question_id",
        type=int
    )

    question_number = request.form.get(
        "question_number",
        type=int
    )

    selected_answer = request.form.get(
        "answer"
    )

    if not question_id:

        return "Invalid question.", 400

    # Check that this question belongs
    # to this exam
    assignment = ExamQuestion.query.filter_by(
        exam_id=exam.id,
        question_id=question_id
    ).first()

    if not assignment:

        return "Invalid question for this exam.", 403

    # Prevent changing an already submitted answer
    existing_answer = Answer.query.filter_by(
        exam_id=exam.id,
        question_id=question_id
    ).first()

    if existing_answer:

        return redirect(
            url_for(
                "student.exam",
                question=question_number + 1
            )
        )

    question = Question.query.get(question_id)

    if not question:

        return "Question not found.", 404

    is_correct = (
        selected_answer == question.correct_answer
    )

    marks = question.marks if is_correct else 0

    answer = Answer(
        exam_id=exam.id,
        question_id=question.id,
        selected_answer=selected_answer,
        is_correct=is_correct,
        marks=marks
    )

    db.session.add(answer)

    db.session.commit()

    # Last question
    if question_number >= 50:

        return redirect(
            url_for("student.submit_exam")
        )

    return redirect(
        url_for(
            "student.exam",
            question=question_number + 1
        )
    )


@student.route("/exam/submit")
@login_required
def submit_exam():

    if not student_required():
        return "Access Denied", 403

    exam_id = session.get("exam_id")

    if not exam_id:
        return redirect(
            url_for("student.dashboard")
        )

    exam = Exam.query.get(exam_id)

    if not exam:
        return "Exam not found.", 404

    student_profile = Student.query.filter_by(
        user_id=current_user.id
    ).first()

    if exam.student_id != student_profile.id:
        return "Access Denied", 403

    # Prevent duplicate submission
    if exam.status != "in_progress":

        return redirect(
            url_for("student.thank_you")
        )

    # Calculate score from saved answers
    answers = Answer.query.filter_by(
        exam_id=exam.id
    ).all()

    score = sum(
        answer.marks
        for answer in answers
    )

    exam.score = score

    exam.status = "completed"

    exam.end_time = datetime.utcnow()

    db.session.commit()

    session.pop("exam_id", None)

    return redirect(
        url_for("student.thank_you")
    )

@student.route("/timeout")
@login_required
def timeout():

    if not student_required():
        return "Access Denied", 403

    session.pop("exam_id", None)

    return render_template(
        "student/timeout.html"
    )


@student.route("/thank-you")
@login_required
def thank_you():

    if not student_required():
        return "Access Denied", 403

    return render_template(
        "student/thank_you.html"
    )