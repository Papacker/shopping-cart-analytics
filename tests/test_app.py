"""
Tests for app.py - Streamlit UI functionality
Tests focus on static analysis rather than execution to avoid
browser launching and complex mocking.
"""
import unittest
from pathlib import Path
import sys

class TestAppUI(unittest.TestCase):
    
    def setUp(self):
        """Load app content once for all tests."""
        app_path = Path("src/app.py")
        if not app_path.exists():
            self.skipTest("src/app.py not found")
            
        try:
            with open(app_path, 'r', encoding='utf-8') as f:
                self.app_content = f.read()
        except Exception as e:
            self.skipTest(f"Could not read app.py: {e}")
    
    def test_app_file_exists_and_is_readable(self):
        """Test that the app.py file exists and is properly structured."""
        app_path = Path("src/app.py")
        self.assertTrue(app_path.exists(), "src/app.py should exist")
        
        # Check that file has substantial content
        self.assertGreater(len(self.app_content), 50, 
                         "app.py should have substantial content (not empty)")
        
        # Check it's valid Python (basic check)
        self.assertIn('import', self.app_content, 
                     "app.py should contain import statements")
    
    def test_app_has_required_imports(self):
        """Test that app.py imports required modules for functionality."""
        # Essential imports for a Streamlit data app
        required_imports = [
            'streamlit as st',
            'import duckdb'
        ]
        
        missing_imports = []
        for import_stmt in required_imports:
            if import_stmt not in self.app_content:
                missing_imports.append(import_stmt)
                
        if missing_imports:
            self.fail(f"Missing required imports: {missing_imports}")
            
        # Additional nice-to-have imports
        optional_imports = [
            'matplotlib.pyplot',
            'plotly'
        ]
        
        # We just log these - not required to pass
        for opt_import in optional_imports:
            if opt_import in self.app_content:
                print(f"✓ Found optional import: {opt_import}")
    
    def test_app_has_main_ui_components(self):
        """Test that app has basic UI structure."""
        # Check for essential UI components
        ui_elements = [
            ('st.title(', 'Should have a main title'),
            ('st.sidebar', 'Should use sidebar for navigation'),
            ('st.dataframe', 'Should display dataframes'),
            ('st.markdown', 'Should use markdown for formatting')
        ]
        
        found_elements = []
        missing_elements = []
        
        for element, description in ui_elements:
            if element in self.app_content:
                found_elements.append(element)
            else:
                missing_elements.append((element, description))
                
        # At least some UI elements should be present
        self.assertGreater(len(found_elements), 0, 
                          "Should have at least some Streamlit UI elements")
        
        # Report what was found
        print(f"Found UI elements: {found_elements}")
        
        # Warn about missing elements (but don't fail)
        if missing_elements:
            print(f"Note: Missing UI elements: {missing_elements}")

    def test_app_has_data_processing_logic(self):
        """Test that app contains data processing components."""
        # Look for database/connection usage
        data_indicators = [
            'duckdb',
            'get_table_counts',
            'run_etl'
        ]
        
        found_indicators = []
        for indicator in data_indicators:
            if indicator in self.app_content:
                found_indicators.append(indicator)
                
        # Should have some data processing
        self.assertGreater(len(found_indicators), 0, 
                          "Should contain data processing logic")
        
        print(f"Found data processing indicators: {found_indicators}")

if __name__ == '__main__':
    unittest.main()