# CI 통합과 착수 인계

회사 CI 제품은 TBD. 이 패키지는 특정 서비스 설정을 선정하지 않고 같은 검증 entrypoint를 제공한다.
CI는 최소 권한의 ephemeral runner에서 source checkout→고정 개발 의존성 설치→TypeScript 설치→브라우저 준비→scripts/release.py 순서로 실행한다.
각 명령 exit code가 0이 아니면 release artifact 업로드·승격을 차단해야 한다(MUST).
verification/results.json, browser-results.json, checksums.sha256, ZIP 및 외부 archive-verification.json을 보존한다.

## 환경 변수
- TSC_PATH: TypeScript compiler의 JS 파일. 생략하면 프로젝트 node_modules/typescript/bin/tsc.
- PLAYWRIGHT_MODULE: Playwright CommonJS module의 절대 경로. 생략하면 설치된 playwright.
- PYTHONPATH: 설치 환경이 분리된 경우에만 검증 의존성 경로를 설정한다.

## 재현성과 공급망
직접 의존성은 requirements-dev.txt와 package.json으로 pin한다.
검증에 사용한 transitive Python 버전은 verification/python-dependencies.txt에 기록한다.
운영용 lockfile·wheelhouse·npm mirror·SBOM·signature store는 회사 toolchain 확정 시 추가해야 한다.
최초 설치/브라우저 다운로드는 인터넷이 필요하다. portal 열람은 완전히 오프라인이다.
release ZIP에는 node_modules, Python interpreter, 외부 모델 credential을 포함하지 않는다.

## 착수 순서
1. Owner/Security/SRE가 기준선과 TBD-01~05를 검토한다.
2. 첫 실제 Agent의 Manifest와 immutable artifact digest를 등록한다.
3. 회사 IdP, workload identity, policy authority, egress adapter로 mock을 대체한다.
4. 실제 tool input/output·모델 routing·RAG ACL·재시도 ledger conformance를 실행한다.
5. risk별 evaluation·부하·복구·승인 증거가 확보된 target만 production-approved로 승격한다.

단계별 일정·인원·예산·업무 품질 수치는 TBD.

