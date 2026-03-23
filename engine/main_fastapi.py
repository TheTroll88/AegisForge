from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict
import os, json, asyncio, csv, random, sys, importlib
from datetime import datetime
from collections import defaultdict
from pydantic import BaseModel
from dotenv import load_dotenv
import requests
import numpy as np

# === Local Imports ===
from core.trader import PaperTrader
from core.config import TraderConfig
# Micro blockchain trader
try:
    from core.micro_trader import MicroTrader
except Exception:
    MicroTrader = None
from core.live_data_feed import LiveDataFeed
from core.trade_logger import TradeLogger
from core.logger import setup_logger

# === Init ===
BASE_DIR = Path(__file__).resolve().parent
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1/chat/completions")

# === Logging and Trading Setup ===
logger = setup_logger()
trade_logger = TradeLogger()
# Choose trader implementation based on config
if TraderConfig.MICRO_MODE and MicroTrader is not None:
    logger.info("🔁 Starting in MICRO trading mode (autonomous on-chain)")
    trader = MicroTrader(logger=logger, trade_logger=trade_logger)
else:
    trader = PaperTrader(logger=logger, trade_logger=trade_logger)

# === App Paths ===
LOG_PATH = BASE_DIR / 'logs' / 'trade_log.json'
PERFORMANCE_PATH = BASE_DIR / 'logs' / 'performance.json'
TRADE_HISTORY_CSV = BASE_DIR / 'logs' / 'trade_history.csv'
STRATEGIES_DIR = BASE_DIR / 'core' / 'strategies'
os.makedirs(BASE_DIR / 'logs', exist_ok=True)

# === Strategy Tracker ===
strategy_states: Dict[str, bool] = {}
strategies = []

if STRATEGIES_DIR.exists():
    for file in STRATEGIES_DIR.iterdir():
        if file.suffix == ".py" and file.name != "__init__.py":
            module_name = file.stem
            class_name = ''.join(part.capitalize() for part in module_name.split('_'))
            try:
                module = importlib.import_module(f"core.strategies.{module_name}")
                # Try exact match first, then search for any class ending with 'Strategy'
                strategy_class = None
                if hasattr(module, class_name):
                    strategy_class = getattr(module, class_name)
                else:
                    # Find the first class that ends with 'Strategy'
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if isinstance(attr, type) and attr_name.endswith('Strategy'):
                            strategy_class = attr
                            break
                
                if strategy_class:
                    strategy_instance = strategy_class()
                    strategies.append((module_name.replace("_strategy", ""), strategy_instance))
                    strategy_states[module_name.replace("_strategy", "")] = True
                    logger.info(f"✅ Loaded strategy: {strategy_class.__name__}")
                else:
                    logger.error(f"❌ Failed to load strategy from {module_name}: No Strategy class found")
            except Exception as e:
                logger.error(f"❌ Failed to load strategy {class_name}: {e}")

# === Live Symbol Chunker ===
def chunk_symbols(symbols, size=50):
    for i in range(0, len(symbols), size):
        yield symbols[i:i + size]

# === Lifespan Hook ===
@asynccontextmanager
async def lifespan(app: FastAPI):
    sys.stdout.reconfigure(encoding='utf-8')
    print("[INFO] AegisForge Engine Booting Up with Live Market Data...")
    asyncio.create_task(strategy_loop())
    yield

# === FastAPI App ===
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === OpenRouter Chat Endpoint ===
def query_openrouter_chat(prompt):
    if not OPENAI_API_KEY:
        raise Exception("OPENAI_API_KEY missing in .env")

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "openai/gpt-4",
        "messages": [
            {"role": "system", "content": "You are an AI assistant named Aegis that helps manage a trading system."},
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.post(OPENAI_BASE_URL, headers=headers, json=payload)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]

# === Routes ===
@app.get("/")
async def home():
    return {"status": "AegisForge API is live"}

@app.post("/chat")
async def chat_endpoint(request: Request):
    body = await request.json()
    prompt = body.get("prompt", "")
    if not prompt:
        raise HTTPException(status_code=400, detail="No prompt provided")
    reply = query_openrouter_chat(prompt)
    return {"response": reply}

@app.get("/strategies")
async def get_strategies():
    return {"strategies": list(strategy_states.keys())}

@app.get("/strategy/{name}/status")
async def get_strategy_status(name: str):
    if name not in strategy_states:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return {"strategy": name, "active": strategy_states[name]}

