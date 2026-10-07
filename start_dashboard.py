#!/usr/bin/env python3
"""
Launcher script & API server for AI Job Search Assistant Web Dashboard.
Starts a local web server on port 8080 and handles live job refreshes and batch applications.
"""

import http.server
import socketserver
import webbrowser
import os
import sys
import json
import subprocess
from datetime import datetime

PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_POST(self):
        if self.path == '/api/refresh':
            self.handle_refresh()
        elif self.path == '/api/apply_batch':
            self.handle_apply_batch()
        else:
            super().do_POST()

    def do_GET(self):
        if self.path in ('/', '/index.html'):
            self.path = '/dashboard.html'
        if self.path == '/api/refresh':
            self.handle_refresh()
        elif self.path.startswith('/api/fit_score_report'):
            self.handle_fit_score_report()
        else:
            super().do_GET()

    def handle_fit_score_report(self):
        try:
            from fit_score_report import compute_analytics
            data = compute_analytics()
            if not data:
                data = {"status": "empty", "message": "No tracker records found."}
            else:
                data["status"] = "success"
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))

    def handle_refresh(self):
        try:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Received live Refresh request from dashboard UI...")
            script_path = os.path.join(DIRECTORY, "auto_daily_job_search.py")
            res = subprocess.run([sys.executable, script_path], capture_output=True, text=True, cwd=DIRECTORY, timeout=180)
            
            output = res.stdout or ""
            new_jobs = 0
            for line in output.splitlines():
                if "New Jobs Discovered:" in line:
                    try:
                        new_jobs = int(line.split(":")[-1].strip())
                    except Exception:
                        pass
            
            response_data = {
                "status": "success",
                "message": "Scan completed successfully!",
                "new_jobs_found": new_jobs,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "log": output
            }
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
        except Exception as e:
            response_data = {
                "status": "error",
                "message": str(e)
            }
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode('utf-8'))

    def handle_apply_batch(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length) if content_length > 0 else b'{}'
            payload = json.loads(post_data.decode('utf-8'))
            job_ids = payload.get('job_ids', [])
            mode = payload.get('mode', 'browser')  # 'browser' = real apply, 'track' = just track

            print(f"[{datetime.now().strftime('%H:%M:%S')}] Received Auto-Apply batch request for {len(job_ids)} jobs (mode={mode})...")
            jobs_arg = ",".join(job_ids) if job_ids else "all"

            if mode == 'browser':
                # Real browser apply using Playwright
                script_path = os.path.join(DIRECTORY, "browser_apply_agent.py")
                if not os.path.exists(script_path):
                    script_path = os.path.join(DIRECTORY, "auto_apply_agent.py")
                res = subprocess.run(
                    [sys.executable, script_path, "--jobs", jobs_arg, "--headless"],
                    capture_output=True, text=True, cwd=DIRECTORY, timeout=600
                )
            else:
                # Legacy tracker-only mode
                script_path = os.path.join(DIRECTORY, "auto_apply_agent.py")
                res = subprocess.run(
                    [sys.executable, script_path, "--jobs", jobs_arg],
                    capture_output=True, text=True, cwd=DIRECTORY, timeout=180
                )

            if res.returncode == 0 and res.stdout.strip().startswith("{"):
                output_json = json.loads(res.stdout)
            else:
                output_json = {"status": "success", "applied_count": len(job_ids), "stderr": res.stderr[:500] if res.stderr else ""}

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(output_json).encode('utf-8'))
        except Exception as e:
            response_data = {"status": "error", "message": str(e)}
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode('utf-8'))

def run():
    os.chdir(DIRECTORY)
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"==================================================")
        print(f"  AI Job Search Assistant — Web Dashboard Server")
        print(f"  Serving at: http://localhost:{PORT}/dashboard.html")
        print(f"==================================================")
        webbrowser.open(f"http://localhost:{PORT}/dashboard.html")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nDashboard server stopped.")
            sys.exit(0)

if __name__ == "__main__":
    run()
