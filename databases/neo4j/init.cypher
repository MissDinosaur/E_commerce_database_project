CREATE CONSTRAINT IF NOT EXISTS FOR (u:UserSession) REQUIRE u.session_id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (c:CursorEvent) REQUIRE c.event_id IS UNIQUE;

CREATE INDEX IF NOT EXISTS FOR (c:CursorEvent) ON (c.timestamp);

CREATE (s:UserSession { session_id: 'demo_session', customer_id: 'demo_customer', timestamp: datetime() });

CREATE (e1:CursorEvent { event_id: 'event1', x: 100, y: 200, timestamp: datetime() });
CREATE (e2:CursorEvent { event_id: 'event2', x: 150, y: 250, timestamp: datetime() });

MATCH (s:UserSession { session_id: 'demo_session' })
MATCH (e1:CursorEvent { event_id: 'event1' })
MATCH (e2:CursorEvent { event_id: 'event2' })
CREATE (s)-[:INTERACTS_WITH]->(e1),
       (s)-[:INTERACTS_WITH]->(e2);
