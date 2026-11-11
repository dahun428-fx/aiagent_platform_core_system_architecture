"""로컬 스택을 별도 프로세스 세 개로 띄운다: 가짜 모델 → Agent Gateway 모델 경로 → Platform APIs.

각 서비스는 127.0.0.1의 빈 포트에 바인딩하고, 표준 출력 첫 줄에 그 포트를 출력한다.
내부 구간 서명 키는 실행마다 새로 만들어 환경 변수로 넘긴다. 파일이나 저장소에는 남지 않는다.
직접 실행하면 스택을 띄운 채로 둔다: python impl/stack.py
"""
from __future__ import annotations

import os
import secrets
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from common import KEY_ENV, call_json  # noqa: E402


class Stack:
    """with 문으로 쓴다. 들어갈 때 세 서비스를 띄우고, 나올 때 모두 끈다. 주소는 self.urls 에 이름별로 담긴다."""

    def __init__(self):
        self.procs = []
        self.urls = {}
        self.internal_key = secrets.token_hex(32)  # Platform과 모델 경로가 공유하는 서명 키(실행마다 새로)

    # 서비스 하나를 띄우고, 첫 줄의 포트를 읽은 뒤 /health/ready 가 200이 될 때까지 최대 10초 기다린다.
    def _start(self, name, script, *args):
        # stderr는 파이프가 아닌 파일로 보낸다: 아무도 읽지 않는 파이프는 traceback이 약 64KB 쌓이면 가득 차서 서비스가 멈춘다.
        err = tempfile.TemporaryFile("w+", encoding="utf-8")
        proc = subprocess.Popen([sys.executable, str(HERE / script), *args], stdout=subprocess.PIPE,
                                stderr=err, text=True, encoding="utf-8", env={**os.environ, KEY_ENV: self.internal_key})
        proc.err = err
        self.procs.append(proc)
        line = proc.stdout.readline().strip()
        if not line.isdigit():
            if not line:  # 표준 출력이 닫혔다 = 프로세스가 죽는 중. traceback이 파일에 다 써질 때까지 기다린다.
                proc.wait(timeout=5)
            err.seek(0)
            raise RuntimeError(f"{name} failed to start: {err.read() or line}")
        url = f"http://127.0.0.1:{line}"
        deadline = time.monotonic() + 10
        while True:
            try:
                if call_json("GET", url + "/health/ready", timeout=1)[0] == 200:
                    break
            except (ConnectionError, TimeoutError):
                pass
            if time.monotonic() > deadline:
                raise RuntimeError(f"{name} did not become ready")
            time.sleep(0.05)
        self.urls[name] = url
        return url

    # 아래쪽 서비스부터 띄운다. 위쪽 서비스가 아래쪽 주소를 인자로 받기 때문이다. 하나라도 실패하면 이미 띄운 것을 모두 끈다.
    def __enter__(self):
        try:
            model = self._start("fake-model", "fakes/fake_model.py")
            gateway = self._start("model-route", "gateway/model_route.py", "--upstream", model)
            self._start("platform-api", "platform_api.py", "--gateway", gateway)
        except Exception:
            self.close()
            raise
        return self

    # 띄운 역순으로 종료 신호를 보내고, 5초 안에 안 꺼지면 강제 종료한다. 열어 둔 출력 스트림과 파일도 닫는다.
    def close(self):
        for proc in reversed(self.procs):
            proc.terminate()
        for proc in self.procs:
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
            for stream in (proc.stdout, proc.err):
                if stream:
                    stream.close()
        self.procs = []

    def __exit__(self, *_):
        self.close()


# make stack: 스택을 띄우고 서비스별 주소를 출력한 뒤 Ctrl-C를 기다린다.
if __name__ == "__main__":
    with Stack() as stack:
        for name, url in stack.urls.items():
            print(f"{name:14} {url}", flush=True)
        print("Ctrl-C to stop", flush=True)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
