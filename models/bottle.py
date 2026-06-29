from models.student import db

class Bottle(db.Model):

    __tablename__ = "bottles"

    barcode = db.Column(
        db.String(20),
        primary_key=True
    )

    brand = db.Column(db.String(100))

    size = db.Column(db.String(20))

    bottle_type = db.Column(db.String(20))

    points = db.Column(db.Integer)

