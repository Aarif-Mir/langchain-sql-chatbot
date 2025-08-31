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
cursor.execute('''INSERT INTO STUDENT VALUES('Faizan','Cyber Security','A',92)''')
cursor.execute('''INSERT INTO STUDENT VALUES('Aatif','Machine Learning','B',78)''')
cursor.execute('''INSERT INTO STUDENT VALUES('Firdous','Cloud Computing','C',65)''')
cursor.execute('''INSERT INTO STUDENT VALUES('Aarif','AI & Robotics','B',95)''')
cursor.execute('''INSERT INTO STUDENT VALUES('Kaif','Blockchain','A',73)''')

# Display all the records
print("The inserted records are")
data=cursor.execute('''Select * from STUDENT''')
for row in data:
    print(row)

# Commit your changes in the database
connection.commit()
connection.close()
