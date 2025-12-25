"""
Script de prueba para el sistema de compatibilidades de sangre.
Demuestra cómo funciona la búsqueda recursiva.
"""

from compatibilidad_sangre import GestorCompatibilidadSangre, COMPATIBILIDADES_ESTANDAR

# Simulación sin BD (solo para ver las compatibilidades)
print("=" * 60)
print("SISTEMA DE COMPATIBILIDADES DE SANGRE")
print("=" * 60)

print("\n📋 Tabla de Compatibilidades Estándar:")
print("-" * 60)
for tipo_receptor, tipos_donables in COMPATIBILIDADES_ESTANDAR.items():
    print(f"{tipo_receptor:8} puede recibir de: {', '.join(tipos_donables)}")

print("\n" + "=" * 60)
print("EJEMPLOS DE BÚSQUEDA RECURSIVA:")
print("=" * 60)

# Escenarios de ejemplo (sin acceder a BD)
escenarios = [
    {
        "solicitud": "O+",
        "volumen": 500,
        "disponible": {
            "O+": 0,
            "O-": 600,
        },
        "esperado": "O- (compatible universal)",
    },
    {
        "solicitud": "AB+",
        "volumen": 400,
        "disponible": {
            "AB+": 200,
            "A+": 300,
        },
        "esperado": "AB+ (200) + A+ (200 del 300 disponible)",
    },
    {
        "solicitud": "A-",
        "volumen": 500,
        "disponible": {
            "A-": 0,
            "O-": 700,
        },
        "esperado": "O- (compatible)",
    },
]

for i, escenario in enumerate(escenarios, 1):
    print(f"\n🔍 Escenario {i}:")
    print(f"   Solicitud: {escenario['solicitud']} ({escenario['volumen']} ml)")
    print(f"   Stock disponible: {escenario['disponible']}")
    print(f"   Resultado esperado: {escenario['esperado']}")
    
    # Mostrar compatibles para este tipo
    compatibles = COMPATIBILIDADES_ESTANDAR.get(escenario['solicitud'], [])
    print(f"   Orden de búsqueda: {' → '.join(compatibles)}")

print("\n" + "=" * 60)
print("FLUJO DE INTEGRACIÓN EN LA APLICACIÓN:")
print("=" * 60)
print("""
1. Usuario solicita transfusión (ej: AB+, 500 ml)
2. Sistema llama a gestor_compat.descontar_stock_con_compatibilidad("AB+", 500)
3. Gestor ejecuta búsqueda recursiva:
   - Verifica si hay AB+ en stock
   - Si no hay suficiente, busca en compatibles: AB-, A+, A-, B+, B-, O+, O-
   - Usa el primero encontrado (FIFO - el más antiguo se descarta primero)
   - Si es necesario, combina múltiples fuentes
4. Si encuentra suficiente stock, descuenta de BD y devuelve mensaje
5. Si no hay, devuelve error y no procesa la solicitud
""")

print("\n✅ Sistema listo para ser usado en la aplicación.")
print("Para ver el sistema en acción, ejecuta la aplicación y:")
print("  1. Ve a 'Solicitudes de Transfusión'")
print("  2. Agrega una solicitud")
print("  3. Cuando la aceptes, verás si busca tipos compatibles automáticamente")
