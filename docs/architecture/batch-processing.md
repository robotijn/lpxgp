# Batch Processing & Orchestration

This document specifies the batch processing system for running debates asynchronously
and caching results for instant retrieval.

---

## Overview

Debates run as **nightly batch jobs**, not in real-time. Results are cached for months
and only recomputed when entities change.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         BATCH PROCESSING ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      SCHEDULER (Railway Cron)                        │    │
│  │                                                                      │    │
│  │  2:00 AM UTC: Nightly full batch                                    │    │
│  │  Every 4h: Incremental updates                                      │    │
│  │  On-demand: Entity-specific triggers                                │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      BATCH PROCESSOR                                 │    │
│  │                                                                      │    │
│  │  1. Identify changed entities (funds, LPs)                          │    │
│  │  2. Determine affected matches                                      │    │
│  │  3. Queue debates for execution                                     │    │
│  │  4. Run debates in parallel (rate-limited)                          │    │
│  │  5. Cache results                                                   │    │
│  │  6. Report metrics                                                  │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      ENTITY CACHE                                    │    │
│  │                                                                      │    │
│  │  - Debate results cached for months                                 │    │
│  │  - Instant retrieval for users                                      │    │
│  │  - Automatic invalidation on entity change                          │    │
│  │  - Manual invalidation API                                          │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Scheduler Configuration

### Railway Cron Jobs

