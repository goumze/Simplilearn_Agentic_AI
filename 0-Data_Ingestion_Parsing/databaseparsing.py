import sqlite3
import os
from langchain_community.utilities import SQLDatabase
from langchain_community.document_loaders import SQLDatabaseLoader
from langchain_core import documents
from langchain_core.documents import Document
from typing import List

if __name__ == "__main__":
    os.makedirs("data/databases", exist_ok=True)

    # Create a sample SQLite database and table
    conn = sqlite3.connect("data/databases/company.db")
    cursor = conn.cursor()

    # Create a sample table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            skills TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            employee_id INTEGER,
            project_name TEXT NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (employee_id) REFERENCES employees (id)
        )
    ''')

    # Insert sample data into the table
    sample_data = [
        (1, "John Doe", "Software Engineer", "Python, JavaScript, SQL"),
        (2, "Jane Smith", "Data Scientist", "Python, R, Machine Learning"),
        (3, "Alice Johnson", "DevOps Engineer", "Docker, Kubernetes, AWS")
    ]

    project = [
        (1, "RAG System", "In Progress"),
        (1, "Data Pipeline", "Completed"),
        (2, "Predictive Analytics", "In Progress"), 
        (2, "Customer Segmentation", "Completed"),
        (3, "CI/CD Pipeline", "In Progress"),
        (3, "Infrastructure Automation", "Completed")
    ]

    cursor.executemany('INSERT INTO employees VALUES (?, ?, ?, ?)', sample_data)
    conn.commit()
    cursor.executemany('INSERT INTO projects VALUES (?, ?, ?)', project)
    conn.commit()
    conn.close()

# Method 1: Sql Database utility
    db = SQLDatabase.from_uri("sqlite:///data/databases/company.db")
    print(db.get_usable_table_names())
    print(db.get_table_info(["employees"]))
    print(db.get_table_info(["projects"]))

    def load_sql_database() -> List[Document]:
        """ Convert SQL database to list of Documents with context """
        conn = sqlite3.connect("data/databases/company.db")
        cursor = conn.cursor()
        documents = []

        #Strategy 1: Create Documents for each table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
    
        for table in tables:
            #Get table name
            table_name = table[0]

            #Get table schema
            cursor.execute(f"PRAGMA table_info({table_name});")
            schema = cursor.fetchall()
            column_names = [col[1] for col in schema]

            #Get table data
            cursor.execute(f"SELECT * FROM {table_name};")
            rows = cursor.fetchall()

            #Create table overview document
            table_content = f"Table: {table_name}\nSchema: {', '.join(column_names)}\nTotal Records: {len(rows)}\n\n"

            #Add sample records
            table_content+= "Sample Records:\n"
            for row in rows[:5]:  # Add first 5 records as sample
                row_data = ", ".join([f"{col}: {val}" for col, val in zip(column_names, row)])
                table_content += f"{row_data}\n"

            doc = Document(page_content=table_content,
                       metadata={"source": f"SQL Table: {table_name}",
                                 "table_name": table_name,
                                 "column_names": column_names,
                                 "record_count": len(rows),
                                 "data_type": "sql_table_overview"})   


            documents.append(doc)

        conn.close()
        return documents

    loaded_documents = load_sql_database()

    print(f"Loaded {len(loaded_documents)} documents from SQL database:")
    for doc in loaded_documents:
        print(f"Document Metadata: {doc.metadata}")
        print(f"Document Content:\n{doc.page_content}\n")

    #Strategy 2: Create relatonship documents between employees and their projects
    print("Strategy 2: Create relationship documents between employees and their projects")
    conn = sqlite3.connect("data/databases/company.db")
    cursor = conn.cursor()
    cursor.execute('''
        SELECT e.name, e.role, p.project_name, p.status
        FROM employees e
        JOIN projects p ON e.id = p.employee_id
    ''')
    rows = cursor.fetchall()
    relationship_documents = []
    for row in rows:
        employee_name, role, project_name, status = row
        content = f"Employee: {employee_name}\nRole: {role}\nProject: {project_name}\nStatus: {status}"
        doc = Document(page_content=content,
                       metadata={"source": "Employee-Project Relationship",
                                 "employee_name": employee_name,
                                 "project_name": project_name,
                                 "relationship_type": "employee_project"})
        relationship_documents.append(doc)    
    conn.close()
    print(f"Loaded {len(relationship_documents)} relationship documents:")
    for doc in relationship_documents:
        print(f"Document Metadata: {doc.metadata}")
        print(f"Document Content:\n{doc.page_content}\n")   
