import pandas as pd
import os
from langchain_community.document_loaders import CSVLoader, UnstructuredExcelLoader
from langchain_core.documents import Document

if __name__ == "__main__":
    os.makedirs('data/structured_files', exist_ok=True)

    #Create sample data
    data = {
        'Product':['Laptop', 'Smartphone', 'Tablet', 'Headphones', 'Smartwatch'],
        'Price':[1200, 800, 400, 150, 250],
        'Category':['Electronics', 'Electronics', 'Electronics', 'Accessories', 'Wearables'],
        'Stock':[50, 100, 75, 200, 150],
        'Description':['High-performance laptop', 'Latest model smartphone', 'Portable tablet', 'Noise-cancelling headphones', 'Feature-rich smartwatch']
    }

    #Save as CSV
    df = pd.DataFrame(data)
    df.to_csv('data/structured_files/products.csv', index=False)

    #Save as Excel
    df.to_excel('data/structured_files/products.xlsx', index=False)

    #Save as excel with multiple sheets
    with pd.ExcelWriter('data/structured_files/products_multisheet.xlsx') as writer:
        df.to_excel(writer, sheet_name='Products', index=False)
        df.to_excel(writer, sheet_name='Inventory', index=False)

        #Add another sheet with summary statistics
        summary_data = {
            'Category': ['Electronics', 'Accessories', 'Wearables'],
            'Total Products': [3, 1, 1],
            'Average Price': [800, 150, 250],
            'Total Stock': [225, 200, 150]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)

    #Method 1: CSV loader - Each row becomes a document
    print("--------CSV Loader---------------------------")
    try:
        csv_loader = CSVLoader(file_path='data/structured_files/products.csv', encoding='utf-8',csv_args={'delimiter': ',', 'quotechar': '"'})
        csv_documents = csv_loader.load()
        print(f"Loaded {len(csv_documents)} documents from CSV")
        for doc_num, page in enumerate(csv_documents):
            print(f"\nDocument {doc_num + 1}:")
            print(f"Content: {page.page_content}")
            print(f"Metadata: {page.metadata}")
    except Exception as e:
        print(f"Error loading CSV: {e}")

#Method 2: Better CSV loader with error handling and support for different delimiters
    print("--------Enhanced CSV Loader---------------------------")
    try:
        enhanced_csv_loader = CSVLoader(file_path='data/structured_files/products.csv', encoding='utf-8', csv_args={'delimiter': ',', 'quotechar': '"'})
        enhanced_csv_documents = enhanced_csv_loader.load()
        print(f"Loaded {len(enhanced_csv_documents)} documents from enhanced CSV loader")
        documents = []  
        
        #Strategy 1: One document per row with structured content
        for idx,row in df.iterrows():
            content = f"Product: {row['Product']}\nPrice: {row['Price']}\nCategory: {row['Category']}\nStock: {row['Stock']}\nDescription: {row['Description']}"
            metadata = {
                'source': 'products.csv',
                'row_index': idx,
                'product': row['Product'],
                'price': row['Price'],
                'category': row['Category'],
                'stock': row['Stock']
            }
            #Create a document for each row with structured content and metadata
            doc = Document(page_content=content, metadata={
                'source': 'products.csv',
                'row_index': idx,
                'product': row['Product'],
                'price': row['Price'],
                'category': row['Category'],
                'stock': row['Stock'],
                'data_type': 'product_info'
            })
            documents.append(doc)
    except Exception as e:
        print(f"Error loading CSV with enhanced loader: {e}")  

    #Excel Processing
    print("--------Pandas based Excel Processing---------------------------")
    def process_excel_with_pandas(file_path):
        try:
            #Read all sheets in the Excel file
            xls = pd.ExcelFile(file_path)
            all_sheets = xls.sheet_names
            print(f"Found sheets: {all_sheets}")
            
            documents = []
            for sheet in all_sheets:
                df = pd.read_excel(xls, sheet_name=sheet)
                content = f"Sheet: {sheet}\n\n{df.to_string(index=False)}"
                metadata = {
                    'source': os.path.basename(file_path),
                    'sheet_name': sheet,
                    'data_type': 'excel_sheet',
                    'num_rows': len(df),
                    'num_columns': len(df.columns),
                    'data_types': 'excel_sheet'              
                }
                doc = Document(page_content=content, metadata=metadata)
                documents.append(doc)
            return documents
        except Exception as e:
            print(f"Error processing Excel with pandas: {e}")
            return []

    print(process_excel_with_pandas('data/structured_files/products_multisheet.xlsx'))

    #Method 3: UnstructuredExcelLoader - Each sheet becomes a document
    print("--------UnstructuredExcelLoader---------------------------")
    try:
        unstructured_excel_loader = UnstructuredExcelLoader(file_path='data/structured_files/products_multisheet.xlsx')
        unstructured_excel_documents = unstructured_excel_loader.load()
        print(f"Loaded {len(unstructured_excel_documents)} documents from UnstructuredExcelLoader")
        for doc_num, page in enumerate(unstructured_excel_documents):
            print(f"\nDocument {doc_num + 1}:")
            print(f"Content: {page.page_content}")
            print(f"Metadata: {page.metadata}")
    except Exception as e:
        print(f"Error loading Excel with UnstructuredExcelLoader: {e}") 