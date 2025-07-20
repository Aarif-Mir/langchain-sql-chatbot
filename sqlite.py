import sqlite3

# connect to sqllite
connection=sqlite3.connect("student.db")

# create a cursor object to insert record,create table
cursor=connection.cursor()

# create the table
table_info="""
create table STUDENT(NAME VARCHAR(25),CLASS VARCHAR(25),
SECTION VARCHAR(25),MARKS INT)
"""

cursor.execute(table_info)

# Insert some more records
cursor.execute('''INSERT INTO STUDENT VALUES('Alice','Cyber Security','A',92)''')
cursor.execute('''INSERT INTO STUDENT VALUES('Bob','Machine Learning','B',78)''')
cursor.execute('''INSERT INTO STUDENT VALUES('Charlie','Cloud Computing','C',65)''')
cursor.execute('''INSERT INTO STUDENT VALUES('David','AI & Robotics','B',88)''')
cursor.execute('''INSERT INTO STUDENT VALUES('Eve','Blockchain','A',73)''')

# Display all the records
print("The inserted records are")
data=cursor.execute('''Select * from STUDENT''')
for row in data:
    print(row)

# Commit your changes in the database
connection.commit()
connection.close()
