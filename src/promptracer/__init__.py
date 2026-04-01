"""PromptRacer — The open-source prompt engineering toolkit."""

from promptracer.prompt import Prompt
from promptracer.compare import compare
from promptracer.eval import evaluate
from promptracer.batch import run_batch, run_suite
from promptracer.chain import Chain
from promptracer.leaderboard import build_leaderboard
from promptracer.dataset import load_cases

__version__ = "0.4.0"
__all__ = [
    "Prompt",
    "compare",
    "evaluate",
    "run_batch",
    "run_suite",
    "Chain",
    "build_leaderboard",
    "load_cases",
]
