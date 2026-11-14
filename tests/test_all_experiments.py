"""
Comprehensive End-to-End Integration Test Suite for IARFMS (Experiments 1 - 7).
Run via: pytest tests/test_all_experiments.py -v
"""
import importlib
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db_core.relational_adapter import RelationalConnection
from exp1_relational_sql.exp1_runner import init_schema_and_seed, run_experiment_1
from exp2_advanced_mysql.exp2_runner import (
    fn_calculate_ticket_charge,
    setup_views_and_triggers,
    sp_book_flight_ticket,
    sp_generate_flight_passenger_manifest,
)


def test_experiment_1_relational_core():
    run_experiment_1()
    db = RelationalConnection()
    tables = [
        r["name"]
        for r in db.fetchall("SELECT name FROM sqlite_master WHERE type='table'")
    ]
    for required in ["Passengers", "Airports", "Aircraft", "Flights", "Reservations", "Payments", "Crew"]:
        assert required in tables, f"Missing required table {required}"

    # Verify TCL saved booking 1009 with SUCCESS payment 5010
    res = db.fetchall("SELECT Booking_Status FROM Reservations WHERE Reservation_ID = 1009")
    assert res and res[0]["Booking_Status"] == "CONFIRMED"
    pay = db.fetchall("SELECT Payment_Status FROM Payments WHERE Reservation_ID = 1009")
    assert len(pay) == 1 and pay[0]["Payment_Status"] == "SUCCESS"
    db.close()


def test_experiment_2_advanced_mysql():
    db = RelationalConnection()
    init_schema_and_seed(db)
    setup_views_and_triggers(db)

    # View check
    v_rows = db.fetchall("SELECT * FROM v_passenger_reservations WHERE Booking_Status = 'CONFIRMED'")
    assert len(v_rows) >= 6

    # Function check
    econ = fn_calculate_ticket_charge(db, "AI-202", "ECONOMY", 10)
    first_urgent = fn_calculate_ticket_charge(db, "AI-202", "FIRST", 2)
    assert first_urgent > econ * 3

    # Procedure check (Valid booking)
    ok, res_id, amt, _ = sp_book_flight_ticket(db, 103, "AI-202", "20A", "BUSINESS")
    assert ok and res_id > 0 and amt > 0

    # Trigger check (Duplicate seat rejected)
    ok_dup, _, _, msg_dup = sp_book_flight_ticket(db, 104, "AI-202", "12A", "ECONOMY")
    assert not ok_dup and "DUPLICATE_SEAT_ERROR" in msg_dup

    # Cursor manifest check
    manifest = sp_generate_flight_passenger_manifest(db, "AI-202")
    assert len(manifest) >= 3
    db.close()


def test_experiment_3_performance_indexing():
    mod = importlib.import_module("exp3_performance_tuning.03_benchmark_runner")
    mod.run_experiment_3()


def test_experiment_4_concurrency_acid_locks_deadlock_mvcc():
    mod = importlib.import_module("exp4_transaction_concurrency.exp4_runner")
    mod.run_experiment_4()


def test_experiment_5_redis_and_mongodb():
    from exp5_redis_mongodb.redis_cache_manager import get_redis_client
    from exp5_redis_mongodb.mongo_document_manager import get_mongo_db, seed_and_run_crud
    from exp5_redis_mongodb.mongo_aggregation_analytics import run_mongo_aggregation

    # Redis atomic seat hold + TTL expiry
    r, _ = get_redis_client()
    key = "seat_hold:TEST:1A"
    r.delete(key)
    assert r.set(key, "p101", ex=1, nx=True) is True
    assert r.set(key, "p102", ex=1, nx=True) is False
    time.sleep(1.1)
    assert r.get(key) is None
    assert r.set(key, "p102", ex=10, nx=True) is True
    r.delete(key)

    # MongoDB CRUD & Aggregation
    seed_and_run_crud()
    run_mongo_aggregation()
    mdb, _ = get_mongo_db()
    agg = list(mdb["passenger_bookings"].aggregate([{"$match": {"booking_status": "CONFIRMED"}}, {"$group": {"_id": "$flight_id", "cnt": {"$sum": 1}}}]))
    assert len(agg) >= 3


def test_experiment_6_cassandra_and_neo4j():
    from exp6_cassandra_neo4j.cassandra_telemetry_runner import EmbeddedCassandraCluster
    from exp6_cassandra_neo4j.neo4j_pathfinder import AirlinePropertyGraph

    cass = EmbeddedCassandraCluster()
    now = datetime(2026, 11, 12, 8, 0)
    cass.insert_flight_activity("AI-202", now, "SCHEDULED", "DEL", "OP1", {})
    cass.insert_flight_activity("AI-202", now + timedelta(minutes=30), "DEPARTED", "DEL", "OP2", {})
    logs = cass.select_by_flight_id("flight_activity_log", "AI-202")
    assert len(logs) == 2 and logs[0]["event_type"] == "DEPARTED"  # DESC clustering order

    pg = AirlinePropertyGraph()
    pg.add_airport("DEL", "IGI", "New Delhi")
    pg.add_airport("BLR", "KIA", "Bengaluru")
    pg.add_airport("MAA", "CIA", "Chennai")
    pg.add_aircraft(1, "A320neo", 180)
    pg.add_flight("AI-715", "DEL", "BLR", 1, datetime(2026, 11, 12, 13, 0), datetime(2026, 11, 12, 15, 45), 6000)
    pg.add_flight("AI-412", "BLR", "MAA", 1, datetime(2026, 11, 12, 17, 0), datetime(2026, 11, 12, 18, 15), 3200)
    routes = pg.find_connecting_flights("New Delhi", "Chennai")
    assert len(routes) == 1 and routes[0]["Flight_Sequence"] == "AI-715 -> AI-412"


def test_experiment_7_distributed_cluster():
    from exp7_distributed_databases.exp7_runner import run_experiment_7
    run_experiment_7()
