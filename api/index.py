from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from supabase import create_client, Client
from datetime import timedelta

app = Flask(__name__)
app.secret_key = 'psk_secret_key_1234'
app.permanent_session_lifetime = timedelta(hours=8)

# Supabase 설정
SUPABASE_URL = "https://pynrccuetoyosgiavejf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB5bnJjY3VldG95b3NnaWF2ZWpmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYzMDg3MzksImV4cCI6MjA5MTg4NDczOX0.sfYn_X331DfKPN8B4IMZtKOLxjpGdQz75ujqYHhMSn8"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 계정 정보
USERS = {
    "pskhmfg": "pskhmfg1234",
    "pskhqm": "pskhqm1234"
}

@app.route('/')
def index():
    if 'logged_in' in session:
        return render_template('index.html')
    return redirect(url_for('login_page'))

@app.route('/login')
def login_page():
    return render_template('login.html')

# 로그인 API (JSON 통신)
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "데이터 형식이 잘못되었습니다."}), 400
    
    uid = data.get('id')
    upw = data.get('pw')
    
    if uid in USERS and USERS[uid] == upw:
        session.permanent = True
        session['logged_in'] = True
        session['username'] = uid
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "아이디 또는 비밀번호가 틀립니다."}), 401

@app.route('/api/logout')
def api_logout():
    session.clear()
    return redirect(url_for('login_page'))

@app.route('/api/user')
def get_user():
    if 'logged_in' not in session: return jsonify({}), 401
    return jsonify({"username": session.get('username')})

@app.route('/api/requests', methods=['GET'])
def get_requests():
    if 'logged_in' not in session: return jsonify([]), 401
    try:
        response = supabase.table("requests").select("*").order("id", desc=True).execute()
        return jsonify(response.data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/requests/sync', methods=['POST'])
def sync_requests():
    if 'logged_in' not in session: return jsonify({"msg": "Unauthorized"}), 401
    data = request.get_json()
    for d in data:
        d['status'] = '검사 요청'
        supabase.table("requests").insert(d).execute()
    return jsonify({"message": "Synced"}), 200

@app.route('/api/respond', methods=['POST'])
def respond_request():
    if 'logged_in' not in session: return jsonify({"msg": "Unauthorized"}), 401
    data = request.get_json()
    req_id = data.pop('id')
    
    # 확정 시 반려 사유를 빈 값으로 덮어써서 잔상 제거
    if data.get('status') == '확정':
        data['reject_reason'] = ''
        
    supabase.table("requests").update(data).eq("id", req_id).execute()
    return jsonify({"message": "Success"}), 200

@app.route('/api/requests/<int:req_id>/delete', methods=['POST'])
def delete_item(req_id):
    if 'logged_in' not in session: return jsonify({"msg": "Unauthorized"}), 401
    if session.get('username') != 'pskhmfg':
        return jsonify({"msg": "권한이 없습니다."}), 403
    supabase.table("requests").delete().eq("id", req_id).execute()
    return jsonify({"message": "Deleted"}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