```python
# src/agents/batch/scheduler.py

from datetime import datetime, timedelta
from enum import Enum
import asyncio

from src.agents.batch.processor import BatchProcessor
from src.db import supabase


class JobType(Enum):
    NIGHTLY_FULL = "nightly_full"
    INCREMENTAL = "incremental"
    ENTITY_SPECIFIC = "entity_specific"
    DEBATE_RERUN = "debate_rerun"


class BatchScheduler:
    """
    Schedules and coordinates batch jobs.

    Job Types:
    - nightly_full: Complete recomputation of all matches (2 AM UTC)
    - incremental: Only changed entities (every 4 hours)
    - entity_specific: Triggered when entity is updated
    - debate_rerun: Manual re-run of specific debates
    """

    def __init__(self):
        self.processor = BatchProcessor()

    async def run_nightly_full(self):
        """
        Nightly full batch job.

        1. Get all active funds
        2. Get all LPs with complete profiles
        3. Run constraint interpretation for any new/changed LP mandates
        4. Run match scoring debates for all fund-LP combinations
        5. Pre-generate pitches for top matches
        """
        job_id = await self._create_job(JobType.NIGHTLY_FULL)

        try:
            # Get entities
            funds = await self._get_active_funds()
            lps = await self._get_scorable_lps()

            total_matches = len(funds) * len(lps)
            await self._update_job(job_id, {"total_items": total_matches})

            # Run constraint interpretation for LPs with changed mandates
            lps_needing_interpretation = [
                lp for lp in lps
                if await self._mandate_changed_since_last_run(lp["id"])
            ]
            await self.processor.run_constraint_debates(lps_needing_interpretation)

            # Run match scoring debates
            for fund in funds:
                for lp in lps:
                    if await self._needs_recompute(fund["id"], lp["id"]):
                        await self.processor.queue_match_debate(fund, lp, job_id)

            # Process queue with rate limiting
            results = await self.processor.process_queue(job_id)

            # Pre-generate pitches for top matches
            await self.processor.pre_generate_pitches(job_id, top_n=10)

            await self._complete_job(job_id, results)

        except Exception as e:
            await self._fail_job(job_id, str(e))
            raise

    async def run_incremental(self):
        """
        Incremental batch job (every 4 hours).

        Only processes:
        - New funds since last run
        - Updated funds since last run
        - New LPs since last run
        - LPs with updated mandates since last run
        """
        job_id = await self._create_job(JobType.INCREMENTAL)

        try:
            last_run = await self._get_last_successful_run()

            # Get changed entities
            new_funds = await self._get_funds_since(last_run)
            updated_funds = await self._get_updated_funds_since(last_run)
            new_lps = await self._get_lps_since(last_run)
            updated_lps = await self._get_updated_lps_since(last_run)

            # Determine affected matches
            affected_matches = set()

            for fund in new_funds + updated_funds:
                # New/updated fund affects all LP matches
                lps = await self._get_scorable_lps()
                for lp in lps:
                    affected_matches.add((fund["id"], lp["id"]))

            for lp in new_lps + updated_lps:
                # New/updated LP affects all fund matches
                funds = await self._get_active_funds()
                for fund in funds:
                    affected_matches.add((fund["id"], lp["id"]))

            await self._update_job(job_id, {"total_items": len(affected_matches)})

            # Queue affected debates
            for fund_id, lp_id in affected_matches:
                fund = await self._get_fund(fund_id)
                lp = await self._get_lp(lp_id)
                await self.processor.queue_match_debate(fund, lp, job_id)

            results = await self.processor.process_queue(job_id)
            await self._complete_job(job_id, results)

        except Exception as e:
            await self._fail_job(job_id, str(e))
            raise

    async def run_entity_specific(self, entity_type: str, entity_id: str):
        """
        Triggered when a specific entity is updated.

        Called from API webhooks when:
        - Fund is created/updated
        - LP is created/updated
        - LP mandate is changed
        """
        job_id = await self._create_job(
            JobType.ENTITY_SPECIFIC,
            scope_filter={"entity_type": entity_type, "entity_id": entity_id}
        )

        try:
            if entity_type == "fund":
                # Invalidate all cached results for this fund
                await self._invalidate_fund_cache(entity_id)

                # Queue debates with all LPs
                fund = await self._get_fund(entity_id)
                lps = await self._get_scorable_lps()

                for lp in lps:
                    await self.processor.queue_match_debate(fund, lp, job_id)

            elif entity_type == "lp":
                # Re-run constraint interpretation
                lp = await self._get_lp(entity_id)
                await self.processor.run_constraint_debate(lp)

                # Invalidate all cached results for this LP
                await self._invalidate_lp_cache(entity_id)

                # Queue debates with all funds
                funds = await self._get_active_funds()
                for fund in funds:
                    await self.processor.queue_match_debate(fund, lp, job_id)

            results = await self.processor.process_queue(job_id)
            await self._complete_job(job_id, results)

        except Exception as e:
            await self._fail_job(job_id, str(e))
            raise

    # Helper methods
    async def _create_job(self, job_type: JobType, scope_filter: dict = None) -> str:
        result = await supabase.table("batch_jobs").insert({
            "job_type": job_type.value,
            "scope_filter": scope_filter or {},
            "status": "pending",
        }).execute()
        return result.data[0]["id"]

    async def _needs_recompute(self, fund_id: str, lp_id: str) -> bool:
        """Check if match needs recomputation."""
        cache = await supabase.table("entity_cache").select("*").eq(
            "entity_type", "match"
        ).eq(
            "entity_id", f"{fund_id}:{lp_id}"
        ).eq(
            "cache_key", "debate_result"
        ).is_("invalidated_at", "null").execute()

        if not cache.data:
            return True  # No cache, needs computation

        # Check if cache is still valid
        cache_entry = cache.data[0]
        if cache_entry.get("valid_until"):
            if datetime.fromisoformat(cache_entry["valid_until"]) < datetime.now():
                return True  # Expired

        return False  # Cache is valid
```

### Railway Cron Configuration

```toml
# railway.toml

[service]
name = "lpxgp"

[[cron]]
schedule = "0 2 * * *"  # 2 AM UTC daily
command = "python -m src.agents.batch.run_nightly"

[[cron]]
schedule = "0 */4 * * *"  # Every 4 hours
command = "python -m src.agents.batch.run_incremental"
```

---

## Batch Processor

