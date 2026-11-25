"""Narrative Detection Engine for discovering, tracking, and clustering Web3 narratives."""

import re
import datetime
from typing import Any, Dict, List, Optional
from zoe.scanner.models import NarrativeRecord, SentimentClass
from zoe.utils.logging import get_logger

logger = get_logger("zoe.scanner.narratives")

# Predefined foundational taxonomy of Web3 narrative clusters & primary keywords
FOUNDATIONAL_NARRATIVES: Dict[str, Dict[str, Any]] = {
    "ai_agents": {
        "name": "Autonomous AI Agents",
        "category": "Artificial Intelligence",
        "description": "Autonomous on-chain agents executing trades, moderation, and decentralized intelligence workflows.",
        "keywords": ["ai agent", "autonomous agent", "virtuals", "elizaos", "ai16z", "swarms", "agentic", "decentralized ai", "llm agent", "bot runner"],
        "known_projects": ["Virtuals Protocol", "ai16z", "Zerebro", "ElizaOS", "Spectral", "Fetch.ai"],
    },
    "depin": {
        "name": "DePIN (Physical Infrastructure)",
        "category": "Infrastructure",
        "description": "Decentralized Physical Infrastructure Networks coordinating real-world hardware, compute, sensors and wireless.",
        "keywords": ["depin", "helium", "render", "io.net", "akash", "compute network", "gpu cluster", "wireless mesh", "grass", "hivemapper"],
        "known_projects": ["Render Network", "Helium", "io.net", "Akash Network", "Grass", "Hivemapper"],
    },
    "rwa": {
        "name": "Real World Assets (RWA)",
        "category": "Tokenization",
        "description": "Tokenization of real-world financial instruments, US Treasuries, private credit, and physical commodities.",
        "keywords": ["rwa", "real world assets", "treasury tokenization", "blackrock buidl", "ondo", "tokenized credit", "gold token", "franklin onchain"],
        "known_projects": ["Ondo Finance", "Mantra", "Clearpool", "Centrifuge", "Maple Finance", "Goldfinch"],
    },
    "layer2": {
        "name": "Layer 2 & Rollup Scaling",
        "category": "Scaling",
        "description": "Optimistic and ZK-rollups scaling Ethereum throughput with low transaction fees and modular execution.",
        "keywords": ["layer 2", "l2", "zk-rollup", "optimism", "arbitrum", "base", "zksync", "starknet", "scroll", "linea", "blob space", "eip-4844"],
        "known_projects": ["Base", "Arbitrum", "Optimism", "zkSync", "Starknet", "Scroll"],
    },
    "restaking": {
        "name": "Restaking & Shared Security",
        "category": "DeFi Security",
        "description": "Extending Ethereum proof-of-stake cryptoeconomic security to external actively validated services (AVSs).",
        "keywords": ["restaking", "eigenlayer", "avs", "symbiotic", "karak", "liquid restaking", "lrt", "etherfi", "renzo", "puffer"],
        "known_projects": ["EigenLayer", "Ether.fi", "Renzo Protocol", "Puffer Finance", "Karak", "Symbiotic"],
    },
    "defi": {
        "name": "Next-Gen DeFi & Perp DEXs",
        "category": "Decentralized Finance",
        "description": "High-performance decentralized derivatives exchanges, concentrated liquidity AMMs, and lending markets.",
        "keywords": ["defi", "dex", "perp dex", "hyperliquid", "uniswap", "aave", "jupiter", "raydium", "orderbook", "amm", "liquidity pool", "yield farming"],
        "known_projects": ["Hyperliquid", "Jupiter", "Uniswap", "Aave", "Raydium", "dYdX"],
    },
    "memecoins": {
        "name": "Cultural & Community Memes",
        "category": "Community",
        "description": "High-velocity cultural community assets, fair-launch bonding curves, and viral tokens.",
        "keywords": ["memecoin", "pump.fun", "bonk", "wif", "dogwifhat", "pepe", "shib", "floki", "fair launch", "bonding curve"],
        "known_projects": ["BONK", "dogwifhat", "Pepe", "Fartcoin", "Popcat"],
    },
    "gaming": {
        "name": "Web3 Gaming & Metaverse",
        "category": "Entertainment",
        "description": "Play-to-own economies, autonomous game worlds, and on-chain gaming engines.",
        "keywords": ["web3 gaming", "gamefi", "immutable", "ronin", "beam", "gala", "on-chain gaming", "autonomous worlds"],
        "known_projects": ["Immutable X", "Ronin", "Beam", "Gala Games", "Illuvium"],
    },
}


