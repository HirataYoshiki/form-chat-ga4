from typing import List, Optional, Dict # Dict is not used, but kept for now
from pydantic import BaseModel, Field
from datetime import date

class SubmissionsCountParams(BaseModel):
    start_date: Optional[date] = Field(None, description="集計開始日 (YYYY-MM-DD)")
    end_date: Optional[date] = Field(None, description="集計終了日 (YYYY-MM-DD)")
    form_id: Optional[str] = Field(None, description="特定のフォームIDでフィルタリングする場合")

class SubmissionsCountResponse(BaseModel):
    count: int = Field(..., description="集計された問い合わせ件数")
    parameters: SubmissionsCountParams = Field(..., description="適用された集計パラメータ")

class FormSummaryItem(BaseModel):
    form_id: str = Field(..., description="フォームID")
    count: int = Field(..., description="該当フォームIDの問い合わせ件数")

class SubmissionsSummaryResponse(BaseModel):
    summary: List[FormSummaryItem] = Field(..., description="フォームID別の問い合わせ件数サマリのリスト")