```python
# src/agents/batch/processor.py

import asyncio
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from typing import AsyncIterator

from langsmith import traceable

from src.agents.orchestrator import DebateOrchestrator
from src.agents.config import DebateType
from src.db import supabase


@dataclass
class QueuedDebate:
    """A debate waiting to be processed."""
    fund_id: str
    lp_id: str
    fund_data: dict
    lp_data: dict
    job_id: str
    priority: int = 0  # Higher = process first


@dataclass
class BatchResults:
    """Results from a batch run."""
    total_items: int
    processed: int
    failed: int
    tokens_used: int
    cost_cents: int
    duration_seconds: float
    errors: list[dict]


class BatchProcessor:
    """
    Processes queued debates with rate limiting and error handling.
    """

    def __init__(
        self,
        max_concurrent: int = 10,
        rate_limit_per_minute: int = 60,
    ):
        self.max_concurrent = max_concurrent
        self.rate_limit_per_minute = rate_limit_per_minute
        self.queue: deque[QueuedDebate] = deque()
        self.orchestrator = DebateOrchestrator()

    async def queue_match_debate(
        self,
        fund: dict,
        lp: dict,
        job_id: str,
        priority: int = 0,
    ):
        """Add a match debate to the queue."""
        self.queue.append(QueuedDebate(
            fund_id=fund["id"],
            lp_id=lp["id"],
            fund_data=fund,
            lp_data=lp,
            job_id=job_id,
            priority=priority,
        ))

    @traceable(name="batch_process_queue", tags=["batch"])
    async def process_queue(self, job_id: str) -> BatchResults:
        """
        Process all queued debates with rate limiting.

        Features:
        - Parallel execution up to max_concurrent
        - Rate limiting to avoid API throttling
        - Error handling with retry
        - Progress tracking
        """
        start_time = datetime.now()

        # Sort by priority
        sorted_queue = sorted(self.queue, key=lambda x: -x.priority)

        total = len(sorted_queue)
        processed = 0
        failed = 0
        tokens = 0
        errors = []

        # Process in batches
        semaphore = asyncio.Semaphore(self.max_concurrent)
        rate_limiter = RateLimiter(self.rate_limit_per_minute)

        async def process_one(item: QueuedDebate):
            nonlocal processed, failed, tokens

            async with semaphore:
                await rate_limiter.acquire()

                try:
                    result = await self.orchestrator.run_match_debate(
                        fund_id=item.fund_id,
                        lp_org_id=item.lp_id,
                        fund_data=item.fund_data,
                        lp_data=item.lp_data,
                    )

                    tokens += result.get("total_tokens", 0)
                    processed += 1

                    # Update job progress
                    await self._update_progress(job_id, processed, total)

                except Exception as e:
                    failed += 1
                    errors.append({
                        "fund_id": item.fund_id,
                        "lp_id": item.lp_id,
                        "error": str(e),
                    })

        # Run all tasks
        tasks = [process_one(item) for item in sorted_queue]
        await asyncio.gather(*tasks, return_exceptions=True)

        duration = (datetime.now() - start_time).total_seconds()

        # Clear queue
        self.queue.clear()

        return BatchResults(
            total_items=total,
            processed=processed,
            failed=failed,
            tokens_used=tokens,
            cost_cents=self._calculate_cost(tokens),
            duration_seconds=duration,
            errors=errors,
        )

    async def run_constraint_debates(self, lps: list[dict]):
        """Run constraint interpretation debates for LPs."""
        from src.agents.core.graphs import constraint_debate_graph

        for lp in lps:
            try:
                result = await constraint_debate_graph.ainvoke({
                    "lp_org_id": lp["id"],
                    "lp_name": lp["name"],
                    "mandate_text": lp.get("mandate_description", ""),
                    "lp_type": lp.get("lp_type", ""),
                    "current_strategies": lp.get("strategies", []),
                    "historical_commitments": [],  # Load from investments
                })

                # Save interpreted constraints
                await supabase.table("lp_interpreted_constraints").upsert({
                    "lp_org_id": lp["id"],
                    "source_text": lp.get("mandate_description", ""),
                    "hard_include": result.get("hard_include", {}),
                    "hard_exclude": result.get("hard_exclude", {}),
                    "soft_preferences": result.get("soft_preferences", {}),
                    "llm_reasoning": result.get("reasoning", ""),
                    "confidence": result.get("confidence", 0),
                }).execute()

            except Exception as e:
                print(f"Error processing LP {lp['id']}: {e}")

    async def pre_generate_pitches(self, job_id: str, top_n: int = 10):
        """Pre-generate pitches for top matches per fund."""
        from src.agents.core.graphs import pitch_debate_graph

        # Get top matches per fund
        funds = await self._get_active_funds()

        for fund in funds:
            # Get top N matches for this fund
            top_matches = await supabase.table("entity_cache").select(
                "entity_id, cache_value"
            ).eq(
                "entity_type", "match"
            ).like(
                "entity_id", f"{fund['id']}:%"
            ).eq(
                "cache_key", "debate_result"
            ).order(
                "cache_value->final_score", desc=True
            ).limit(top_n).execute()

            for match in top_matches.data:
                # Extract LP ID from entity_id (format: fund_id:lp_id)
                lp_id = match["entity_id"].split(":")[1]

                try:
                    # Generate pitch
                    result = await pitch_debate_graph.ainvoke({
                        "fund_id": fund["id"],
                        "lp_org_id": lp_id,
                        "fund_data": fund,
                        "lp_data": await self._get_lp(lp_id),
                        "match_data": match["cache_value"],
                    })

                    # Cache pitch
                    await supabase.table("entity_cache").upsert({
                        "entity_type": "pitch",
                        "entity_id": f"{fund['id']}:{lp_id}",
                        "cache_key": "generated_pitch",
                        "cache_value": result,
                    }).execute()

                except Exception as e:
                    print(f"Error generating pitch for {fund['id']}:{lp_id}: {e}")

    async def _update_progress(self, job_id: str, processed: int, total: int):
        """Update job progress in database."""
        await supabase.table("batch_jobs").update({
            "processed_items": processed,
        }).eq("id", job_id).execute()

    def _calculate_cost(self, tokens: int) -> int:
        """Calculate cost in cents."""
        # Claude Sonnet pricing (approximate)
        cost_per_1k = 0.003
        return int((tokens / 1000) * cost_per_1k * 100)


class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, rate_per_minute: int):
        self.rate = rate_per_minute
        self.tokens = rate_per_minute
        self.last_refill = datetime.now()
        self.lock = asyncio.Lock()

    async def acquire(self):
        """Wait until a token is available."""
        async with self.lock:
            now = datetime.now()
            elapsed = (now - self.last_refill).total_seconds()

            # Refill tokens
            self.tokens = min(
                self.rate,
                self.tokens + (elapsed * self.rate / 60)
            )
            self.last_refill = now

            if self.tokens < 1:
                # Wait for token
                wait_time = (1 - self.tokens) * 60 / self.rate
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= 1
```

