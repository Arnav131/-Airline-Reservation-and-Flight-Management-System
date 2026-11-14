# IARFMS Study Notes & Complete Project Profile (Hinglish Edition)

**Project**: Integrated Airline Reservation and Flight Management System (Group 4)  
**Scope**: Relational SQL, Advanced MySQL, Query Optimization, Concurrency & Locks, Redis & MongoDB, Cassandra & Neo4j, aur Distributed Databases.

---

## 1. Project Actually Chahta Kya Hai? (Problem Statement & Requirements)

So basically, tumhare project ka case study ek real-world airline ke char sabse bade dard (pain points) solve karne ke liye banaya gaya hai:
- **Double seat bookings**: Do passengers ek hi time par "Book Now" dabate hain aur dono ko seat `12A` mil jaati hai. Chaos!
- **Slow flight retrieval**: Jab hazaaron bookings ho jaati hain, toh flight search aur ticket lookup crawl karne lagta hai.
- **Inconsistent records**: Payment kat gaya par ticket confirm nahi hui, ya ek airport par flight `DELAYED` dikha rahi hai aur dusre par `ON_TIME`.
- **Multi-airport coordination**: Delhi, Mumbai aur Bengaluru jaise hubs ke beech data sync karna bina system hang kiye.

In problems ko solve karne ke liye assignment ne **7 Experiments** diye hain, aur har experiment database engineering ki ek alag layer check karta hai:
- **Experiment 1** maangta hai clean relational design (`Passengers`, `Airports`, `Aircraft`, `Flights`, `Reservations`, `Payments`, `Crew`), proper JOINs, available seat calculation, permissions (RBAC), aur transaction control (`SAVEPOINT`, `ROLLBACK`, `COMMIT`).
- **Experiment 2** maangta hai database ke andar logic daalna — Views, Duplicate seat rokne wala Trigger, atomic ticket booking Stored Procedure, dynamic fare Function, aur passenger manifest nikaalne ke liye Cursor.
- **Experiment 3** maangta hai performance tuning — `EXPLAIN` se query scan check karna, B-Tree indexes lagana, SHA-256 computed hash column banana, aur indexing se pehle aur baad ki speed compare karna.
- **Experiment 4** thoda tricky hai — ismein ACID properties live proof karni hain, 8 threads se ek hi seat par race condition karwani hai, Shared vs Exclusive locks dikhane hain, intentional **Deadlock** create karke resolve karna hai, aur **MVCC** snapshot behavior examine karna hai.
- **Experiment 5** NoSQL side par aata hai — Redis mein sessions, flight cache, aur expiring seat-holds (`TTL`); MongoDB mein flexible passenger preferences, baggage details, travel history CRUD, aur flight-wise aggregation stats.
- **Experiment 6** big-data aur graph side cover karta hai — Cassandra mein `Flight_ID` partition key ke saath telemetry logs, aur Neo4j mein `Passenger`, `Flight`, `Airport`, `Aircraft` nodes jodkar connecting flights dhoondhna.
- **Experiment 7** distributed systems simulate karta hai — 3 airport nodes (`DEL`, `BOM`, `BLR`), sharding, schedule replication, aur eventual consistency jab alag-alag airports par flight status change ho.

---

## 2. Implementation Plan & Humne Yahi Approach Kyun Chuna?

Toh dekho, ek normal student kya karta hai? Wo sirf `.sql` files likh kar chhod deta hai ya sirf screenshots laga deta hai. Problem yeh hai ki agar evaluator bol de *"Chala ke dikhao"* aur uske laptop par MySQL, Redis, MongoDB, Cassandra, aur Neo4j teeno-paanchon server ek saath install na hon (aur sach bolun toh Cassandra + Neo4j + MongoDB ek saath chalane mein 6–8 GB RAM lag jaati hai), toh pura demo wahi crash ho jaata hai.

Isliye humne **Dual-Mode Polyglot Architecture** choose kiya:

