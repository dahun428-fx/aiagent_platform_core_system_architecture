"""로컬 스택을 별도 프로세스로 띄운다: 가짜 모델·가짜 도구 → Agent Gateway 모델 경로·도구 경로 → Platform APIs.

각 서비스는 127.0.0.1의 빈 포트에 바인딩하고, 표준 출력 첫 줄에 그 포트를 출력한다.
내부 구간 서명 키는 실행마다 새로 만들어 환경 변수로 넘긴다. 파일이나 저장소에는 남지 않는다.
도구 경로의 effect ledger는 PostgreSQL을 쓴다. 환경 변수 IMPL_DATABASE_URL이 있으면 그 DB를 쓰고(예: compose로 띄운 DB),
없으면 설치된 PostgreSQL(initdb·pg_ctl)로 임시 DB를 만들어 띄우고 끝나면 지운다.
직접 실행하면 스택을 띄운 채로 둔다: python impl/stack.py
"""
from __future__ import annotations

import glob
import os
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from common import DATABASE_ENV, KEY_ENV, call_json  # noqa: E402


# PostgreSQL 실행 파일(initdb, pg_ctl)이 있는 폴더를 찾는다. PATH → PGBIN(GitHub Windows 러너) → 흔한 설치 위치 순서.
def postgres_bin():
    if shutil.which("initdb"):
        return str(Path(shutil.which("initdb")).parent)
    candidates = [os.environ.get("PGBIN", "")]
    for pattern in ("/usr/lib/postgresql/*/bin", "/opt/homebrew/opt/postgresql*/bin", "/usr/local/opt/postgresql*/bin",
                    "/Applications/Postgres.app/Contents/Versions/latest/bin", "C:/Program Files/PostgreSQL/*/bin"):
        candidates += sorted(glob.glob(pattern), reverse=True)  # 버전이 높은 것부터
    for folder in candidates:
        if folder and (Path(folder) / ("initdb.exe" if os.name == "nt" else "initdb")).exists():
            return folder
    raise RuntimeError(f"PostgreSQL not found: install it (initdb, pg_ctl) or set {DATABASE_ENV} (see impl/README.md)")


# 빈 TCP 포트 하나를 고른다(임시 DB용). 고른 뒤 바로 닫으므로 아주 드물게 다른 프로그램이 먼저 가져갈 수 있다.
def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class TempPostgres:
    """이 스택 전용 임시 PostgreSQL. 임시 폴더에 initdb로 DB를 만들고 127.0.0.1의 빈 포트로만 띄운다(비밀번호 없는 로컬 trust 인증)."""

    def __init__(self):
        self.bin = postgres_bin()
        # 임시 폴더를 mkdtemp(권한 0o700)로 만들지 않는다. Windows에서 그 권한은 관리자 그룹에만 열리는데,
        # initdb는 관리자 권한을 뺀 채로 돌아서 그 안에 data 폴더를 만들지 못한다. 기본 권한으로 직접 만든다.
        self.root = Path(tempfile.gettempdir()) / f"impl-pg-{secrets.token_hex(6)}"
        self.root.mkdir()
        self.data = self.root / "data"
        port = free_port()
        try:
            self.run("initdb", "-D", str(self.data), "-U", "impl", "--auth=trust", "-E", "UTF8")
            # 유닉스 소켓을 끄고 TCP 루프백만 연다. 설정 파일에 적으면 운영체제마다 다른 명령줄 따옴표 규칙을 피할 수 있다.
            with open(self.data / "postgresql.conf", "a", encoding="utf-8") as conf:
                conf.write(f"\nport = {port}\nlisten_addresses = '127.0.0.1'\nunix_socket_directories = ''\nfsync = off\n")
            self.run("pg_ctl", "-D", str(self.data), "-l", str(self.root / "log"), "-w", "start")
        except BaseException:  # 띄우다 실패하면 임시 폴더를 남기지 않는다
            shutil.rmtree(self.root, ignore_errors=True)
            raise
        self.url = f"postgresql://impl@127.0.0.1:{port}/postgres"

    # PostgreSQL 명령 하나를 실행한다. 실패하면 출력을 담아 알린다.
    # 출력은 파이프가 아닌 임시 파일로 받는다. Windows에서 `pg_ctl start`가 띄운 서버가 파이프를 물려받아 계속 열어 두면,
    # 파이프가 닫히기를 기다리는 subprocess.run이 영원히 끝나지 않는다.
    def run(self, tool, *args):
        with tempfile.TemporaryFile("w+", encoding="utf-8", errors="replace") as out:
            code = subprocess.run([str(Path(self.bin) / tool), *args], stdout=out, stderr=subprocess.STDOUT).returncode
            if code != 0:
                out.seek(0)
                raise RuntimeError(f"{tool} failed: {out.read()}")

    # DB를 끄고 임시 폴더를 지운다.
    def close(self):
        try:
            self.run("pg_ctl", "-D", str(self.data), "-m", "fast", "-w", "stop")
        finally:
            shutil.rmtree(self.root, ignore_errors=True)


