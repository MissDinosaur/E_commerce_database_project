# E-Commerce Transaction Analysis Pipeline

## Project Overview

This project aims to analyze e-commerce transactions from the Olist dataset to detect potential fraud and provide insights into customer purchasing patterns. The pipeline ingests data in a simulated real-time environment, processes it using big data tools, and applies machine learning for fraud detection and analytics.

## Technologies Used

- **Data Simulation**: Custom Python script for streaming data generation.
- **Data Ingestion**: Apache Kafka for real-time data streaming.
- **Data Storage**: PostgreSQL, MongoDB, Neo4j.
- **Data Processing**: Apache Spark.
- **Machine Learning**: Scikit-learn, TensorFlow.
- **Visualization**: Python scripts for generating graphs from machine learning models.

## Installation

### Prerequisites

- Docker
- Python 3.11
- Access to a Kafka server (can be local or remote)

### Setup

1. Clone the repository:
   ```bash
   git clone [repository-url]
   cd [project-folder-name]
   ```

2. Build Docker containers:
   ```bash
   docker-compose up --build
   ```

3. Initialize the databases:
   ```bash
   docker exec -it [postgres-container-id] bash
   psql -U postgres -f /scripts/init_db.sql
   ```

   ```bash
   docker exec -it [mongo-container-id] bash
   mongo < /scripts/init_mongo.js
   ```

   ```bash
   docker exec -it [neo4j-container-id] bash
   cypher-shell -u neo4j -p [password] < /scripts/init_neo4j.cypher
   ```

## Running the Project

1. Start the data simulation:
   ```bash
   python scripts/simulate_data.py
   ```

2. Run the Spark processing:
   ```bash
   spark-submit scripts/process_data.py
   ```

3. Execute machine learning models:
   ```bash
   python scripts/run_models.py
   ```

4. Generate visualizations:
   ```bash
   python scripts/generate_graphs.py
   ```

## Contributing

Feel free to fork the project and submit pull requests. You can also open issues if you find any bugs or have feature suggestions.

## License

MIT