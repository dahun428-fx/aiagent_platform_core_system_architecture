"""1단계: 정문 뒤에 선 Agent. 요청을 직접 받지 않고 내용만 건네받습니다."""
import re

import world

ERP_PASSWORD = "erp-s3cret"


def handle(content):
    invoice_id = re.search(r"INV-\d+", content).group()
    invoice = world.erp_read(ERP_PASSWORD, invoice_id)
    return world.model(f"{invoice['vendor']} {invoice['amount']:,}원, 납기 {invoice['due']}")