---

## Cache Management

```python
# src/agents/batch/cache.py

from datetime import datetime, timedelta
from typing import Optional

from src.db import supabase


class EntityCache:
    """
    Manages cached debate results.

    Cache Lifetime:
    - Match results: Valid until entity changes (months)
    - Pitches: Valid until match or entity changes
    - Constraints: Valid until mandate changes

    Invalidation Triggers:
    - Fund updated → Invalidate all fund's matches and pitches
    - LP updated → Invalidate all LP's matches and pitches
    - LP mandate changed → Re-run constraint interpretation + invalidate matches
    """

    @staticmethod
    async def get_match_result(fund_id: str, lp_id: str) -> Optional[dict]:
        """Get cached match result if valid."""
        cache = await supabase.table("entity_cache").select("*").eq(
            "entity_type", "match"
        ).eq(
            "entity_id", f"{fund_id}:{lp_id}"
        ).eq(
            "cache_key", "debate_result"
        ).is_("invalidated_at", "null").single().execute()

        if not cache.data:
            return None

        entry = cache.data

        # Check validity
        if entry.get("valid_until"):
            if datetime.fromisoformat(entry["valid_until"]) < datetime.now():
                return None

        return entry["cache_value"]

    @staticmethod
    async def set_match_result(
        fund_id: str,
        lp_id: str,
        result: dict,
        debate_id: str,
        valid_for_days: int = 90,
    ):
        """Cache a match result."""
        await supabase.table("entity_cache").upsert({
            "entity_type": "match",
            "entity_id": f"{fund_id}:{lp_id}",
            "cache_key": "debate_result",
            "cache_value": result,
            "source_debate_id": debate_id,
            "valid_from": datetime.now().isoformat(),
            "valid_until": (datetime.now() + timedelta(days=valid_for_days)).isoformat(),
        }).execute()

    @staticmethod
    async def invalidate_fund(fund_id: str, reason: str = "fund_updated"):
        """Invalidate all cached results for a fund."""
        # Invalidate matches
        await supabase.table("entity_cache").update({
            "invalidated_at": datetime.now().isoformat(),
            "invalidation_reason": reason,
        }).eq(
            "entity_type", "match"
        ).like(
            "entity_id", f"{fund_id}:%"
        ).execute()

        # Invalidate pitches
        await supabase.table("entity_cache").update({
            "invalidated_at": datetime.now().isoformat(),
            "invalidation_reason": reason,
        }).eq(
            "entity_type", "pitch"
        ).like(
            "entity_id", f"{fund_id}:%"
        ).execute()

    @staticmethod
    async def invalidate_lp(lp_id: str, reason: str = "lp_updated"):
        """Invalidate all cached results for an LP."""
        # Invalidate matches
        await supabase.table("entity_cache").update({
            "invalidated_at": datetime.now().isoformat(),
            "invalidation_reason": reason,
        }).eq(
            "entity_type", "match"
        ).like(
            "entity_id", f"%:{lp_id}"
        ).execute()

        # Invalidate pitches
        await supabase.table("entity_cache").update({
            "invalidated_at": datetime.now().isoformat(),
            "invalidation_reason": reason,
        }).eq(
            "entity_type", "pitch"
        ).like(
            "entity_id", f"%:{lp_id}"
        ).execute()

        # Invalidate constraints
        await supabase.table("entity_cache").update({
            "invalidated_at": datetime.now().isoformat(),
            "invalidation_reason": reason,
        }).eq(
            "entity_type", "lp"
        ).eq(
            "entity_id", lp_id
        ).execute()

    @staticmethod
    async def get_cache_stats() -> dict:
        """Get cache statistics."""
        # Total cached items
        total = await supabase.table("entity_cache").select(
            "id", count="exact"
        ).is_("invalidated_at", "null").execute()

        # By type
        matches = await supabase.table("entity_cache").select(
            "id", count="exact"
        ).eq("entity_type", "match").is_("invalidated_at", "null").execute()

        pitches = await supabase.table("entity_cache").select(
            "id", count="exact"
        ).eq("entity_type", "pitch").is_("invalidated_at", "null").execute()

        return {
            "total_cached": total.count,
            "matches_cached": matches.count,
            "pitches_cached": pitches.count,
        }
```

