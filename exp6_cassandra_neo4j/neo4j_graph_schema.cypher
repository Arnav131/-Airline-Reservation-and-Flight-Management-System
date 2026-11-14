// ============================================================================
// Experiment 6.2: Neo4j Graph Schema & Connecting Flight Queries (Cypher)
// Nodes: Passenger, Flight, Airport, Aircraft
// Relationships: BOOKED, DEPARTS_FROM, ARRIVES_AT, OPERATED_BY
// ============================================================================

// Clean Slate
MATCH (n) DETACH DELETE n;

// 1. Create Airport Nodes
CREATE (del:Airport {code: 'DEL', name: 'Indira Gandhi International', city: 'New Delhi'})
CREATE (bom:Airport {code: 'BOM', name: 'Chhatrapati Shivaji Maharaj', city: 'Mumbai'})
CREATE (blr:Airport {code: 'BLR', name: 'Kempegowda International', city: 'Bengaluru'})
CREATE (maa:Airport {code: 'MAA', name: 'Chennai International', city: 'Chennai'})
CREATE (sin:Airport {code: 'SIN', name: 'Singapore Changi', city: 'Singapore'})
CREATE (dxb:Airport {code: 'DXB', name: 'Dubai International', city: 'Dubai'})

// 2. Create Aircraft Nodes
CREATE (a320:Aircraft {id: 1, model: 'Airbus A320neo', capacity: 180})
CREATE (b737:Aircraft {id: 2, model: 'Boeing 737-800', capacity: 186})
CREATE (b787:Aircraft {id: 3, model: 'Boeing 787-9 Dreamliner', capacity: 290})

// 3. Create Flight Nodes
CREATE (f202:Flight {flight_id: 'AI-202', departure: datetime('2026-11-12T08:30:00'), arrival: datetime('2026-11-12T10:40:00'), fare: 5200})
CREATE (f304:Flight {flight_id: 'AI-304', departure: datetime('2026-11-12T12:15:00'), arrival: datetime('2026-11-12T14:00:00'), fare: 4100})
CREATE (f408:Flight {flight_id: 'AI-408', departure: datetime('2026-11-12T15:30:00'), arrival: datetime('2026-11-12T16:40:00'), fare: 3200})
CREATE (f715:Flight {flight_id: 'AI-715', departure: datetime('2026-11-12T13:00:00'), arrival: datetime('2026-11-12T15:45:00'), fare: 6100})
CREATE (f820:Flight {flight_id: 'AI-820', departure: datetime('2026-11-12T18:00:00'), arrival: datetime('2026-11-13T00:30:00'), fare: 22000})

// 4. Create Passenger Nodes
CREATE (p1:Passenger {id: 101, name: 'Aarav Sharma'})
CREATE (p2:Passenger {id: 102, name: 'Diya Patel'})
CREATE (p3:Passenger {id: 103, name: 'Rohan Verma'})

// 5. Establish Relationships (DEPARTS_FROM, ARRIVES_AT, OPERATED_BY, BOOKED)
CREATE (f202)-[:DEPARTS_FROM]->(del), (f202)-[:ARRIVES_AT]->(bom), (f202)-[:OPERATED_BY]->(a320)
CREATE (f304)-[:DEPARTS_FROM]->(bom), (f304)-[:ARRIVES_AT]->(blr), (f304)-[:OPERATED_BY]->(b737)
CREATE (f408)-[:DEPARTS_FROM]->(blr), (f408)-[:ARRIVES_AT]->(maa), (f408)-[:OPERATED_BY]->(a320)
CREATE (f715)-[:DEPARTS_FROM]->(del), (f715)-[:ARRIVES_AT]->(blr), (f715)-[:OPERATED_BY]->(b737)
CREATE (f820)-[:DEPARTS_FROM]->(blr), (f820)-[:ARRIVES_AT]->(sin), (f820)-[:OPERATED_BY]->(b787)

CREATE (p1)-[:BOOKED {seat: '12A', status: 'CONFIRMED'}]->(f202)
CREATE (p2)-[:BOOKED {seat: '12B', status: 'CONFIRMED'}]->(f202)
CREATE (p3)-[:BOOKED {seat: '04C', status: 'CONFIRMED'}]->(f304);

// 6. Query: Find Connecting Flights between New Delhi and Chennai (1-Stop & 2-Stop)
MATCH path = (src:Airport {city: 'New Delhi'})<-[:DEPARTS_FROM]-(f1:Flight)-[:ARRIVES_AT]->(hub:Airport)<-[:DEPARTS_FROM]-(f2:Flight)-[:ARRIVES_AT]->(dst:Airport {city: 'Chennai'})
WHERE f2.departure >= f1.arrival + duration({minutes: 45})
  AND f2.departure <= f1.arrival + duration({hours: 6})
RETURN f1.flight_id AS Leg1, hub.code AS Layover, f2.flight_id AS Leg2,
       duration.between(f1.departure, f2.arrival) AS TotalJourneyTime;
