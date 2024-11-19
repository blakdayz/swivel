from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///bluetooth_tracking.db"
Base = declarative_base()


class Place(Base):
    """
    Represents a place entity.

    Attributes:
        id (int): Primary key, auto-incremented.
        name (str): Name of the place, cannot be null.
        latitude (float): Latitude of the place, optional.
        longitude (float): Longitude of the place, optional.
        description (str): Description of the place, optional.
    Methods:
        to_dict:
            Convert place data to a dictionary.
    """

    __tablename__ = "places"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    description = Column(String, nullable=True)

    def to_dict(self):
        """Convert place data to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "description": self.description,
        }


# SQLAlchemy setup
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


class PlaceService:
    """
    Provides services to manage places.
    """

    def __init__(self):
        self.session = Session()

    def create_place(
        self, name, latitude=None, longitude=None, description=None
    ):
        """Create a new place and save it to the database."""
        new_place = Place(
            name=name,
            latitude=latitude,
            longitude=longitude,
            description=description,
        )
        try:
            self.session.add(new_place)
            self.session.commit()
            return new_place
        except:
            self.session.rollback()
            raise

    def get_place_by_id(self, place_id: int):
        """Retrieve a place by its ID."""
        return self.session.query(Place).filter(Place.id == place_id).first()

    def list_places(self):
        """List all available places."""
        return self.session.query(Place).all()

    def update_place(
        self,
        place_id,
        name=None,
        latitude=None,
        longitude=None,
        description=None,
    ):
        """Update an existing place's details."""
        place = self.get_place_by_id(place_id)
        if place:
            if name:
                place.name = name
            if latitude:
                place.latitude = latitude
            if longitude:
                place.longitude = longitude
            if description:
                place.description = description
            self.session.commit()

    def delete_place(self, place_id):
        """Delete a place by its ID."""
        place = self.get_place_by_id(place_id)
        if place:
            self.session.delete(place)
            self.session.commit()

    def close(self):
        """Close the database session."""
        self.session.close()


if __name__ == "__main__":
    # Ensure tables are created
    Base.metadata.create_all(engine)
    place_service = PlaceService()
    new_place = place_service.create_place(
        "Alpha",
        latitude=30.267684688241992,
        longitude=-97.74599651245279,
        description="ZAZA",
    )
    for place in place_service.list_places():
        print(
            place.id,
            place.name,
            place.latitude,
            place.longitude,
            place.description,
        )
    place_service.delete_place(new_place.id)
    place_service.close()
