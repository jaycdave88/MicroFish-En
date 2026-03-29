#!/usr/bin/env python3
"""A2A (Agent-to-Agent) server wrapper for MicroFish (MiroFish-En).

Exposes MicroFish's multi-agent simulation engine as an A2A-compliant agent
so OpenFang can dispatch simulation/prediction tasks to it.

Port: 5001 (same as MicroFish Flask backend — this wraps it)
The MicroFish Flask app runs on port 5002 internally.
"""

import json
import re
import uuid
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI(title="MicroFish A2A Wrapper")

MICROFISH_BACKEND_URL = "http://localhost:5002"

AGENT_CARD = {
    "name": "microfish",
    "description": "Multi-agent swarm intelligence simulation engine. Extracts entities from documents, builds knowledge graphs, generates agent personas, and runs simulations.",
    "url": "http://localhost:5001",
    "version": "1.0.0",
    "skills": [
        {
            "id": "simulation",
            "name": "Multi-Agent Simulation",
            "description": "Run multi-agent simulations from documents — extracts entities, builds knowledge graph, generates personas, simulates interactions",
        },
        {
            "id": "scenario-analysis",
            "name": "Scenario Analysis",
            "description": "What-if analysis and scenario planning using multi-agent simulation",
        },
        {
            "id": "document-simulation",
            "name": "Document Simulation",
            "description": "Upload documents and simulate how agents interpret and respond to the content",
        },
        {
            "id": "trading-analysis",
            "name": "Trading Probability Analysis",
            "description": "Analyze market events and produce probability distributions for stock price movements. Generates bull/bear/neutral scenarios with confidence scores.",
        },
    ],
    "capabilities": {
        "streaming": False,
        "pushNotifications": False,
        "stateTransitionHistory": False,
    },
    "defaultInputModes": ["text/plain"],
    "defaultOutputModes": ["text/plain"],
}

tasks: dict[str, dict] = {}


@app.get("/.well-known/agent.json")
async def agent_card():
    return JSONResponse(content=AGENT_CARD)


