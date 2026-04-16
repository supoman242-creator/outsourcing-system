<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PSK 출하검사 시스템</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
        body { font-family: 'Noto Sans KR', sans-serif; background-color: #f8fafc; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .nav-btn.active { background-color: #4f46e5; color: white; }
        th { font-size: 11px; padding: 12px; background: #f1f5f9; border-bottom: 2px solid #e2e8f0; sticky; top: 0; }
        td { font-size: 12px; padding: 10px; border-bottom: 1px solid #f1f5f9; text-align: center; }
        .filter-input { width: 100%; font-size: 10px; padding: 4px; border: 1px solid #e2e8f0; border-radius: 4px; }
        .master-only { display: none; }
        .master-active .master-only { display: table-cell; }
    </style>
</head>
<body class="p-6">
    <div id="toast" class="fixed top-5 right-5 hidden bg-slate-800 text-white px-6 py-3 rounded-xl shadow-xl font-bold z-[500]"></div>

    <div class="max-w-full mx-auto">
        <div class="flex justify-between items-center mb-6 pb-4 border-b">
            <h1 class="text-2xl font-black text-slate-900 italic">SHIPMENT SYSTEM</h1>
            <div class="flex items-center gap-4">
                <select id="date-filter" onchange="filterTable()" class="text-xs font-bold border-2 p-2 rounded-xl">
                    <option value="all">전체 일정</option>
                    <option value="today">오늘 (Today)</option>
                </select>
                <div id="admin-tools" style="display:none;">
                    <button onclick="toggleMaster()" class="bg-white border-2 px-4 py-2 rounded-xl text-[10px] font-black text-slate-400">Master Mode</button>
                </div>
                <a href="/api/logout" class="bg-rose-500 text-white px-4 py-2 rounded-xl text-xs font-bold">로그아웃</a>
            </div>
        </div>

        <div class="flex space-x-2 mb-6 font-bold">
            <button onclick="changeTab('list')" id="btn-list" class="nav-btn active px-6 py-2 rounded-lg bg-white shadow-sm">리스트</button>
            <button onclick="changeTab('qm')" id="btn-qm" class="nav-btn px-6 py-2 rounded-lg bg-white shadow-sm relative">
                QM 피드백 <span id="qm-badge" class="absolute -top-1 -right-1 bg-red-500 text-white text-[10px] px-1.5 rounded-full hidden">0</span>
            </button>
        </div>

        <div id="tab-list" class="tab-content active">
            <div id="excel-area" class="mb-6 hidden bg-white p-4 rounded-2xl border-2 border-dashed border-slate-200">
                <textarea id="excel-input" class="w-full h-24 p-3 text-xs outline-none resize-none" placeholder="엑셀 데이터를 이곳에 붙여넣으세요..."></textarea>
                <div id="sync-preview" class="hidden mt-3 flex justify-between items-center">
                    <span class="text-xs font-bold text-indigo-600"><span id="sync-count">0</span>개 항목 감지됨</span>
                    <button onclick="submitSync()" class="bg-indigo-600 text-white px-4 py-2 rounded-lg font-black text-xs">DB 저장</button>
                </div>
            </div>

            <div class="bg-white rounded-2xl shadow-sm border overflow-hidden">
                <table class="w-full border-collapse" id="main-table">
                    <thead>
                        <tr>
                            <th>상태</th><th>LOT</th><th>W/O</th><th>S/N</th><th>고객사</th><th>Model</th><th>Module</th><th>MFG</th><th>요청일시</th><th>QM 피드백</th><th class="master-only">액션</th>
                        </tr>
                        <tr class="bg-white">
                            <th></th>
                            <th><input type="text" class="filter-input" onkeyup="filterTable()"></th>
                            <th><input type="text" class="filter-input" onkeyup="filterTable()"></th>
                            <th><input type="text" class="filter-input" onkeyup="filterTable()"></th>
                            <th><input type="text" class="filter-input" onkeyup="filterTable()"></th>
                            <th><input type="text" class="filter-input" onkeyup="filterTable()"></th>
                            <th><input type="text" class="filter-input" onkeyup="filterTable()"></th>
                            <th><input type="text" class="filter-input" onkeyup="filterTable()"></th>
                            <th><input type="text" class="filter-input" onkeyup="filterTable()"></th>
                            <th></th>
                            <th class="master-only"></th>
                        </tr>
                    </thead>
                    <tbody id="list-body"></tbody>
                </table>
            </div>
        </div>

        <div id="tab-qm" class="tab-content">
            <div id="qm-list" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"></div>
        </div>
    </div>

    <script>
        let allData = [];
        let currentUser = "";

        async function init() {
            const userRes = await fetch('/api/user');
            if(!userRes.ok) { location.href = '/login'; return; }
            const userData = await userRes.json();
            currentUser = userData.username;

            if(currentUser === 'pskhmfg') {
                document.getElementById('excel-area').style.display = 'block';
                document.getElementById('admin-tools').style.display = 'block';
            }
            loadData();
        }

        async function loadData() {
            const res = await fetch('/api/requests');
            allData = await res.json();
            renderTable();
            renderQM();
        }

        function renderTable() {
            const body = document.getElementById('list-body');
            body.innerHTML = allData.map(i => {
                const sColor = i.status === '확정' ? 'text-green-600 bg-green-50' : i.status === '반려' ? 'text-red-600 bg-red-50' : 'text-amber-600 bg-amber-50';
                const qmDetail = (i.status === '반려' && i.reject_reason) ? `${i.qm_pic} <span class="text-red-500 text-[10px] ml-1">[사유: ${i.reject_reason}]</span>` : (i.qm_pic || '-');
                
                return `
                <tr class="hover:bg-slate-50">
                    <td><span class="px-2 py-0.5 rounded font-bold text-[10px] ${sColor}">${i.status}</span></td>
                    <td class="font-bold">${i.lot}</td>
                    <td>${i.wo}</td>
                    <td class="font-black text-indigo-600">${i.sn}</td>
                    <td>${i.cus}</td>
                    <td class="font-bold text-left">${i.model}</td>
                    <td class="font-bold text-violet-600">${i.module}</td>
                    <td>${i.mfg_pic}</td>
                    <td class="text-[10px] text-slate-400">${i.req_date} ${i.req_time}</td>
                    <td class="text-left font-bold text-slate-700">${qmDetail}</td>
                    <td class="master-only"><button onclick="deleteItem(${i.id})" class="text-red-400 font-bold">삭제</button></td>
                </tr>`;
            }).join('');
            filterTable();
        }

        function renderQM() {
            const qmWait = allData.filter(i => i.status === '검사 요청');
            const badge = document.getElementById('qm-badge');
            badge.innerText = qmWait.length;
            badge.classList.toggle('hidden', qmWait.length === 0);

            const container = document.getElementById('qm-list');
            if(qmWait.length === 0) { container.innerHTML = `<div class="col-span-full py-20 text-center text-slate-300 font-bold">대기 중인 요청이 없습니다.</div>`; return; }

            container.innerHTML = qmWait.map(i => `
                <div class="bg-white p-5 rounded-2xl border shadow-sm">
                    <div class="flex justify-between mb-2"><span class="text-[10px] font-black text-indigo-500 italic">SN: ${i.sn}</span><span class="text-[10px] text-slate-400">${i.req_date}</span></div>
                    <h3 class="font-black text-slate-800 mb-3">${i.model}</h3>
                    <div class="flex gap-2">
                        <select id="pic-${i.id}" class="flex-1 bg-slate-50 border p-2 rounded-lg text-xs font-bold">
                            <option value="">담당자 선택</option><option value="김구원">김구원</option><option value="위대명">위대명</option><option value="박진주">박진주</option>
                        </select>
                        <button onclick="respond(${i.id}, '확정')" class="bg-slate-900 text-white px-4 rounded-lg font-black text-xs">확정</button>
                    </div>
                    <div class="mt-3 flex gap-2">
                        <input id="rej-${i.id}" class="flex-1 bg-rose-50 border border-rose-100 p-2 rounded-lg text-xs" placeholder="반려 사유 입력">
                        <button onclick="respond(${i.id}, '반려')" class="bg-rose-500 text-white px-4 rounded-lg font-black text-xs">반려</button>
                    </div>
                </div>`).join('');
        }

        async function respond(id, status) {
            const pic = document.getElementById(`pic-${id}`).value;
            const reason = document.getElementById(`rej-${id}`).value;
            if(status === '확정' && !pic) return alert("담당자를 선택하세요.");
            if(status === '반려' && !reason) return alert("반려 사유를 입력하세요.");

            const res = await fetch('/api/respond', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ id, status, qm_pic: pic, reject_reason: reason })
            });
            if(res.ok) { showToast(`${status} 처리 완료`); loadData(); changeTab('list'); }
        }

        function filterTable() {
            const rows = document.getElementById('list-body').rows;
            const inputs = document.querySelectorAll('.filter-input');
            const dateFilter = document.getElementById('date-filter').value;
            const todayStr = new Date().toLocaleDateString();

            for (let i = 0; i < rows.length; i++) {
                let visible = true;
                
                // 날짜 필터
                if(dateFilter === 'today' && !rows[i].cells[8].innerText.includes(todayStr)) visible = false;

                // 검색 필터
                inputs.forEach((input, idx) => {
                    const val = input.value.toLowerCase();
                    if(val && !rows[i].cells[idx+1].innerText.toLowerCase().includes(val)) visible = false;
                });
                
                rows[i].style.display = visible ? "" : "none";
            }
        }

        document.getElementById('excel-input').addEventListener('input', function() {
            const lines = this.value.trim().split('\n');
            const data = lines.map(line => {
                const c = line.split('\t');
                if(c.length < 13) return null;
                return { lot: c[0], wo: c[2], sn: c[3], cus: c[4], model: c[6], module: c[7], mfg_pic: c[10], req_date: c[11], req_time: c[12] };
            }).filter(i => i && !i.lot.includes("LOT"));
            
            window.tempSyncData = data;
            document.getElementById('sync-count').innerText = data.length;
            document.getElementById('sync-preview').classList.toggle('hidden', data.length === 0);
        });

        async function submitSync() {
            const res = await fetch('/api/requests/sync', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(window.tempSyncData) });
            if(res.ok) { document.getElementById('excel-input').value = ""; document.getElementById('sync-preview').classList.add('hidden'); loadData(); showToast("저장되었습니다."); }
        }

        async function deleteItem(id) { if(confirm("삭제하시겠습니까?")) { await fetch(`/api/requests/${id}/delete`, {method: 'POST'}); loadData(); } }
        function changeTab(n) { document.querySelectorAll('.tab-content, .nav-btn').forEach(e => e.classList.remove('active')); document.getElementById('tab-'+n).classList.add('active'); document.getElementById('btn-'+n).classList.add('active'); }
        function toggleMaster() { document.getElementById('main-table').classList.toggle('master-active'); }
        function showToast(m) { const t = document.getElementById('toast'); t.innerText = m; t.style.display='block'; setTimeout(() => t.style.display='none', 2000); }
        
        window.onload = init;
    </script>
</body>
</html>
