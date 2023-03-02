from models_results_checker.domain.data_access_layer.db import db


class PhotoIds(db.Model):
    __tablename__ = 'photo_id'

    id = db.Column(db.BigInteger, primary_key=True)

    def __repr__(self):
        return f'<Photo id: {self.id!r}>'