"""Mindshare Engine calculating mathematical attention share and category comparisons."""

import math
from typing import Any, Dict, List, Optional
from zoe.scanner.models import MindshareResult
from zoe.utils.logging import get_logger

logger = get_logger("zoe.scanner.mindshare")


class MindshareEngine:
    """Calculates data-grounded mindshare percentages across Web3 projects and narratives."""

    @staticmethod
    def calculate_project_mindshare(
        category: str,
        project_data: List[Dict[str, Any]],
        timeframe: str = "24h",
    ) -> MindshareResult:
        """
        Calculate mathematical mindshare percentage for projects in a category.
        Formula:
          diversity_ratio = unique_authors / total_posts
          weighted_mentions = total_posts * sqrt(diversity_ratio)
          mindshare_pct = (weighted_mentions / total_category_weighted_mentions) * 100
        """
        if not project_data:
            return MindshareResult(
                category=category,
                timeframe=timeframe,
                total_mentions_in_category=0,
                total_unique_authors=0,
                projects=[],
            )

        total_posts_sum = sum(p.get("posts_count", 0) for p in project_data)
        total_unique_authors_sum = sum(p.get("unique_authors", 0) for p in project_data)

        # Calculate weighted mentions for each project
        weighted_scores: Dict[str, float] = {}
        for p in project_data:
            name = p.get("name", "Unknown")
            posts = p.get("posts_count", 0)
            authors = p.get("unique_authors", posts)
            diversity = (authors / posts) if posts > 0 else 1.0
            # Discount spam/astroturfing using square root of author diversity
            weighted = posts * math.sqrt(max(0.1, diversity))
            weighted_scores[name] = weighted

        total_weighted = sum(weighted_scores.values()) or 1.0

        ranked_projects = []
        for p in project_data:
            name = p.get("name", "Unknown")
            symbol = p.get("symbol", "")
            posts = p.get("posts_count", 0)
            authors = p.get("unique_authors", posts)
            weighted = weighted_scores[name]
            share_pct = round((weighted / total_weighted) * 100, 2)
            prev_share = float(p.get("previous_mindshare_pct", share_pct))
            change_pct = round(share_pct - prev_share, 2)

            ranked_projects.append({
                "name": name,
                "symbol": symbol,
                "posts_count": posts,
                "unique_authors": authors,
                "mindshare_pct": share_pct,
                "previous_mindshare_pct": prev_share,
                "change_pct": change_pct,
                "author_diversity_ratio": round(authors / max(posts, 1), 2),
            })

        # Sort descending by mindshare percentage
        ranked_projects.sort(key=lambda x: x["mindshare_pct"], reverse=True)

        return MindshareResult(
            category=category,
            timeframe=timeframe,
            total_mentions_in_category=total_posts_sum,
            total_unique_authors=total_unique_authors_sum,
            projects=ranked_projects,
        )
