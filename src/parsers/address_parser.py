import re
from typing import Dict, Optional

UBIGEO_MAP = {
    # Ubigeos for major Peruvian capitals and districts
    "LIMA/LIMA/LIMA": "150101",
    "LIMA/LIMA/MIRAFLORES": "150122",
    "LIMA/LIMA/SAN ISIDRO": "150131",
    "LIMA/LIMA/SANTIAGO DE SURCO": "150140",
    "LIMA/LIMA/LA MOLINA": "150114",
    "LIMA/LIMA/SAN BORJA": "150130",
    "LIMA/LIMA/ATE": "150103",
    "LIMA/LIMA/LINCE": "150116",
    "LIMA/LIMA/MAGDALENA DEL MAR": "150120",
    "LIMA/LIMA/JESUS MARIA": "150113",
    "AREQUIPA/AREQUIPA/AREQUIPA": "040101",
    "LA LIBERTAD/TRUJILLO/TRUJILLO": "130101",
    "LAMBAYEQUE/CHICLAYO/CHICLAYO": "140101",
    "PIURA/PIURA/PIURA": "200101",
    "CUSCO/CUSCO/CUSCO": "080101",
    "CALLAO/CALLAO/CALLAO": "070101",
    "JUNIN/HUANCAYO/HUANCAYO": "120101",
    "ANCASH/HUARAZ/HUARAZ": "020101",
    "ICA/ICA/ICA": "110101",
    "CAJAMARCA/CAJAMARCA/CAJAMARCA": "060101"
}

PERU_DEPARTMENTS = [
    "AMAZONAS", "ANCASH", "APURIMAC", "AREQUIPA", "AYACUCHO", "CAJAMARCA",
    "CALLAO", "CUSCO", "HUANCAVELICA", "HUANUCO", "ICA", "JUNIN",
    "LA LIBERTAD", "LAMBAYEQUE", "LIMA", "LORETO", "MADRE DE DIOS",
    "MOQUEGUA", "PASCO", "PIURA", "PUNO", "SAN MARTIN", "TACNA",
    "TUMBES", "UCAYALI"
]


def parse_fiscal_address(original_address: Optional[str]) -> Dict[str, str]:
    """
    Parses a fiscal address string without ever modifying or replacing the original address.
    Returns a dictionary with:
      - Domicilio Fiscal Original (EXACT copy of input)
      - Dirección
      - Distrito
      - Provincia
      - Departamento/Región
      - Ubigeo
    """
    exact_original = str(original_address) if original_address is not None else ""

    result = {
        "Domicilio Fiscal Original": exact_original,
        "Dirección": "",
        "Distrito": "",
        "Provincia": "",
        "Departamento/Región": "",
        "Ubigeo": ""
    }

    if not exact_original.strip():
        return result

    raw = exact_original.strip()

    # SUNAT standard format ending in " - DEPARTAMENTO - PROVINCIA - DISTRITO"
    # Example: "AV. CANAVAL Y MOREYRA NRO. 150 LIMA - LIMA - SAN ISIDRO"
    parts = [p.strip() for p in raw.split(' - ') if p.strip()]

    if len(parts) >= 3:
        dist = parts[-1]
        prov = parts[-2]
        dept_and_street = " - ".join(parts[:-2])

        dept_found = ""
        street_found = dept_and_street

        # Check multi-word or single-word departments at end of string
        dept_and_street_upper = dept_and_street.upper()
        for dept_candidate in sorted(PERU_DEPARTMENTS, key=len, reverse=True):
            if dept_and_street_upper.endswith(" " + dept_candidate):
                dept_found = dept_candidate
                street_found = dept_and_street[:-len(dept_candidate)].strip()
                break
            elif dept_and_street_upper == dept_candidate:
                dept_found = dept_candidate
                street_found = dept_and_street
                break

        result["Dirección"] = street_found
        result["Departamento/Región"] = dept_found or (parts[-3] if len(parts) >= 4 else "")
        result["Provincia"] = prov
        result["Distrito"] = dist
    else:
        # Slash format e.g. "AV. PANAMA 123 (LIMA / LIMA / SAN ISIDRO)"
        slash_match = re.search(r'([A-Z\s]+)\s*/\s*([A-Z\s]+)\s*/\s*([A-Z\s]+)$', raw, re.IGNORECASE)
        if slash_match:
            dept = slash_match.group(1).strip()
            prov = slash_match.group(2).strip()
            dist = slash_match.group(3).strip()
            street = raw[:slash_match.start()].strip().rstrip('(-/')
            result["Dirección"] = street
            result["Departamento/Región"] = dept
            result["Provincia"] = prov
            result["Distrito"] = dist
        else:
            result["Dirección"] = raw

    # Deduce Ubigeo if Dept, Prov, Dist available
    if result["Departamento/Región"] and result["Provincia"] and result["Distrito"]:
        key = f"{result['Departamento/Región'].upper()}/{result['Provincia'].upper()}/{result['Distrito'].upper()}"
        if key in UBIGEO_MAP:
            result["Ubigeo"] = UBIGEO_MAP[key]

    return result
