from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask("lets walk")  # Using __name__ is more conventional
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///steps.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # To suppress warning
db = SQLAlchemy(app)

class StepRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10), nullable=False, unique=True)  # Added unique constraint
    steps = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'<StepRecord {self.date}: {self.steps} steps>'

@app.route('/')
def main():
    records = StepRecord.query.order_by(StepRecord.date.desc()).all()
    total_steps = sum(record.steps for record in records)  # Calculate total steps
    return render_template('index.html', 
                         records=records, 
                         total_steps=total_steps,
                         current_date=datetime.now().strftime('%Y-%m-%d'))

@app.route('/add', methods=['POST'])
def add_record():
    data = request.get_json()  # More explicit than request.json
    
    # Add validation
    if not data or 'date' not in data or 'steps' not in data:
        return jsonify({'status': 'error', 'message': 'Missing data'}), 400
    
    try:
        steps = int(data['steps'])
        if steps <= 0:
            return jsonify({'status': 'error', 'message': 'Steps must be positive'}), 400
    except ValueError:
        return jsonify({'status': 'error', 'message': 'Invalid steps value'}), 400

    # Check for existing date
    if StepRecord.query.filter_by(date=data['date']).first():
        return jsonify({'status': 'error', 'message': 'Record for this date already exists'}), 400

    new_record = StepRecord(date=data['date'], steps=steps)
    db.session.add(new_record)
    db.session.commit()
    
    return jsonify({
        'status': 'success', 
        'id': new_record.id,
        'date': new_record.date,
        'steps': new_record.steps
    })

@app.route('/clear', methods=['DELETE'])
def clear_records():
    try:
        num_deleted = db.session.query(StepRecord).delete()
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': f'Deleted {num_deleted} records'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