1. **Pure SQL / CQL / Cypher Scripts + Docker Compose (`docker-compose.yml`)**: Agar tumhare paas Docker Desktop chal raha hai, toh ek command (`docker-compose up -d`) mein asli MySQL 8, Redis 7, MongoDB 6, Cassandra 4.1, aur Neo4j 5 uth jaate hain.
2. **Smart Dual-Engine Adapter (`db_core/config.py` & `db_core/relational_adapter.py`)**: Har Python script pehle check karti hai ki ports `3306, 6379, 27017, 9042, 7687` open hain ya nahi. Agar live database mil gaya, toh wahi connect karti hai. Agar nahi mila, toh automatically high-fidelity embedded engines par switch ho jaati hai — jaise WAL-enabled SQLite with Triggers/SHA2, real clock-based TTL Redis store, MongoDB aggregation pipeline engine, consistent-hash Cassandra ring, aur `NetworkX` property graph!

**Humne koi aur approach (jaise sirf ek single SQLite/MySQL monolith ya fake `print()` mocks) kyun nahi li?**  
Fake `print()` statements viva mein turant pakde jaate hain kyunki real database errors, locking delays, ya latency benchmarks fake nahi lagte. Aur sirf ek MySQL database mein sab kuch thoonss dena (Polyglot ke bajaye) case study ko fail kar deta — kyunki graph multi-hop flights SQL `SELF JOIN` par slow hoti hain, aur 10-minute checkout seat hold ke liye disk-based SQL table par cron jobs chalana Redis TTL ke muqable kaafi clumsy hota hai. Yeh Dual-Mode approach dono duniya ka best deta hai: asli schema/queries bhi hain, aur zero-dependency live execution bhi.

---

## 3. Har Concept, Table aur Technology Kaise Kaam Karti Hai (With Analogies)

### Relational Core, Normalization & JOINs (Experiment 1)

Socho tum ek railway ya airline ka register maintain kar rahe ho. Agar tum ek hi Excel sheet mein passenger ka naam, flight ka naam, airport ka city, aur payment sab likh doge, toh jab 180 log `AI-202` book karenge, tumhe `Indira Gandhi International Airport` 180 baar likhna padega!

Isliye humne data ko **7 Core Tables** (+ `Crew_Assignments`) mein normalize kiya:
- `Passengers(Passenger_ID, Name, Email, Contact)` — Sirf passenger ki identity.
- `Airports(Airport_ID, Airport_Name, City)` — IATA code (`DEL`, `BOM`, `BLR`) primary key.
- `Aircraft(Aircraft_ID, Aircraft_Model, Capacity)` — Plane ka model aur total seats.
- `Flights(Flight_ID, Source_Airport, Destination_Airport, Aircraft_ID, Departure_Time)` — Kaunsa plane kis airport se kab ud raha hai (`Source_Airport <> Destination_Airport` check ke saath).
- `Reservations(Reservation_ID, Passenger_ID, Flight_ID, Seat_Number, Booking_Status)` — Kaunse passenger ne kis flight mein kaunsi seat li.
- `Payments(Payment_ID, Reservation_ID, Amount, Payment_Status)` — Paise aaye ya fail/refund hue.
- `Crew(Crew_ID, Name, Designation)` aur `Crew_Assignments` — Pilot aur cabin crew mapping.

**Normalization (1NF → BCNF) simple bhasha mein**:
- **1NF**: Har cell mein sirf ek value (no comma-separated phone numbers or seats).
- **2NF**: Koi partial dependency nahi (har non-key column poori primary key par depend karta hai).
- **3NF & BCNF**: Koi transitive dependency nahi. Jaise `City` seedha `Airport_ID` par depend karta hai, `Flight_ID` ke through ghoom kar nahi.

Jab humein poora ticket dikhana hota hai, toh hum **JOINs** lagate hain (`exp1_relational_sql/03_complex_joins.sql`), jo alag-alag tables ke tukde jodkar ek complete itinerary table bana dete hain. Available seats nikaalne ke liye simple formula chalta hai: `Aircraft.Capacity - COUNT(CONFIRMED Reservations)`. Aur **RBAC (`04_permissions_rbac.sql`)** mein humne `airline_admin_role`, `booking_agent_role`, aur `passenger_read_role` banaye taaki ek booking desk agent galti se bhi `Flights` ya `Aircraft` table drop na kar sake.

