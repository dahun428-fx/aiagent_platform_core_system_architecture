"""플랫폼 바깥 세계의 대역: ERP와 모델. 모든 단계가 같은 세계를 씁니다."""
ERP_PASSWORD = "erp-s3cret"
INVOICES = {"INV-2048": {"vendor": "한빛상사", "amount": 12400000, "due": "2026-11-30"}}
model_calls = 0


def erp_read(password, invoice_id):
    if password != ERP_PASSWORD:
        raise PermissionError("ERP 로그인 실패")
    return INVOICES[invoice_id]


def model(prompt):
    global model_calls
    model_calls += 1
    return "요약: " + prompt
