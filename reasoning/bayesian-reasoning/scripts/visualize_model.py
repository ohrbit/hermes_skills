#!/usr/bin/env python3
"""
Visualization Script for Bayesian Reasoning Skill.

Visualize model graphs, inference results, and learning progress.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any

try:
    import networkx as nx
    import matplotlib.pyplot as plt
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False

try:
    import graphviz
    GRAPHVIZ_AVAILABLE = True
except ImportError:
    GRAPHVIZ_AVAILABLE = False

try:
    import pgmpy
    from pgmpy.models import BayesianNetwork
    PGMPY_AVAILABLE = True
except ImportError:
    PGMPY_AVAILABLE = False
    BayesianNetwork = object

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

logger = logging.getLogger(__name__)


def visualize_model(
    model_name: str,
    model: Any,
    output_path: str = None,
    layout: str = "dot",
    show_cpts: bool = False,
    highlight_path: list = None,
):
    """
    Visualize a Bayesian/Markov network.
    
    Args:
        model_name: Name for title
        model: pgmpy BayesianNetwork or MarkovNetwork
        output_path: Path to save (png, pdf, svg) or None to display
        layout: graphviz layout engine (dot, neato, fdp, sfdp, circo, twopi)
        show_cpts: Show CPT info in node labels
        highlight_path: List of nodes to highlight (e.g., causal path)
    """
    if not NETWORKX_AVAILABLE:
        raise RuntimeError("networkx required: pip install networkx")
    
    if not GRAPHVIZ_AVAILABLE:
        raise RuntimeError("graphviz required: pip install graphviz AND system graphviz")
    
    # Convert pgmpy model to networkx
    if hasattr(model, 'edges'):
        G = nx.DiGraph() if isinstance(model, BayesianNetwork) else nx.Graph()
        G.add_nodes_from(model.nodes())
        G.add_edges_from(model.edges())
    else:
        raise ValueError(f"Unsupported model type: {type(model)}")
    
    # Create graphviz graph
    if isinstance(model, BayesianNetwork):
        dot = graphviz.Digraph(name=model_name, format='png')
    else:
        dot = graphviz.Graph(name=model_name, format='png')
    
    dot.attr(rankdir='LR', fontsize='12', fontname='Helvetica')
    dot.attr('node', shape='ellipse', style='filled', fillcolor='lightblue',
             fontname='Helvetica', fontsize='10')
    dot.attr('edge', fontname='Helvetica', fontsize='9')
    
    # Add nodes
    for node in G.nodes():
        label = node
        if show_cpts and hasattr(model, 'get_cpds'):
            cpd = model.get_cpds(node)
            if cpd:
                parents = list(model.get_parents(node))
                label = f"{node}\nP({node}|{','.join(parents)})" if parents else f"{node}\nP({node})"
        
        # Highlight path
        color = 'lightcoral' if highlight_path and node in highlight_path else 'lightblue'
        if node in (highlight_path or [])[:1]:
            color = 'lightgreen'  # source
        elif node in (highlight_path or [])[-1:]:
            color = 'gold'  # target
        
        dot.node(node, label=label, fillcolor=color)
    
    # Add edges
    for u, v in G.edges():
        dot.edge(u, v)
    
    # Add legend
    with dot.subgraph(name='cluster_legend') as c:
        c.attr(label='Legend', style='dashed', color='gray')
        c.node('legend1', 'Normal', shape='ellipse', style='filled', fillcolor='lightblue')
        c.node('legend2', 'Intervention/Source', shape='ellipse', style='filled', fillcolor='lightgreen')
        c.node('legend3', 'Target/Query', shape='ellipse', style='filled', fillcolor='gold')
        c.node('legend4', 'Highlighted Path', shape='ellipse', style='filled', fillcolor='lightcoral')
        c.edge('legend1', 'legend2', style='invis')
        c.edge('legend2', 'legend3', style='invis')
        c.edge('legend3', 'legend4', style='invis')
    
    # Render
    if output_path:
        dot.render(output_path.replace('.png', ''), cleanup=True)
        logger.info(f"Graph saved to {output_path}")
    else:
        dot.view()


def visualize_inference_result(
    result: Any,
    output_path: str = None,
    max_vars: int = 10,
):
    """
    Visualize inference result marginals as bar charts.
    
    Args:
        result: InferenceResult from InferenceEngine
        output_path: Path to save figure
        max_vars: Max variables to plot
    """
    if not NUMPY_AVAILABLE or not NETWORKX_AVAILABLE:
        raise RuntimeError("numpy and matplotlib required")
    
    import matplotlib.pyplot as plt
    
    vars_to_plot = list(result.marginals.keys())[:max_vars]
    n = len(vars_to_plot)
    
    fig, axes = plt.subplots(1, n, figsize=(4*n, 4))
    if n == 1:
        axes = [axes]
    
    for i, var in enumerate(vars_to_plot):
        ax = axes[i]
        marginal = result.marginal(var)
        states = list(marginal.keys())
        probs = list(marginal.values())
        
        bars = ax.bar(range(len(states)), probs, 
                     color='steelblue', edgecolor='darkblue', alpha=0.7)
        
        # Highlight MAP
        map_idx = np.argmax(probs)
        bars[map_idx].set_color('coral')
        
        ax.set_xticks(range(len(states)))
        ax.set_xticklabels(states, rotation=45, ha='right')
        ax.set_ylabel('Probability')
        ax.set_title(f"{var} (MAP: {states[map_idx]})")
        ax.set_ylim(0, max(probs) * 1.2)
        
        # Add value labels
        for bar, prob in zip(bars, probs):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                   f'{prob:.3f}', ha='center', va='bottom', fontsize=8)
    
    fig.suptitle(f"Inference Result: {result.model_name}\nEvidence: {result.evidence}", 
                fontsize=12, y=1.02)
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        logger.info(f"Plot saved to {output_path}")
    else:
        plt.show()


def visualize_learning_curve(
    history: list[dict],
    output_path: str = None,
):
    """
    Plot structure learning progress.
    
    Args:
        history: List of dicts with keys: iteration, score, edges_changed
        output_path: Path to save figure
    """
    if not NUMPY_AVAILABLE:
        raise RuntimeError("numpy required")
    
    import matplotlib.pyplot as plt
    
    iters = [h['iteration'] for h in history]
    scores = [h['score'] for h in history]
    edges_changed = [h.get('edges_changed', 0) for h in history]
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 8))
    
    # Score curve
    ax1.plot(iters, scores, 'b-o', linewidth=2, markersize=6)
    ax1.set_xlabel('Iteration')
    ax1.set_ylabel('BIC Score (higher=better)')
    ax1.set_title('Structure Learning: Score Convergence')
    ax1.grid(True, alpha=0.3)
    
    # Edges changed
    ax2.bar(iters, edges_changed, color='orange', alpha=0.7, edgecolor='darkorange')
    ax2.set_xlabel('Iteration')
    ax2.set_ylabel('Edges Added/Removed')
    ax2.set_title('Graph Changes per Iteration')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        logger.info(f"Plot saved to {output_path}")
    else:
        plt.show()


def visualize_sensitivity(
    explanation: Any,
    output_path: str = None,
):
    """
    Plot sensitivity analysis from Explanation object.
    """
    if not NUMPY_AVAILABLE:
        raise RuntimeError("numpy required")
    
    import matplotlib.pyplot as plt
    
    # Sensitivity heatmap
    vars = list(explanation.sensitivity.keys())
    if not vars:
        logger.warning("No sensitivity data to plot")
        return
    
    # Collect all states
    all_states = set()
    for v in vars:
        all_states.update(explanation.sensitivity[v].keys())
    all_states = sorted(all_states)
    
    # Build matrix
    matrix = np.zeros((len(vars), len(all_states)))
    for i, v in enumerate(vars):
        for j, s in enumerate(all_states):
            matrix[i, j] = explanation.sensitivity[v].get(s, 0)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    im = ax.imshow(matrix, cmap='RdBu_r', aspect='auto', vmin=-0.5, vmax=0.5)
    
    ax.set_xticks(range(len(all_states)))
    ax.set_xticklabels(all_states, rotation=45)
    ax.set_yticks(range(len(vars)))
    ax.set_yticklabels(vars)
    ax.set_title(f'Sensitivity Analysis for {explanation.target}\n'
                f'Prediction: {explanation.prediction} (confidence: {explanation.confidence:.2f})')
    
    plt.colorbar(im, ax=ax, label='ΔP (change in prediction probability)')
    
    # Add text annotations
    for i in range(len(vars)):
        for j in range(len(all_states)):
            color = 'white' if abs(matrix[i, j]) > 0.25 else 'black'
            ax.text(j, i, f'{matrix[i, j]:.3f}', ha='center', va='center', 
                   color=color, fontsize=8)
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        logger.info(f"Plot saved to {output_path}")
    else:
        plt.show()


def visualize_counterfactuals(
    explanation: Any,
    output_path: str = None,
):
    """
    Plot counterfactual outcomes.
    """
    if not explanation.counterfactuals:
        logger.warning("No counterfactuals to plot")
        return
    
    import matplotlib.pyplot as plt
    
    cfs = explanation.counterfactuals[:10]  # Top 10
    
    # Build data
    labels = []
    probs = []
    changes = []
    for cf in cfs:
        inter = cf['intervention']
        label = ', '.join(f"{k}={v}" for k, v in inter.items())
        labels.append(label)
        probs.append(cf['probability'])
        changes.append(cf['change'])
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    y_pos = range(len(labels))
    bars = ax.barh(y_pos, probs, color='steelblue', alpha=0.7, edgecolor='darkblue')
    
    # Color by change direction
    for bar, change in zip(bars, changes):
        if change > 0:
            bar.set_color('seagreen')
        elif change < 0:
            bar.set_color('coral')
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels)
    ax.set_xlabel('Probability')
    ax.set_title(f'Counterfactuals: {explanation.target} = {explanation.prediction}')
    
    # Add baseline reference
    ax.axvline(explanation.confidence, color='black', linestyle='--', 
              label=f'Baseline: {explanation.confidence:.3f}', alpha=0.5)
    ax.legend()
    
    # Add value labels
    for bar, prob, change in zip(bars, probs, changes):
        ax.text(prob + 0.01, bar.get_y() + bar.get_height()/2,
               f'{prob:.3f} ({change:+.3f})', va='center', fontsize=8)
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        logger.info(f"Plot saved to {output_path}")
    else:
        plt.show()


def main():
    parser = argparse.ArgumentParser(description="Visualize Bayesian models and inference")
    parser.add_argument("--model", help="Model name to visualize")
    parser.add_argument("--registry", default="models/registry.yaml", help="Registry path")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--layout", default="dot", choices=["dot", "neato", "fdp", "sfdp", "circo", "twopi"])
    parser.add_argument("--show-cpts", action="store_true", help="Show CPT info in nodes")
    parser.add_argument("--highlight", nargs="+", help="Nodes to highlight")
    parser.add_argument("--inference-result", help="Path to inference result JSON")
    parser.add_argument("--learning-history", help="Path to learning history JSON")
    parser.add_argument("--explanation", help="Path to explanation JSON")
    parser.add_argument("--list-models", action="store_true", help="List available models")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    if args.list_models:
        # Load registry and list
        from scripts.model_registry import ModelRegistry
        registry = ModelRegistry(args.registry)
        for name in registry.list_models():
            model = registry.get(name)
            print(f"  {name}: {model.model_type.value} - {model.description}")
        return
    
    if args.model:
        # Load model from engine
        from scripts.inference import InferenceEngine
        engine = InferenceEngine()
        
        # This would need actual model loading
        # For now, show template
        logger.info(f"Model visualization for {args.model}")
        logger.info("Run with actual loaded model from InferenceEngine")
        
        # Example with synthetic model
        if PGMPY_AVAILABLE:
            from pgmpy.models import BayesianNetwork
            from pgmpy.factors.discrete import TabularCPD
            
            model = BayesianNetwork([("A", "C"), ("B", "C"), ("C", "D")])
            model.name = args.model
            cpd_a = TabularCPD("A", 2, [[0.6], [0.4]])
            cpd_b = TabularCPD("B", 2, [[0.7], [0.3]])
            cpd_c = TabularCPD("C", 2, [[0.9,0.6,0.7,0.1],[0.1,0.4,0.3,0.9]], 
                              evidence=["A","B"], evidence_card=[2,2])
            cpd_d = TabularCPD("D", 2, [[0.8,0.2],[0.2,0.8]], evidence=["C"], evidence_card=[2])
            model.add_cpds(cpd_a, cpd_b, cpd_c, cpd_d)
            
            out = args.output or f"{args.model}_graph"
            visualize_model(args.model, model, out, args.layout, args.show_cpts, args.highlight)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()