### Procedural SQL — Views, Triggers, Procedures, Functions & Cursors (Experiment 2)

Yeh wala layer database ko "smart" banata hai taaki har chhoti check ke liye application code par bharosa na karna pade:
- **View (`v_passenger_reservations`)**: Ek virtual window ki tarah hai. 6 tables ko baar-baar JOIN likhne ke bajaye ek saved query bana di.
- **Trigger (`trg_prevent_duplicate_seat`)**: Yeh ek security guard hai jo `Reservations` par har `INSERT` se pehle khada rehta hai. Wait — yahan ek classic viva trap hai! Humne `(Flight_ID, Seat_Number)` par simple `UNIQUE` constraint kyun nahi lagaya? Kyunki agar Aarav ne seat `12A` book karke `CANCELLED` kar di, toh simple `UNIQUE` constraint Diya ko dubara `12A` lene hi nahi dega! Hamara trigger check karta hai ki kya same seat par koi **active** (`CONFIRMED` ya `PENDING`) booking hai. Cancelled seat ko wo allow karta hai (yeh humne `exp2_runner.py` mein seat `14D` par live prove bhi kiya hai).
- **Function (`fn_calculate_ticket_charge`)**: Dynamic pricing calculator — Base Fare × Class Multiplier (`Economy 1.0x`, `Business 2.1x`, `First 3.2x`) × Urgency Surge (`<=3 days` par 25% extra) + 12% GST.
- **Stored Procedure (`sp_book_flight_ticket`)**: Ek atomic package. Capacity check karta hai, function se fare nikaalta hai, reservation aur payment insert karta hai, aur agar kahin bhi error aaya toh `ROLLBACK` kar deta hai.
- **Cursor (`sp_generate_flight_passenger_manifest`)**: Jab flight udne wali hoti hai, toh gate staff ko row-by-row boarding list chahiye hoti hai. Cursor ek pointer ki tarah har confirmed passenger par loop chalakar boarding pass code (`BP-AI-202-12A-1001`) generate karta hai.

### Performance Optimization — EXPLAIN, B-Tree & Computed Hash (Experiment 3)

Imagine karo ek 500-page ki moti kitaab mein se tumhe "MVCC" dhoondhna hai. Bina index ke tum Page 1 se Page 500 tak scan karoge (**Full Table Scan** — `SCAN Reservations_Bench`). B-Tree index us kitaab ke peeche wala alphabetical index hai jo 3-4 jumps mein exact page par le jaata hai (**Index Search** — `SEARCH USING INDEX`).

Humne `exp3_performance_tuning/03_benchmark_runner.py` mein **2,000 flights aur 25,000 reservations** generate kiye aur teeno type ke indexes test kiye:
- Single B-Tree indexes `Flight_ID` aur `Passenger_ID` par.
- Composite index `(Source_Airport, Destination_Airport, Departure_Time)` par (Leftmost Prefix rule follow karte hue).
- **Computed SHA-256 Hash Column (`Ticket_Ref_Hash`)**: PNR/Ticket reference strings lambi aur random hoti hain. Unka deterministic `SHA2(..., 256)` stored hash bana kar uspar `UNIQUE INDEX` lagane se exact lookup lightning fast ho jaata hai.

### Concurrency, Locks, Deadlocks & MVCC (Experiment 4)

