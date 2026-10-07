import pandas as pd
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from flask_login import login_required, current_user

from .. import db
from ..models import (
    User,
    Student,
    Question,
    Exam,
    ExamQuestion,
    Answer
)
from ..email_service import send_student_credentials


admin = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin"
)


def admin_required():

    if not current_user.is_authenticated:
        return False

    return current_user.role == "admin"


@admin.route("/dashboard")
@login_required
def dashboard():

    if not admin_required():
        return "Access Denied", 403

    student_count = Student.query.count()
    question_count = Question.query.count()
    exam_count = Exam.query.count()
    completed_exams = Exam.query.filter_by(
        status="completed"
    ).count()

    return render_template(
        "admin/dashboard.html",
        student_count=student_count,
        question_count=question_count,
        exam_count=exam_count,
        completed_exams=completed_exams
    )


@admin.route("/students/register", methods=["GET", "POST"])
@login_required
def register_student():

    if not admin_required():
        return "Access Denied", 403

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        college = request.form.get("college", "").strip()
        department = request.form.get("department", "").strip()
        branch = request.form.get("branch", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not all([
            name, email, phone, college, department,
            branch, username, password
        ]):
            flash("All student fields are required.", "danger")
            return redirect(url_for("admin.register_student"))

        existing_username = User.query.filter_by(
            username=username
        ).first()

        if existing_username:
            flash("Username already exists.", "danger")
            return redirect(url_for("admin.register_student"))

        existing_email = User.query.filter_by(
            email=email
        ).first()

        if existing_email:
            flash("Email address is already registered.", "danger")
            return redirect(url_for("admin.register_student"))

        user = User(
            username=username,
            email=email,
            role="student"
        )
        user.set_password(password)

        db.session.add(user)
        db.session.flush()

        student = Student(
            user_id=user.id,
            name=name,
            email=email,
            phone=phone,
            college=college,
            department=department,
            branch=branch
        )

        db.session.add(student)
        db.session.commit()

        # Email the credentials after the database transaction succeeds.
        sent, email_message = send_student_credentials(
            name=name,
            email=email,
            username=username,
            password=password
        )

        if sent:
            flash(
                f"Student {name} registered successfully. Login credentials were emailed to {email}.",
                "success"
            )
        else:
            flash(
                f"Student {name} was registered successfully, but the email could not be sent. {email_message}",
                "warning"
            )

        return redirect(url_for("admin.students"))

    return render_template("admin/register_student.html")


@admin.route("/students")
@login_required
def students():

    if not admin_required():
        return "Access Denied", 403

    students = Student.query.order_by(
        Student.id.desc()
    ).all()

    return render_template(
        "admin/students.html",
        students=students
    )


@admin.route("/students/clear-all", methods=["POST"])
@login_required
def clear_all_students():

    if not admin_required():
        return "Access Denied", 403

    students = Student.query.all()
    user_ids = [student.user_id for student in students]
    student_ids = [student.id for student in students]

    if student_ids:
        exams = Exam.query.filter(
            Exam.student_id.in_(student_ids)
        ).all()
        exam_ids = [exam.id for exam in exams]

        if exam_ids:
            Answer.query.filter(
                Answer.exam_id.in_(exam_ids)
            ).delete(synchronize_session=False)

            ExamQuestion.query.filter(
                ExamQuestion.exam_id.in_(exam_ids)
            ).delete(synchronize_session=False)

            Exam.query.filter(
                Exam.id.in_(exam_ids)
            ).delete(synchronize_session=False)

        Student.query.filter(
            Student.id.in_(student_ids)
        ).delete(synchronize_session=False)

    if user_ids:
        User.query.filter(
            User.id.in_(user_ids),
            User.role == "student"
        ).delete(synchronize_session=False)

    db.session.commit()

    flash(
        f"All student records were cleared ({len(student_ids)} students).",
        "success"
    )

    return redirect(url_for("admin.students"))


@admin.route("/questions/upload", methods=["GET", "POST"])
@login_required
def upload_questions():

    if not admin_required():
        return "Access Denied", 403

    if request.method == "POST":

        if "excel_file" not in request.files:
            flash("No Excel file selected.", "danger")
            return redirect(url_for("admin.upload_questions"))

        file = request.files["excel_file"]

        if file.filename == "":
            flash("Please select an Excel file.", "danger")
            return redirect(url_for("admin.upload_questions"))

        if not file.filename.lower().endswith(".xlsx"):
            flash("Only .xlsx Excel files are allowed.", "danger")
            return redirect(url_for("admin.upload_questions"))

        try:
            df = pd.read_excel(file)
        except Exception:
            flash("Unable to read the Excel file.", "danger")
            return redirect(url_for("admin.upload_questions"))

        required_columns = [
            "Question",
            "Option_A",
            "Option_B",
            "Option_C",
            "Option_D",
            "Correct_Answer",
            "Marks",
            "Category"
        ]

        missing_columns = [
            column for column in required_columns
            if column not in df.columns
        ]

        if missing_columns:
            flash(
                "Missing columns: " + ", ".join(missing_columns),
                "danger"
            )
            return redirect(url_for("admin.upload_questions"))

        imported = 0
        errors = []

        for index, row in df.iterrows():

            excel_row = index + 2

            question_text = str(row["Question"]).strip()
            option_a = str(row["Option_A"]).strip()
            option_b = str(row["Option_B"]).strip()
            option_c = str(row["Option_C"]).strip()
            option_d = str(row["Option_D"]).strip()
            correct_answer = str(
                row["Correct_Answer"]
            ).strip().upper()
            category = str(row["Category"]).strip()

            try:
                marks = int(row["Marks"])
            except (ValueError, TypeError):
                errors.append(
                    f"Row {excel_row}: Invalid marks."
                )
                continue

            if not question_text:
                errors.append(
                    f"Row {excel_row}: Question is empty."
                )
                continue

            if correct_answer not in ["A", "B", "C", "D"]:
                errors.append(
                    f"Row {excel_row}: Correct answer must be A, B, C or D."
                )
                continue

            question = Question(
                question_text=question_text,
                option_a=option_a,
                option_b=option_b,
                option_c=option_c,
                option_d=option_d,
                correct_answer=correct_answer,
                marks=marks,
                category=category
            )

            db.session.add(question)
            imported += 1

        db.session.commit()

        if imported:
            flash(
                f"{imported} questions imported successfully.",
                "success"
            )

        for error in errors:
            flash(error, "warning")

        return redirect(url_for("admin.questions"))

    return render_template("admin/upload_questions.html")


@admin.route("/questions")
@login_required
def questions():

    if not admin_required():
        return "Access Denied", 403

    questions = Question.query.order_by(
        Question.id.desc()
    ).all()

    return render_template(
        "admin/questions.html",
        questions=questions
    )


@admin.route("/questions/<int:question_id>/edit", methods=["GET", "POST"])
@login_required
def edit_question(question_id):

    if not admin_required():
        return "Access Denied", 403

    question = Question.query.get_or_404(question_id)

    if request.method == "POST":

        question_text = request.form.get(
            "question_text", ""
        ).strip()

        option_a = request.form.get("option_a", "").strip()
        option_b = request.form.get("option_b", "").strip()
        option_c = request.form.get("option_c", "").strip()
        option_d = request.form.get("option_d", "").strip()

        correct_answer = request.form.get(
            "correct_answer", ""
        ).strip().upper()

        category = request.form.get("category", "").strip()

        try:
            marks = int(request.form.get("marks", "2"))
        except ValueError:
            marks = 2

        if not all([
            question_text, option_a, option_b,
            option_c, option_d, category
        ]):
            flash("All question fields are required.", "danger")
            return render_template(
                "admin/edit_question.html",
                question=question
            )

        if correct_answer not in ["A", "B", "C", "D"]:
            flash("Correct answer must be A, B, C or D.", "danger")
            return render_template(
                "admin/edit_question.html",
                question=question
            )

        question.question_text = question_text
        question.option_a = option_a
        question.option_b = option_b
        question.option_c = option_c
        question.option_d = option_d
        question.correct_answer = correct_answer
        question.marks = marks
        question.category = category

        db.session.commit()

        flash(
            f"Question #{question.id} updated successfully.",
            "success"
        )

        return redirect(url_for("admin.questions"))

    return render_template(
        "admin/edit_question.html",
        question=question
    )


@admin.route("/questions/<int:question_id>/delete", methods=["POST"])
@login_required
def delete_question(question_id):

    if not admin_required():
        return "Access Denied", 403

    question = Question.query.get_or_404(question_id)

    # Keep historical exams/results safe. A question that has already
    # been assigned to an exam cannot be physically deleted.
    used_in_exam = ExamQuestion.query.filter_by(
        question_id=question.id
    ).first()

    has_answer = Answer.query.filter_by(
        question_id=question.id
    ).first()

    if used_in_exam or has_answer:
        flash(
            "This question is already linked to an exam/result and cannot be deleted. You can edit it instead.",
            "warning"
        )
        return redirect(url_for("admin.questions"))

    db.session.delete(question)
    db.session.commit()

    flash(
        f"Question #{question.id} deleted successfully.",
        "success"
    )

    return redirect(url_for("admin.questions"))


@admin.route("/results")
@login_required
def results():

    if not admin_required():
        return "Access Denied", 403

    exams = Exam.query.order_by(
        Exam.id.desc()
    ).all()

    results = []

    for exam in exams:

        student = Student.query.get(exam.student_id)

        results.append({
            "exam": exam,
            "student": student,
            "percentage": round(
                (exam.score or 0) / 100 * 100,
                1
            )
        })

    return render_template(
        "admin/results.html",
        results=results
    )


@admin.route("/results/clear-all", methods=["POST"])
@login_required
def clear_all_results():

    if not admin_required():
        return "Access Denied", 403

    answer_count = Answer.query.delete(
        synchronize_session=False
    )

    exam_question_count = ExamQuestion.query.delete(
        synchronize_session=False
    )

    exam_count = Exam.query.delete(
        synchronize_session=False
    )

    db.session.commit()

    flash(
        f"All exam results were cleared ({exam_count} exam attempts, "
        f"{answer_count} answers and {exam_question_count} exam-question records).",
        "success"
    )

    return redirect(url_for("admin.results"))
