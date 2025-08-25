#!/usr/bin/env python3
"""
Simple PostgreSQL Database Browser for OpsFlow Guardian 2.0
A basic GUI tool to view and interact with your database
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import psycopg2
import psycopg2.extras
import json
from datetime import datetime

class DatabaseBrowser:
    def __init__(self, root):
        self.root = root
        self.root.title("OpsFlow Guardian 2.0 - Database Browser")
        self.root.geometry("1200x800")
        
        # Connection details
        self.conn_params = {
            'host': 'localhost',
            'port': '5432',
            'database': 'opsflow_guardian',
            'user': 'opsflow',
            'password': '12345'
        }
        
        self.connection = None
        self.setup_ui()
        self.connect_to_database()
        
    def setup_ui(self):
        """Setup the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Connection status
        self.status_label = ttk.Label(main_frame, text="Connecting to database...")
        self.status_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tables tab
        self.create_tables_tab()
        
        # Query tab
        self.create_query_tab()
        
        # Data viewer tab
        self.create_data_tab()
        
        # Schema tab
        self.create_schema_tab()
        
    def create_tables_tab(self):
        """Create tables overview tab"""
        tables_frame = ttk.Frame(self.notebook)
        self.notebook.add(tables_frame, text="Tables Overview")
        
        # Table list
        ttk.Label(tables_frame, text="Database Tables:", font=('Arial', 12, 'bold')).pack(anchor=tk.W, pady=(10, 5))
        
        # Create treeview for tables
        self.tables_tree = ttk.Treeview(tables_frame, columns=('rows', 'columns'), show='tree headings')
        self.tables_tree.heading('#0', text='Table Name')
        self.tables_tree.heading('rows', text='Row Count')
        self.tables_tree.heading('columns', text='Column Count')
        
        # Scrollbar for tables
        tables_scrollbar = ttk.Scrollbar(tables_frame, orient=tk.VERTICAL, command=self.tables_tree.yview)
        self.tables_tree.configure(yscrollcommand=tables_scrollbar.set)
        
        # Pack table view
        table_frame = ttk.Frame(tables_frame)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.tables_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tables_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Refresh button
        ttk.Button(tables_frame, text="Refresh Tables", command=self.load_tables).pack(pady=10)
        
    def create_query_tab(self):
        """Create SQL query tab"""
        query_frame = ttk.Frame(self.notebook)
        self.notebook.add(query_frame, text="SQL Query")
        
        # Query input
        ttk.Label(query_frame, text="SQL Query:", font=('Arial', 12, 'bold')).pack(anchor=tk.W, pady=(10, 5))
        
        self.query_text = scrolledtext.ScrolledText(query_frame, height=8, wrap=tk.WORD)
        self.query_text.pack(fill=tk.BOTH, expand=False, pady=(0, 10))
        
        # Sample queries
        self.query_text.insert('1.0', '''-- Sample queries to get you started:

-- 1. View all companies
SELECT * FROM companies;

-- 2. View users with their companies
SELECT u.full_name, u.email, c.name as company_name, uc.role 
FROM users u 
JOIN user_companies uc ON u.id = uc.user_id 
JOIN companies c ON uc.company_id = c.id;

-- 3. View workflow performance
SELECT * FROM workflow_performance;

-- 4. View recent workflow executions
SELECT w.name, we.status, we.started_at, we.duration_seconds 
FROM workflow_executions we 
JOIN workflows w ON we.workflow_id = w.id 
ORDER BY we.started_at DESC LIMIT 10;''')
        
        # Execute button
        ttk.Button(query_frame, text="Execute Query", command=self.execute_query).pack(pady=5)
        
        # Results
        ttk.Label(query_frame, text="Query Results:", font=('Arial', 12, 'bold')).pack(anchor=tk.W, pady=(10, 5))
        
        self.results_tree = ttk.Treeview(query_frame)
        results_scrollbar_v = ttk.Scrollbar(query_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        results_scrollbar_h = ttk.Scrollbar(query_frame, orient=tk.HORIZONTAL, command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=results_scrollbar_v.set, xscrollcommand=results_scrollbar_h.set)
        
        # Pack results
        results_frame = ttk.Frame(query_frame)
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        results_scrollbar_v.pack(side=tk.RIGHT, fill=tk.Y)
        results_scrollbar_h.pack(side=tk.BOTTOM, fill=tk.X)
        
    def create_data_tab(self):
        """Create data viewer tab"""
        data_frame = ttk.Frame(self.notebook)
        self.notebook.add(data_frame, text="Data Viewer")
        
        # Table selector
        selector_frame = ttk.Frame(data_frame)
        selector_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(selector_frame, text="Select Table:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.table_var = tk.StringVar()
        self.table_combo = ttk.Combobox(selector_frame, textvariable=self.table_var, state='readonly')
        self.table_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.table_combo.bind('<<ComboboxSelected>>', self.load_table_data)
        
        ttk.Button(selector_frame, text="Load Data", command=self.load_table_data).pack(side=tk.LEFT)
        
        # Data display
        ttk.Label(data_frame, text="Table Data:", font=('Arial', 12, 'bold')).pack(anchor=tk.W, pady=(10, 5))
        
        self.data_tree = ttk.Treeview(data_frame)
        data_scrollbar_v = ttk.Scrollbar(data_frame, orient=tk.VERTICAL, command=self.data_tree.yview)
        data_scrollbar_h = ttk.Scrollbar(data_frame, orient=tk.HORIZONTAL, command=self.data_tree.xview)
        self.data_tree.configure(yscrollcommand=data_scrollbar_v.set, xscrollcommand=data_scrollbar_h.set)
        
        # Pack data view
        data_view_frame = ttk.Frame(data_frame)
        data_view_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.data_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        data_scrollbar_v.pack(side=tk.RIGHT, fill=tk.Y)
        data_scrollbar_h.pack(side=tk.BOTTOM, fill=tk.X)
        
    def create_schema_tab(self):
        """Create database schema tab"""
        schema_frame = ttk.Frame(self.notebook)
        self.notebook.add(schema_frame, text="Database Schema")
        
        self.schema_text = scrolledtext.ScrolledText(schema_frame, wrap=tk.WORD)
        self.schema_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Button(schema_frame, text="Load Schema", command=self.load_schema).pack(pady=5)
        
    def connect_to_database(self):
        """Connect to PostgreSQL database"""
        try:
            self.connection = psycopg2.connect(**self.conn_params)
            self.status_label.config(text="✅ Connected to opsflow_guardian database", foreground="green")
            self.load_tables()
            self.load_table_names()
        except Exception as e:
            self.status_label.config(text=f"❌ Connection failed: {str(e)}", foreground="red")
            messagebox.showerror("Connection Error", f"Failed to connect to database:\n{str(e)}")
            
    def load_tables(self):
        """Load table information"""
        if not self.connection:
            return
            
        try:
            cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # Clear existing items
            for item in self.tables_tree.get_children():
                self.tables_tree.delete(item)
                
            # Get table information
            cursor.execute("""
                SELECT 
                    t.table_name,
                    (SELECT COUNT(*) FROM information_schema.columns 
                     WHERE table_name = t.table_name AND table_schema = 'public') as column_count
                FROM information_schema.tables t
                WHERE t.table_schema = 'public' 
                AND t.table_type = 'BASE TABLE'
                ORDER BY t.table_name
            """)
            
            tables = cursor.fetchall()
            
            for table in tables:
                # Get row count
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table['table_name']}")
                    row_count = cursor.fetchone()[0]
                except:
                    row_count = "N/A"
                
                self.tables_tree.insert('', 'end', 
                                      text=table['table_name'],
                                      values=(row_count, table['column_count']))
            
            cursor.close()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load tables: {str(e)}")
            
    def load_table_names(self):
        """Load table names for combobox"""
        if not self.connection:
            return
            
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            
            tables = [row[0] for row in cursor.fetchall()]
            self.table_combo['values'] = tables
            
            cursor.close()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load table names: {str(e)}")
            
    def execute_query(self):
        """Execute SQL query"""
        if not self.connection:
            return
            
        query = self.query_text.get('1.0', tk.END).strip()
        if not query:
            return
            
        try:
            cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute(query)
            
            # Clear previous results
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)
            
            if cursor.description:  # SELECT query
                # Setup columns
                columns = [desc[0] for desc in cursor.description]
                self.results_tree['columns'] = columns
                self.results_tree['show'] = 'headings'
                
                for col in columns:
                    self.results_tree.heading(col, text=col)
                    self.results_tree.column(col, width=100)
                
                # Insert data
                results = cursor.fetchall()
                for row in results:
                    values = []
                    for col in columns:
                        value = row[col]
                        if isinstance(value, (dict, list)):
                            value = json.dumps(value, indent=2)
                        elif isinstance(value, datetime):
                            value = value.strftime('%Y-%m-%d %H:%M:%S')
                        elif value is None:
                            value = "NULL"
                        values.append(str(value))
                    self.results_tree.insert('', 'end', values=values)
                
                messagebox.showinfo("Success", f"Query executed successfully. {len(results)} rows returned.")
            else:  # INSERT, UPDATE, DELETE, etc.
                self.connection.commit()
                messagebox.showinfo("Success", "Query executed successfully.")
            
            cursor.close()
            
        except Exception as e:
            messagebox.showerror("Query Error", f"Failed to execute query:\n{str(e)}")
            
    def load_table_data(self, event=None):
        """Load data for selected table"""
        table_name = self.table_var.get()
        if not table_name or not self.connection:
            return
            
        try:
            cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 100")
            
            # Clear previous data
            for item in self.data_tree.get_children():
                self.data_tree.delete(item)
            
            if cursor.description:
                # Setup columns
                columns = [desc[0] for desc in cursor.description]
                self.data_tree['columns'] = columns
                self.data_tree['show'] = 'headings'
                
                for col in columns:
                    self.data_tree.heading(col, text=col)
                    self.data_tree.column(col, width=100)
                
                # Insert data
                results = cursor.fetchall()
                for row in results:
                    values = []
                    for col in columns:
                        value = row[col]
                        if isinstance(value, (dict, list)):
                            value = json.dumps(value, default=str)[:50] + "..." if len(str(value)) > 50 else json.dumps(value, default=str)
                        elif isinstance(value, datetime):
                            value = value.strftime('%Y-%m-%d %H:%M:%S')
                        elif value is None:
                            value = "NULL"
                        else:
                            value = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
                        values.append(value)
                    self.data_tree.insert('', 'end', values=values)
            
            cursor.close()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load table data: {str(e)}")
            
    def load_schema(self):
        """Load database schema information"""
        if not self.connection:
            return
            
        try:
            cursor = self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            schema_info = "🗄️ OpsFlow Guardian 2.0 - Database Schema\n"
            schema_info += "=" * 60 + "\n\n"
            
            # Get all tables
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            
            tables = cursor.fetchall()
            
            for table in tables:
                table_name = table['table_name']
                schema_info += f"📋 TABLE: {table_name.upper()}\n"
                schema_info += "-" * 30 + "\n"
                
                # Get columns
                cursor.execute("""
                    SELECT 
                        column_name, 
                        data_type, 
                        is_nullable,
                        column_default
                    FROM information_schema.columns 
                    WHERE table_name = %s 
                    AND table_schema = 'public'
                    ORDER BY ordinal_position
                """, (table_name,))
                
                columns = cursor.fetchall()
                
                for col in columns:
                    nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                    default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                    schema_info += f"  • {col['column_name']:<25} {col['data_type']:<15} {nullable}{default}\n"
                
                # Get row count
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    row_count = cursor.fetchone()[0]
                    schema_info += f"\n  📊 Total Records: {row_count}\n"
                except:
                    schema_info += f"\n  📊 Total Records: N/A\n"
                
                schema_info += "\n"
            
            # Add views
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.views 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            
            views = cursor.fetchall()
            
            if views:
                schema_info += "\n🔍 VIEWS:\n"
                schema_info += "-" * 30 + "\n"
                for view in views:
                    schema_info += f"  • {view['table_name']}\n"
            
            self.schema_text.delete('1.0', tk.END)
            self.schema_text.insert('1.0', schema_info)
            
            cursor.close()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load schema: {str(e)}")

def main():
    # Check if required modules are available
    try:
        import psycopg2
    except ImportError:
        print("❌ psycopg2 not found. Install with: pip install psycopg2-binary")
        return
    
    root = tk.Tk()
    app = DatabaseBrowser(root)
    root.mainloop()

if __name__ == "__main__":
    main()
