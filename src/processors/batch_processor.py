import time
import logging
import datetime
from typing import List, Dict, Any, Callable, Optional
from config import BATCH_SIZE, MAX_RETRIES, INITIAL_BACKOFF, PAUSE_BETWEEN_BATCHES
from src.checkpoint.manager import CheckpointManager
from src.sources.sunat_sources import BaseRUCSource, MockRUCSource

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class BatchProcessor:
    """
    Orchestrates batch processing of RUC queries with exponential backoff,
    checkpoint persistence, and pause/resume capability.
    """
    def __init__(self,
                 source: Optional[BaseRUCSource] = None,
                 checkpoint_mgr: Optional[CheckpointManager] = None,
                 batch_size: int = BATCH_SIZE,
                 max_retries: int = MAX_RETRIES,
                 pause_between_batches: float = PAUSE_BETWEEN_BATCHES):
        self.source = source or MockRUCSource()
        self.checkpoint_mgr = checkpoint_mgr or CheckpointManager()
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.pause_between_batches = pause_between_batches

    def process_rucs(self,
                     ruc_list: List[str],
                     progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
                     stop_checker: Optional[Callable[[], bool]] = None) -> List[Dict[str, Any]]:
        """
        Processes a list of unique valid RUCs:
        - Checks checkpoint DB for already processed RUCs
        - Fetches pending RUCs in batches
        - Applies exponential backoff for temporary errors
        - Saves results incrementally to SQLite
        - Triggers progress_callback with real-time stats
        """
        # Load already processed RUCs
        processed_map = self.checkpoint_mgr.get_processed_rucs()

        pending_rucs = [r for r in ruc_list if r not in processed_map]
        logging.info(f"Total RUCs: {len(ruc_list)} | Ya consultados: {len(ruc_list) - len(pending_rucs)} | Pendientes: {len(pending_rucs)}")

        # Notify initial progress
        if progress_callback:
            stats = self.checkpoint_mgr.get_summary_stats(ruc_list)
            progress_callback(stats)

        # Process in batches
        for i in range(0, len(pending_rucs), self.batch_size):
            if stop_checker and stop_checker():
                logging.info("Proceso detenido por el usuario.")
                break

            batch = pending_rucs[i:i + self.batch_size]
            batch_results = []

            for ruc in batch:
                if stop_checker and stop_checker():
                    break

                rec = self._fetch_with_retry(ruc)
                self.checkpoint_mgr.save_record(rec)
                batch_results.append(rec)

            if progress_callback:
                stats = self.checkpoint_mgr.get_summary_stats(ruc_list)
                progress_callback(stats)

            if self.pause_between_batches > 0:
                time.sleep(self.pause_between_batches)

        # Return full results for all input RUCs
        all_records = []
        with self.checkpoint_mgr._get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ",".join("?" for _ in ruc_list)
            if placeholders:
                cursor.execute(f"SELECT * FROM ruc_consultas WHERE ruc IN ({placeholders})", ruc_list)
                all_records = [dict(row) for row in cursor.fetchall()]

        return all_records

    def _fetch_with_retry(self, ruc: str) -> Dict[str, Any]:
        """
        Fetches a RUC record using exponential backoff on temporary errors.
        """
        attempt = 0
        backoff = INITIAL_BACKOFF

        while attempt < self.max_retries:
            attempt += 1
            res = self.source.fetch_ruc(ruc)
            res["intentos"] = attempt

            status = res.get("estado_consulta", "")

            # If successful or permanent non-existent state, return immediately
            if status in ["CONSULTADO", "RUC NO ENCONTRADO", "REQUIERE REVISIÓN"]:
                return res

            # If temporary error and attempts remain, wait backoff
            if status == "ERROR TEMPORAL" and attempt < self.max_retries:
                logging.warning(f"Error temporal para RUC {ruc} (intento {attempt}/{self.max_retries}). Reintentando en {backoff}s...")
                time.sleep(backoff)
                backoff *= 2.0
            else:
                return res

        return res
