"""Run independent AI analysis jobs concurrently."""

from concurrent.futures import ThreadPoolExecutor, as_completed


def run_parallel_ai_jobs(jobs, analyze, on_result, max_workers=5):
    """Run AI jobs in worker threads and deliver results on the caller thread."""
    if not jobs:
        return

    worker_count = min(max_workers, len(jobs))
    with ThreadPoolExecutor(
        max_workers=worker_count,
        thread_name_prefix="deepseek-analysis",
    ) as executor:
        future_to_job = {
            executor.submit(analyze, job): job
            for job in jobs
        }
        for future in as_completed(future_to_job):
            job = future_to_job[future]
            try:
                result = future.result()
            except Exception as exc:
                result = ("error", f"AI 分析失败：{str(exc)[:200]}")
            on_result(job, result)
