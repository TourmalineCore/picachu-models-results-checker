
from models_results_checker.domain import PhotoIds
from models_results_checker.domain.data_access_layer.session import session


class CheckPhotoQuery:
    def __init__(self):
        pass

    def by_id(self, photo_id):
        current_session = session()
        try:
            return current_session \
                .query(PhotoIds) \
                .filter(PhotoIds.id == photo_id) \
                .one_or_none()

        finally:
            current_session.close()
