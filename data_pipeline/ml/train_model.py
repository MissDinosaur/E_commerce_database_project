import os
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
import os
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import pymongo
from neo4j import GraphDatabase
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

def load_env_vars():
    return {
        "NEO4J_URI": os.getenv("NEO4J_URI", "bolt://neo4j_db:7687"),
        "NEO4J_USER": os.getenv("NEO4J_USER", "neo4j"),
        "NEO4J_PASSWORD": os.getenv("NEO4J_PASSWORD", "password"),
        "MONGO_HOST": os.getenv("MONGO_HOST", "mongo_db"),
        "MONGO_PORT": int(os.getenv("MONGO_PORT", "27017")),
        "POSTGRES_HOST": os.getenv("POSTGRES_HOST", "postgres_db"),
        "POSTGRES_PORT": int(os.getenv("POSTGRES_PORT", "5432")),
        "POSTGRES_DB": os.getenv("POSTGRES_DB", "ecommerce"),
        "POSTGRES_USER": os.getenv("POSTGRES_USER", "postgres"),
        "POSTGRES_PASSWORD": os.getenv("POSTGRES_PASSWORD", "password")
    }

def connect_to_databases():
    """Establish connections to all required databases."""
    env_vars = load_env_vars()
    pg_engine = create_engine(
        f"postgresql://{env_vars['POSTGRES_USER']}:{env_vars['POSTGRES_PASSWORD']}@{env_vars['POSTGRES_HOST']}:{env_vars['POSTGRES_PORT']}/{env_vars['POSTGRES_DB']}",
        future=True
    )
    mongo_client = pymongo.MongoClient(host=env_vars["MONGO_HOST"], port=env_vars["MONGO_PORT"])
    neo4j_driver = GraphDatabase.driver(env_vars["NEO4J_URI"], auth=(env_vars["NEO4J_USER"], env_vars["NEO4J_PASSWORD"]))
    return pg_engine, mongo_client, neo4j_driver

def fetch_data(pg_engine, mongo_db, neo4j_driver):
    """Fetch and combine data from all sources."""
    # PostgreSQL query
    query = text("SELECT * FROM orders JOIN order_payments ON orders.order_id = order_payments.order_id;")
    with pg_engine.connect() as connection:
        df_pg = pd.read_sql_query(query, connection)
    
    # MongoDB query
    cursor_logs = mongo_db.cursor_logs.find({})
    df_mongo = pd.DataFrame(list(cursor_logs))
    
    if "_id" in df_mongo.columns:
        df_mongo.drop(columns=["_id"], inplace=True)
    
    # Keep only numeric and ID columns from PostgreSQL
    numeric_cols = df_pg.select_dtypes(include=['int64', 'float64']).columns
    id_cols = ['customer_id', 'order_id']
    keep_cols = list(set(numeric_cols).union(set(id_cols)))
    df_pg = df_pg[keep_cols]
    
    # Merge PostgreSQL and MongoDB data
    df = df_pg.merge(df_mongo, on="customer_id", how="left")
    
    # Neo4j data fetch (if still needed for other features)
    neo4j_query = "MATCH (c:Customer)-[r:MADE]->(o:Order) RETURN c.customer_id, o.order_id, o.fraud_score"
    with neo4j_driver.session() as session:
        results = session.run(neo4j_query)
        df_neo4j = pd.DataFrame([record.values() for record in results], 
                               columns=["customer_id", "order_id", "fraud_score"])
    
    # Merge Neo4j data if needed
    df = df.merge(df_neo4j, on="customer_id", how="left")
    
    # Prepare final features and target
    X = df.select_dtypes(include=['int64', 'float64'])
    
    # Use fraud_label from MongoDB as the target variable
    y = df["fraud_label"]  # Ensure this column exists in df
    
    # Drop fraud_score if it exists in X
    if 'fraud_score' in X.columns:
        X = X.drop(columns=['fraud_score'])
    
    return X, y

def prepare_data(X, y):
    """Prepare data for modeling by handling missing values and scaling."""
    if isinstance(X, pd.DataFrame):
        numeric_columns = X.select_dtypes(include=['int64', 'float64']).columns
        X = X[numeric_columns]
    
    # Handle missing values
    imputer = SimpleImputer(strategy='mean')
    X = imputer.fit_transform(X)
    
    # Scale features
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    
    return X, y

