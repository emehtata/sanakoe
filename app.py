from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS quiz_groups (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            language_from TEXT NOT NULL,
            language_to TEXT NOT NULL
        );
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS words (
            id INTEGER PRIMARY KEY,
            word TEXT NOT NULL,
            translation TEXT NOT NULL,
            group_id INTEGER,
            FOREIGN KEY (group_id) REFERENCES quiz_groups(id)
        );
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return "Tervetuloa sanakoepeliin!"

@app.route('/teacher', methods=['GET', 'POST'])
def teacher():
    if request.method == 'POST':
        group_name = request.form['group_name']
        language_from = request.form['language_from']
        language_to = request.form['language_to']
        word_list = request.form['word_list'].strip().split('\n')
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('INSERT INTO quiz_groups (name, language_from, language_to) VALUES (?, ?, ?)',
                  (group_name, language_from, language_to))
        group_id = c.lastrowid
        for line in word_list:
            word, translation = map(str.strip, line.split(';'))
            c.execute('INSERT INTO words (word, translation, group_id) VALUES (?, ?, ?)',
                      (word, translation, group_id))
        conn.commit()
        conn.close()
        return redirect(url_for('teacher'))
    return render_template('teacher.html')

@app.route('/student', methods=['GET', 'POST'])
def student():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    if request.method == 'POST':
        group_id = request.form['group_id']
        c.execute('SELECT word FROM words WHERE group_id = ?', (group_id,))
        words = c.fetchall()
        conn.close()
        return render_template('student_quiz.html', words=[w[0] for w in words])
    else:
        c.execute('SELECT id, name, language_from, language_to FROM quiz_groups')
        groups = c.fetchall()
        conn.close()
        return render_template('student.html', groups=groups)

@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    answers = request.form
    correct_count = 0
    total_count = len([key for key in answers.keys() if key.startswith('word_')])
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    results = []
    for i in range(1, total_count + 1):
        word = answers[f'word_{i}']
        answer = answers[f'answer_{i}'].strip().lower()
        c.execute('SELECT translation FROM words WHERE word = ?', (word,))
        correct_translation = c.fetchone()[0].lower()
        if answer == correct_translation:
            correct_count += 1
            results.append((word, answer, 'Oikein'))
        else:
            results.append((word, answer, f'Väärin (oikea: {correct_translation})'))
    conn.close()
    return render_template('quiz_result.html', results=results, correct_count=correct_count, total_count=total_count)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
