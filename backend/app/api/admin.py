"""
Admin API endpoints for chat tracing and debugging.

Provides read-only access to session history, LLM requests, and prompt breakdowns
for debugging tool selection and prompt composition issues.

No authentication required - localhost development tool only.
"""
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Query, HTTPException
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
import logfire

from ..models.session import Session
from ..models.message import Message
from ..models.llm_request import LLMRequest
from ..database import get_database_service


router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/sessions")
async def list_sessions(
    account: Optional[str] = Query(None, description="Filter by account slug"),
    agent: Optional[str] = Query(None, description="Filter by agent instance slug"),
    limit: int = Query(50, le=100, description="Max results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset")
):
    """
    List sessions with optional filtering by account or agent.
    
    Returns paginated list of sessions with message counts for debugging.
    """
    db_service = get_database_service()
    
    async with db_service.get_session() as db_session:
        try:
            # Build query with optional filters and eager load relationships
            query = (
                select(
                    Session,
                    func.count(Message.id).label('message_count')
                )
                .options(
                    selectinload(Session.account),
                    selectinload(Session.agent_instance)
                )
                .outerjoin(Message, Message.session_id == Session.id)
                .group_by(Session.id)
            )
            
            # Apply filters
            if account:
                from ..models.account import Account
                query = query.join(Account, Session.account_id == Account.id).where(Account.slug == account)
            
            if agent:
                from ..models.agent_instance import AgentInstanceModel
                query = query.join(
                    AgentInstanceModel,
                    Session.agent_instance_id == AgentInstanceModel.id
                ).where(AgentInstanceModel.slug == agent)
            
            # Count total matching records
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await db_session.execute(count_query)
            total = total_result.scalar()
            
            # Apply pagination and ordering
            query = query.order_by(desc(Session.created_at)).limit(limit).offset(offset)
            
            result = await db_session.execute(query)
            sessions_with_counts = result.all()
            
            # Format response
            sessions_list = []
            for session, message_count in sessions_with_counts:
                sessions_list.append({
                    "id": str(session.id),
                    "account_slug": session.account.slug if session.account else None,
                    "agent_instance_slug": session.agent_instance.instance_slug if session.agent_instance else None,
                    "created_at": session.created_at.isoformat(),
                    "message_count": message_count
                })
            
            logfire.info(
                'api.admin.sessions.listed',
                total=total,
                returned=len(sessions_list),
                account_filter=account,
                agent_filter=agent
            )
            
            return {
                "sessions": sessions_list,
                "total": total,
                "limit": limit,
                "offset": offset
            }
            
        except Exception as e:
            logfire.exception(
                'api.admin.sessions.error',
                error_type=type(e).__name__
            )
            raise HTTPException(status_code=500, detail="Failed to retrieve sessions")


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: str):
    """
    Get all messages for a session with LLM request metadata.
    
    Returns chronological list of messages with tool calls and LLM details.
    """
    db_service = get_database_service()
    
    async with db_service.get_session() as db_session:
        try:
            session_uuid = UUID(session_id)
            
            # Query messages with LLM request data
            query = (
                select(Message, LLMRequest)
                .outerjoin(LLMRequest, Message.llm_request_id == LLMRequest.id)
                .where(Message.session_id == session_uuid)
                .order_by(Message.created_at)
            )
            
            result = await db_session.execute(query)
            messages_with_llm = result.all()
            
            # Format response
            messages_list = []
            for message, llm_request in messages_with_llm:
                message_data = {
                    "id": str(message.id),
                    "role": message.role,
                    "content": message.content,
                    "created_at": message.created_at.isoformat(),
                    "llm_request_id": str(message.llm_request_id) if message.llm_request_id else None
                }
                
                # Add LLM metadata if available (for assistant messages)
                if llm_request:
                    message_data["meta"] = {
                        "model": llm_request.model,
                        "input_tokens": llm_request.prompt_tokens,
                        "output_tokens": llm_request.completion_tokens,
                        "cost": float(llm_request.total_cost) if llm_request.total_cost else 0.0
                    }
                    
                    # Add tool calls from message.meta if present
                    if message.meta and "tool_calls" in message.meta:
                        message_data["meta"]["tool_calls"] = message.meta["tool_calls"]
                
                messages_list.append(message_data)
            
            logfire.info(
                'api.admin.session_messages.retrieved',
                session_id=session_id,
                message_count=len(messages_list)
            )
            
            return {
                "session_id": session_id,
                "messages": messages_list
            }
            
        except ValueError as e:
            logfire.error(
                'api.admin.session_messages.invalid_id',
                session_id=session_id
            )
            raise HTTPException(status_code=400, detail="Invalid session ID format")
        except Exception as e:
            logfire.exception(
                'api.admin.session_messages.error',
                session_id=session_id,
                error_type=type(e).__name__
            )
            raise HTTPException(status_code=500, detail="Failed to retrieve messages")


@router.get("/llm-requests/{request_id}")
async def get_llm_request(request_id: str):
    """
    Get detailed LLM request information including prompt breakdown.
    
    Returns full prompt breakdown, tool calls, token usage, and costs for debugging.
    """
    db_service = get_database_service()
    
    async with db_service.get_session() as db_session:
        try:
            request_uuid = UUID(request_id)
            
            # Query LLM request
            query = select(LLMRequest).where(LLMRequest.id == request_uuid)
            result = await db_session.execute(query)
            llm_request = result.scalar_one_or_none()
            
            if not llm_request:
                raise HTTPException(status_code=404, detail="LLM request not found")
            
            # Extract prompt breakdown from meta
            prompt_breakdown = None
            if llm_request.meta and "prompt_breakdown" in llm_request.meta:
                prompt_breakdown = llm_request.meta["prompt_breakdown"]
            
            # Query associated messages for tool calls
            messages_query = select(Message).where(Message.llm_request_id == request_uuid)
            messages_result = await db_session.execute(messages_query)
            messages = messages_result.scalars().all()
            
            # Extract tool calls from assistant messages
            tool_calls = []
            for message in messages:
                if message.role == "assistant" and message.meta and "tool_calls" in message.meta:
                    tool_calls.extend(message.meta["tool_calls"])
            
            logfire.info(
                'api.admin.llm_request.retrieved',
                request_id=request_id,
                has_prompt_breakdown=prompt_breakdown is not None,
                tool_call_count=len(tool_calls)
            )
            
            return {
                "id": str(llm_request.id),
                "model": llm_request.model,
                "prompt_breakdown": prompt_breakdown,
                "tool_calls": tool_calls,
                "response": {
                    "content": None,  # Full content is in messages table
                    "input_tokens": llm_request.prompt_tokens,
                    "output_tokens": llm_request.completion_tokens,
                    "total_tokens": llm_request.total_tokens,
                    "cost": float(llm_request.total_cost) if llm_request.total_cost else 0.0,
                    "latency_ms": llm_request.latency_ms
                }
            }
            
        except ValueError as e:
            logfire.error(
                'api.admin.llm_request.invalid_id',
                request_id=request_id
            )
            raise HTTPException(status_code=400, detail="Invalid request ID format")
        except HTTPException:
            raise
        except Exception as e:
            logfire.exception(
                'api.admin.llm_request.error',
                request_id=request_id,
                error_type=type(e).__name__
            )
            raise HTTPException(status_code=500, detail="Failed to retrieve LLM request")

