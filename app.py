from flask import Flask, render_template, request, redirect, url_for
import json
import os
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

DATA_FILE = 'car_maintenance_data.json'

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {'cars': {}, 'maintenance': {}, 'history': {}}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# -----------------------------------
# HOME PAGE
# -----------------------------------
@app.route('/')
def home():
    return render_template('home.html')


# -----------------------------------
# MAINTENANCE TASKS
# -----------------------------------
@app.route('/maintenance_tasks')
def maintenance_tasks():
    """
    Show a list of pending maintenance tasks for each car,
    and link to complete them.
    """
    data = load_data()
    return render_template('maintenance_tasks.html',
                           maintenance=data['maintenance'],
                           enumerate=enumerate)

@app.route('/add_maintenance', methods=['GET', 'POST'])
def add_maintenance():
    data = load_data()

    if request.method == 'POST':
        # Handle form submission to create a new maintenance task
        car_name = request.form['car_name']
        task = request.form['task']
        due_date = request.form['due_date']

        # Ensure the selected car exists
        if car_name not in data['cars']:
            # Optionally handle error or redirect
            return redirect(url_for('maintenance_tasks'))

        # Initialize maintenance list if needed
        if car_name not in data['maintenance']:
            data['maintenance'][car_name] = []

        # Add the new maintenance task
        data['maintenance'][car_name].append({
            'task': task,
            'due_date': due_date,
            'completed': False
        })

        # Save updated data to disk
        save_data(data)
        return redirect(url_for('maintenance_tasks'))

    # If GET, render the form so user can add a new task
    return render_template('add_maintenance.html', cars=data['cars'])

@app.route('/complete_maintenance_form/<car_name>/<int:task_index>')
def complete_maintenance_form(car_name, task_index):
    """
    Displays a form so the user can enter a note about what
    they did when completing the maintenance task.
    """
    return render_template('complete_maintenance.html',
                           car_name=car_name,
                           task_index=task_index)

@app.route('/complete_maintenance/<car_name>/<int:task_index>', methods=['POST'])
def complete_maintenance(car_name, task_index):
    """
    Marks a maintenance task as completed, storing any user note,
    and moves it to the history.
    """
    data = load_data()
    if car_name in data['maintenance'] and 0 <= task_index < len(data['maintenance'][car_name]):
        task = data['maintenance'][car_name].pop(task_index)
        task['completed'] = True
        task['completion_date'] = datetime.now().strftime('%Y-%m-%d')

        # Capture the note from the form
        note = request.form.get('note', '').strip()
        if note:
            task['note'] = note

        # Move completed task to history
        if car_name not in data['history']:
            data['history'][car_name] = []
        data['history'][car_name].append(task)

        save_data(data)
    return redirect(url_for('maintenance_tasks'))


# -----------------------------------
# MAINTENANCE HISTORY
# -----------------------------------
@app.route('/maintenance_history')
def maintenance_history():
    """
    Displays completed maintenance tasks by car, including notes.
    """
    data = load_data()
    return render_template('maintenance_history.html',
                           history=data['history'])


# -----------------------------------
# GARAGE
# -----------------------------------
@app.route('/garage')
def garage():
    """
    Displays the garage page, showing all cars and allowing
    the user to add a new car, edit car details, or remove a car.
    """
    data = load_data()
    return render_template('garage.html', cars=data['cars'])

@app.route('/add_car', methods=['POST'])
def add_car():
    """
    Adds a new car to the garage.
    """
    car_name = request.form['car_name']
    model_year = request.form['model_year']
    image = request.files['image']
    image_path = ''
    if image and image.filename.strip():
        image_filename = secure_filename(image.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
        image.save(image_path)

    data = load_data()
    if car_name not in data['cars']:
        data['cars'][car_name] = {
            'model_year': model_year,
            'image_path': image_path
        }
        save_data(data)
    return redirect(url_for('garage'))

@app.route('/edit_car/<car_name>', methods=['POST'])
def edit_car(car_name):
    """
    Edit an existing car's model year or image.
    """
    data = load_data()
    if car_name not in data['cars']:
        return redirect(url_for('garage'))

    model_year = request.form['model_year']
    image = request.files['image']

    data['cars'][car_name]['model_year'] = model_year
    if image and image.filename.strip():
        image_filename = secure_filename(image.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
        image.save(image_path)
        data['cars'][car_name]['image_path'] = image_path

    save_data(data)
    return redirect(url_for('garage'))

@app.route('/remove_car/<car_name>')
def remove_car(car_name):
    """
    Removes a car from the garage, along with its maintenance tasks
    and history.
    """
    data = load_data()
    if car_name in data['cars']:
        data['cars'].pop(car_name, None)
        data['maintenance'].pop(car_name, None)
        data['history'].pop(car_name, None)
        save_data(data)
    return redirect(url_for('garage'))


if __name__ == '__main__':
    app.run(debug=True)
