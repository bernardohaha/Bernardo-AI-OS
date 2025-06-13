import sys
import os

# Garante que o Python encontra o módulo backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.agents.supervisor_agent import supervisor_agent

if __name__ == "__main__":
    result = supervisor_agent("SUI")  # substitui por outro símbolo se quiseres
    print(result)
