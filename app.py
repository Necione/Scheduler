from flask import Flask, request, render_template, redirect, url_for
import sqlite3

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('schedule.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL
    )''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS classes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        level TEXT CHECK(level IN ('HL', 'SL', 'None'))  -- 'None' for CIS/TOK
    )''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS student_classes (
        student_id INTEGER,
        class_id INTEGER,
        FOREIGN KEY (student_id) REFERENCES students (id),
        FOREIGN KEY (class_id) REFERENCES classes (id),
        PRIMARY KEY (student_id, class_id)
    )''')

    classes = [
        ('Math', 'HL'), ('Math', 'SL'),
        ('Biology', 'HL'), ('Biology', 'SL'),
        ('Chemistry', 'HL'), ('Chemistry', 'SL'),
        ('Physics', 'HL'), ('Physics', 'SL'),
        ('English', 'HL'), ('English', 'SL'),
        ('French', 'HL'), ('French', 'SL'),
        ('Spanish', 'HL'), ('Spanish', 'SL'),
        ('CIS/TOK', 'None')
    ]

    cursor.execute('SELECT COUNT(*) FROM classes')
    count = cursor.fetchone()[0]
    if count == 0:
        cursor.executemany('INSERT INTO classes (name, level) VALUES (?, ?)', classes)

    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    conn = sqlite3.connect('schedule.db')
    conn.row_factory = sqlite3.Row  
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM students')
    students_rows = cursor.fetchall()

    students = [dict(student) for student in students_rows]  

    for student in students:
        cursor.execute('''
            SELECT c.name, c.level 
            FROM classes c
            JOIN student_classes sc ON c.id = sc.class_id
            WHERE sc.student_id = ?
        ''', (student['id'],))
        student_classes = cursor.fetchall()
        student['classes'] = [dict(cls) for cls in student_classes]  

    conn.close()
    return render_template('index.html', students=students)

@app.route('/add_student', methods=['POST'])
def add_student():
    name = request.form['name']
    conn = sqlite3.connect('schedule.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO students (name) VALUES (?)', (name,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/remove_student/<int:student_id>', methods=['POST'])
def remove_student(student_id):
    print(f"Removing student with ID: {student_id}")
    conn = sqlite3.connect('schedule.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM students WHERE id = ?', (student_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/assign_class/<int:student_id>', methods=['GET'])
def assign_class_form(student_id):
    conn = sqlite3.connect('schedule.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, name, level FROM classes
        WHERE id NOT IN (
            SELECT class_id FROM student_classes WHERE student_id = ?
        )
    ''', (student_id,))
    unassigned_classes = cursor.fetchall()

    cursor.execute('''
        SELECT c.id, c.name, c.level FROM classes c
        JOIN student_classes sc ON c.id = sc.class_id
        WHERE sc.student_id = ?
    ''', (student_id,))
    assigned_classes = cursor.fetchall()
    conn.close()
    return render_template('assign_class.html', student_id=student_id, classes=unassigned_classes, assigned_classes=assigned_classes)

@app.route('/remove_class/<int:student_id>/<int:class_id>', methods=['POST'])
def remove_class(student_id, class_id):
    conn = sqlite3.connect('schedule.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM student_classes WHERE student_id = ? AND class_id = ?', (student_id, class_id))
    conn.commit()
    conn.close()
    return redirect(url_for('assign_class_form', student_id=student_id))

@app.route('/assign_class/<int:student_id>', methods=['POST'])
def assign_class(student_id):
    class_id = request.form['class_id']
    if not class_id:
        print("No class_id found in form submission.")
        return redirect(url_for('assign_class_form', student_id=student_id))

    conn = sqlite3.connect('schedule.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM student_classes WHERE student_id = ? AND class_id = ?', (student_id, class_id))
    if cursor.fetchone() is None:
        cursor.execute('INSERT INTO student_classes (student_id, class_id) VALUES (?, ?)', (student_id, class_id))
        conn.commit()
        print(f"Class {class_id} assigned to student {student_id}.")
    else:
        print(f"Class {class_id} already assigned to student {student_id}.")
    conn.close()
    return redirect(url_for('assign_class_form', student_id=student_id))



if __name__ == '__main__':
    app.run(debug=True)