---

## API Integration

### Webhook for Entity Updates

```python
# src/routes/webhooks.py

from fastapi import APIRouter, BackgroundTasks

from src.agents.batch.scheduler import BatchScheduler
from src.agents.batch.cache import EntityCache

router = APIRouter()


@router.post("/webhooks/fund-updated/{fund_id}")
async def fund_updated(fund_id: str, background_tasks: BackgroundTasks):
    """
    Called when a fund is created or updated.

    Triggers:
    1. Immediate cache invalidation
    2. Background job to recompute affected matches
    """
    # Immediate invalidation
    await EntityCache.invalidate_fund(fund_id, reason="fund_updated")

    # Queue background recomputation
    scheduler = BatchScheduler()
    background_tasks.add_task(
        scheduler.run_entity_specific,
        entity_type="fund",
        entity_id=fund_id,
    )

    return {"status": "queued", "fund_id": fund_id}


@router.post("/webhooks/lp-updated/{lp_id}")
async def lp_updated(lp_id: str, background_tasks: BackgroundTasks):
    """Called when an LP is created or updated."""
    await EntityCache.invalidate_lp(lp_id, reason="lp_updated")

    scheduler = BatchScheduler()
    background_tasks.add_task(
        scheduler.run_entity_specific,
        entity_type="lp",
        entity_id=lp_id,
    )

    return {"status": "queued", "lp_id": lp_id}


@router.post("/webhooks/lp-mandate-changed/{lp_id}")
async def lp_mandate_changed(lp_id: str, background_tasks: BackgroundTasks):
    """Called when an LP's mandate is changed."""
    await EntityCache.invalidate_lp(lp_id, reason="mandate_changed")

    scheduler = BatchScheduler()
    background_tasks.add_task(
        scheduler.run_entity_specific,
        entity_type="lp",
        entity_id=lp_id,
    )

    return {"status": "queued", "lp_id": lp_id}
```

### Match Results Endpoint

