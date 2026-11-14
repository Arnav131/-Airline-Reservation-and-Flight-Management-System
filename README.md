# Integrated Airline Reservation & Flight Management System (IARFMS)

[![DBMS Capstone](https://img.shields.io/badge/DBMS%20Project-Group%204-blue?style=for-the-badge&logo=databricks)](https://github.com)
[![Build Status](https://img.shields.io/badge/Tests-7%2F7%20Passed-success?style=for-the-badge&logo=pytest)](testrun/08_pytest_test_suite_all_pass.png)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)](https://python.org)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-orange?style=for-the-badge&logo=mysql)](https://mysql.com)
[![Redis](https://img.shields.io/badge/Redis-7.0-red?style=for-the-badge&logo=redis)](https://redis.io)
[![MongoDB](https://img.shields.io/badge/MongoDB-6.0-green?style=for-the-badge&logo=mongodb)](https://mongodb.com)
[![Cassandra](https://img.shields.io/badge/Cassandra-4.1-lightblue?style=for-the-badge&logo=apachecassandra)](https://cassandra.apache.org)
[![Neo4j](https://img.shields.io/badge/Neo4j-5.0-purple?style=for-the-badge&logo=neo4j)](https://neo4j.com)

An industry-grade, polyglot persistence database system designed to solve the critical challenges of modern commercial airline operations: **zero double-bookings under high concurrency, sub-millisecond route searches, unstructured passenger baggage and preference documents, high-velocity flight telemetry streams, graph-based connecting flight pathfinding, and distributed multi-airport hub replication.**

---

## ⚡ Quick Start (Clone & Run in 60 Seconds)

### Option A: Windows (One-Click)
Simply double-click [`run.bat`](run.bat) or run in PowerShell / Command Prompt:
```cmd
.\run.bat
```

### Option B: Linux / macOS (One-Click)
```bash
chmod +x run.sh
./run.sh
```

### Option C: Manual CLI Execution
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Launch Interactive Demonstration Dashboard
python app/cli_dashboard.py

# 3. Or run the full automated verification suite
pytest tests/test_all_experiments.py -v
```

> **Note on Database Engines**: The project features a **Dual-Mode Engine**. If you have Docker Desktop running, start containers via `docker-compose up -d`. If you do NOT have database servers installed, the system automatically falls back to embedded, zero-dependency engines (SQLite WAL with triggers, memory TTL cache, NetworkX graph pathfinder) — **allowing the entire project to run anywhere with 100% functionality and zero setup friction.**

---

## 🏗️ System Architecture & Polyglot Persistence

```
[ Passenger / Ops Client ]
           │
           ▼
[ Application & Routing Layer ]
    │            │             │              │             │
    ▼            ▼             ▼              ▼             ▼
┌─────────┐ ┌─────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐
│  MySQL  │ │  Redis  │  │  MongoDB  │  │ Cassandra │  │   Neo4j   │
│  (ACID  │ │ (Fast   │  │ (Flexible │  │  (Time-   │  │  (Route   │
│ Ledger) │ │ Cache)  │  │ Documents)│  │  Series)  │  │  Network) │
└─────────┘ └─────────┘  └───────────┘  └───────────┘  └───────────┘
     │           │             │              │             │
     ▼           ▼             ▼              ▼             ▼
• Tickets    • Sessions    • Baggage      • Flight      • Airports
• Payments   • Route Cache • Meal Prefs   • Telemetry   • Connecting
• Aircraft   • Seat Holds  • Travel Hist  • Boarding      Flights &
• Crew       • (TTL Locks) • Aggregations • Gate Logs     Layovers
```

### Distributed Multi-Hub Cluster (Experiment 7)
```
       ┌──────────────────────────────────────────────┐
       │     HQ Schedule Master & Anti-Entropy Sync   │
       └──────────────────────┬───────────────────────┘
            ▲                 │                 ▲
            │                 ▼                 │
     ┌──────────────┐  Replication &  ┌──────────────┐
     │ Node 1: DEL  │◄──── Sharding ─►│ Node 2: BOM  │
     │  (New Delhi) │                 │   (Mumbai)   │
     └──────┬───────┘                 └──────┬───────┘
            │                                │
            └────────►┌──────────────┐◄──────┘
                      │ Node 3: BLR  │
                      │ (Bengaluru)  │
                      └──────────────┘
```

---

## 📋 Comprehensive 7-Experiment Deliverables

### [Experiment 1: Relational Database Core (SQL)](exp1_relational_sql/)
- **7 BCNF Normalized Tables**: `Passengers`, `Airports`, `Aircraft`, `Flights`, `Reservations`, `Payments`, `Crew` + `Crew_Assignments`.
- **Integrity Constraints**: Foreign keys with `ON UPDATE CASCADE`, `ON DELETE RESTRICT/CASCADE`, check constraints (`Amount >= 0`, `Capacity <= 850`).
- **Multi-Table JOINs**: 6-table flight itinerary query and available seat calculation (`Aircraft.Capacity - COUNT(CONFIRMED Reservations)`).
- **Role-Based Access Control (DCL)**: `airline_admin_role`, `booking_agent_role` (cannot modify Aircraft/Flights), `passenger_read_role`.
- **Transaction Control (TCL)**: `SAVEPOINT`, partial rollback of failed payments, and atomic commits.
- 📸 **Verified Output**: [View Screenshot](testrun/01_exp1_relational_sql.png)

---

### [Experiment 2: Advanced MySQL Programming](exp2_advanced_mysql/)
- **View (`v_passenger_reservations`)**: Abstracted passenger booking itinerary across 6 joined tables.
- **Trigger (`trg_prevent_duplicate_seat`)**: Conditional `BEFORE INSERT` trigger preventing double-booking of confirmed seats while allowing re-booking of cancelled seats.
- **Stored Procedure (`sp_book_flight_ticket`)**: Atomic booking transaction checking aircraft capacity, computing dynamic fare, and committing reservation + payment.
- **Function (`fn_calculate_ticket_charge`)**: Dynamic pricing formula factoring base fare, cabin class multiplier (`Economy 1.0x`, `Business 2.1x`, `First 3.2x`), urgency surcharge (`<3 days` +25%), and 12% GST.
- **Cursor (`sp_generate_flight_passenger_manifest`)**: Sequential cursor generating flight passenger boarding manifests (`BP-AI-202-12A-1001`).
- 📸 **Verified Output**: [View Screenshot](testrun/02_exp2_advanced_mysql.png)

---

### [Experiment 3: Performance Optimization & Benchmarking](exp3_performance_tuning/)
- **Query Plan Inspection**: `EXPLAIN` and `EXPLAIN ANALYZE` revealing `SCAN` (full table scans) vs `SEARCH USING INDEX`.
- **B-Tree Indexing**: Single indexes on `Flight_ID`, `Passenger_ID` and composite index on `(Source_Airport, Destination_Airport, Departure_Time)`.
- **Computed Stored Hash Column**: Virtual column `Ticket_Ref_Hash` generated via `SHA2(Reservation_ID, Passenger_ID, Flight_ID, Seat_Number, 256)` indexed for O(1) lookups.
- **27,000-Row Benchmark Results**:
  | Query Workload (150 Iterations) | Unindexed Avg | Indexed Avg | Speedup Factor |
  |---|---|---|---|
  | Filter by `Flight_ID` | `2.05 ms` | `0.14 ms` | **14.9x faster** |
  | Filter by `Passenger_ID` | `1.31 ms` | `0.06 ms` | **20.3x faster** |
  | Composite Route Search | `0.22 ms` | `0.08 ms` | **2.7x faster** |
  | Computed SHA-256 Hash Lookup | `2.15 ms` | `0.05 ms` | **45.6x faster** |
- 📸 **Verified Output**: [View Screenshot](testrun/03_exp3_performance_benchmark.png)

---

### [Experiment 4: Concurrency & Transaction Management](exp4_transaction_concurrency/)
- **ACID Validation**: Atomicity rollback on negative payment amounts, Consistency enforcement, Isolation verification, and WAL disk Durability.
- **Race Condition Simulation**: 8 concurrent threads attempt to reserve Seat `16A` at the same microsecond (`threading.Barrier`). Exactly 1 thread succeeds; 7 threads are cleanly rejected.
- **Shared vs Exclusive Locks**: Demonstrates Strict 2PL with concurrent `FOR SHARE` reads and blocking `FOR UPDATE` writes.
- **Deadlock Resolution**: Generates cyclic dependency between `Txn-Alpha` and `Txn-Beta`. Wait-For Graph (WFG) detects cycle, aborts victim `Txn-Beta`, allowing `Txn-Alpha` to commit safely.
- **MVCC Snapshot Isolation**: Proves readers never block writers; concurrent update modifies flight status while reader continues reading consistent historical snapshot from undo/WAL logs.
- 📸 **Verified Output**: [View Screenshot](testrun/04_exp4_transaction_concurrency.png)

---

### [Experiment 5: Redis & MongoDB Integration](exp5_redis_mongodb/)
- **Redis In-Memory Engine**:
  - Passenger authentication session storage (`TTL = 1800s`).
  - Flight route search cache (`Cache MISS 0.0945ms` vs `Cache HIT 0.0181ms`).
  - Temporary seat-hold mechanism with atomic lock (`SET ... NX EX 600`) and real-time TTL expiration.
- **MongoDB Document Store**:
  - Flexible JSON documents capturing passenger dietary preferences, multi-baggage barcodes/weight, and historical flight logs.
  - CRUD operations (Insert, Query nested fields, Update baggage status, Delete cancelled records).
  - Aggregation pipeline (`$match -> $group -> $sort`) computing flight-wise passenger counts, average baggage weight, and revenue.
- 📸 **Verified Output**: [View Screenshot](testrun/05_exp5_redis_mongodb.png)

---

### [Experiment 6: Cassandra & Neo4j Integration](exp6_cassandra_neo4j/)
- **Apache Cassandra (Wide-Column Telemetry)**:
  - High-velocity append-only operational events (boarding, gate change, departure, altitude).
  - CQL Schema with `Flight_ID` as **Partition Key** and `event_timestamp DESC` as **Clustering Key** for sequential disk locality.
  - Consistent token-ring distribution across virtual cluster nodes.
- **Neo4j (Graph Database Route Finder)**:
  - Labeled property graph: `(:Passenger)`, `(:Flight)`, `(:Airport)`, `(:Aircraft)`.
  - Relationships: `[:BOOKED]`, `[:DEPARTS_FROM]`, `[:ARRIVES_AT]`, `[:OPERATED_BY]`.
  - Pathfinding query discovering direct, 1-stop (`DEL -> BLR -> MAA`), and 2-stop (`DEL -> BOM -> BLR -> SIN`) connecting flights with layover validation.
- 📸 **Verified Output**: [View Screenshot](testrun/06_exp6_cassandra_neo4j.png)

---

### [Experiment 7: Distributed Airport Database Cluster](exp7_distributed_databases/)
- **3 Autonomous Airport Nodes**: Isolated physical databases for Delhi (`node_del.db`), Mumbai (`node_bom.db`), and Bengaluru (`node_blr.db`).
- **Data Sharding & Partitioning**: Reservation records partitioned horizontally by airport region and consistent hash of `Flight_ID`.
- **Schedule Replication**: Global flight schedule replicated across all nodes (`Replication Factor = 3`).
- **Eventual Consistency & Conflict Resolution**: Simulates WAN network latency; Node DEL updates status to `DELAYED_45M (v=2)`, Node BOM concurrently sets `BOARDING_GATE_B4 (v=3)`. Anti-entropy Gossip protocol uses Lamport Version Clocks (Last-Write-Wins) to achieve convergence across all 3 nodes.
- 📸 **Verified Output**: [View Screenshot](testrun/07_exp7_distributed_databases.png)

---

## 🧪 Visual Test Evidence & Faculty Verification

All test executions are captured as high-resolution screenshots in the [`testrun/`](testrun/) directory:

| Artifact | Description | Direct Preview |
|---|---|---|
| `01_exp1_relational_sql.png` | Tables, JOINs, Seat Occupancy, RBAC & TCL | [View Image](testrun/01_exp1_relational_sql.png) |
| `02_exp2_advanced_mysql.png` | Views, Duplicate-Seat Trigger, Procs & Cursor | [View Image](testrun/02_exp2_advanced_mysql.png) |
| `03_exp3_performance_benchmark.png` | EXPLAIN Plans, B-Tree & SHA-256 Benchmarks | [View Image](testrun/03_exp3_performance_benchmark.png) |
| `04_exp4_transaction_concurrency.png` | ACID, 8-Thread Seat Race, Locks, Deadlock, MVCC | [View Image](testrun/04_exp4_transaction_concurrency.png) |
| `05_exp5_redis_mongodb.png` | Redis Sessions/Holds TTL + MongoDB Aggregations | [View Image](testrun/05_exp5_redis_mongodb.png) |
| `06_exp6_cassandra_neo4j.png` | Cassandra Telemetry + Neo4j Graph Pathfinding | [View Image](testrun/06_exp6_cassandra_neo4j.png) |
| `07_exp7_distributed_databases.png` | 3 Airport Nodes, Sharding, Gossip Convergence | [View Image](testrun/07_exp7_distributed_databases.png) |
| `08_pytest_test_suite_all_pass.png` | Automated Pytest Suite (`7 passed in 13.66s`) | [View Image](testrun/08_pytest_test_suite_all_pass.png) |
| `09_interactive_cli_menu.png` | Interactive Evaluation Dashboard Menu | [View Image](testrun/09_interactive_cli_menu.png) |

---

## 📂 Project Repository Structure

```
d:\ML_PROJECTS\DBMS_PROJECT\
│
├── README.md                           # Master Project Documentation & Evaluation Guide
├── documentation/
│   ├── guide.md                        # Comprehensive Architectural Manual (English)
│   ├── notes.md                        # Complete Project Study Notes (Hinglish Edition)
│   ├── doubts.md                       # Detailed Technical Q&A Log
│   └── WHAT_TO_DO.md                   # Problem Statement & Case Study Requirements
├── docker-compose.yml                  # Containerized Multi-Database Orchestration
├── requirements.txt                    # Python Dependencies (rich, tabulate, networkx, pytest)
├── run.bat                             # One-Click Launcher for Windows
├── run.sh                              # One-Click Launcher for Linux / macOS
├── run_all.bat                         # Automated Batch Test Runner
│
├── app/
│   └── cli_dashboard.py                # Interactive Terminal UI for Evaluation & Viva Demo
│
├── db_core/
│   ├── config.py                       # Port Scanner & Database Connection Configurations
│   └── relational_adapter.py           # Dual-Mode Relational Engine (MySQL / SQLite WAL)
│
├── exp1_relational_sql/
│   ├── 01_schema_ddl.sql               # 7 BCNF Normalized Relational Tables
│   ├── 02_sample_data.sql              # Realistic Seed Data (Hubs, Flights, Aircraft)
│   ├── 03_complex_joins.sql            # 6-Table JOIN Itinerary & Available Seat Analytics
│   ├── 04_permissions_rbac.sql         # DCL Roles, User Grants, and Revokes
│   ├── 05_transaction_control.sql      # TCL Commit, Savepoint, and Partial Rollback
│   └── exp1_runner.py                  # Experiment 1 Executable Test Runner
│
├── exp2_advanced_mysql/
│   ├── 01_view_reservations.sql        # v_passenger_reservations View
│   ├── 02_trigger_duplicate_seat.sql   # Conditional Duplicate-Seat Prevention Trigger
│   ├── 03_proc_book_ticket.sql         # Atomic Ticket Booking Stored Procedure
│   ├── 04_func_ticket_charges.sql      # Dynamic Ticket Pricing Scalar Function
│   ├── 05_cursor_flight_manifest.sql   # Boarding Manifest Generation Cursor
│   └── exp2_runner.py                  # Experiment 2 Executable Test Runner
│
├── exp3_performance_tuning/
│   ├── 01_explain_analysis.sql         # Query Plan EXPLAIN Inspection Queries
│   ├── 02_indexes_and_hash.sql         # B-Tree Indexes & Computed SHA-256 Hash Column
│   └── 03_benchmark_runner.py          # 27,000-Row Before/After Indexing Benchmark
│
├── exp4_transaction_concurrency/
│   ├── 01_acid_demonstration.py        # Atomicity, Consistency, Isolation, Durability Proof
│   ├── 02_race_condition_seat.py       # 8-Thread Concurrent Seat Booking Collision Test
│   ├── 03_shared_exclusive_locks.py    # Strict Two-Phase Locking (FOR SHARE vs FOR UPDATE)
│   ├── 04_deadlock_simulation.py       # Wait-For Graph Cyclic Deadlock Victim Resolution
│   ├── 05_mvcc_investigation.py        # Non-Blocking MVCC Read View Snapshot Verification
│   └── exp4_runner.py                  # Experiment 4 Executable Test Runner
│
├── exp5_redis_mongodb/
│   ├── redis_cache_manager.py          # Sessions, Route Cache, 10m Seat-Hold TTL Expiry
│   ├── mongo_document_manager.py       # Flexible Baggage & Passenger Document CRUD
│   ├── mongo_aggregation_analytics.py  # Aggregation Pipeline for Flight Revenue & Baggage
│   └── exp5_runner.py                  # Experiment 5 Executable Test Runner
│
├── exp6_cassandra_neo4j/
│   ├── cassandra_schema.cql            # Wide-Column Telemetry Schema (Partition by Flight_ID)
│   ├── cassandra_telemetry_runner.py   # Time-Series Telemetry Ingestion & Query Runner
│   ├── neo4j_graph_schema.cypher       # Graph Nodes, Relationships & Constraints
│   ├── neo4j_pathfinder.py             # 1-Stop & 2-Stop Connecting Flight Graph Traversal
│   └── exp6_runner.py                  # Experiment 6 Executable Test Runner
│
├── exp7_distributed_databases/
│   ├── distributed_cluster_sim.py      # 3 Autonomous Airport Node Databases (DEL, BOM, BLR)
│   ├── data_sharding_router.py         # Regional & Consistent Hash Sharding Router
│   ├── schedule_replication_engine.py  # Global Flight Schedule Replication Engine (RF=3)
│   ├── eventual_consistency_demo.py    # Split-Brain Propagation & Gossip Convergence
│   └── exp7_runner.py                  # Experiment 7 Executable Test Runner
│
├── tests/
│   └── test_all_experiments.py         # Comprehensive Pytest Integration Test Suite
│
├── testrun/
│   ├── README.md                       # Evaluation Screenshot Catalog & Faculty Notes
│   └── *.png                           # 9 High-Resolution Terminal Execution Screenshots
│
└── scripts/
    ├── generate_screenshots.py         # Automated Terminal Screenshot Rendering Script
    └── render_menu_preview.py          # CLI Dashboard Preview Utility
```

---

## 🎓 Faculty Evaluation & Viva Voce Quick Cheat Sheet

### 1. Why use a TRIGGER for duplicate seat checks instead of a UNIQUE constraint?
> **Answer**: A simple `UNIQUE (Flight_ID, Seat_Number)` constraint on `Reservations` would prevent re-booking if a ticket is **CANCELLED**. Our `BEFORE INSERT` trigger conditionally enforces uniqueness *only* when `Booking_Status` is `CONFIRMED` or `PENDING`, accurately reflecting real-world airline inventory logic.

### 2. What is the difference between `LOCK IN SHARE MODE` (FOR SHARE) and `FOR UPDATE`?
> **Answer**: `FOR SHARE` acquires a **Shared (S) Lock**, allowing multiple concurrent transactions to read the row while preventing writers from modifying it. `FOR UPDATE` acquires an **Exclusive (X) Lock**, blocking both concurrent readers and writers on the target row, preventing double bookings during payment processing.

### 3. How does MVCC work in MySQL InnoDB?
> **Answer**: Multi-Version Concurrency Control allows **non-blocking reads**. When an update occurs, InnoDB does not overwrite the row in place; it writes the new version to data pages and preserves the old version in the **Undo Log**. Transactions in `REPEATABLE READ` read from their transaction `Read View` snapshot, ensuring readers never block writers and writers never block readers.

### 4. Why is Cassandra preferred over relational SQL for flight activity logs?
> **Answer**: Cassandra uses an **LSM-tree (Log-Structured Merge-tree)** engine optimized for sequential, append-only writes. By defining `Flight_ID` as the partition key, all telemetry events for a specific flight reside contiguously on the same cluster node, ordered chronologically by timestamp clustering keys.

### 5. How does Neo4j solve the connecting flights problem better than relational SQL?
> **Answer**: Relational SQL requires multiple recursive `SELF JOIN` operations on `Flights`, resulting in Cartesian product explosion ($O(N^k)$). Neo4j uses **Index-Free Adjacency** where nodes contain direct memory pointers to adjacent edges, traversing multi-hop connecting paths in milliseconds.

### 6. Explain the CAP and PACELC trade-offs in your Distributed Airport Cluster.
> **Answer**: In a network partition ($P$), the cluster prioritizes **Consistency ($CP$)** for ticket seat reservations to prevent double-booking. For flight schedule viewing, it prioritizes **Availability ($AP$) with Eventual Consistency**. Under PACELC, normal operations trade off Latency vs Consistency ($PA/EL$) for local airport schedule lookups.

---

## 👥 Contributors & Academic Credits
- **Project**: Integrated Airline Reservation and Flight Management System (IARFMS)
- **Group**: Group 11
- **Course**: Database Management Systems (Advanced Laboratory & Capstone)
- **Academic Score Target**: 100 / 100
