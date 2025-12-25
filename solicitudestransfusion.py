import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import mysql.connector
from compatibilidad_sangre import GestorCompatibilidadSangre


class VerSolicitud:
    def __init__(self, parent, conn):
        self.parent = parent
        self.conn = conn
        self.stock_data = []  # Inicializar lista de datos para evitar errores
        self.gestor_compat = GestorCompatibilidadSangre(conn)  # Inicializar gestor de compatibilidades

        # Título
        tk.Label(self.parent, text="Solicitudes de Transfusión", font=("Arial", 16), bg="white").pack(pady=10)

        # Botón para agregar nueva solicitud
        tk.Button(self.parent, text="➕ Agregar Solicitud", bg="#4CAF50", fg="white", command=self.agregar_solicitud).pack(pady=5)

        # Cargar solicitudes
        self.cargar_solicitud()

        # Columnas para la tabla
        columnas = ("ID Solicitud", "Hospital", "Dirección", "Teléfono", "Volumen Solicitado", "Estado", "Tipo de Sangre")
        self.tabla_solicitudes = ttk.Treeview(self.parent, columns=columnas, show="headings", height=15)

        for col in columnas:
            self.tabla_solicitudes.heading(col, text=col)
            self.tabla_solicitudes.column(col, width=120)

        self.tabla_solicitudes.pack(pady=10)

        # Insertar los datos de las solicitudes en la tabla
        self.mostrar_solicitudes()

        # Botones
        button_frame = tk.Frame(parent, bg="white")
        button_frame.pack(pady=20)

        tk.Button(button_frame, text="Editar Solicitud", bg="#a37676", fg="white", command=self.editar_solicitud).pack(side="left", padx=10)
        tk.Button(self.parent, text="Cancelar", bg="#f8f8f8", command=self.limpiar).pack(side="top", padx=5)

    def cargar_solicitud(self):
        """Carga las solicitudes desde la base de datos y las almacena en self.stock_data."""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute('''
                    SELECT s.id, h.Nombre, h.direccion, h.telefono, s.VolumenSolic, s.Estado, ts.TipodeSangre
                    FROM hospital h
                    JOIN solicitud s ON h.id = s.id_Hospital
                    JOIN tipodesangre ts ON ts.id = s.id_TipodeSangre;
                ''')
                self.stock_data = cursor.fetchall()
        except mysql.connector.Error as e:
            messagebox.showerror("Error", f"No se pudo cargar las solicitudes: {e}")
            self.stock_data = []

    def cargar_hospitales(self):
        """Devuelve una lista de cadenas 'id - Nombre' de hospitales existentes."""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT id, Nombre FROM hospital ORDER BY Nombre ASC")
                rows = cursor.fetchall()
                return [f"{r[0]} - {r[1]}" for r in rows]
        except mysql.connector.Error:
            return []

    def cargar_tipos_sangre(self):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT TipodeSangre FROM tipodesangre ORDER BY TipodeSangre ASC")
                return [row[0] for row in cursor.fetchall()]
        except mysql.connector.Error:
            return []

    def mostrar_solicitudes(self):
        """Muestra las solicitudes en la tabla."""
        for item in self.tabla_solicitudes.get_children():
            self.tabla_solicitudes.delete(item)

        for solicitud in self.stock_data:
            self.tabla_solicitudes.insert("", "end", values=solicitud)

    def agregar_solicitud(self):
        """Abre una ventana para agregar una nueva solicitud de transfusión."""
        ventana_nueva = tk.Toplevel(self.parent)
        ventana_nueva.title("Nueva Solicitud de Transfusión")
        ventana_nueva.geometry("400x400")

        # Hospital: seleccionar existente o crear nuevo
        tk.Label(ventana_nueva, text="Hospital:", font=("Arial", 10, "bold")).pack(anchor="w", padx=10, pady=(8,2))
        hospitales = ["Nuevo hospital..."] + self.cargar_hospitales()
        hospital_var = tk.StringVar()
        combo_hospital = ttk.Combobox(ventana_nueva, values=hospitales, textvariable=hospital_var, state="readonly")
        combo_hospital.current(0)
        combo_hospital.pack(fill="x", padx=10)

        # Frame para datos de nuevo hospital (oculto por defecto)
        nuevo_frame = tk.Frame(ventana_nueva)
        tk.Label(nuevo_frame, text="Nombre del Hospital: *").pack(anchor="w", padx=2, pady=(6,0))
        entry_nuevo_nombre = tk.Entry(nuevo_frame)
        entry_nuevo_nombre.pack(fill="x", padx=2, pady=(0,6))
        tk.Label(nuevo_frame, text="Dirección:").pack(anchor="w", padx=2, pady=(0,0))
        entry_nuevo_dir = tk.Entry(nuevo_frame)
        entry_nuevo_dir.pack(fill="x", padx=2, pady=(0,6))
        tk.Label(nuevo_frame, text="Teléfono:").pack(anchor="w", padx=2, pady=(0,0))
        entry_nuevo_tel = tk.Entry(nuevo_frame)
        entry_nuevo_tel.pack(fill="x", padx=2, pady=(0,6))

        # Volumen y tipo de sangre para la solicitud
        tk.Label(ventana_nueva, text="Volumen Solicitado (ml):", font=("Arial", 10, "bold")).pack(anchor="w", padx=10, pady=(8,2))
        entry_volumen = tk.Entry(ventana_nueva)
        entry_volumen.pack(fill="x", padx=10)

        tk.Label(ventana_nueva, text="Tipo de Sangre:", font=("Arial", 10, "bold")).pack(anchor="w", padx=10, pady=(8,2))
        tipos = self.cargar_tipos_sangre()
        combo_tipo = ttk.Combobox(ventana_nueva, values=tipos, state="readonly")
        combo_tipo.pack(fill="x", padx=10)

        # Función para mostrar/ocultar el formulario de nuevo hospital
        def _on_hospital_change(event=None):
            sel = hospital_var.get()
            if sel == "Nuevo hospital...":
                nuevo_frame.pack(fill="x", padx=10, pady=(6,4))
            else:
                nuevo_frame.forget()

        combo_hospital.bind("<<ComboboxSelected>>", _on_hospital_change)

        def guardar():
            sel_hosp = hospital_var.get()
            volumen = entry_volumen.get().strip()
            tipo_sangre = combo_tipo.get().strip()

            # Validaciones básicas
            if not volumen or not tipo_sangre:
                messagebox.showerror("Error", "Volumen y Tipo de Sangre son obligatorios.")
                return
            try:
                volumen_float = float(volumen)
                if volumen_float <= 0:
                    messagebox.showerror("Error", "El volumen debe ser un número positivo.")
                    return
                if volumen_float > 25500:
                    messagebox.showerror("Error", "Volumen demasiado grande.")
                    return
            except ValueError:
                messagebox.showerror("Error", "El volumen debe ser un número válido.")
                return

            try:
                with self.conn.cursor() as cursor:
                    # Obtener id del tipo de sangre
                    cursor.execute("SELECT id FROM tipodesangre WHERE TipodeSangre = %s", (tipo_sangre,))
                    tipo_row = cursor.fetchone()
                    if not tipo_row:
                        messagebox.showerror("Error", f"Tipo de sangre '{tipo_sangre}' no encontrado.")
                        return
                    id_tipo = tipo_row[0]

                    # Si se creó un nuevo hospital, insertarlo y usar el id autogenerado
                    if sel_hosp == "Nuevo hospital...":
                        nombre = entry_nuevo_nombre.get().strip()
                        direccion = entry_nuevo_dir.get().strip() or None
                        telefono = entry_nuevo_tel.get().strip() or None

                        if not nombre:
                            messagebox.showerror("Error", "El nombre del nuevo hospital es obligatorio.")
                            return

                        cursor.execute('''
                            INSERT INTO hospital (Nombre, direccion, telefono)
                            VALUES (%s, %s, %s)
                        ''', (nombre, direccion, telefono))
                        # Obtener id autogenerado
                        nuevo_id = cursor.lastrowid
                        id_hosp = nuevo_id
                    else:
                        # Extraer id desde "id - Nombre"
                        try:
                            id_hosp = int(sel_hosp.split(" - ")[0])
                        except Exception:
                            messagebox.showerror("Error", "ID de hospital inválido.")
                            return

                    # Insertar la solicitud referenciando al hospital
                    cursor.execute('''
                        INSERT INTO solicitud (id_Hospital, VolumenSolic, id_TipodeSangre)
                        VALUES (%s, %s, %s)
                    ''', (id_hosp, volumen_float, id_tipo))
                    self.conn.commit()

                messagebox.showinfo("Éxito", f"Solicitud agregada correctamente.\n(Volumen: {volumen_float} ml)")
                ventana_nueva.destroy()
                # Refrescar datos y vista
                self.cargar_solicitud()
                self.mostrar_solicitudes()
            except mysql.connector.Error as e:
                messagebox.showerror("Error de BD", f"No se pudo agregar la solicitud.\nDetalles: {str(e)}")

        tk.Button(ventana_nueva, text="Guardar", bg="#4CAF50", fg="white", command=guardar).pack(pady=12)

    def editar_solicitud(self):
        """Permite editar una solicitud seleccionada de la tabla y, si es aceptada, descuenta la reserva."""
        seleccion = self.tabla_solicitudes.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Seleccione una solicitud para editar.")
            return

        item = seleccion[0]
        valores = self.tabla_solicitudes.item(item, "values")
        id_solicitud = valores[0]  # ID de la solicitud (ahora es el correcto)
        volumen_solicitado = valores[4]  # Volumen solicitado
        tipo_sangre = valores[6]  # Tipo de sangre

        ventana_editar = tk.Toplevel(self.parent)
        ventana_editar.title("Editar Solicitud")
        ventana_editar.geometry("400x300")

        tk.Label(ventana_editar, text="Estado:", font=("Arial", 10)).pack(anchor="w", padx=10, pady=(8,2))
        estados = ["Pendiente", "Aceptada", "Rechazada"]
        entrada_estado = ttk.Combobox(ventana_editar, values=estados, state="readonly")
        try:
            entrada_estado.set(valores[5])
        except Exception:
            entrada_estado.set("Pendiente")
        entrada_estado.pack(fill="x", padx=10)

        def guardar_cambios():
            nuevo_estado = entrada_estado.get().strip()

            try:
                with self.conn.cursor() as cursor:
                    # Actualizar el estado de la solicitud
                    cursor.execute('''
                        UPDATE solicitud SET Estado = %s WHERE ID = %s
                    ''', (nuevo_estado, id_solicitud))
                    self.conn.commit()

                    # Si el estado es "Aceptada", descontar del stock de sangre con compatibilidad
                    if nuevo_estado == "Aceptada":
                        volumen_float = float(volumen_solicitado)
                        exito, mensaje = self.gestor_compat.descontar_stock_con_compatibilidad(
                            tipo_sangre, volumen_float
                        )

                        if exito:
                            messagebox.showinfo("Éxito", f"Solicitud aceptada.\n{mensaje}")
                        else:
                            messagebox.showwarning("Advertencia", f"No se pudo descontar el stock:\n{mensaje}")
                            # Revertir el cambio de estado ya que no hay stock disponible
                            cursor.execute('''
                                UPDATE solicitud SET Estado = %s WHERE ID = %s
                            ''', ("Pendiente", id_solicitud))
                            self.conn.commit()
                            return

                ventana_editar.destroy()
                self.cargar_solicitud()
                self.mostrar_solicitudes()

            except mysql.connector.Error as e:
                messagebox.showerror("Error", f"No se pudo actualizar la solicitud: {e}")

        tk.Button(ventana_editar, text="Guardar", command=guardar_cambios, bg="#a37676", fg="white").pack(pady=10)

    def borrar_solicitud(self):
        """Permite borrar una solicitud seleccionada de la tabla."""
        seleccion = self.tabla_solicitudes.selection()
        if seleccion:
            for item in seleccion:
                valores = self.tabla_solicitudes.item(item, "values")
                id_solicitud = valores[0]

                try:
                    with self.conn.cursor() as cursor:
                        cursor.execute("SET FOREIGN_KEY_CHECKS=0")
                        cursor.execute('DELETE FROM solicitud WHERE ID = %s', (id_solicitud,))
                        cursor.execute("SET FOREIGN_KEY_CHECKS=1")
                        self.conn.commit()
                    self.tabla_solicitudes.delete(item)
                except mysql.connector.Error as e:
                    messagebox.showerror("Error", f"No se pudo borrar la solicitud: {e}")

    def limpiar(self):
        """Limpia la pantalla."""
        for widget in self.parent.winfo_children():
            widget.destroy()
