import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.agents.agent_macro import agent_macro

if __name__ == "__main__":
    result = agent_macro("SUI")
    print(result)
