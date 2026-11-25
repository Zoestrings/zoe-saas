"""AI NFT Generation Studio Tool (Pillar 2).

Uses the free Pollinations.ai image generation endpoint to create unique Web3
NFT artwork at zero infrastructure cost.
"""

import logging
import urllib.parse
import httpx

logger = logging.getLogger("zoe.tools.nft_studio")


async def generate_nft_image(prompt: str) -> str:
    """Generate AI NFT artwork using Pollinations.ai and return the image URL."""
    clean_prompt = (prompt or "").strip()
    if not clean_prompt:
        raise ValueError("Prompt cannot be empty.")

    encoded_prompt = urllib.parse.quote(clean_prompt, safe="")
    image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"

    # Pre-warm / verify the Pollinations endpoint via httpx
    try:
        async with httpx.AsyncClient(timeout=25.0, follow_redirects=True) as client:
            resp = await client.get(image_url)
            if resp.status_code == 200:
                return str(resp.url) if resp.url else image_url
            logger.warning("Pollinations returned status %s; returning direct URL.", resp.status_code)
    except Exception as exc:
        logger.warning("Pollinations pre-warm request encountered error (%s); returning direct URL.", exc)

    return image_url
