from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import functools

app = Flask(__name__)
app.secret_key = "psk_inspection_key_2026"

USERS = {
    "pskhmfg": "pskhmfg1234",
    "pskhqm": "pskhqm1234"
}

requests_data = []
next_id = 1

def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            if request.path.startswith('/api/'):
                return jsonify({"error": "Unauthorized"}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if USERS.get(username) == password:
            session.permanent = True
            session['username'] = username
            return redirect(url_for('index'))
        return "<script>alert('아이디 또는 비밀번호가 틀렸습니다.'); history.back();</script>", 401
    return render_template('login.html')

@app.route('/api/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/user')
@login_required
def get_user():
    return jsonify({"username": session['username']})

@app.route('/api/requests', methods=['GET'])
@login_required
def get_requests():
    return jsonify(requests_data)

@app.route('/api/requests/sync', methods=['POST'])
@login_required
def sync_requests():
    global next_id
    new_items = request.json
    if not new_items: return jsonify({"success": True})
    for item in new_items:
        item['id'] = next_id
        item['status'] = '검사 요청'
        item['qm_pic'] = ''
        item['reject_reason'] = ''
        requests_data.append(item)
        next_id += 1
    return jsonify({"success": True})

@app.route('/api/respond', methods=['POST'])
@login_required
def respond_request():
    data = request.json
    req_id = data.get('id')
    for item in requests_data:
        if item['id'] == req_id:
            if 'status' in data: item['status'] = data['status']
            if 'qm_pic' in data: item['qm_pic'] = data['qm_pic']
            if 'reject_reason' in data: item['reject_reason'] = data['reject_reason']
            if 'req_date' in data: item['req_date'] = data['req_date']
            if 'req_time' in data: item['req_time'] = data['req_time']
            if data.get('status') == '확정':
                item['reject_reason'] = ''
            return jsonify({"success": True})
    return jsonify({"error": "Not found"}), 404

@app.route('/api/requests/<int:req_id>/delete', methods=['POST'])
@login_required
def delete_request(req_id):
    if session.get('username') != 'pskhmfg':
        return jsonify({"error": "Permission denied"}), 403
    global requests_data
    requests_data = [i for i in requests_data if i['id'] != req_id]
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
