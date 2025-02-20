import pandas as pd
from sqlalchemy import create_engine, Table, MetaData, select, func
from sqlalchemy.engine import reflection
import streamlit as st
import os
POSTGRES_URL = "postgresql://postgres:password@localhost:5432/ecommerce"
#POSTGRES_URL = f"postgresql://{os.getenv('POSTGRES_USER', 'postgres')}:{os.getenv('POSTGRES_PASSWORD', 'password')}@{os.getenv('POSTGRES_HOST', 'postgres')}:{os.getenv('POSTGRES_PORT', '5432')}/{os.getenv('POSTGRES_DB', 'ecommerce')}"


print(POSTGRES_URL)
# Connect to PostgreSQL
pg_engine = create_engine(POSTGRES_URL)
inspector = reflection.Inspector.from_engine(pg_engine)
metadata = MetaData()
table_names = inspector.get_table_names()
#table_names = ['order_items', 'order_payments', 'order_reviews', 'orders', 'customers', 'geolocation', 'products', 'product_category_name_translation', 'sellers', 'leads_qualified', 'leads_closed']

def get_all_columns(table_name):
    columns = inspector.get_columns(table_name)
    column_names = {}
    for col in columns:
        column_names[col.get("name")] = col.get("type")
    return column_names
    
def show_postgres_tables(table_names: str):
    st.write(f"We have below {len(table_names)} tables in our Postgresql with DB = ecommerce.")
    st.write("They are namely")
    st.write(f"{', '.join(table_names)}.")
    
    tables = []
    table_schemas = []
    for name in table_names:
        table = Table(name, metadata, autoload_with=pg_engine)
        tables.append(table)
        columns = inspector.get_columns(name)
        
        for column in columns:
            dict = {}
            dict["table"] = name
            dict["col_name"] = column.get("name")
            dict["col_type"] = str(column.get("type"))
            table_schemas.append(dict)

    st.write("And here are their schemas.")
    df = pd.DataFrame(table_schemas)
    st.dataframe(df)

    count_dict = {}
    with pg_engine.connect() as conn:
        for table in tables:
            stmt = select(func.count()).select_from(table)
            result = conn.execute(stmt)
            count = result.scalar() 
            count_dict[str(table)] = count

    count_df = pd.DataFrame([{"table": name, "count": count} for name, count in count_dict.items()])
    st.write("How many rows do they have seperately:")  
    st.dataframe(count_df)  

@st.cache_data(ttl=0)
def check_data(table_option, columns_option, size: int, filter):
    query = ""
    if "All" in columns_option:
        query = f"SELECT * FROM {table_option} {filter} LIMIT {size}"
    else:
        query = f"SELECT {', '.join(columns_option)} FROM {table_option} {filter} LIMIT {size}"
    
    df = pd.read_sql(query, pg_engine)
    st.dataframe(df, use_container_width=True)

if __name__ == "__main__":   
    st.write("# Welcme to PostgreSQL")
    st.write("* **Table summary**")
    show_postgres_tables(table_names)


    st.write("* **Check data**")
    col1, col2 = st.columns(2)
    with col1:
        table_option = st.selectbox("Select table", tuple(table_names))
        columns_option = st.multiselect("Select columns", ("All", ) + tuple(get_all_columns(table_option).keys()))
    with col2:
        st.write("Filter condition")
        column = st.selectbox("Column", tuple(get_all_columns(table_option).keys()))
        logic = st.selectbox("Logic", tuple("="))
        value = st.text_input("Type in to the value") # c31a859e34e3adac22f376954e19b39d
    
    filter_condition = ""
    if all(x is not None and x != "" for x in (column, logic, value)):
        filter_condition = f"WHERE {column} {logic} '{value}'"   
        st.write(f"SELECT {columns_option} FROM {table_option} {filter_condition}")
    else:
        st.write(f"SELECT {columns_option} FROM {table_option}")
    

    size = st.slider("How many rows you wanna check?", 1, 100, 10)
    st.write("You selected:", table_option)

    check_button = st.button("Check", type="primary")

    if check_button:
        check_data(table_option, columns_option, size, filter_condition)
