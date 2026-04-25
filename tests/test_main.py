"""
Tests for main.py - ETL functionality
"""
import unittest
import tempfile
import os
import duckdb

class TestMainETL(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.test_dir, "test_store.db")
        
    def tearDown(self):
        """Tear down test fixtures after each test method."""
        # Clean up test database and directory
        if os.path.exists(self.test_db_path):
            os.unlink(self.test_db_path)
        if os.path.exists(self.test_dir):
            import shutil
            shutil.rmtree(self.test_dir)
            
    def test_initialize_database_function_exists(self):
        """Test that initialize_database function can be imported."""
        try:
            from main import initialize_database
            self.assertTrue(callable(initialize_database), "initialize_database should be callable")
        except ImportError:
            self.fail("Failed to import initialize_database function from main.py")
            
    def test_database_initialization_with_simple_schema(self):
        """Test database initialization with a simple schema."""
        # Create a simple schema file for testing
        schema_path = os.path.join(self.test_dir, "test_schema.sql")
        schema_content = '''
        CREATE TABLE IF NOT EXISTS test_table (
            id INTEGER PRIMARY KEY,
            name VARCHAR
        );
        '''
        
        with open(schema_path, 'w') as f:
            f.write(schema_content)
            
        # Import the function we want to test
        from main import initialize_database
        
        # Initialize database connection
        con = duckdb.connect(self.test_db_path)
        initialize_database(con, schema_path)
        
        # Check if tables are created properly
        tables = con.execute("SHOW TABLES").fetchall()
        self.assertIsNotNone(tables, "Database should have tables")
        
        # Check if our test table exists
        table_names = [table[0] for table in tables]
        self.assertIn('test_table', table_names, "test_table should exist")
        
        # Close connection
        con.close()
        
    def test_database_connection_works(self):
        """Test that we can create and connect to a DuckDB database."""
        # This is a very basic test to ensure DuckDB works
        con = duckdb.connect(self.test_db_path)
        
        # Create a simple table
        con.execute("CREATE TABLE IF NOT EXISTS sanity_check (id INTEGER)")
        
        # Check if table exists
        tables = con.execute("SHOW TABLES").fetchall()
        table_names = [table[0] for table in tables]
        self.assertIn('sanity_check', table_names, "Should be able to create tables")
        
        # Close connection
        con.close()
        self.assertTrue(os.path.exists(self.test_db_path), "Database file should exist")

if __name__ == '__main__':
    unittest.main()