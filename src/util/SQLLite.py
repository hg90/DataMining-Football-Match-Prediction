import sqlite3

from src.util import util

sqllite_connection = None

class SQLiteConnection(object):
    def __init__(self, database_path="data/db/database.sqlite"):
        self.connection = sqlite3.connect(util.get_project_directory()+database_path)
        self.cursor = self.connection.cursor()

    def getTableNameDataBase(self):
        tables = []
        for row in self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';"):
            tables.append(row[0])
        return tables

    def getColumnFromTable(self, table_name):
        columns = []
        for r in self.cursor.execute("PRAGMA table_info("+table_name+");"):
            columns.append(r[1])
        return columns

    def select(self, table_name, column_filter='*', **id):
        id_condition = ""
        if len(id) > 0:
            id_condition = "WHERE "

            for attrbiute, value in id.items():
                id_condition += attrbiute+"='"+str(value)+"' AND "
            id_condition = id_condition[0:-4]

        if column_filter=='*':
            column_names = self.getColumnFromTable(table_name)
        else:
            column_names = column_filter.split(",")

        row_results = []
        for sqllite_row in self.cursor.execute("SELECT "+column_filter+" FROM "+table_name+" "+id_condition+";"):
            if sqllite_row is None:
                continue
            row = {}
            for i, name in enumerate(column_names):
                row[name] = sqllite_row[i]
            row_results.append(row)
        return row_results

    def execute_query(self, query):
        rows = []
        for row in self.cursor.execute(query):
            rows.append(row)
        return rows



def get_connection():
    global sqllite_connection
    if sqllite_connection is None:
        sqllite_connection = SQLiteConnection()

    return sqllite_connection

def read_all(table_name):
    return get_connection().select(table_name)