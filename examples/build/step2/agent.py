"""2단계: 비밀번호가 사라진 Agent. ERP는 이름으로만 부릅니다."""
import re

import world


def handle(ctx, content):
    invoice_id = re.search(r"INV-\d+", content).group()
    invoice = ctx.call_tool("tool-erp-read", {"invoice_id": invoice_id})
    return world.model(f"{invoice['vendor']} {invoice['amount']:,}원, 납기 {invoice['due']}")