class NarrativeDetectionEngine:
    """Discovers, groups, and tracks narrative velocity over time."""

    def __init__(self):
        self._historical_baselines: Dict[str, int] = {
            "ai_agents": 45,
            "depin": 28,
            "rwa": 22,
            "layer2": 35,
            "restaking": 18,
            "defi": 50,
            "memecoins": 65,
            "gaming": 15,
        }

    def extract_narratives_from_corpus(
        self,
        documents: List[Dict[str, Any]],
    ) -> List[NarrativeRecord]:
        """Analyze a corpus of news articles and social posts to measure narrative frequencies."""
        now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        counts: Dict[str, int] = {k: 0 for k in FOUNDATIONAL_NARRATIVES}
        associated_mentions: Dict[str, Dict[str, int]] = {k: {} for k in FOUNDATIONAL_NARRATIVES}
        sentiment_scores: Dict[str, List[float]] = {k: [] for k in FOUNDATIONAL_NARRATIVES}

        for doc in documents:
            text = f"{doc.get('title', '')} {doc.get('snippet', '')} {doc.get('text', '')}".lower()
            doc_sentiment = float(doc.get("sentiment_score", 0.0))

            for nid, nmeta in FOUNDATIONAL_NARRATIVES.items():
                matched = False
                for kw in nmeta["keywords"]:
                    if kw in text:
                        matched = True
                        break

                if matched:
                    counts[nid] += 1
                    sentiment_scores[nid].append(doc_sentiment)

                    # Check for known projects
                    for proj in nmeta["known_projects"]:
                        if proj.lower() in text:
                            associated_mentions[nid][proj] = associated_mentions[nid].get(proj, 0) + 1

        total_mentions = sum(counts.values()) or 1
        results: List[NarrativeRecord] = []

        for nid, nmeta in FOUNDATIONAL_NARRATIVES.items():
            freq = counts[nid]
            baseline = self._historical_baselines.get(nid, 20)
            # Calculate momentum as percentage change over historical baseline
            momentum_pct = round(((freq - baseline) / max(baseline, 1)) * 100, 1) if baseline else 0.0
            mindshare_pct = round((freq / total_mentions) * 100, 1)

            # Determine emergence / status
            if freq >= 5 and momentum_pct >= 50.0:
                status = "surging"
            elif momentum_pct >= 15.0:
                status = "accelerating"
            elif momentum_pct <= -25.0:
                status = "declining"
            else:
                status = "steady"

            # Compute avg sentiment
            scores = sentiment_scores[nid]
            avg_sentiment = round(sum(scores) / len(scores), 2) if scores else 0.1
            if avg_sentiment > 0.25:
                s_label = SentimentClass.POSITIVE
            elif avg_sentiment < -0.2:
                s_label = SentimentClass.NEGATIVE
            else:
                s_label = SentimentClass.NEUTRAL

            # Top linked projects
            top_projects = sorted(
                associated_mentions[nid].keys(),
                key=lambda p: associated_mentions[nid][p],
                reverse=True,
            )[:5]

            # If no direct matches in this batch, use default known projects
            if not top_projects:
                top_projects = nmeta["known_projects"][:3]

            results.append(
                NarrativeRecord(
                    id=nid,
                    name=nmeta["name"],
                    category=nmeta["category"],
                    description=nmeta["description"],
                    keywords=nmeta["keywords"],
                    status=status,
                    current_frequency=freq,
                    historical_frequency=baseline,
                    momentum_pct=momentum_pct,
                    mindshare_pct=mindshare_pct,
                    sentiment_score=avg_sentiment,
                    sentiment_label=s_label,
                    associated_projects=top_projects,
                    sample_size=freq,
                    updated_at=now_str,
                )
            )

        # Sort by momentum percentage descending
        results.sort(key=lambda r: r.momentum_pct, reverse=True)
        return results

    def get_narrative_by_id(self, narrative_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve full taxonomy and metadata for a specific narrative."""
        meta = FOUNDATIONAL_NARRATIVES.get(narrative_id.lower())
        if not meta:
            return None
        return {
            "id": narrative_id,
            "name": meta["name"],
            "category": meta["category"],
            "description": meta["description"],
            "keywords": meta["keywords"],
            "known_projects": meta["known_projects"],
        }
