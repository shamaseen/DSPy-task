import sqlite3
from typing import List, Dict, Any, Optional

class SQLiteTool:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def get_schema(self) -> str:
        """Returns the schema of the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        schema_str = ""
        for table in tables:
            table_name = table[0]
            cursor.execute(f"PRAGMA table_info('{table_name}');")
            columns = cursor.fetchall()
            
            schema_str += f"Table: {table_name}\n"
            for col in columns:
                # col[1] is name, col[2] is type
                schema_str += f"  - {col[1]} ({col[2]})\n"
            schema_str += "\n"
            
        conn.close()
        return schema_str

    def execute_query(self, query: str) -> Dict[str, Any]:
        """Executes a SQL query and returns the results."""
        try:
            conn = sqlite3.connect(self.db_path)
            # Use a row factory to get dictionary-like results if needed, 
            # but for now we'll stick to tuples and return column names.
            cursor = conn.cursor()
            cursor.execute(query)
            
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            
            conn.close()
            return {
                "columns": columns,
                "rows": rows,
                "error": None
            }
        except Exception as e:
            return {
                "columns": [],
                "rows": [],
                "error": str(e)
            }
