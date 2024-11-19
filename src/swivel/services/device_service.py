from sqlalchemy import Column, Integer, String, ForeignKey, Float
from sqlalchemy.orm import relationship, Session
from swivel.database.ble_dto import Device


class DeviceService:
    """
    Provides operations to manage devices.
    """

    def __init__(self):
        self.session = Session()

    def create_device(self, address, name, place_id=None):
        """Create a new device and link it to a place."""
        try:
            new_device = Device(address=address, name=name, place_id=place_id)
            self.session.add(new_device)
            self.session.commit()
            return new_device
        except Exception as e:
            self.session.rollback()
            print(f"Failed to create device: {e}")

    def get_device_by_address(self, address):
        """Get a device by its address."""
        try:
            return (
                self.session.query(Device)
                .filter(Device.address == address)
                .first()
            )
        except Exception as e:
            print(f"Failed to get device: {e}")

    def update_device_place(self, device_id, place_id):
        """Update the place linked to a device."""
        try:
            device = (
                self.session.query(Device)
                .filter(Device.id == device_id)
                .first()
            )
            if device:
                device.place_id = place_id
                self.session.commit()
        except Exception as e:
            self.session.rollback()
            print(f"Failed to update device place: {e}")

    def delete_device(self, device_id):
        """Delete a device from the database."""
        try:
            device = (
                self.session.query(Device)
                .filter(Device.id == device_id)
                .first()
            )
            if device:
                self.session.delete(device)
                self.session.commit()
        except Exception as e:
            self.session.rollback()
            print(f"Failed to delete device: {e}")

    def close(self):
        """Close the database session."""
        self.session.close()


if __name__ == "__main__":

    device_service = DeviceService()
    device_service.create_device(
        name="DUMMY DEVICE", address="192.168.1.1", place_id=1
    )