@app.post("/strategy/{name}/toggle")
async def toggle_strategy(name: str):
    if name not in strategy_states:
        raise HTTPException(status_code=404, detail="Strategy not found")
    strategy_states[name] = not strategy_states[name]
    return {"strategy": name, "active": strategy_states[name]}

@app.get("/trade-logs")
async def get_trade_logs():
    if not LOG_PATH.exists():
        raise HTTPException(status_code=404, detail="Trade logs not found")
    with open(LOG_PATH, 'r') as file:
        return {"logs": json.load(file)}

@app.get("/performance")
async def get_performance():
    if PERFORMANCE_PATH.exists():
        with open(PERFORMANCE_PATH, 'r') as file:
            return json.load(file)
    raise HTTPException(status_code=404, detail="Performance data not found")

@app.get("/performance/live")
async def get_live_performance():
    if not LOG_PATH.exists():
        raise HTTPException(status_code=404, detail="Log file not found")

    with open(LOG_PATH, "r") as f:
        try:
            trades = json.load(f)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Invalid log format")

    total = len(trades)
    wins = sum(1 for t in trades if t.get("success") is True)
    roi_sum = sum(t.get("roi", 0) for t in trades)

    strat_summary = defaultdict(lambda: {"wins": 0, "losses": 0, "roi": 0, "trades": 0})
    for t in trades:
        strat = t.get("strategy", "unknown")
        strat_summary[strat]["trades"] += 1
        if t.get("success"):
            strat_summary[strat]["wins"] += 1
        else:
            strat_summary[strat]["losses"] += 1
        strat_summary[strat]["roi"] += t.get("roi", 0)

    for s in strat_summary.values():
        if s["trades"] > 0:
            s["roi"] = round(s["roi"] / s["trades"], 2)

    return {
        "total_trades": total,
        "win_rate": round((wins / total) * 100, 2) if total > 0 else 0,
        "average_roi": round(roi_sum / total, 2) if total > 0 else 0,
        "profit_loss": "🧠 Simulated only",
        "strategies": strat_summary
    }

@app.get("/strategy/{name}/config")
async def get_strategy_config(name: str):
    strategy_file = next(
        (f for f in STRATEGIES_DIR.glob("*.py") if f.name != "__init__.py" and f.stem.lower().startswith(name.lower())),
        None
    )
    if not strategy_file:
        raise HTTPException(status_code=404, detail="Strategy file not found")

    with open(strategy_file, "r") as f:
        lines = f.readlines()
    config_lines = [line.strip() for line in lines if "=" in line and not line.strip().startswith("#")]

    return {"strategy": name, "config": config_lines}

@app.post("/strategy/{name}/config/update")
async def update_strategy_config(name: str, request: Request):
    strategy_file = next(
        (f for f in STRATEGIES_DIR.glob("*.py") if f.name != "__init__.py" and f.stem.lower().startswith(name.lower())),
        None
    )
    if not strategy_file:
        raise HTTPException(status_code=404, detail="Strategy file not found")

    data = await request.json()
    new_lines = data.get("config_lines", None)
    if not new_lines or not isinstance(new_lines, list):
        raise HTTPException(status_code=400, detail="Invalid config data")

    with open(strategy_file, "w") as f:
        for line in new_lines:
            f.write(f"{line}\n")

    return {"status": "success", "message": f"{strategy_file.name} updated"}

# === Background Market Scanner ===
async def strategy_loop():
    print("[LIVE] AegisForge market loop online...")
    market = LiveDataFeed()
    symbols = market.symbols
    symbol_chunks = list(chunk_symbols(symbols, 50))
    chunk_index = 0

    while True:
        current_symbols = symbol_chunks[chunk_index % len(symbol_chunks)]
        chunk_index += 1

        market.symbols = current_symbols
        live_data = market.get_all()

        for data in live_data:
                for name, strategy in strategies:
                if not strategy_states.get(name):
                    continue
                try:
                    signal = strategy.evaluate(data)
                    action = signal.get("action")
                    if action in ["buy", "sell"]:
                            # Execute using the configured trader (paper or micro/live)
                            try:
                                trader.execute(signal, data, strategy_name=name)
                            except Exception as e:
                                logger.error(f"⚠️ Trader execution failed: {e}")
                except Exception as e:
                    logger.warning(f"⚠️ Strategy {name} failed: {e}")

        # After processing signals, check any open positions for TP/SL
        try:
            if hasattr(trader, 'check_positions'):
                trader.check_positions()
        except Exception as e:
            logger.error(f"⚠️ Position check failed: {e}")

        await asyncio.sleep(3)

np