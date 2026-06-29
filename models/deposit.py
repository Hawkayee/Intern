from models.student import db
from datetime import datetime

class Deposit(db.Model):

    __tablename__ = "deposits"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    reg_no = db.Column(
        db.String(20),
        db.ForeignKey("students.reg_no")
    )

    barcode = db.Column(
        db.String(20),
        db.ForeignKey("bottles.barcode")
    )

    points_earned = db.Column(db.Integer)

    deposited_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )
