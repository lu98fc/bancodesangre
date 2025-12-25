"""
Módulo de compatibilidades de sangre.
Implementa búsqueda recursiva de tipos compatibles cuando el tipo solicitado no está disponible.
"""

import mysql.connector
from typing import List, Tuple, Optional

# Tabla de compatibilidades estándar:
# Un paciente con tipo X puede recibir sangre de los tipos listados
# Por orden de preferencia (el primero es el mejor)
COMPATIBILIDADES_ESTANDAR = {
    "O+": ["O+", "O-"],
    "O-": ["O-"],
    "A+": ["A+", "A-", "O+", "O-"],
    "A-": ["A-", "O-"],
    "B+": ["B+", "B-", "O+", "O-"],
    "B-": ["B-", "O-"],
    "AB+": ["AB+", "AB-", "A+", "A-", "B+", "B-", "O+", "O-"],
    "AB-": ["AB-", "A-", "B-", "O-"],
}


class GestorCompatibilidadSangre:
    """Gestiona la búsqueda y asignación de sangre compatible."""

    def __init__(self, conn):
        """
        Inicializa el gestor con una conexión a BD.
        
        Args:
            conn: Conexión mysql.connector a la BD
        """
        self.conn = conn
        self.compatibilidades = self._cargar_compatibilidades()

    def _cargar_compatibilidades(self) -> dict:
        """
        Carga las compatibilidades desde la BD si existen.
        Si no, usa las compatibilidades estándar.
        
        Returns:
            Dict con tipo_sangre -> lista de tipos compatibles ordenados
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute('''
                    SELECT ts1.TipodeSangre, ts2.TipodeSangre 
                    FROM compatibilidad c
                    JOIN tipodesangre ts1 ON c.id_TipodeSangreReceptor = ts1.id
                    JOIN tipodesangre ts2 ON c.id_TipodeSangreDonable = ts2.id
                    ORDER BY c.preferencia ASC
                ''')
                resultados = cursor.fetchall()
                
                # Reorganizar en dict
                compat = {}
                for receptor, donable in resultados:
                    if receptor not in compat:
                        compat[receptor] = []
                    compat[receptor].append(donable)
                
                return compat if compat else COMPATIBILIDADES_ESTANDAR
        except Exception:
            # Si hay error, usar estándares
            return COMPATIBILIDADES_ESTANDAR

    def obtener_compatibles(self, tipo_sangre: str) -> List[str]:
        """
        Obtiene la lista de tipos de sangre compatibles (incluyendo el mismo tipo).
        
        Args:
            tipo_sangre: Tipo de sangre solicitado (ej: "O+")
            
        Returns:
            Lista de tipos compatibles en orden de preferencia
        """
        return self.compatibilidades.get(tipo_sangre, [tipo_sangre])

    def buscar_sangre_disponible_recursivo(
        self,
        tipo_sangre_solicitado: str,
        volumen_requerido: float,
        visitados: Optional[set] = None
    ) -> Tuple[Optional[str], float]:
        """
        Busca sangre disponible de forma recursiva, considerando compatibilidades.
        
        Algoritmo:
        1. Si el tipo solicitado está disponible con volumen suficiente, devolverlo.
        2. Si no, probar los tipos compatibles en orden de preferencia.
        3. Si alguno tiene volumen parcial, devolverlo y restar lo que falta.
        4. Si ninguno tiene suficiente individual, combinar múltiples fuentes.
        
        Args:
            tipo_sangre_solicitado: Tipo solicitado (ej: "O+")
            volumen_requerido: Volumen necesario en unidades
            visitados: Set de tipos ya visitados (para evitar ciclos)
            
        Returns:
            Tupla (tipo_sangre_usado, volumen_obtenido)
            Si no hay disponible, retorna (None, 0)
        """
        if visitados is None:
            visitados = set()

        # Evitar ciclos infinitos
        if tipo_sangre_solicitado in visitados:
            return (None, 0)
        visitados.add(tipo_sangre_solicitado)

        try:
            with self.conn.cursor() as cursor:
                # Obtener stock disponible del tipo solicitado
                cursor.execute('''
                    SELECT SUM(VolumenDisp) FROM reserva 
                    WHERE TipodeSangre = %s
                ''', (tipo_sangre_solicitado,))
                resultado = cursor.fetchone()
                volumen_disponible = float(resultado[0]) if resultado[0] else 0.0

                # Si hay suficiente volumen, usar este tipo
                if volumen_disponible >= volumen_requerido:
                    return (tipo_sangre_solicitado, volumen_requerido)

                # Si hay volumen parcial, guardarlo y buscar lo que falta
                if volumen_disponible > 0:
                    volumen_faltante = volumen_requerido - volumen_disponible
                    
                    # Intentar encontrar los tipos compatibles
                    compatibles = self.obtener_compatibles(tipo_sangre_solicitado)
                    
                    for tipo_compatible in compatibles:
                        if tipo_compatible == tipo_sangre_solicitado:
                            continue  # Ya lo intentamos
                        
                        tipo_encontrado, vol_encontrado = self.buscar_sangre_disponible_recursivo(
                            tipo_compatible, volumen_faltante, visitados.copy()
                        )
                        
                        if vol_encontrado > 0:
                            # Devolvemos el tipo original pero con volumen combinado
                            return (tipo_sangre_solicitado, volumen_disponible + vol_encontrado)
                    
                    # Si no encontramos complemento, devolver lo que hay
                    return (tipo_sangre_solicitado, volumen_disponible)

                # No hay volumen en el tipo solicitado, buscar en compatibles
                compatibles = self.obtener_compatibles(tipo_sangre_solicitado)
                
                for tipo_compatible in compatibles:
                    if tipo_compatible == tipo_sangre_solicitado:
                        continue
                    
                    tipo_encontrado, vol_encontrado = self.buscar_sangre_disponible_recursivo(
                        tipo_compatible, volumen_requerido, visitados.copy()
                    )
                    
                    if vol_encontrado >= volumen_requerido:
                        return (tipo_compatible, vol_encontrado)

                # No hay sangre compatible disponible
                return (None, 0)

        except mysql.connector.Error as e:
            print(f"Error en búsqueda recursiva: {e}")
            return (None, 0)

    def obtener_recomendacion(self, tipo_sangre: str) -> str:
        """
        Genera un mensaje amigable con las recomendaciones de tipos compatibles.
        
        Args:
            tipo_sangre: Tipo de sangre del paciente (ej: "O+")
            
        Returns:
            String con la recomendación
        """
        compatibles = self.obtener_compatibles(tipo_sangre)
        if not compatibles:
            return f"No hay información de compatibilidad para {tipo_sangre}"
        
        return f"Tipos aceptados para {tipo_sangre}: {', '.join(compatibles)}"

    def descontar_stock_con_compatibilidad(
        self,
        tipo_sangre_solicitado: str,
        volumen_requerido: float
    ) -> Tuple[bool, str]:
        """
        Descuenta del stock considerando compatibilidades.
        Usa búsqueda recursiva para encontrar la mejor fuente.
        
        Args:
            tipo_sangre_solicitado: Tipo solicitado
            volumen_requerido: Volumen a descontar
            
        Returns:
            Tupla (éxito, mensaje)
        """
        try:
            # Buscaremos y descontaremos reservas por orden de vencimiento,
            # probando tipos compatibles en orden de preferencia.
            compatibles = self.obtener_compatibles(tipo_sangre_solicitado)
            volumen_faltante = float(volumen_requerido)

            try:
                with self.conn.cursor() as cursor:
                    # Desactivar chequeo de claves foráneas mientras modificamos reservas
                    cursor.execute("SET FOREIGN_KEY_CHECKS=0")

                    for tipo in compatibles:
                        if volumen_faltante <= 0:
                            break

                        # Obtener reservas ordenadas por vencimiento (FIFO por antigüedad de vencimiento)
                        cursor.execute('''
                            SELECT ID, VolumenDisp FROM reserva
                            WHERE TipodeSangre = %s
                            ORDER BY Vencimiento ASC
                        ''', (tipo,))
                        filas = cursor.fetchall()

                        for fila in filas:
                            if volumen_faltante <= 0:
                                break
                            id_res = fila[0]
                            vol_disp = float(fila[1]) if fila[1] is not None else 0.0

                            if vol_disp <= 0:
                                continue

                            if vol_disp <= volumen_faltante + 1e-6:
                                # Consumir toda la reserva
                                cursor.execute('DELETE FROM reserva WHERE ID = %s', (id_res,))
                                volumen_faltante -= vol_disp
                            else:
                                # Reducir el VolumenDisp de la reserva
                                nuevo_vol = vol_disp - volumen_faltante
                                cursor.execute('UPDATE reserva SET VolumenDisp = %s WHERE ID = %s', (nuevo_vol, id_res))
                                volumen_faltante = 0
                                break

                    # Reactivar FK checks
                    cursor.execute("SET FOREIGN_KEY_CHECKS=1")
                    self.conn.commit()

                if volumen_faltante > 0:
                    return (False, f"Stock insuficiente. Faltan {volumen_faltante:.2f} ml para cubrir {volumen_requerido} ml.")

                msg = f"Stock descontado correctamente para {tipo_sangre_solicitado}: {volumen_requerido} ml"
                return (True, msg)

            except mysql.connector.Error as e:
                return (False, f"Error al descontar stock: {str(e)}")

        except mysql.connector.Error as e:
            return (False, f"Error al descontar stock: {str(e)}")
