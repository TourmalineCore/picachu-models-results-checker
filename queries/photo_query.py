from domain.dal import create_session

from domain import PhotoIds


class CheckPhotoQuery:
    def __init__(self):
        pass

    def by_id(self, photo_id):
        current_session = create_session()
        try:

            return current_session \
                .query(PhotoIds) \
                .filter(PhotoIds.id == photo_id) \
                .one_or_none()

        finally:
            current_session.close()
