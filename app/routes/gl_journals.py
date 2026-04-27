"""GL journal routes — /api/gl/*"""

import json
import logging

import backend
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from routes._utils import DecimalEncoder

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/gl", tags=["gl_journals"])


class GenerateJournalsRequest(BaseModel):
    user: str = Field(default="system", max_length=256)


class PostJournalRequest(BaseModel):
    user: str = Field(min_length=1, max_length=256)


class ReverseJournalRequest(BaseModel):
    user: str = Field(min_length=1, max_length=256)
    reason: str = Field(default="", max_length=2000)


@router.post("/generate/{project_id}")
def gl_generate_journals(project_id: str, body: GenerateJournalsRequest):
    try:
        journal = backend.generate_ecl_journals(project_id, body.user)
        return json.loads(json.dumps(journal, cls=DecimalEncoder))
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        log.exception("Failed to generate GL journals")
        raise HTTPException(500, f"Failed to generate journals: {e}")


@router.get("/journals/{project_id}")
def gl_list_journals(project_id: str):
    try:
        journals = backend.list_journals(project_id)
        return json.loads(json.dumps(journals, cls=DecimalEncoder))
    except Exception as e:
        raise HTTPException(500, f"Failed to list journals: {e}")


@router.get("/journal/{journal_id}")
def gl_get_journal(journal_id: str):
    try:
        journal = backend.get_journal(journal_id)
        if not journal:
            raise HTTPException(404, "Journal not found")
        return json.loads(json.dumps(journal, cls=DecimalEncoder))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to get journal: {e}")


@router.post("/journal/{journal_id}/post")
def gl_post_journal(journal_id: str, body: PostJournalRequest):
    try:
        journal = backend.post_journal(journal_id, body.user)
        return json.loads(json.dumps(journal, cls=DecimalEncoder))
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Failed to post journal: {e}")


@router.post("/journal/{journal_id}/reverse")
def gl_reverse_journal(journal_id: str, body: ReverseJournalRequest):
    try:
        journal = backend.reverse_journal(journal_id, body.user, body.reason)
        return json.loads(json.dumps(journal, cls=DecimalEncoder))
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Failed to reverse journal: {e}")


@router.get("/trial-balance/{project_id}")
def gl_trial_balance(project_id: str):
    try:
        tb = backend.get_gl_trial_balance(project_id)
        return json.loads(json.dumps(tb, cls=DecimalEncoder))
    except Exception as e:
        raise HTTPException(500, f"Failed to get trial balance: {e}")


@router.get("/chart-of-accounts")
def gl_chart_of_accounts():
    try:
        chart = backend.get_gl_chart()
        return json.loads(json.dumps(chart, cls=DecimalEncoder))
    except Exception as e:
        raise HTTPException(500, f"Failed to get chart of accounts: {e}")
