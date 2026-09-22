import time
import logging
import datetime
from typing import List, Dict, Any, Callable, Optional
from config import BATCH_SIZE, MAX_RETRIES, INITIAL_BACKOFF, PAUSE_BETWEEN_BATCHES, LOG_FILE
from src.checkpoint.manager import CheckpointManager
from src.sources.sunat_sources import BaseRUCSource, PadronReducidoSource

logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

class BatchProcessor:
    """
    High-performance batch processor supporting local indexed padrón searches (50,000+ RUCs in seconds).
    """
    def __init__(self,
                 source: Optional[BaseRUCSource] = None,
                 checkpoint_mgr: Optional[CheckpointManager] = None,
                 batch_size: int = BATCH_SIZE,
                 pause_between_batches: float = PAUSE_BETWEEN_BATCHES):
        self.source = source or PadronReducidoSource()
        self.checkpoint_mgr = checkpoint_mgr or CheckpointManager()
        self.batch_size = batch_size
        self.pause_between_batches = pause_between_batches

    def process_rucs(self,
                     ruc_list: List[str],
                     progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
                     stop_checker: Optional[Callable[[], bool]] = None) -> List[Dict[str, Any]]:

        source_name = self.source.source_name
        dataset_ver = self.source.dataset_version

        # Get already processed RUCs specific to this (fuente + dataset_ver)
        processed_map = self.checkpoint_mgr.get_processed_rucs(source_name, dataset_ver)
        pending_rucs = [r for r in ruc_list if r not in processed_map]

        logging.info(f"Iniciando procesador | Fuente: {source_name} ({dataset_ver}) | Total: {len(ruc_list)} | Pendientes: {len(pending_rucs)}")

        if progress_callback:
            stats = self.checkpoint_mgr.get_summary_stats(ruc_list, source_name, dataset_ver)
            progress_callback(stats)

        # Process pending RUCs in chunks
        for i in range(0, len(pending_rucs), self.batch_size):
            if stop_checker and stop_checker():
                logging.info("Proceso detenido por el usuario.")
                break

            batch = pending_rucs[i:i + self.batch_size]
            batch_results = self.source.fetch_bulk_rucs(batch)

            for rec in batch_results:
                self.checkpoint_mgr.save_record(rec)

            if progress_callback:
                stats = self.checkpoint_mgr.get_summary_stats(ruc_list, source_name, dataset_ver)
                progress_callback(stats)

            if self.pause_between_batches > 0:
                time.sleep(self.pause_between_batches)

        # Retrieve full merged records from checkpoint DB
        all_records = []
        with self.checkpoint_mgr._get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ",".join("?" for _ in ruc_list)
            if placeholders:
                cursor.execute(
                    f"SELECT * FROM ruc_consultas WHERE ruc IN ({placeholders}) AND fuente = ? AND dataset_ver = ?",
                    ruc_list + [source_name, dataset_ver]
                )
                all_records = [dict(row) for row in cursor.fetchall()]

        return all_records
