from domain import PhotoIds
from domain.dal import create_session


class NewPhotoIdCommand:
    def __init__(self):
        pass

    @staticmethod
    def add_photo_id(photo_id_entity: PhotoIds) -> int:
        current_session = create_session()

        try:
            current_session.add(photo_id_entity)
            current_session.commit()
            return photo_id_entity.id

        finally:
            current_session.close()