Yeh part sabse tricky hai, par ek baar samajh aa gaya toh mazaa aa jaata hai:
- **ACID (`01_acid_demonstration.py`)**: Agar payment negative amount se fail ho jaaye, toh reservation bhi rollback ho jaati hai (Atomicity). Uncommitted data dusre connection ko nahi dikhta (Isolation). Close karke wapas kholne par data milta hai (Durability).
- **Race Condition (`02_race_condition_seat.py`)**: 8 threads ek hi millisecond par `threading.Barrier` ke through Seat `16A` book karne daudte hain. Database transaction lock aur trigger ensure karte hain ki sirf **1 thread** jeete aur baaki 7 ko clean rejection mile.
- **Shared vs Exclusive Locks (`03_shared_exclusive_locks.py`)**: Shared Lock (`FOR SHARE`) library ki reference book padhne jaisa hai — do log ek saath padh sakte hain, par koi page faad/edit nahi kar sakta. Exclusive Lock (`FOR UPDATE`) trial room ke darwaze jaisa hai — jab tak ek banda andar update kar raha hai, koi dusra padh ya likh nahi sakta.
- **Deadlock (`04_deadlock_simulation.py`)**: Socho ek patli gali mein do gaadiyan aamne-saamne aa gayin; dono piche hatne ko taiyaar nahi. `Txn-Alpha` ne `Reservation:1001` lock kiya aur `Payment:5002` maanga; `Txn-Beta` ne `Payment:5002` lock kiya aur `Reservation:1001` maanga. Hamara **Wait-For Graph** cycle detect karta hai (`Txn-Beta <-> Txn-Alpha`), younger transaction (`Txn-Beta`) ko victim banakar rollback karta hai, aur `Txn-Alpha` safely commit ho jaata hai!
- **MVCC (`05_mvcc_investigation.py`)**: Multi-Version Concurrency Control ka matlab hai *"Readers never block writers, writers never block readers."* Socho `Reader-A` ne 10:00 AM par ek snapshot (read view) khola. Usi waqt `Writer-B` ne flight ka status `DELAYED_30M` karke commit kar diya. `Reader-A` jab dobara apni open transaction mein padhta hai, toh usse purana Undo/WAL snapshot (`ON_TIME`) hi dikhta hai — bina `Writer-B` ko roke! Jab `Reader-C` nayi transaction kholta hai, tab usse naya committed data dikhta hai.

### Polyglot NoSQL — Redis, MongoDB, Cassandra & Neo4j (Experiments 5 & 6)

Har kaam ke liye SQL use karna aisa hi hai jaise har cheez hathode se thokna:
- **Redis (`exp5_redis_mongodb/redis_cache_manager.py`)**: Memory mein chalta hai, microsecond speed. Teen kaam karta hai: user sessions rakhna, baar-baar search hone wale `DEL->BOM` routes cache karna, aur **Temporary Seat Hold**. Jab tum flight checkout par jaate ho aur 10 minute ka timer chalta hai, wo Redis ka atomic `SET seat_hold:AI-202:19A ... NX EX 600` hota hai. Agar tumne payment nahi ki, TTL expire hote hi seat apne aap free ho jaati hai — zero cleanup code!
- **MongoDB (`mongo_document_manager.py` & `mongo_aggregation_analytics.py`)**: Passenger ki meal preference (`Vegan`, `Jain`), wheelchair need, 3 baggage tags, aur purani travel history har passenger ke liye alag-alag shape ki hoti hai. SQL mein iske liye 10 `NULL`-bhari columns banani padti. MongoDB mein sab ek clean JSON document mein baith jaata hai, aur `$match -> $group -> $sort` aggregation pipeline turant flight-wise revenue aur average baggage weight nikaal deti hai.
- **Cassandra (`exp6_cassandra_neo4j/cassandra_telemetry_runner.py`)**: Jab 500 flights har second gate change, boarding scan, aur altitude telemetry bhejti hain, toh write throughput massive hota hai. Cassandra mein humne `Flight_ID` ko **Partition Key** aur `event_timestamp DESC` ko **Clustering Key** banaya. Iska matlab `AI-202` ka sara data consistent hashing se ek hi partition node par time ke reverse order mein store hota hai — latest event sabse upar, O(1) partition lookup!
- **Neo4j (`exp6_cassandra_neo4j/neo4j_pathfinder.py`)**: Agar tumhe Delhi se Chennai ya Singapore jaana hai aur direct flight nahi hai, toh SQL mein 2-stop ya 3-stop connecting flights dhoondhne ke liye multiple self-joins lagenge jo data badhne par slow ho jaate hain. Graph DB mein `Airport`, `Flight`, `Aircraft`, aur `Passenger` nodes hain aur `DEPARTS_FROM`, `ARRIVES_AT`, `OPERATED_BY`, `BOOKED` edges hain. Graph traversal seedha edges follow karke 45-min+ layover constraint check karte hue 1-stop (`AI-715 -> AI-412`) aur 2-stop (`AI-202 -> AI-304 -> AI-820`) paths turant nikaal deta hai.

