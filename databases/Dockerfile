FROM postgres:latest

# Environment Variables
ENV POSTGRES_DB=fraud_detection
ENV POSTGRES_USER=admin
ENV POSTGRES_PASSWORD=admin

# Copy PostgreSQL Initialization Script
COPY postgres/init.sql /docker-entrypoint-initdb.d/

# MongoDB Service
FROM mongo:latest

# Copy MongoDB Initialization Script
COPY mongo/init.js /docker-entrypoint-initdb.d/

# Neo4j Service
FROM neo4j:latest

# Copy Neo4j Initialization Script
COPY neo4j/init.cypher /var/lib/neo4j/import/