#!/usr/bin/env python3
"""
SwarmSim — Simulate multi-agent swarms before deploying. Find bottlenecks, test patterns.
Usage: python swarmsim.py --agents 16 --topology hierarchical --tasks 100
"""

import random, time, json, argparse
from dataclasses import dataclass, field
from typing import List, Dict
from collections import defaultdict

TOPOLOGIES = {
    "flat": "All agents communicate directly — best for <5 agents",
    "hierarchical": "Orchestrator → Specialists → Workers — best for 5-50 agents",
    "mesh": "Every agent talks to nearest neighbors — best for distributed tasks",
    "hub_spoke": "One coordinator, N workers — simple but bottleneck at coordinator",
}

@dataclass
class Agent:
    id: int
    role: str
    processing_speed: float  # tasks/second
    failure_rate: float  # 0-1

@dataclass
class SimResult:
    topology: str
    agent_count: int
    task_count: int
    completed: int
    failed: int
    total_time_s: float
    throughput: float  # tasks/second
    bottlenecks: List[str] = field(default_factory=list)
    agent_stats: List[Dict] = field(default_factory=list)

def simulate_hierarchical(agents: List[Agent], tasks: int) -> SimResult:
    """Simulate hierarchical swarm topology."""
    t0 = time.time()
    orchestrator = agents[0]
    specialists = agents[1:4] if len(agents) >= 4 else agents[1:]
    workers = agents[4:] if len(agents) >= 4 else []
    
    completed = 0
    failed = 0
    worker_loads = defaultdict(int)
    
    for task_id in range(tasks):
        # Orchestrator routes to specialist
        if random.random() < orchestrator.failure_rate:
            failed += 1
            continue
        
        # Specialist delegates to worker
        if specialists:
            spec = random.choice(specialists)
            if random.random() < spec.failure_rate:
                failed += 1
                continue
        
        # Worker processes
        if workers:
            worker = random.choice(workers)
            worker_loads[worker.id] += 1
            if random.random() < worker.failure_rate:
                failed += 1
                continue
            # Simulate processing time
            processing_delay = 1.0 / worker.processing_speed
        else:
            processing_delay = 1.0 / orchestrator.processing_speed
        
        completed += 1
    
    elapsed = time.time() - t0
    bottlenecks = []
    if specialists and len(workers) < len(specialists) * 2:
        bottlenecks.append("Worker pool too small for specialist count")
    if orchestrator.processing_speed < 2.0:
        bottlenecks.append("Orchestrator is bottleneck — increase processing speed")
    
    worker_stats = [{"id": wid, "load": load} for wid, load in worker_loads.items()]
    
    return SimResult(
        topology="hierarchical",
        agent_count=len(agents),
        task_count=tasks,
        completed=completed,
        failed=failed,
        total_time_s=round(elapsed, 2),
        throughput=round(completed / elapsed, 1) if elapsed > 0 else 0,
        bottlenecks=bottlenecks,
        agent_stats=worker_stats,
    )

def simulate_flat(agents: List[Agent], tasks: int) -> SimResult:
    """Simulate flat topology — all agents process directly."""
    t0 = time.time()
    completed = 0
    failed = 0
    
    for _ in range(tasks):
        agent = random.choice(agents)
        if random.random() < agent.failure_rate:
            failed += 1
        else:
            completed += 1
    
    elapsed = time.time() - t0
    bottlenecks = []
    if len(agents) > 8:
        bottlenecks.append("Flat topology degrades above 8 agents — consider hierarchical")
    
    return SimResult(
        topology="flat",
        agent_count=len(agents),
        task_count=tasks,
        completed=completed,
        failed=failed,
        total_time_s=round(elapsed, 2),
        throughput=round(completed / elapsed, 1) if elapsed > 0 else 0,
        bottlenecks=bottlenecks,
    )

def generate_agents(count: int) -> List[Agent]:
    roles = ["orchestrator", "specialist", "worker"]
    agents = []
    for i in range(count):
        role = roles[0] if i == 0 else (roles[1] if i < min(4, count) else roles[2])
        agents.append(Agent(
            id=i,
            role=role,
            processing_speed=round(random.uniform(0.5, 3.0), 1),
            failure_rate=round(random.uniform(0, 0.1), 2),
        ))
    return agents

def main():
    parser = argparse.ArgumentParser(description="SwarmSim — Multi-agent swarm simulator")
    parser.add_argument("--agents", "-n", type=int, default=8, help="Number of agents")
    parser.add_argument("--tasks", "-t", type=int, default=100, help="Number of tasks")
    parser.add_argument("--topology", choices=["flat", "hierarchical", "both"], default="both",
                       help="Topology to test")
    parser.add_argument("--output", "-o", help="Save results to JSON")
    
    args = parser.parse_args()
    
    agents = generate_agents(args.agents)
    results = []
    
    print(f"\n🐝 SwarmSim — {args.agents} agents, {args.tasks} tasks\n")
    
    if args.topology in ("flat", "both"):
        r = simulate_flat(agents, args.tasks)
        results.append(r)
        print(f"📐 FLAT:       {r.completed}/{r.tasks} done | {r.throughput} tasks/s | {r.failed} failed")
        for b in r.bottlenecks:
            print(f"   ⚠️  {b}")
    
    if args.topology in ("hierarchical", "both"):
        r = simulate_hierarchical(agents, args.tasks)
        results.append(r)
        print(f"🏗️  HIERARCHY:  {r.completed}/{r.tasks} done | {r.throughput} tasks/s | {r.failed} failed")
        for b in r.bottlenecks:
            print(f"   ⚠️  {b}")
    
    if len(results) == 2:
        faster = max(results, key=lambda r: r.throughput)
        print(f"\n🏆 Recommendation: {faster.topology.upper()} topology is {faster.throughput}x faster")
    
    if args.output:
        with open(args.output, "w") as f:
            json.dump([{"topology": r.topology, "throughput": r.throughput, 
                        "bottlenecks": r.bottlenecks} for r in results], f, indent=2)
        print(f"\n📄 Saved to {args.output}")

if __name__ == "__main__":
    main()
