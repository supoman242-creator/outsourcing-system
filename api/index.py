from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime
import functools

app = Flask(__name__)
app.secret_key = "psk_secret_key_2026" # 세션 보안을 위한 키

# 1. 사용자 계정 정보 (요청하신 계정 반영)
USERS = {
    "pskhmfg": "pskhmfg1234", # 제조 G (Master 권한)
    "pskhqm": "pskhqm1234"    # 품질 G (조회/피드백 권한)
}

# 데이터 저장용 (DB 대신 메모리 사용 - 실제 운영시 DB 연결 권장)
requests_data = []
next_id = 1

# 로그인 체크 데코레이터
def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if USERS.get(username) == password:
            session['username'] = username
            return redirect(url_for('index'))
        return "로그인 실패: 아이디 또는 비밀번호를 확인하세요.", 401
    return '''
        <form method="post" style="display:flex; flex-direction:column; width:300px; margin:100px auto; gap:10px;">
            <h2 style="text-align:center;">출하검사 시스템 로그인</h2>
            <input name="username" placeholder="아이디" required style="padding:10px;">
            <input name="password" type="password" placeholder="비밀번호" required style="padding:10px;">
            <button type="submit" style="padding:10px; background:#5b21b6; color:white; border:none; cursor:pointer;">로그인</button>
        </form>
    '''

@app.route('/api/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

# 현재 로그인한 유저 정보 반환 (index.html에서 권한 제어용으로 사용)
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
            # 수정 모드(제조)와 확정/반려 모드(품질) 통합 처리
            if 'status' in data: item['status'] = data['status']
            if 'qm_pic' in data: item['qm_pic'] = data['qm_pic']
            if 'reject_reason' in data: item['reject_reason'] = data['reject_reason']
            if 'req_date' in data: item['req_date'] = data['req_date']
            if 'req_time' in data: item['req_time'] = data['req_time']
            
            # 개선: 확정(ACCEPT) 시에는 기존의 반려 사유를 초기화하여 '11' 같은 잔상이 남지 않게 함
            if data.get('status') == '확정':
                item['reject_reason'] = ''
            return jsonify({"success": True})
    return jsonify({"error": "Not found"}), 404

@app.route('/api/requests/<int:req_id>/delete', methods=['POST'])
@login_required
def delete_request(req_id):
    # 보안: 제조 계정(pskhmfg)만 삭제 가능하도록 서버에서도 체크
    if session.get('username') != 'pskhmfg':
        return jsonify({"error": "Permission denied"}), 403
        
    global requests_data
    requests_data = [i for i in requests_data if i['id'] != req_id]
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
