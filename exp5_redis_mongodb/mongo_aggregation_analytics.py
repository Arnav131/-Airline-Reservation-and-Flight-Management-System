"""
Experiment 5.3: MongoDB Aggregation Pipeline for Flight-Wise Passenger Statistics.
Computes passenger counts, baggage totals, average weight, and total revenue per flight.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.panel import Panel
from db_core.relational_adapter import render_table
from exp5_redis_mongodb.mongo_document_manager import get_mongo_db, seed_and_run_crud

console = Console()


def run_mongo_aggregation():
    console.print(Panel.fit("[bold cyan]5.3 MongoDB Aggregation Pipeline: Flight-Wise Passenger Statistics[/bold cyan]"))
    mdb, _ = get_mongo_db()
    bookings_col = mdb["passenger_bookings"]

    if not list(bookings_col.find({})):
        seed_and_run_crud()

    pipeline = [
        {"$match": {"booking_status": "CONFIRMED"}},
        {
            "$group": {
                "_id": "$flight_id",
                "Total_Passengers": {"$sum": 1},
                "Total_Bags": {"$sum": "$baggage.bags_count"},
                "Total_Baggage_Kg": {"$sum": "$baggage.total_weight_kg"},
                "Avg_Baggage_Kg": {"$avg": "$baggage.total_weight_kg"},
                "Total_Revenue": {"$sum": "$fare_paid"},
                "Meal_Preferences": {"$addToSet": "$preferences.meal"},
            }
        },
        {"$sort": {"Total_Revenue": -1}},
    ]

    agg_results = list(bookings_col.aggregate(pipeline))
    formatted = [
        {
            "Flight_ID": r["_id"],
            "Confirmed_Pax": r["Total_Passengers"],
            "Total_Bags": int(r["Total_Bags"]),
            "Total_Weight_Kg": r["Total_Baggage_Kg"],
            "Avg_Weight_Kg": r["Avg_Baggage_Kg"],
            "Revenue (INR)": r["Total_Revenue"],
            "Meal_Types": ", ".join(r["Meal_Preferences"]),
        }
        for r in agg_results
    ]
    render_table("MongoDB Aggregation Result ($match -> $group -> $sort)", formatted)


if __name__ == "__main__":
    seed_and_run_crud()
    run_mongo_aggregation()
