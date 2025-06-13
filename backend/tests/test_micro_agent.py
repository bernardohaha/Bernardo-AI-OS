import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.agents.agent_micro import agent_micro

if __name__ == "__main__":
    result = agent_micro("SUI")
    print(result)
