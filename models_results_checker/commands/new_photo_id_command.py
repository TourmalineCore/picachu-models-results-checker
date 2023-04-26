from models_results_checker.domain import PhotoIds
from models_results_checker.domain.data_access_layer.session import session


class NewPhotoIdCommand:
    def __init__(self):
        pass

    @staticmethod
    def add_photo_id(photo_id_entity: PhotoIds) -> int:
        current_session = session()

        try:
            current_session.add(photo_id_entity)
            current_session.commit()
            return photo_id_entity.id

        finally:
            current_session.close()
