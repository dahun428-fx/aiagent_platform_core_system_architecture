"""0단계: 플랫폼 없이 짠 청구서 요약 Agent."""
import re

import world

ERP_PASSWORD = "erp-s3cret"


def invoke(request):
    invoice_id = re.search(r"INV-\d+", request["content"]).group()
    invoice = world.erp_read(ERP_PASSWORD, invoice_id)
    summary = world.model(f"{invoice['vendor']} {invoice['amount']:,}원, 납기 {invoice['due']}")
    return {"status": 200, "output": summary}
