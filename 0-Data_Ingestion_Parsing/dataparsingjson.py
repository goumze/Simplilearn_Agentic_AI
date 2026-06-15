import json
import os
from langchain_community.document_loaders import JSONLoader
from langchain_core.documents import Document
from typing import List
import json

if __name__ == "__main__":
    os.makedirs("data/json_files", exist_ok=True)


    sample_json_data = {
        "company": "Tech Solutions Inc.",
        "employees": [
        {
            "id":1,
            "name":"John Doe",
            "role":"Software Engineer",
            "skills":["Python", "JavaScript", "SQL"],
            "projects":[
                {"name":"RAG System", " status":"In Progress"},
                {"name":"Data Pipeline", "status":"Completed"}
            ]
        },
        {
            "id":2,
            "name":"Jane Smith",
            "role":"Data Scientist",
            "skills":["Python", "R", "Machine Learning"],
            "projects":[
                {"name":"Predictive Analytics", "status":"In Progress"},
                {"name":"Customer Segmentation", "status":"Completed"}
            ]
        },
        {
            "id":3,
            "name":"Alice Johnson",
            "role":"DevOps Engineer",
            "skills":["Docker", "Kubernetes", "AWS"],
            "projects":[
                {"name":"CI/CD Pipeline", "status":"In Progress"},
                {"name":"Infrastructure Automation", "status":"Completed"}
            ]
        }
        ],
        "departments":[
            {"name":"Engineering", "head":"John Doe"},
            {"name":"Data Science", "head":"Jane Smith"},
            {"name":"DevOps", "head":"Alice Johnson"}
        ]
    }

    with open("data/json_files/sample_data.json", "w") as json_file:
        json.dump(sample_json_data, json_file, indent=4)

    # Save formats in jsonl format
    jsonl_data = [
        {"id": 1, "name": "John Doe", "role": "Software Engineer", "skills": ["Python", "JavaScript", "SQL"]},
        {"id": 2, "name": "Jane Smith", "role": "Data Scientist", "skills": ["Python", "R", "Machine Learning"]},
        {"id": 3, "name": "Alice Johnson", "role": "DevOps Engineer", "skills": ["Docker", "Kubernetes", "AWS"]}
    ]

    with open("data/json_files/employee_profiles.jsonl", "w") as jsonl_file:
        for entry in jsonl_data:
            jsonl_file.write(json.dumps(entry) + "\n")  

    #Method 1: Json loader with jq schema
    print("Method 1: Json loader with jq schema")
    print("Json Loader - Extract specific fields")

    #Extract employee information
    employee_loader = JSONLoader(file_path="data/json_files/sample_data.json", jq_schema=".employees[] | {id, name, role, skills}", text_content=False)

    employee_docs = employee_loader.load()
    print(f"Loaded {len(employee_docs)} employee documents:")
    print(f"First employee document: {employee_docs[0].page_content}")
    print(employee_docs)

    def process_json_intelligently(json_file_path: str) -> List[Document]:
        """
        Process a JSON file intelligently and return a list of Document objects.
        
        Args:
            json_file_path (str): The path to the JSON file.
        """
        with open(json_file_path, 'r') as file:
            data = json.load(file)

        documents = []

        #Strategy 1: Create documents for each employee with full context
        for employee in data.get("employees", []):
            content = f"Employee ID: {employee['id']}\nName: {employee['name']}\nRole: {employee['role']}\nSkills: {', '.join(employee['skills'])}\nProjects: {', '.join([project['name'] + ')' for project in employee.get('projects', [])])}"
            
            doc = Document(page_content=content, metadata={
                "type": "employee", 
                "id": employee['id'],
                "source": json_file_path,
                "data_type": "employee_profile",
                'employee_name': employee['name'],
                'role': employee['role']
                })
            documents.append(doc)
        return documents
        

    # Process the sample JSON file intelligently
    processed_documents = process_json_intelligently("data/json_files/sample_data.json")
    print(f"Processed {len(processed_documents)} documents from the JSON file.")

            

