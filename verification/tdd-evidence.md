# 테스트 선행·실패 재현 기록

- Runtime 예제 작성 전 test_runtime.py를 실행하여 아직 없는 platform_ref.py를 찾지 못하는 초기 실패를 확인했다. 이 최초 실행은 assertion 실패가 아닌 import error다.
- 계약/포털 전체 검사에서 URI 음성 fixture가 통과하는 실제 실패를 확인했다. 선택 format 의존성 추가 후 거부됨을 재검증했다.
- Broker trace 회귀 테스트는 다른 traceparent를 넣었을 때 audit event correlation assertion이 실패함을 확인했다. Broker로 호출 trace를 전달한 뒤 통과했다.
- 최초 전체 검사에서 미생성 포털 링크가 실패했고 HTML 생성 후 통과했다.
- 모든 함수를 개별 red-green 사이클로 개발했다고 주장하지 않는다. 최종 실제 실행 로그는 results.json에 제공한다.

