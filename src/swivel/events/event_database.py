import datetime
from datetime import timezone

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    event_type = Column(
        Enum("ACCESS_POINT", "BLE_DEVICE", name="event_types")
    )  # Type of RF device detected
    bssid = Column(String)  # BSSID or MAC address of the device
    timestamp = Column(
        DateTime, default=timezone.utcnow
    )  # Timestamp when the event occurred

    place_id = Column(Integer, ForeignKey("places.id"))
    place = relationship(
        "Place", back_populates="events"
    )  # One-to-many relationship with Place


class Place(Base):
    __tablename__ = "places"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)  # Name of the place
    geotag_id = Column(Integer, ForeignKey("geotags.id"))

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    events = relationship(
        "Event", back_populates="place"
    )  # One-to-many relationship with Event


# Adding the relationships in GeoTag if needed
class GeoTag(Base):
    __tablename__ = "geotags"

    id = Column(Integer, primary_key=True)
    bssid = Column(String, unique=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    places = relationship("Place", back_populates="geotag")


class EvilTwinEvent(Event):
    __tablename__ = "evil_twin_events"

    id = Column(Integer, ForeignKey("events.id"), primary_key=True)

    # Specific fields for evil twin events
    ssid = Column(String)  # Service Set Identifier of the network

    __mapper_args__ = {
        "polymorphic_identity": "EVIL_TWIN",
        "inherits": Event,
    }


class BLEDeviceEvent(Event):
    __tablename__ = "ble_device_events"

    id = Column(Integer, ForeignKey("events.id"), primary_key=True)

    # Specific fields for BLE device events
    device_name = Column(String)  # Name of the BLE device (e.g., Flipper)

    __mapper_args__ = {
        "polymorphic_identity": "BLE_DEVICE",
        "inherits": Event,
    }


if __name__ == "__main__":
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    engine = create_engine("sqlite:///event_data.db", echo=True)

    Base.metadata.create_all(engine)  # Create all tables in the database

    session = Session(bind=engine)

    # Example data insertion for an evil twin event
    geotag1 = GeoTag(bssid="00:11:22:33:44:55")
    place1 = Place(name="Apartment building 8", geotag=geotag1)

    session.add(geotag1)
    session.add(place1)

    # Detecting an evil twin network
    evil_twin_event = EvilTwinEvent(event_type="EVIL_TWIN", bssid="00:23:45")