def get_transformed_data():
    """Main function to get transformed data ready for modeling."""
    pg_engine, mongo_client, neo4j_driver = connect_to_databases()
    mongo_db = mongo_client['ecommerce']
    X, y = fetch_data(pg_engine, mongo_db, neo4j_driver)
    
    # Validate data
    if len(np.unique(y)) < 2:
        print("Warning: Dataset contains only one class!")
        print(f"Total samples: {len(y)}")
        print(f"Unique classes: {np.unique(y)}")
        raise ValueError("Dataset must contain samples from at least 2 classes")
    
    X, y = prepare_data(X, y)
    return X, y

# Create output directory for models and plots
output_dir = './ml/visual'
os.makedirs(output_dir, exist_ok=True)

def plot_confusion_matrix(cm, model_name):
    """Plot confusion matrix."""
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', cbar=False,
                xticklabels=['Not Fraud', 'Fraud'], yticklabels=['Not Fraud', 'Fraud'])
    plt.title(f'Confusion Matrix for {model_name}')
    plt.xlabel('Predicted')
    plt.ylabel('True')
    plt.savefig(f'{output_dir}confusion_matrix_{model_name}.png')
    plt.close()

def plot_model_performance(results):
    """Plot performance metrics for each model."""
    metrics = pd.DataFrame(results).T
    metrics = metrics[['AUC-ROC', 'F1 Score']]
    
    plt.figure(figsize=(10, 6))
    metrics.plot(kind='bar', legend=True)
    plt.title('Model Performance Comparison')
    plt.ylabel('Score')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f'{output_dir}model_performance_comparison.png')
    plt.close()

def plot_feature_importance(model, feature_names, model_name):
    """Plot feature importance for tree-based models."""
    if hasattr(model, 'feature_importances_'):
        importances = model.feature_importances_
        indices = np.argsort(importances)[::-1]
        
        plt.figure(figsize=(10, 6))
        plt.title(f'Feature Importances for {model_name}')
        plt.bar(range(len(importances)), importances[indices], align='center')
        plt.xticks(range(len(importances)), np.array(feature_names)[indices], rotation=90)
        plt.xlim([-1, len(importances)])
        plt.tight_layout()
        plt.savefig(f'{output_dir}feature_importance_{model_name}.png')
        plt.close()

def plot_correlation_heatmap(X):
    """Plot heatmap of feature correlations."""
    plt.figure(figsize=(12, 10))
    correlation_matrix = pd.DataFrame(X).corr()
    sns.heatmap(correlation_matrix, annot=True, fmt=".2f", cmap='coolwarm', square=True)
    plt.title('Feature Correlation Heatmap')
    plt.tight_layout()
    plt.savefig(f'{output_dir}feature_correlation_heatmap.png')
    plt.close()
    
def save_best_model(results, models):
    best_model_name = max(results, key=lambda x: results[x]["R2"])
    best_model = models[best_model_name]
    path = f"/app/ml/{best_model_name.replace(' ', '_').lower()}_model.pkl"
    joblib.dump(best_model, path)
    return path, best_model_name, results[best_model_name]

def main():
    # Get transformed data
    X, y = get_transformed_data()
    
    # Check the distribution of the target variable
    print("Class distribution:")
    print(y.value_counts())
    
    # Split the dataset into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Initialize models
    models = {
        "Logistic Regression": LogisticRegression(),
        "Random Forest": RandomForestClassifier(),
        "Gradient Boosting": GradientBoostingClassifier()
    }
    
    results = {}
    
    for model_name, model in models.items():
        # Train the model
        model.fit(X_train, y_train)
        
        # Make predictions
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        
        # Evaluate the model
        print(f"Classification Report for {model_name}:")
        report = classification_report(y_test, y_pred, output_dict=True)
        print(classification_report(y_test, y_pred))
        
        # Confusion Matrix
        cm = confusion_matrix(y_test, y_pred)
        plot_confusion_matrix(cm, model_name)
        
        # Get the positive class label
        positive_class = str(1) if 1 in np.unique(y) else str(0)  # Adjust based on your class labels
        
        # Store results
        results[model_name] = {
            "AUC-ROC": roc_auc_score(y_test, y_pred_proba),
            "F1 Score": report[positive_class]['f1-score']  # Access F1 Score for the positive class
        }
        
        # Plot feature importance for tree-based models
        if model_name in ["Random Forest", "Gradient Boosting"]:
            plot_feature_importance(model, feature_names=X.columns, model_name=model_name)
            
        save_best_model(results, models)
    
    # Plot model performance
    plot_model_performance(results)
    
    # Plot correlation heatmap
    plot_correlation_heatmap(X)

if __name__ == "__main__":
    main()