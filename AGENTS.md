# Guía para Agentes - Consulta RUC SUNAT

Este repositorio contiene la solución modular para consulta masiva, validación, reanudación y consolidación de RUCs de SUNAT (Perú).

## Reglas Clave de Desarrollo

1. **Inmutabilidad de Domicilio Fiscal Original**:
   `Domicilio Fiscal Original` NUNCA debe ser alterado ni recortado.
2. **Motor Principal**:
   Usar Padrón Reducido SUNAT / Datos Abiertos oficial indexado localmente en SQLite.
3. **MOCK Isolation**:
   Las ejecuciones con fuentes MOCK deben tener claves compuestas (`ruc`, `fuente`, `dataset_ver`) para evitar contaminar la base de datos de producción real.
4. **Preservación de Trazabilidad**:
   Celdas vacías y RUCs inválidos se registran con trazabilidad completa (archivo, hoja, fila origen).
