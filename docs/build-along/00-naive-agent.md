# 0. 플랫폼 없이 짠 Agent

> 만들면서 배우는 경로입니다. 열 줄 남짓한 Agent 하나에 Core System을 한 장에 한 조각씩 붙여 갑니다. 코드는 모두 `examples/build/`에 있고, 내 PC에서 그대로 실행됩니다.

{{blocks:0}}

## 이 경로를 읽는 법

모든 장이 같은 순서로 진행됩니다.

1. **지금 코드의 아픈 곳** 하나를 직접 실행해서 봅니다.
2. 위 그림에 **조각 하나**를 붙입니다.
3. 그 조각이 안에서 하는 일을 **의사코드** 열 줄 안팎으로 봅니다.
4. 내 Agent 코드가 어떻게 바뀌는지 **앞 장과의 차이**로 봅니다.
5. 같은 **검사 여섯 개**를 다시 돌려, 실패하던 줄이 통과로 바뀌는 것을 확인합니다.

검사 여섯 개는 처음부터 끝까지 바뀌지 않습니다. 0장에서는 여섯 개가 모두 실패하고, 조각이 붙을 때마다 통과하는 줄이 늘어납니다.

## 출발점: 열 줄 남짓한 Agent

재무팀 서연이 "청구서 INV-2048 요약해 줘"라고 보내면 ERP에서 청구서를 읽어 모델에게 요약을 시키는 Agent입니다. 개발자 민준이 플랫폼 없이 가장 빠른 길로 짰습니다.

<!-- kind: example -->
```python
# examples/build/step0/agent.py
import re

import world

ERP_PASSWORD = "erp-s3cret"


def invoke(request):
    invoice_id = re.search(r"INV-\d+", request["content"]).group()
    invoice = world.erp_read(ERP_PASSWORD, invoice_id)
    summary = world.model(f"{invoice['vendor']} {invoice['amount']:,}원, 납기 {invoice['due']}")
    return {"status": 200, "output": summary}
```

`world`는 플랫폼 바깥에 있는 ERP와 모델을 흉내 낸 파일(`examples/build/world.py`)입니다. 모든 장이 같은 `world`를 쓰므로, 장마다 달라지는 것은 Agent 코드와 플랫폼 조각뿐입니다.

## 실행해 본다

```bash
python examples/build/check.py step0
```

<!-- kind: run boundary: local -->
```text
응답 {'status': 200, 'output': '요약: 한빛상사 12,400,000원, 납기 2026-11-30'}
FAIL 1 토큰 없는 요청은 거절한다
FAIL 2 같은 요청이 두 번 와도 한 번만 실행한다
FAIL 3 Agent 코드에 ERP 비밀번호가 없다
FAIL 4 Manifest에 없는 도구는 부를 수 없다
FAIL 5 권한이 모자란 하준은 거절한다
FAIL 6 Agent 코드가 모델을 직접 부르지 않는다
0/6
```

첫 줄을 보면 Agent는 잘 동작합니다. 서연은 원하는 요약을 받았습니다. 그런데 그 아래 여섯 줄이 모두 실패합니다. 동작하는 것과 회사에서 운영할 수 있는 것 사이의 거리가 이 여섯 줄입니다.

## 여섯 줄이 뜻하는 것

| 검사 | 지금 코드에서 벌어지는 일 | 붙일 조각 |
|---|---|---|
| 1. 토큰 없는 요청은 거절한다 | 누가 보냈는지 묻지 않고 누구에게나 청구서를 요약해 줍니다 | [1장 정문](01-entry.md) |
| 2. 같은 요청이 두 번 와도 한 번만 실행한다 | 앱이 응답을 못 받아 다시 보내면 모델을 두 번 부릅니다 | [1장 정문](01-entry.md) |
| 3. Agent 코드에 ERP 비밀번호가 없다 | 비밀번호가 코드에 적혀 저장소에 함께 올라갑니다 | [2장 도구 경로](02-tools.md) |
| 4. Manifest에 없는 도구는 부를 수 없다 | Agent가 무엇을 부를 수 있는지 정해 둔 곳이 없습니다 | [2장 도구 경로](02-tools.md) |
| 5. 권한이 모자란 하준은 거절한다 | 인턴 하준이 불러도 서연과 같은 답이 나갑니다 | Agent Identity |
| 6. Agent 코드가 모델을 직접 부르지 않는다 | 모델을 바꾸거나 모델이 느려질 때 Agent마다 코드를 고쳐야 합니다 | Agent Gateway |

Agent가 하나일 때는 민준이 여섯 가지를 직접 고칠 수도 있습니다. 하지만 팀마다 Agent를 만들기 시작하면 모든 팀이 같은 여섯 가지를 각자 다시 짜게 되고, 한 팀이라도 빠뜨리면 그 Agent가 회사의 구멍이 됩니다. 그래서 이 여섯 가지를 Agent 코드 밖으로 꺼내 한 번만 만듭니다. 그 꺼낸 부분이 플랫폼이고, 꺼내는 단위가 맨 위 그림의 조각입니다.

## 지금까지 만든 것

- Agent 코드 하나. 동작하지만 검사는 0/6입니다.
- 플랫폼 조각은 아직 없습니다.

다음 장에서 첫 조각인 정문을 붙이면 검사 1과 2가 통과로 바뀝니다.