class Stack:
    """with 문으로 쓴다. 들어갈 때 서비스들을 띄우고, 나올 때 모두 끈다. 주소는 self.urls 에 이름별로 담긴다."""

    def __init__(self):
        self.procs = {}  # 서비스 이름 → 프로세스
        self.commands = {}  # 서비스 이름 → (스크립트, 인자). 재시작할 때 같은 명령을 다시 쓴다.
        self.urls = {}
        self.internal_key = secrets.token_hex(32)  # Platform과 Gateway가 공유하는 서명 키(실행마다 새로)
        self.database = None  # 직접 띄운 임시 PostgreSQL(있을 때만)
        self.database_url = os.environ.get(DATABASE_ENV)

    # 서비스 하나를 띄우고, 첫 줄의 포트를 읽은 뒤 /health/ready 가 200이 될 때까지 최대 10초 기다린다.
    def _start(self, name, script, *args):
        # stderr는 파이프가 아닌 파일로 보낸다: 아무도 읽지 않는 파이프는 traceback이 약 64KB 쌓이면 가득 차서 서비스가 멈춘다.
        err = tempfile.TemporaryFile("w+", encoding="utf-8")
        env = {**os.environ, KEY_ENV: self.internal_key, DATABASE_ENV: self.database_url or ""}
        proc = subprocess.Popen([sys.executable, str(HERE / script), *args], stdout=subprocess.PIPE,
                                stderr=err, text=True, encoding="utf-8", env=env)
        proc.err = err
        self.procs[name] = proc
        self.commands.setdefault(name, (script, args))  # 처음 띄운 명령(포트 지정 없음)을 기억한다
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

    # DB부터, 그다음 아래쪽 서비스부터 띄운다. 위쪽 서비스가 아래쪽 주소를 인자로 받기 때문이다.
    # 하나라도 실패하면 이미 띄운 것을 모두 끈다.
    def __enter__(self):
        try:
            if not self.database_url:
                self.database = TempPostgres()
                self.database_url = self.database.url
            model = self._start("fake-model", "fakes/fake_model.py")
            tool = self._start("fake-tool", "fakes/fake_tool.py")
            model_route = self._start("model-route", "gateway/model_route.py", "--upstream", model)
            tool_route = self._start("tool-route", "gateway/tool_route.py", "--upstream", tool)
            # 같은 DB를 쓰는 두 번째 도구 경로 worker. 동시 실행 시나리오가 두 worker에 요청을 나눠 보낸다.
            self._start("tool-route-2", "gateway/tool_route.py", "--upstream", tool)
            self._start("platform-api", "platform_api.py", "--gateway", model_route, "--tools", tool_route)
        except Exception:
            self.close()
            raise
        return self

    # 서비스 하나를 끄고 같은 명령·같은 포트로 다시 띄운다. 메모리 상태는 사라지고 DB에 쓴 것만 남는다.
    def restart(self, name):
        script, args = self.commands[name]
        port = self.urls[name].rsplit(":", 1)[1]
        self._stop(self.procs.pop(name))
        self._start(name, script, *args, "--port", port)

    # 프로세스 하나에 종료 신호를 보내고, 5초 안에 안 꺼지면 강제 종료한다. 열어 둔 출력 스트림과 파일도 닫는다.
    @staticmethod
    def _stop(proc):
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        for stream in (proc.stdout, proc.err):
            if stream:
                stream.close()

    # 띄운 역순으로 모두 끄고, 직접 띄운 임시 DB도 끈다.
    def close(self):
        for name in reversed(list(self.procs)):
            self._stop(self.procs.pop(name))
        if self.database:
            self.database.close()
            self.database = None

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
