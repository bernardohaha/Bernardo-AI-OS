import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.agents.agent_meso import agent_meso

if __name__ == "__main__":
    result = agent_meso("SUI")
    print(result)
