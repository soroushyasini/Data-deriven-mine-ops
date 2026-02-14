"""
Database models for PostgreSQL storage using SQLAlchemy ORM.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, JSON, ForeignKey, Text, Date
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Facility(Base):
    """Grinding facilities."""
    __tablename__ = 'facilities'
    
    id = Column(Integer, primary_key=True)
    code = Column(String(1), unique=True, nullable=False)  # A, B, C
    name_fa = Column(String(100), nullable=False)
    name_en = Column(String(100), nullable=False)
    bunker_sheet_name = Column(String(100))
    truck_destination = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    shipments = relationship("Shipment", back_populates="facility")
    bunker_loads = relationship("BunkerLoad", back_populates="facility")
    lab_samples = relationship("LabSample", back_populates="facility")


class Driver(Base):
    """Driver registry with canonical names."""
    __tablename__ = 'drivers'
    
    id = Column(Integer, primary_key=True)
    canonical_name = Column(String(100), unique=True, nullable=False)
    aliases = Column(JSON)  # Array of name variants
    status = Column(String(20), default='active')  # active, pending_review
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    shipments = relationship("Shipment", back_populates="driver")
    bunker_loads = relationship("BunkerLoad", back_populates="driver")
    payments = relationship("Payment", back_populates="driver")


class Truck(Base):
    """Truck registry."""
    __tablename__ = 'trucks'
    
    id = Column(Integer, primary_key=True)
    number = Column(String(20), unique=True, nullable=False)
    status = Column(String(20), default='active')  # active, inactive
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    shipments = relationship("Shipment", back_populates="truck")


class Shipment(Base):
    """Mine → Grinding facility truck shipments."""
    __tablename__ = 'shipments'
    
    id = Column(Integer, primary_key=True)
    date = Column(String(10), nullable=False)  # Jalali date YYYY/MM/DD
    receipt_number = Column(String(50))
    tonnage_kg = Column(Float, nullable=False)
    destination = Column(String(100), nullable=False)
    cost_per_ton_rial = Column(Float)
    total_cost_rial = Column(Float)
    notes = Column(Text)
    
    # Foreign keys
    facility_id = Column(Integer, ForeignKey('facilities.id'))
    driver_id = Column(Integer, ForeignKey('drivers.id'))
    truck_id = Column(Integer, ForeignKey('trucks.id'))
    
    # Relationships
    facility = relationship("Facility", back_populates="shipments")
    driver = relationship("Driver", back_populates="shipments")
    truck = relationship("Truck", back_populates="shipments")
    
    created_at = Column(DateTime, default=datetime.utcnow)


class BunkerLoad(Base):
    """Grinding facility → Factory bunker loads."""
    __tablename__ = 'bunker_loads'
    
    id = Column(Integer, primary_key=True)
    date = Column(String(10), nullable=False)  # Jalali date YYYY/MM/DD
    tonnage_kg = Column(Float, nullable=False)
    cumulative_tonnage_kg = Column(Float)
    transport_cost_rial = Column(Float)
    sheet_name = Column(String(100))
    
    # Foreign keys
    facility_id = Column(Integer, ForeignKey('facilities.id'))
    driver_id = Column(Integer, ForeignKey('drivers.id'))
    
    # Relationships
    facility = relationship("Facility", back_populates="bunker_loads")
    driver = relationship("Driver", back_populates="bunker_loads")
    
    created_at = Column(DateTime, default=datetime.utcnow)


class LabSample(Base):
    """Lab analysis samples."""
    __tablename__ = 'lab_samples'
    
    id = Column(Integer, primary_key=True)
    sample_code = Column(String(50), unique=True, nullable=False)
    sheet_name = Column(String(100))
    
    # Gold content
    au_ppm = Column(Float)
    au_detected = Column(Boolean, default=True)
    below_detection_limit = Column(Boolean, default=False)
    
    # Parsed sample code fields
    sample_type = Column(String(50))  # K, L, T, CR, RC - widened from 10 to 50
    date = Column(String(10))  # Jalali date YYYY/MM/DD
    year = Column(String(4))
    month = Column(String(2))
    day = Column(String(2))
    sample_number = Column(String(10))
    is_special = Column(Boolean, default=False)
    
    # Foreign key
    facility_id = Column(Integer, ForeignKey('facilities.id'))
    
    # Relationships
    facility = relationship("Facility", back_populates="lab_samples")
    
    created_at = Column(DateTime, default=datetime.utcnow)


class TransportCost(Base):
    """Transport cost records (costs change over time)."""
    __tablename__ = 'transport_costs'
    
    id = Column(Integer, primary_key=True)
    route = Column(String(50), nullable=False)  # mine_to_grinding, grinding_to_factory
    cost_per_ton_rial = Column(Float, nullable=False)
    valid_from = Column(String(10))  # Jalali date
    valid_to = Column(String(10))  # Jalali date
    
    # Optional facility-specific costs
    facility_id = Column(Integer, ForeignKey('facilities.id'))
    
    created_at = Column(DateTime, default=datetime.utcnow)


class Payment(Base):
    """Driver payment records."""
    __tablename__ = 'payments'
    
    id = Column(Integer, primary_key=True)
    date = Column(String(10), nullable=False)  # Jalali date
    amount_rial = Column(Float, nullable=False)
    payment_type = Column(String(20), nullable=False)  # owed, paid
    notes = Column(Text)
    
    # Foreign key
    driver_id = Column(Integer, ForeignKey('drivers.id'))
    
    # Relationships
    driver = relationship("Driver", back_populates="payments")
    
    created_at = Column(DateTime, default=datetime.utcnow)


class Alert(Base):
    """Alert history."""
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True)
    level = Column(String(20), nullable=False)  # info, warning, critical
    rule = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    data = Column(JSON)
    acknowledged = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    acknowledged_at = Column(DateTime)
