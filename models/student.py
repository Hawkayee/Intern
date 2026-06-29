from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Student(db.Model):

    __tablename__ = "students"

    reg_no = db.Column(
        db.String(20),
        primary_key=True
    )

    name = db.Column(
        db.String(100)
    )

    student_class = db.Column(
        db.String(20)
    )

    total_points = db.Column(
        db.Integer,
        default=0
    )