async def handle_trading_analysis(text: str) -> str:
    """
    Trading-specific analysis using multi-persona approach.

    Instead of generic simulation, create a structured trading analysis:
    1. Parse the input for ticker, event, context
    2. Create trading-specific personas via LLM
    3. Have each persona analyze the situation
    4. Aggregate into probability distribution
    """
    from openai import AsyncOpenAI

    # Use Ollama for local LLM
    client = AsyncOpenAI(
        base_url="http://localhost:11434/v1",
        api_key="ollama"
    )

    # Define trading personas
    personas = [
        {
            "name": "Bull Analyst",
            "role": "You are an aggressive growth-focused equity analyst. You look for upside catalysts, momentum signals, and reasons to buy. You're optimistic but back your views with data.",
        },
        {
            "name": "Bear Analyst",
            "role": "You are a cautious, risk-focused analyst. You look for downside risks, overvaluation, competitive threats, and reasons to sell or avoid. You're skeptical of hype.",
        },
        {
            "name": "Macro Strategist",
            "role": "You are a macro economist focused on interest rates, Fed policy, geopolitics, sector rotation, and how macro trends affect individual stocks.",
        },
        {
            "name": "Risk Manager",
            "role": "You are a portfolio risk manager. You evaluate position sizing, correlation risk, drawdown potential, and whether the risk/reward ratio justifies a trade.",
        },
        {
            "name": "Technical Analyst",
            "role": "You are a technical analyst focused on price action, support/resistance levels, volume patterns, moving averages, and chart patterns.",
        },
    ]

    # Step 1: Each persona analyzes the situation
    analyses = []
    for persona in personas:
        try:
            resp = await client.chat.completions.create(
                model="qwen2.5-coder:32b-instruct-q4_K_M",
                messages=[
                    {"role": "system", "content": f"{persona['role']}\n\nProvide your analysis in this JSON format:\n{{\"direction\": \"up|down|flat\", \"confidence\": 0-100, \"target_move_pct\": float, \"timeframe_days\": int, \"key_reasons\": [\"reason1\", \"reason2\"], \"risks\": [\"risk1\", \"risk2\"]}}"},
                    {"role": "user", "content": f"Analyze this market situation and give your trading view:\n\n{text}"}
                ],
                temperature=0.7,
                max_tokens=500,
            )
            analysis_text = resp.choices[0].message.content
            # Try to parse JSON from response
            json_match = re.search(r'\{[^{}]*\}', analysis_text, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
                analysis["persona"] = persona["name"]
                analyses.append(analysis)
            else:
                analyses.append({"persona": persona["name"], "raw": analysis_text, "direction": "flat", "confidence": 50})
        except Exception as e:
            analyses.append({"persona": persona["name"], "error": str(e), "direction": "flat", "confidence": 50})

    # Step 2: Aggregate into probability distribution
    up_votes = sum(1 for a in analyses if a.get("direction") == "up")
    down_votes = sum(1 for a in analyses if a.get("direction") == "down")
    flat_votes = sum(1 for a in analyses if a.get("direction") == "flat")
    total = len(analyses)

    avg_confidence = sum(a.get("confidence", 50) for a in analyses) / total if total > 0 else 50
    avg_target = sum(a.get("target_move_pct", 0) for a in analyses if a.get("target_move_pct")) / max(1, sum(1 for a in analyses if a.get("target_move_pct")))

    consensus_direction = "up" if up_votes > down_votes and up_votes > flat_votes else ("down" if down_votes > up_votes else "flat")

    result = {
        "consensus": {
            "direction": consensus_direction,
            "probability_up": round(up_votes / total * 100, 1) if total > 0 else 33.3,
            "probability_down": round(down_votes / total * 100, 1) if total > 0 else 33.3,
            "probability_flat": round(flat_votes / total * 100, 1) if total > 0 else 33.3,
            "avg_confidence": round(avg_confidence, 1),
            "avg_target_move_pct": round(avg_target, 2),
        },
        "persona_analyses": analyses,
        "recommendation": f"{'BUY' if consensus_direction == 'up' and avg_confidence > 60 else 'SELL' if consensus_direction == 'down' and avg_confidence > 60 else 'HOLD'} (Confidence: {avg_confidence:.0f}%)",
    }

    return json.dumps(result, indent=2, ensure_ascii=False)


@app.post("/a2a")
async def handle_a2a_task(request: Request):
    body = await request.json()
    method = body.get("method", "")
    params = body.get("params", {})

    if method == "tasks/send":
        return await send_task(params, body.get("id"))
    elif method == "tasks/get":
        return get_task(params.get("id"), body.get("id"))
    elif method == "tasks/cancel":
        return cancel_task(params.get("id"), body.get("id"))
    else:
        return JSONResponse(content={"jsonrpc": "2.0", "id": body.get("id"), "error": {"code": -32601, "message": f"Unknown method: {method}"}})


async def send_task(params: dict, rpc_id=None):
    message_parts = params.get("message", {}).get("parts", [])
    text = next((p["text"] for p in message_parts if p.get("type") == "text"), "Run simulation")

    task_id = str(uuid.uuid4())
    tasks[task_id] = {"id": task_id, "status": {"state": "working"}, "created": datetime.now(timezone.utc).isoformat()}

    # Detect trading-related requests
    trading_keywords = ["stock", "trade", "trading", "market", "ticker", "buy", "sell", "price", "earnings",
                        "bull", "bear", "analysis", "probability", "scenario", "forecast",
                        "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "TSLA", "META", "JPM"]
    is_trading = any(kw.lower() in text.lower() for kw in trading_keywords)

    try:
        if is_trading:
            response_text = await handle_trading_analysis(text)
        else:
            # Original generic simulation path
            async with httpx.AsyncClient(timeout=300) as client:
                resp = await client.post(
                    f"{MICROFISH_BACKEND_URL}/api/simulation/quick",
                    json={"text": text, "description": text},
                    timeout=300,
                )
                if resp.status_code == 200:
                    result = resp.json()
                    response_text = json.dumps(result, indent=2, ensure_ascii=False)
                else:
                    response_text = f"MicroFish returned status {resp.status_code}: {resp.text[:500]}"
    except httpx.ConnectError:
        response_text = f"MicroFish backend not running at {MICROFISH_BACKEND_URL}. Start it with: cd backend && uv run python run.py"
    except Exception as e:
        response_text = f"MicroFish error: {str(e)}"

    tasks[task_id]["status"] = {"state": "completed"}
    tasks[task_id]["artifacts"] = [{"parts": [{"type": "text", "text": response_text}]}]
    return JSONResponse(content={"jsonrpc": "2.0", "id": rpc_id, "result": tasks[task_id]})


def get_task(task_id: str, rpc_id=None):
    task = tasks.get(task_id)
    if not task:
        return JSONResponse(content={"jsonrpc": "2.0", "id": rpc_id, "error": {"code": -32602, "message": "Task not found"}})
    return JSONResponse(content={"jsonrpc": "2.0", "id": rpc_id, "result": task})


def cancel_task(task_id: str, rpc_id=None):
    task = tasks.get(task_id)
    if task:
        task["status"] = {"state": "canceled"}
    return JSONResponse(content={"jsonrpc": "2.0", "id": rpc_id, "result": {"id": task_id, "status": {"state": "canceled"}}})


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5001)