### Distributed Airport Cluster (Experiment 7)

Imagine karo Delhi (`DEL`), Mumbai (`BOM`), aur Bengaluru (`BLR`) airport ke apne local servers hain (`data/nodes/node_del.db`, `node_bom.db`, `node_blr.db`).
- **Sharding (`data_sharding_router.py`)**: Passenger reservations ko humne regions aur `Flight_ID` consistent hashing se 3 alag physical database files mein baant diya, taaki ek hi server par saara bojh na pade.
- **Replication (`schedule_replication_engine.py`)**: Global flight schedule teeno nodes par replicated hai (`RF=3`), taaki Mumbai counter ko schedule dekhne ke liye Delhi server ko ping na karna pade.
- **Eventual Consistency (`eventual_consistency_demo.py`)**: Maan lo Delhi aur Mumbai ke beech WAN internet kuch seconds ke liye lag kar gaya. Delhi node par `AI-202` ka status `DELAYED_45M (v=2)` ho gaya, aur lag ke beech Mumbai par gate update hokar `BOARDING_GATE_B4 (v=3)` ho gaya. Temporary **split-brain divergence** dikhta hai (`DEL` kuch aur bol raha hai, `BLR` purana `ON_TIME (v=1)` bol raha hai). Jaise hi network theek hota hai, **Anti-Entropy Gossip Sync** highest Lamport Version Clock (`v=3`) ke basis par teeno nodes ko converge karke ek identical state par le aata hai!

---

## 4. Code Architecture Ka Quick Map (File-by-File)

- `db_core/` — `config.py` (port scanning & connection configs) aur `relational_adapter.py` (MySQL/SQLite unified query runner + Rich tables).
- `exp1_relational_sql/` — `01_schema_ddl.sql`, `02_sample_data.sql`, `03_complex_joins.sql`, `04_permissions_rbac.sql`, `05_transaction_control.sql`, aur runner `exp1_runner.py`.
- `exp2_advanced_mysql/` — Views, Triggers, Stored Procs, Functions, Cursors ki `.sql` files aur `exp2_runner.py`.
- `exp3_performance_tuning/` — `EXPLAIN` & Index `.sql` files + `03_benchmark_runner.py` (27,000 rows synthetic benchmark).
- `exp4_transaction_concurrency/` — 5 alag Python scripts (`01_acid_demonstration.py` se `05_mvcc_investigation.py`) + `exp4_runner.py`.
- `exp5_redis_mongodb/` — `redis_cache_manager.py`, `mongo_document_manager.py`, `mongo_aggregation_analytics.py`, aur `exp5_runner.py`.
- `exp6_cassandra_neo4j/` — `cassandra_schema.cql`, `cassandra_telemetry_runner.py`, `neo4j_graph_schema.cypher`, `neo4j_pathfinder.py`, aur `exp6_runner.py`.
- `exp7_distributed_databases/` — `distributed_cluster_sim.py`, `data_sharding_router.py`, `schedule_replication_engine.py`, `eventual_consistency_demo.py`, aur `exp7_runner.py`.
- `app/cli_dashboard.py` — Viva demo ke liye interactive terminal dashboard.
- `tests/test_all_experiments.py` — Complete end-to-end `pytest` verification suite.

---

## 5. Yeh System Real Production System Ke Kitna Kareeb Hai?

Honest engineering assessment dekhein toh:

**Jo Cheezein Bilkul Production-Grade Hain:**
- BCNF normalized schema with `RESTRICT`/`CASCADE` referential integrity aur conditional seat-reuse trigger.
- Stored SHA-256 hash column lookups aur composite leftmost-prefix B-Tree indexes.
- Atomic checkout holds using Redis `SET NX EX` (yahi pattern Ticketmaster aur BookMyShow use karte hain!).
- Cassandra time-series modeling (`((flight_id), event_timestamp DESC)`) aur Neo4j property graph routing.
- Lamport version-clock based anti-entropy reconciliation in distributed nodes.

