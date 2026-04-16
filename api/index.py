from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from supabase import create_client, Client
from datetime import timedelta
import os

app = Flask(__name__, template_folder='../templates')
app.secret_key = 'psk_secret_key_1234'
app.permanent_session_lifetime = timedelta(hours=8)

# 사용자 정보 및 데이터베이스 설정 반영 완료
SUPABASE_URL = "https://pynrccuetoyosgiavejf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB5bnJjY3VldG95b3NnaWF2ZWpmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYzMDg3MzksImV4cCI6MjA5MTg4NDczOX0.sfYn_X331DfKPN8B4IMZtKOLxjpGdQz75ujqYHhMSn8"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 로그인 정보
USER_DATA = {"id": "pskhmfg", "pw": "pskhmfg1234"}

@app.route('/')
def index():
    if 'logged_in' in session: return render_template('index.html')
    return redirect(url_for('login_page'))

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    if data.get('id') == USER_DATA['id'] and data.get('pw') == USER_DATA['pw']:
        session['logged_in'] = True
        return jsonify({"success": True})
    return jsonify({"success": False}), 401

@app.route('/api/logout')
def api_logout():
    session.pop('logged_in', None)
    return redirect(url_for('login_page'))

@app.route('/api/requests', methods=['GET'])
def get_requests():
    if 'logged_in' not in session: return jsonify([]), 401
    # DB에서 최신순으로 데이터 로드
    response = supabase.table("requests").select("*").order("id", desc=True).execute()
    return jsonify(response.data)

@app.route('/api/requests/sync', methods=['POST'])
def sync_requests():
    if 'logged_in' not in session: return jsonify({"msg": "Unauthorized"}), 401
    data = request.get_json()
    for d in data:
        d['status'] = '검사 요청'
        # 엑셀 데이터 DB 저장
        supabase.table("requests").insert(d).execute()
    return jsonify({"message": "Synced"}), 200

@app.route('/api/respond', methods=['POST'])
def respond_request():
    if 'logged_in' not in session: return jsonify({"msg": "Unauthorized"}), 401
    data = request.get_json()
    req_id = data.pop('id')
    # QM 피드백 결과 업데이트
    supabase.table("requests").update(data).eq("id", req_id).execute()
    return jsonify({"message": "Success"}), 200

@app.route('/api/requests/<int:req_id>/delete', methods=['POST'])
def delete_item(req_id):
    if 'logged_in' not in session: return jsonify({"msg": "Unauthorized"}), 401
    # 항목 삭제
    supabase.table("requests").delete().eq("id", req_id).execute()
    return jsonify({"message": "Deleted"}), 200

# Vercel 배포용 핸들러 설정
def handler(event, context):
    return app(event, context)

if __name__ == '__main__':
    app.run(debug=True)