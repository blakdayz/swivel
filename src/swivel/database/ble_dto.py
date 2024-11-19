# ble_dto.py

from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    ForeignKey,
    Float,
    Index,
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class Device(Base):
    __tablename__ = "devices"

    id = Column(String, primary_key=True)
    name = Column(String)
    address = Column(String)
    geodata = Column(String)
    times_seen = Column(Integer, default=0)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)

    # Relationships
    seen_records = relationship(
        "Seen", back_populates="device", lazy="selectin"
    )
    places = relationship(
        "PlaceDevice", back_populates="device", lazy="selectin"
    )
    relocations = relationship(
        "Relocation", back_populates="device", lazy="selectin"
    )


class Place(Base):
    __tablename__ = "places"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    radius = Column(Float, default=50.0)

    # Relationships
    devices = relationship(
        "PlaceDevice", back_populates="place", lazy="selectin"
    )
    seen_records = relationship(
        "Seen", back_populates="place", lazy="selectin"
    )


class PlaceDevice(Base):
    __tablename__ = "place_devices"

    place_id = Column(Integer, ForeignKey("places.id"), primary_key=True)
    device_id = Column(String, ForeignKey("devices.id"), primary_key=True)
    times_seen = Column(Integer, default=1)

    # Relationships
    place = relationship("Place", back_populates="devices", lazy="selectin")
    device = relationship("Device", back_populates="places", lazy="selectin")


class Relocation(Base):
    __tablename__ = "relocations"

    id = Column(Integer, primary_key=True)
    device_id = Column(String, ForeignKey("devices.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    old_geodata = Column(String)
    new_geodata = Column(String)

    # Relationships
    device = relationship(
        "Device", back_populates="relocations", lazy="selectin"
    )


class Seen(Base):
    __tablename__ = "seen"

    id = Column(Integer, primary_key=True)
    device_id = Column(String, ForeignKey("devices.id"))
    place_id = Column(Integer, ForeignKey("places.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    rssi = Column(Integer)
    gatt_signature = Column(String)

    # Index for performance on gatt_signature
    __table_args__ = (Index("idx_gatt_signature", "gatt_signature"),)

    # Relationships
    device = relationship(
        "Device", back_populates="seen_records", lazy="selectin"
    )
    place = relationship(
        "Place", back_populates="seen_records", lazy="selectin"
    )