**Real Airline (100 Million+ Users) Par Scale Karne Ke Liye Kya Upgrade Hoga?**
- Local SQLite/in-memory fallbacks ki jagah Docker/Kubernetes par dedicated multi-node clusters (`docker-compose.yml` iska pehla step hai).
- In-process `RowLockManager` ki jagah InnoDB / PostgreSQL ke native distributed row locks + connection pooling (`PgBouncer` / `ProxySQL`).
- Synchronous gossip loop ki jagah Apache Kafka / Debezium CDC (Change Data Capture) event streams taaki MySQL booking events automatically MongoDB, Cassandra, aur Neo4j mein stream ho sakein.

---

## 6. Kaise Run Karein, Dry Run & Real Scale Verification

### A. Interactive Demo / Dry Run Kaise Chalayein
Project root `d:\ML_PROJECTS\DBMS_PROJECT` mein terminal kholo:
```powershell
# Interactive Menu (Viva mein professor ke saamne best lagta hai)
python app/cli_dashboard.py

# Ya ek saath saare 7 experiments run karne ke liye:
python app/cli_dashboard.py --all
```
*(Agar live database containers par chalana hai, toh Docker Desktop start karke `docker-compose up -d` chalao — code khud detect karke live containers par switch ho jayega.)*

### B. Complete End-to-End Test & Verification Results
Humne verify karne ke liye ki yeh architecture scale aur correctness dono maintain karta hai, `pytest` integration suite (`tests/test_all_experiments.py`) run kiya aur **7/7 tests pass** hue (`7 passed in 13.66s`). Exact observed dry-run metrics yeh rahe:

- **Experiment 1 & 2**: 7+1 tables create aur seed hue; `SAVEPOINT` ne failed payment `5009` rollback karke `5010` commit kiya; duplicate seat `12A` trigger ne block kiya (`DUPLICATE_SEAT_ERROR`), aur cancelled seat `14D` re-book ho gayi.
- **Experiment 3 (27,000-Row Scale Benchmark)**:
  - `Flight_ID` lookup: `306.88 ms` se ghatkar `20.56 ms` (**14.9x faster**).
  - `Passenger_ID` lookup: `195.99 ms` se ghatkar `9.66 ms` (**20.3x faster**).
  - Computed `SHA-256 Ticket_Ref_Hash` lookup: `322.82 ms` se ghatkar `7.08 ms` (**45.6x faster**), aur `EXPLAIN` plan `SCAN` se `SEARCH USING INDEX` mein badal gaya.
- **Experiment 4 (Concurrency Stress)**: 8 parallel threads ne seat `16A` par attack kiya — strictly **1 winner**, 7 rejected. Deadlock script ne `Txn-Beta <-> Txn-Alpha` cycle pakad kar `Txn-Beta` ko rollback kiya aur `Txn-Alpha` safely commit hua. MVCC ne `Reader-A` ko purana snapshot bina writer ko block kiye serve kiya.
- **Experiment 5 (Redis & MongoDB)**: Redis `Cache MISS` (`0.0945 ms`) vs `Cache HIT` (`0.0181 ms`) verified; `seat_hold:AI-202:19A` ne Passenger 102 ko block kiya aur `2.2s` TTL expiry ke baad automatically release ho gaya. MongoDB aggregation ne flight-wise baggage aur revenue totals nikaale.
- **Experiment 6 (Cassandra & Neo4j)**: Cassandra consistent hashing ne flights ko 3 virtual nodes par distribute kiya; Neo4j pathfinder ne `New Delhi -> Chennai` ke liye 1-stop (`AI-715 -> AI-412`, `5h 25m`) aur 2-stop (`AI-202 -> AI-304 -> AI-408`, `8h 10m`) connecting itineraries dhoondhe.
- **Experiment 7 (Distributed Cluster)**: Reservations 3 physical node files (`node_del.db`, `node_bom.db`, `node_blr.db`) mein shard hue, aur split-brain divergence (`DELAYED_45M` vs `BOARDING_GATE_B4` vs `ON_TIME`) gossip sync ke baad teeno nodes par `BOARDING_GATE_B4` par converge ho gaya.