```python
# src/routes/matches.py

from fastapi import APIRouter, HTTPException

from src.agents.batch.cache import EntityCache

router = APIRouter()


@router.get("/matches/{fund_id}/{lp_id}")
async def get_match(fund_id: str, lp_id: str):
    """
    Get match result (from cache or indicate pending).

    Returns cached result if available.
    If not cached, returns status indicating computation is pending.
    """
    # Try cache first
    cached = await EntityCache.get_match_result(fund_id, lp_id)

    if cached:
        return {
            "status": "ready",
            "match": cached,
            "from_cache": True,
        }

    # Check if debate is in progress
    pending = await _check_pending_debate(fund_id, lp_id)

    if pending:
        return {
            "status": "computing",
            "message": "Match analysis in progress",
            "estimated_ready": pending.get("estimated_completion"),
        }

    return {
        "status": "pending",
        "message": "Match will be computed in next batch run",
    }
```

---

## Monitoring

### Batch Job Dashboard

```python
# src/agents/batch/monitoring.py

from datetime import datetime, timedelta

from src.db import supabase


async def get_batch_metrics(days: int = 7) -> dict:
    """Get batch processing metrics for dashboard."""
    cutoff = datetime.now() - timedelta(days=days)

    # Recent jobs
    jobs = await supabase.table("batch_jobs").select("*").gte(
        "created_at", cutoff.isoformat()
    ).order("created_at", desc=True).execute()

    # Aggregate metrics
    total_jobs = len(jobs.data)
    completed = sum(1 for j in jobs.data if j["status"] == "completed")
    failed = sum(1 for j in jobs.data if j["status"] == "failed")

    total_items = sum(j.get("total_items", 0) for j in jobs.data)
    processed_items = sum(j.get("processed_items", 0) for j in jobs.data)
    failed_items = sum(j.get("failed_items", 0) for j in jobs.data)

    total_tokens = sum(j.get("tokens_used", 0) for j in jobs.data)
    total_cost = sum(j.get("cost_cents", 0) for j in jobs.data)

    return {
        "period_days": days,
        "jobs": {
            "total": total_jobs,
            "completed": completed,
            "failed": failed,
            "success_rate": completed / total_jobs if total_jobs > 0 else 0,
        },
        "items": {
            "total": total_items,
            "processed": processed_items,
            "failed": failed_items,
            "success_rate": processed_items / total_items if total_items > 0 else 0,
        },
        "cost": {
            "total_tokens": total_tokens,
            "total_cost_cents": total_cost,
            "avg_cost_per_debate": total_cost / processed_items if processed_items > 0 else 0,
        },
        "recent_jobs": jobs.data[:10],
    }


async def get_cache_health() -> dict:
    """Get cache health metrics."""
    stats = await EntityCache.get_cache_stats()

    # Check for stale cache entries
    stale_cutoff = datetime.now() - timedelta(days=30)
    stale = await supabase.table("entity_cache").select(
        "id", count="exact"
    ).lt("valid_from", stale_cutoff.isoformat()).is_("invalidated_at", "null").execute()

    return {
        **stats,
        "stale_entries": stale.count,
        "health": "good" if stale.count < 100 else "degraded",
    }
```

---

## Error Handling

### Retry Strategy

```python
# src/agents/batch/retry.py

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
import httpx


# Retry configuration for API calls
RETRY_CONFIG = {
    "stop": stop_after_attempt(3),
    "wait": wait_exponential(multiplier=1, min=2, max=30),
    "retry": retry_if_exception_type((
        httpx.TimeoutException,
        httpx.HTTPStatusError,
    )),
}


# Failed debates are queued for next batch
async def handle_debate_failure(
    fund_id: str,
    lp_id: str,
    error: Exception,
    job_id: str,
):
    """Handle a failed debate - queue for retry."""
    await supabase.table("batch_job_errors").insert({
        "job_id": job_id,
        "fund_id": fund_id,
        "lp_id": lp_id,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "retry_count": 0,
        "next_retry": datetime.now() + timedelta(hours=4),
    }).execute()
```

---

## Summary

The batch processing system ensures:

1. **Efficiency**: Only recompute what changed
2. **Reliability**: Rate limiting, retries, error handling
3. **Speed**: Results served instantly from cache
4. **Freshness**: Automatic invalidation when entities change
5. **Visibility**: Full metrics and monitoring

Users see instant results; the heavy computation happens in the background.
