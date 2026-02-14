"""
Data ingestion - load validated JSON data into PostgreSQL.
"""

from typing import Any, Dict, List
from sqlalchemy.orm import Session

from src.database.models import (
    Facility, Driver, Truck, Shipment, BunkerLoad, LabSample,
    TransportCost, Payment, Alert
)
from src.database.connection import get_db


class DataIngestion:
    """Handles data ingestion into PostgreSQL."""
    
    def __init__(self, db_connection=None):
        """Initialize data ingestion."""
        self.db = db_connection or get_db()
    
    def ingest_facilities(self, facilities: Dict[str, Dict[str, Any]]) -> int:
        """
        Ingest facility data.
        
        Args:
            facilities: Dictionary of facility configurations
            
        Returns:
            Number of facilities created/updated
        """
        count = 0
        
        with self.db.get_session() as session:
            for code, facility_data in facilities.items():
                # Check if exists
                existing = session.query(Facility).filter_by(code=code).first()
                
                if existing:
                    # Update
                    existing.name_fa = facility_data.get('name_fa', '')
                    existing.name_en = facility_data.get('name_en', '')
                    existing.bunker_sheet_name = facility_data.get('bunker_sheet', '')
                    existing.truck_destination = facility_data.get('truck_dest', '')
                else:
                    # Create
                    facility = Facility(
                        code=code,
                        name_fa=facility_data.get('name_fa', ''),
                        name_en=facility_data.get('name_en', ''),
                        bunker_sheet_name=facility_data.get('bunker_sheet', ''),
                        truck_destination=facility_data.get('truck_dest', '')
                    )
                    session.add(facility)
                
                count += 1
        
        return count
    
    def ingest_drivers(self, drivers_data: Dict[str, Any]) -> int:
        """
        Ingest driver data.
        
        Args:
            drivers_data: Driver configuration with canonical names and aliases
            
        Returns:
            Number of drivers created/updated
        """
        count = 0
        canonical_drivers = drivers_data.get('canonical_drivers', {})
        
        with self.db.get_session() as session:
            for canonical_name, driver_info in canonical_drivers.items():
                # Check if exists
                existing = session.query(Driver).filter_by(canonical_name=canonical_name).first()
                
                if existing:
                    # Update
                    existing.aliases = driver_info.get('aliases', [])
                    existing.status = driver_info.get('status', 'active')
                else:
                    # Create
                    driver = Driver(
                        canonical_name=canonical_name,
                        aliases=driver_info.get('aliases', []),
                        status=driver_info.get('status', 'active')
                    )
                    session.add(driver)
                
                count += 1
        
        return count
    
    def ingest_shipments(self, shipments: List[Dict[str, Any]]) -> int:
        """
        Ingest truck shipment data.
        
        Args:
            shipments: List of shipment records
            
        Returns:
            Number of shipments created
        """
        count = 0
        
        with self.db.get_session() as session:
            for shipment_data in shipments:
                # Get or create facility
                facility_code = shipment_data.get('facility_code')
                facility = None
                if facility_code:
                    facility = session.query(Facility).filter_by(code=facility_code).first()
                
                # Get or create driver
                driver_info = shipment_data.get('driver_info', {})
                canonical_name = driver_info.get('canonical')
                driver = None
                if canonical_name:
                    driver = session.query(Driver).filter_by(canonical_name=canonical_name).first()
                    if not driver and not driver_info.get('is_known'):
                        # Create pending driver
                        driver = Driver(
                            canonical_name=canonical_name,
                            aliases=[driver_info.get('original', '')],
                            status='pending_review'
                        )
                        session.add(driver)
                        session.flush()
                
                # Get or create truck
                truck_number = shipment_data.get('truck_number')
                truck = None
                if truck_number:
                    truck = session.query(Truck).filter_by(number=truck_number).first()
                    if not truck:
                        truck = Truck(number=truck_number, status='active')
                        session.add(truck)
                        session.flush()
                
                # Create shipment
                shipment = Shipment(
                    date=shipment_data.get('date', ''),
                    receipt_number=shipment_data.get('receipt_number'),
                    tonnage_kg=shipment_data.get('tonnage_kg', 0),
                    destination=shipment_data.get('destination', ''),
                    cost_per_ton_rial=shipment_data.get('cost_per_ton_rial', 0),
                    total_cost_rial=shipment_data.get('total_cost_rial', 0),
                    notes=shipment_data.get('notes', ''),
                    facility_id=facility.id if facility else None,
                    driver_id=driver.id if driver else None,
                    truck_id=truck.id if truck else None
                )
                session.add(shipment)
                count += 1
        
        return count
    
    def ingest_bunker_loads(self, loads: List[Dict[str, Any]]) -> int:
        """
        Ingest bunker load data.
        
        Args:
            loads: List of bunker load records
            
        Returns:
            Number of loads created
        """
        count = 0
        
        with self.db.get_session() as session:
            for load_data in loads:
                # Get facility
                facility_code = load_data.get('facility_code')
                facility = None
                if facility_code:
                    facility = session.query(Facility).filter_by(code=facility_code).first()
                
                # Get or create driver
                driver_info = load_data.get('driver_info', {})
                canonical_name = driver_info.get('canonical')
                driver = None
                if canonical_name:
                    driver = session.query(Driver).filter_by(canonical_name=canonical_name).first()
                
                # Create load
                load = BunkerLoad(
                    date=load_data.get('date', ''),
                    tonnage_kg=load_data.get('tonnage_kg', 0),
                    cumulative_tonnage_kg=load_data.get('cumulative_tonnage_kg', 0),
                    transport_cost_rial=load_data.get('transport_cost_rial', 0),
                    sheet_name=load_data.get('sheet_name', ''),
                    facility_id=facility.id if facility else None,
                    driver_id=driver.id if driver else None
                )
                session.add(load)
                count += 1
        
        return count
    
    def ingest_lab_samples(self, samples: List[Dict[str, Any]]) -> int:
        """
        Ingest lab sample data.
        
        Args:
            samples: List of lab sample records
            
        Returns:
            Number of samples created
        """
        count = 0
        
        with self.db.get_session() as session:
            for sample_data in samples:
                sample_code = sample_data.get('sample_code', '')
                sheet_name = sample_data.get('sheet_name', '')
                
                # Check if sample already exists with the same code and sheet
                # This checks both existing DB records and pending inserts in the current session
                existing = session.query(LabSample).filter_by(
                    sample_code=sample_code,
                    sheet_name=sheet_name
                ).first()
                
                if existing:
                    # Skip duplicate (same sample code in the same sheet)
                    continue
                
                # Get facility
                facility_code = sample_data.get('facility_code')
                facility = None
                if facility_code:
                    facility = session.query(Facility).filter_by(code=facility_code).first()
                
                # Create sample
                sample = LabSample(
                    sample_code=sample_code,
                    sheet_name=sheet_name,
                    au_ppm=sample_data.get('au_ppm'),
                    au_detected=sample_data.get('au_detected', True),
                    below_detection_limit=sample_data.get('below_detection_limit', False),
                    sample_type=sample_data.get('sample_type', ''),
                    date=sample_data.get('date', ''),
                    year=sample_data.get('year', ''),
                    month=sample_data.get('month', ''),
                    day=sample_data.get('day', ''),
                    sample_number=sample_data.get('sample_number', ''),
                    is_special=sample_data.get('is_special', False),
                    facility_id=facility.id if facility else None
                )
                session.add(sample)
                # Flush to make this sample visible to subsequent queries in the same transaction
                session.flush()
                count += 1
        
        return count
    
    def ingest_alerts(self, alerts: List[Dict[str, Any]]) -> int:
        """
        Ingest validation alerts.
        
        Args:
            alerts: List of alert dictionaries
            
        Returns:
            Number of alerts created
        """
        count = 0
        
        with self.db.get_session() as session:
            for alert_data in alerts:
                alert = Alert(
                    level=alert_data.get('level', 'info'),
                    rule=alert_data.get('rule', ''),
                    message=alert_data.get('message', ''),
                    data=alert_data.get('data', {})
                )
                session.add(alert)
                count += 1
        
        return count
