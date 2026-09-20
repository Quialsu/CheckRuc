import re
from typing import Tuple, List, Dict, Any, Set

VALID_PREFIXES = {'10', '15', '17', '20'}
WEIGHTS = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]

def validate_ruc_checksum(ruc: str) -> bool:
    """
    Validates Peruvian RUC using the Modulo 11 check digit algorithm.
    """
    if not isinstance(ruc, str) or len(ruc) != 11 or not ruc.isdigit():
        return False

    digits = [int(c) for c in ruc]
    checksum = sum(digits[i] * WEIGHTS[i] for i in range(10))
    remainder = checksum % 11
    check_digit = 11 - remainder

    if check_digit == 10:
        check_digit = 0
    elif check_digit == 11:
        check_digit = 1

    return check_digit == digits[10]


def validate_ruc(raw_val: Any) -> Tuple[bool, str, str]:
    """
    Validates a raw RUC input value.
    Returns a tuple: (is_valid, clean_ruc, error_reason)
    """
    if raw_val is None:
        return False, "", "Valor nulo o vacío"

    # Convert float / int to string safely without scientific notation
    if isinstance(raw_val, float):
        if raw_val.is_integer():
            val_str = str(int(raw_val))
        else:
            val_str = f"{raw_val:.0f}"
        if len(val_str) < 11 and val_str.isdigit():
            val_str = val_str.zfill(11)
    elif isinstance(raw_val, int):
        val_str = str(raw_val)
        if len(val_str) < 11 and val_str.isdigit():
            val_str = val_str.zfill(11)
    else:
        val_str = str(raw_val).strip()

    if not val_str:
        return False, "", "Valor vacío"

    if not val_str.isdigit():
        return False, val_str, f"Contiene caracteres no numéricos: '{val_str}'"

    if len(val_str) != 11:
        return False, val_str, f"Longitud incorrecta ({len(val_str)} dígitos en lugar de 11)"

    prefix = val_str[:2]
    if prefix not in VALID_PREFIXES:
        return False, val_str, f"Prefijo de RUC no válido ('{prefix}'). Debe iniciar con 10, 15, 17 o 20"

    if not validate_ruc_checksum(val_str):
        return False, val_str, "Dígito verificador inválido (Módulo 11)"

    return True, val_str, ""


def process_ruc_list(ruc_list: List[Any]) -> Dict[str, Any]:
    """
    Processes a list of raw RUCs:
    - Validates each
    - Deduplicates valid ones (preserving order)
    - Records duplicates and invalid ones with technical reasons
    """
    valid_rucs = []
    seen_valid: Set[str] = set()
    invalid_records = []
    duplicate_records = []

    for idx, raw in enumerate(ruc_list):
        is_valid, clean_ruc, error_msg = validate_ruc(raw)
        row_num = idx + 1

        if is_valid:
            if clean_ruc in seen_valid:
                duplicate_records.append({
                    "fila": row_num,
                    "ruc_original": str(raw),
                    "ruc_limpio": clean_ruc,
                    "motivo": "RUC duplicado en la lista de entrada"
                })
            else:
                seen_valid.add(clean_ruc)
                valid_rucs.append(clean_ruc)
        else:
            invalid_records.append({
                "fila": row_num,
                "ruc_original": str(raw),
                "ruc_limpio": clean_ruc,
                "motivo": error_msg
            })

    return {
        "valid_rucs": valid_rucs,
        "unique_count": len(valid_rucs),
        "invalid_records": invalid_records,
        "duplicate_records": duplicate_records,
        "total_input": len(ruc_list)
    }
