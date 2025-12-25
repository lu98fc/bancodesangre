import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import mysql.connector
from datetime import datetime
from compatibilidad_sangre import GestorCompatibilidadSangre


class Reserva:
    # Volumen estándar por unidad de sangre (ml). Asumimos 450 ml por unidad estándar.
    # Si querés otro valor, dime y lo cambio.
    STANDARD_UNIT_ML = 450.0
    # Estados disponibles para la tabla Reserva (según el script de la BD)
    # La tabla Reserva define: Estado ENUM('Vencida', 'No vencida') DEFAULT 'No vencida'
    ESTADOS_DISPONIBLES = ["No vencida", "Vencida"]
    # Mapeo identidad (etiqueta legible -> valor en BD)
    ESTADOS_MAP = {
        "No vencida": "No vencida",
        "Vencida": "Vencida",
    }
    # Inverso: valor en BD -> etiqueta legible para mostrar en UI (idéntico aquí)
    ESTADOS_REVERSE = {v: k for k, v in ESTADOS_MAP.items()}
    
    def __init__(self, parent, conn):
        self.parent = parent
        self.conn = conn
        self.gestor_compat = GestorCompatibilidadSangre(conn)

        # Título principal (más compacto)
        tk.Label(parent, text="Gestión de Reserva de Sangre", font=("Arial", 16, "bold"), bg="white").pack(pady=6)

        # Crear frame principal
        main_frame = tk.Frame(parent, bg="white")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)

        # ==================== SECCIÓN 1: FORMULARIO ====================
        form_frame = tk.LabelFrame(main_frame, text="Registrar Nueva Reserva", font=("Arial", 12, "bold"), 
                                   bg="#f0f0f0", fg="#333", padx=10, pady=8)
        form_frame.pack(fill=tk.X, pady=6)

        # Crear dos columnas para el formulario
        col1_frame = tk.Frame(form_frame, bg="#f0f0f0")
        col1_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        col2_frame = tk.Frame(form_frame, bg="#f0f0f0")
        col2_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        self.entries = {}

        # COLUMNA 1
        # Volumen (Requerido)
        tk.Label(col1_frame, text="Volumen Donado (ml): *", font=("Arial", 10, "bold"), 
                bg="#f0f0f0", fg="#d9534f").pack(anchor="w", pady=(5, 2))
        entry_volumen = tk.Entry(col1_frame, width=25, font=("Arial", 10))
        entry_volumen.pack(anchor="w", pady=(0, 10))
        self.entries["Volúmen donado:"] = entry_volumen

        # Fecha de donación (Requerido)
        tk.Label(col1_frame, text="Fecha de Donación (YYYY-MM-DD): *", font=("Arial", 10, "bold"),
                bg="#f0f0f0", fg="#d9534f").pack(anchor="w", pady=(5, 2))
        entry_fecha_don = tk.Entry(col1_frame, width=25, font=("Arial", 10))
        entry_fecha_don.pack(anchor="w", pady=(0, 10))
        self.entries["Fecha de donación:"] = entry_fecha_don

        # Vencimiento (Requerido)
        tk.Label(col1_frame, text="Vencimiento (YYYY-MM-DD): *", font=("Arial", 10, "bold"),
                bg="#f0f0f0", fg="#d9534f").pack(anchor="w", pady=(5, 2))
        entry_vencimiento = tk.Entry(col1_frame, width=25, font=("Arial", 10))
        entry_vencimiento.pack(anchor="w", pady=(0, 10))
        self.entries["Vencimiento:"] = entry_vencimiento

        # COLUMNA 2
        # Tipo de Sangre (Requerido)
        tk.Label(col2_frame, text="Tipo de Sangre: *", font=("Arial", 10, "bold"),
                bg="#f0f0f0", fg="#d9534f").pack(anchor="w", pady=(5, 2))
        tipos_sangre = self.cargar_tipos_sangre()
        entry_tipo = ttk.Combobox(col2_frame, values=tipos_sangre, state="readonly", width=22, font=("Arial", 10))
        entry_tipo.pack(anchor="w", pady=(0, 10))
        self.entries["Tipo de Sangre:"] = entry_tipo

        # Estado (Requerido)
        tk.Label(col2_frame, text="Estado: *", font=("Arial", 10, "bold"),
                bg="#f0f0f0", fg="#d9534f").pack(anchor="w", pady=(5, 2))
        entry_estado = ttk.Combobox(col2_frame, values=self.ESTADOS_DISPONIBLES, state="readonly", 
                                    width=22, font=("Arial", 10))
        entry_estado.set("No vencida")  # Estado por defecto acorde a la BD
        entry_estado.pack(anchor="w", pady=(0, 10))
        self.entries["Estado:"] = entry_estado

        # Info sobre compatibilidades
        info_frame = tk.Frame(form_frame, bg="#e8f4f8", bd=1, relief="solid")
        info_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(info_frame, text="💡 Información de Compatibilidades:", 
                font=("Arial", 10, "bold"), bg="#e8f4f8", fg="#003d6b").pack(anchor="w", padx=5, pady=(3, 0))
        
        self.info_label = tk.Label(info_frame, text="Selecciona un tipo de sangre para ver su compatibilidad",
                                  font=("Arial", 9), bg="#e8f4f8", fg="#004080", 
                                  wraplength=600, justify="left")
        self.info_label.pack(anchor="w", padx=5, pady=5)
        
        # Vincular cambios en el campo de tipo de sangre
        entry_tipo.bind("<<ComboboxSelected>>", self._actualizar_info_compatibilidad)

        # ==================== SECCIÓN 2: CAMPOS OPCIONALES ====================
        optional_frame = tk.LabelFrame(main_frame, text="Información Adicional (Opcional)", 
                                      font=("Arial", 11, "bold"), bg="#f9f9f9", fg="#666", 
                                      padx=10, pady=8)
        optional_frame.pack(fill=tk.X, pady=6)

        # Crear dos columnas para opcionales
        opt_col1_frame = tk.Frame(optional_frame, bg="#f9f9f9")
        opt_col1_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        opt_col2_frame = tk.Frame(optional_frame, bg="#f9f9f9")
        opt_col2_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        # Id Donante (Opcional)
        tk.Label(opt_col1_frame, text="Donante:", font=("Arial", 10),
                bg="#f9f9f9", fg="#666").pack(anchor="w", pady=(5, 2))
        tk.Label(opt_col1_frame, text="(Opcional - dejar en blanco si no aplica)", 
                font=("Arial", 8, "italic"), bg="#f9f9f9", fg="#999").pack(anchor="w", pady=(0, 2))
        
        # Combobox para seleccionar donante existente
        self.donantes_data = [] # Inicializar
        combo_donante = ttk.Combobox(opt_col1_frame, values=[], state="readonly", 
                                     width=35, font=("Arial", 10))
        combo_donante.pack(anchor="w", pady=(0, 10))
        combo_donante['values'] = self.cargar_donantes_para_combo() # Cargar valores después de crear
        self.entries["Id Donante:"] = combo_donante
        
        # Vincular la selección del donante para autocompletar el tipo de sangre
        combo_donante.bind("<<ComboboxSelected>>", self._on_donante_selected)


        # Id Compatibilidad (Opcional)
        tk.Label(opt_col2_frame, text="ID Compatibilidad:", font=("Arial", 10),
                bg="#f9f9f9", fg="#666").pack(anchor="w", pady=(5, 2))
        tk.Label(opt_col2_frame, text="(Opcional - dejar en blanco si no aplica)", 
                font=("Arial", 8, "italic"), bg="#f9f9f9", fg="#999").pack(anchor="w", pady=(0, 2))
        entry_id_compat = tk.Entry(opt_col2_frame, width=25, font=("Arial", 10))
        entry_id_compat.pack(anchor="w", pady=(0, 10))
        self.entries["Id Compatibilidad:"] = entry_id_compat

        # ==================== SECCIÓN 3: BOTONES ====================
        button_frame = tk.Frame(main_frame, bg="white")
        button_frame.pack(pady=15)

        tk.Button(button_frame, text="✅ Guardar", bg="#5cb85c", fg="white", font=("Arial", 11, "bold"),
                 command=self.guardar_reserva, padx=20, pady=8).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="🔄 Limpiar", bg="#f0ad4e", fg="white", font=("Arial", 11, "bold"),
                 command=self._limpiar_campos, padx=20, pady=8).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="❌ Cancelar", bg="#d9534f", fg="white", font=("Arial", 11, "bold"),
                 command=self.limpiar, padx=20, pady=8).pack(side=tk.LEFT, padx=5)

        # ==================== SECCIÓN 4: VISTA DE STOCK ====================
        stock_frame = tk.LabelFrame(main_frame, text="Stock de Sangre Registrado", font=("Arial", 12, "bold"),
                                   bg="white", fg="#333", padx=8, pady=8)
        stock_frame.pack(fill=tk.BOTH, expand=True, pady=4)

        # Nota sobre unidad estándar (no mostramos etiquetas por tipo)
        # Se usa STANDARD_UNIT_ML para convertir volumen a unidades estándar
        self.unit_note = tk.Label(stock_frame, text=f"Unidad estándar: {self.STANDARD_UNIT_ML:.0f} ml", font=("Arial", 10, "italic"), bg="white", fg="#555")
        self.unit_note.pack(anchor="w", padx=6, pady=(0,6))

        columnas = ("ID", "Volumen (ml)", "Vencimiento", "Tipo", "Estado")
        # Aumentar tamaño visual de la tabla: fuente y alto de fila
        style = ttk.Style()
        try:
            style.configure("Treeview", font=("Arial", 11), rowheight=26)
            style.configure("Treeview.Heading", font=("Arial", 12, "bold"))
        except Exception:
            pass
        # Mayor altura inicial para ocupar más espacio al maximizar
        self.tabla_stock = ttk.Treeview(stock_frame, columns=columnas, show="headings", height=20)

        for col in columnas:
            self.tabla_stock.heading(col, text=col)
            if col == "ID":
                self.tabla_stock.column(col, width=40)
            elif col == "Volumen (ml)":
                self.tabla_stock.column(col, width=100)
            elif col == "Vencimiento":
                self.tabla_stock.column(col, width=100)
            elif col == "Tipo":
                self.tabla_stock.column(col, width=80)
            else:
                self.tabla_stock.column(col, width=100)

        # Empaquetar expandiendo; la tabla ahora crecerá más al maximizar
        self.tabla_stock.pack(fill=tk.BOTH, expand=True)

        # Label para mostrar totales por tipo de sangre (texto extendido)
        self.total_label = tk.Label(stock_frame, text="", font=("Arial", 11, "bold"), bg="white", fg="#28a745")
        self.total_label.pack(pady=6)

        # Ahora que la tabla y labels existen, cargar el stock desde BD
        self.cargar_stock()

        # ==================== SECCIÓN 5: BOTONES DE TABLA ====================
        table_button_frame = tk.Frame(main_frame, bg="white")
        table_button_frame.pack(pady=10)

        tk.Button(table_button_frame, text="✏️ Editar", bg="#0275d8", fg="white", font=("Arial", 10, "bold"),
                 command=self.editar_reserva, padx=15, pady=6).pack(side=tk.LEFT, padx=5)
        tk.Button(table_button_frame, text="🗑️ Eliminar", bg="#dc3545", fg="white", font=("Arial", 10, "bold"),
                 command=self.borrar_reserva, padx=15, pady=6).pack(side=tk.LEFT, padx=5)

    def cargar_tipos_sangre(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT TipodeSangre FROM tipodesangre")
            return [row[0] for row in cursor.fetchall()]
        except mysql.connector.Error as e:
            messagebox.showerror("Error", f"Error al cargar tipos de sangre: {e}")
            return []

    def cargar_donantes_para_combo(self):
        """Carga los donantes para el combobox en formato 'ID - DNI - Nombre'."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT d.id, d.dni, d.nombre, d.apellido, ts.TipodeSangre
                FROM donante d
                LEFT JOIN tipodesangre ts ON d.id_TipodeSangre = ts.id
                ORDER BY d.apellido, d.nombre
            ''')
            self.donantes_data = cursor.fetchall()
            # Formatear para mostrar en el combobox
            return [f"{row[0]} - {row[1]} - {row[2]} {row[3]}" for row in self.donantes_data]
        except mysql.connector.Error as e:
            messagebox.showerror("Error", f"Error al cargar donantes: {e}")
            return []

    def _on_donante_selected(self, event=None):
        """Autocompleta el tipo de sangre cuando se selecciona un donante."""
        seleccion = self.entries["Id Donante:"].get()
        if not seleccion:
            return
        
        id_donante_sel = int(seleccion.split(" - ")[0])
        for donante in self.donantes_data:
            if donante[0] == id_donante_sel:
                self.entries["Tipo de Sangre:"].set(donante[4]) # donante[4] es el TipodeSangre
                break

    def _actualizar_info_compatibilidad(self, event=None):
        """Actualiza la información de compatibilidad cuando cambia el tipo de sangre."""
        tipo_sangre = self.entries["Tipo de Sangre:"].get().strip()
        if tipo_sangre:
            info = self.gestor_compat.obtener_recomendacion(tipo_sangre)
            self.info_label.config(text=info)
        else:
            self.info_label.config(text="Selecciona un tipo de sangre para ver su compatibilidad")

    def _limpiar_campos(self):
        """Limpia todos los campos del formulario."""
        for key, entry in self.entries.items():
            if isinstance(entry, ttk.Combobox):
                entry.set("")
            else:
                entry.delete(0, tk.END)
        self.info_label.config(text="Selecciona un tipo de sangre para ver su compatibilidad")

    def guardar_reserva(self):
        try:
            datos = {key: entry.get() for key, entry in self.entries.items()}
            
            # Validar campos requeridos
            campos_requeridos = ["Volúmen donado:", "Fecha de donación:", "Vencimiento:", 
                               "Tipo de Sangre:", "Estado:"]
            campos_vacios = [k for k in campos_requeridos if not datos[k].strip()]
            
            if campos_vacios:
                raise ValueError(f"Los siguientes campos son requeridos: {', '.join(campos_vacios)}")

            # Convertir volumen a decimal
            try:
                volumen_decimal = float(datos["Volúmen donado:"])
                if volumen_decimal <= 0:
                    raise ValueError("El volumen debe ser un número positivo.")
            except ValueError:
                raise ValueError("El volumen debe ser un número válido (puede incluir decimales).")

            # Validar fechas con formato YYYY-MM-DD
            try:
                fecha_extraccion = datetime.strptime(datos["Fecha de donación:"], "%Y-%m-%d").date()
                vencimiento = datetime.strptime(datos["Vencimiento:"], "%Y-%m-%d").date()
            except Exception:
                raise ValueError("Las fechas deben tener formato YYYY-MM-DD (ej: 2025-11-12).")

            # Validar ids numéricos (opcionales - pueden quedar como NULL)
            id_donante = None
            donante_seleccionado = datos["Id Donante:"].strip()
            if donante_seleccionado:
                try:
                    # Extraer el ID del string 'ID - DNI - Nombre'
                    id_donante = int(donante_seleccionado.split(" - ")[0])
                except (ValueError, IndexError):
                    raise ValueError("El donante seleccionado no es válido. Por favor, selecciónelo de la lista.")


            id_compat = None
            if datos["Id Compatibilidad:"].strip():
                try:
                    id_compat = int(datos["Id Compatibilidad:"])
                except ValueError:
                    raise ValueError("ID Compatibilidad debe ser un número o estar vacío.")

            # Guardar en la base de datos
            cursor = self.conn.cursor()
            # Mapear el estado legible al valor esperado por la BD
            estado_seleccionado = datos["Estado:"]
            estado_bd = self.ESTADOS_MAP.get(estado_seleccionado, estado_seleccionado)
            # Antes de insertar, verificar si ya existe una reserva con mismo Vencimiento y Tipo
            venc_str = vencimiento.strftime("%Y-%m-%d")
            tipo = datos["Tipo de Sangre:"]
            try:
                cursor.execute('''
                    SELECT ID, VolumenDisp FROM reserva
                    WHERE Vencimiento = %s AND TipodeSangre = %s AND Estado = %s
                    LIMIT 1
                ''', (venc_str, tipo, estado_bd))
                existente = cursor.fetchone()
                if existente:
                    # Actualizar sumando el volumen
                    id_exist = existente[0]
                    volumen_exist = float(existente[1]) if existente[1] is not None else 0.0
                    nuevo_vol = volumen_exist + volumen_decimal
                    cursor.execute('''
                        UPDATE reserva SET VolumenDisp = %s WHERE ID = %s
                    ''', (nuevo_vol, id_exist))
                else:
                    cursor.execute('''
                        INSERT INTO reserva (VolumenDisp, FechaExtraccion, Vencimiento, TipodeSangre, Estado, id_Donante, id_Compatibilidad)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ''', (volumen_decimal, fecha_extraccion.strftime("%Y-%m-%d"), venc_str,
                          tipo, estado_bd, id_donante, id_compat))
                self.conn.commit()
            except Exception as e:
                # Re-raise as mysql error for outer handler
                raise

            # Mostrar el estado en forma legible
            messagebox.showinfo("Éxito", f"✅ Reserva registrada correctamente.\nVolumen: {volumen_decimal} ml\nTipo: {datos['Tipo de Sangre:']}\nEstado: {datos['Estado:']}")
            
            # Refrescar la tabla y limpiar formulario
            self.cargar_stock()
            self.actualizar_tabla()
            self._limpiar_campos()
            
        except ValueError as e:
            messagebox.showerror("Error de validación", str(e))
        except mysql.connector.Error as err:
            messagebox.showerror("Error de base de datos", f"Error: {str(err)}\n\nVerifica que los datos sean válidos.")

    def cargar_stock(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
            SELECT r.ID, r.VolumenDisp, r.Vencimiento, r.TipodeSangre, r.Estado
            FROM reserva r
            ORDER BY r.Vencimiento ASC;
            ''')
            self.stock_data = cursor.fetchall()
            # actualizar la vista
            self.actualizar_tabla()
        except mysql.connector.Error as e:
            messagebox.showerror("Error", f"No se pudo cargar el stock: {e}")
            self.stock_data = []

    def editar_reserva(self):
        seleccion = self.tabla_stock.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Selecciona una reserva para editar.")
            return

        item = seleccion[0]
        valores = self.tabla_stock.item(item, "values")
        id_reserva = valores[0]
        volumen = valores[1]
        vencimiento = valores[2]
        tipo_sangre = valores[3]
        estado = valores[4]
        # Si el estado viene como código corto desde la BD, mostrar la etiqueta legible
        estado_mostrar = self.ESTADOS_REVERSE.get(estado, estado)

        ventana_editar = tk.Toplevel(self.parent)
        ventana_editar.title("Editar Reserva")
        ventana_editar.geometry("450x350")

        tk.Label(ventana_editar, text="Editar Reserva", font=("Arial", 14, "bold"), bg="white").pack(pady=10)

        tk.Label(ventana_editar, text="Volumen (ml):", font=("Arial", 10), bg="white").pack(anchor="w", padx=20, pady=(10, 2))
        entrada_volumen = tk.Entry(ventana_editar, width=40, font=("Arial", 10))
        entrada_volumen.insert(0, volumen)
        entrada_volumen.pack(anchor="w", padx=20, pady=(0, 10))

        tk.Label(ventana_editar, text="Vencimiento (YYYY-MM-DD):", font=("Arial", 10), bg="white").pack(anchor="w", padx=20, pady=(10, 2))
        entrada_vencimiento = tk.Entry(ventana_editar, width=40, font=("Arial", 10))
        entrada_vencimiento.insert(0, vencimiento)
        entrada_vencimiento.pack(anchor="w", padx=20, pady=(0, 10))

        tk.Label(ventana_editar, text="Tipo de Sangre:", font=("Arial", 10), bg="white").pack(anchor="w", padx=20, pady=(10, 2))
        tipos_sangre = self.cargar_tipos_sangre()
        entrada_tipo_sangre = ttk.Combobox(ventana_editar, values=tipos_sangre, state="readonly", width=37, font=("Arial", 10))
        entrada_tipo_sangre.set(tipo_sangre)
        entrada_tipo_sangre.pack(anchor="w", padx=20, pady=(0, 10))

        tk.Label(ventana_editar, text="Estado:", font=("Arial", 10), bg="white").pack(anchor="w", padx=20, pady=(10, 2))
        entrada_estado = ttk.Combobox(ventana_editar, values=self.ESTADOS_DISPONIBLES, state="readonly", width=37, font=("Arial", 10))
        entrada_estado.set(estado_mostrar)
        entrada_estado.pack(anchor="w", padx=20, pady=(0, 10))

        def guardar_cambios():
            nuevo_volumen = entrada_volumen.get()
            nuevo_vencimiento = entrada_vencimiento.get()
            nuevo_tipo_sangre = entrada_tipo_sangre.get()
            nuevo_estado = entrada_estado.get()
            # Mapear al valor de BD antes de guardar
            nuevo_estado_bd = self.ESTADOS_MAP.get(nuevo_estado, nuevo_estado)

            try:
                volumen_decimal = float(nuevo_volumen)
                if volumen_decimal <= 0:
                    raise ValueError("El volumen debe ser positivo.")
                datetime.strptime(nuevo_vencimiento, "%Y-%m-%d")
            except ValueError as e:
                messagebox.showerror("Error", f"Datos inválidos: {str(e)}")
                return

            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                    UPDATE reserva
                    SET VolumenDisp = %s, Vencimiento = %s, TipodeSangre = %s, Estado = %s
                    WHERE ID = %s
                ''', (volumen_decimal, nuevo_vencimiento, nuevo_tipo_sangre, nuevo_estado_bd, id_reserva))
                self.conn.commit()
                messagebox.showinfo("Éxito", "✅ Reserva actualizada correctamente.")
                ventana_editar.destroy()
                self.cargar_stock()
                self.actualizar_tabla()
            except mysql.connector.Error as e:
                messagebox.showerror("Error", f"No se pudo actualizar: {str(e)}")

        tk.Button(ventana_editar, text="💾 Guardar", bg="#5cb85c", fg="white", font=("Arial", 10, "bold"),
                 command=guardar_cambios, padx=20, pady=8).pack(pady=15)

    def borrar_reserva(self):
        seleccion = self.tabla_stock.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Selecciona una reserva para eliminar.")
            return

        for item in seleccion:
            valores = self.tabla_stock.item(item, "values")
            id_reserva = valores[0]

            respuesta = messagebox.askyesno("Confirmación", 
                f"¿Estás seguro de que deseas eliminar la reserva ID {id_reserva}?")
            if respuesta:
                try:
                    cursor = self.conn.cursor()
                    cursor.execute("SET FOREIGN_KEY_CHECKS=0")
                    cursor.execute('DELETE FROM reserva WHERE ID = %s', (id_reserva,))
                    cursor.execute("SET FOREIGN_KEY_CHECKS=1")
                    self.conn.commit()
                    messagebox.showinfo("Éxito", "✅ Reserva eliminada correctamente.")
                    self.cargar_stock()
                    self.actualizar_tabla()
                except mysql.connector.Error as e:
                    messagebox.showerror("Error", f"No se pudo eliminar: {str(e)}")

    def actualizar_tabla(self):
        """Limpia tabla y la vuelve a llenar desde self.stock_data."""
        try:
            if not hasattr(self, 'tabla_stock'):
                return
            for row in self.tabla_stock.get_children():
                self.tabla_stock.delete(row)

            # Calcular totales por tipo de sangre
            totales = {}
            for rec in self.stock_data:
                # rec: (ID, VolumenDisp, Vencimiento, TipodeSangre, Estado)
                try:
                    vol = float(rec[1])
                except Exception:
                    vol = 0.0
                tipo = rec[3]
                totales[tipo] = totales.get(tipo, 0.0) + vol
                # Mostrar valores con formato legible (convertir código de BD a etiqueta)
                display_estado = self.ESTADOS_REVERSE.get(rec[4], rec[4])
                valores_formato = (rec[0], f"{rec[1]} ml", rec[2], rec[3], display_estado)
                self.tabla_stock.insert("", "end", values=valores_formato)

            # Mostrar totales
            if hasattr(self, 'total_label') and totales:
                partes = [f"{k}: {v} ml" for k, v in totales.items()]
                self.total_label.config(text="📊 Totales por tipo: " + " | ".join(partes))
            # Actualizar resumen compacto: mostrar volumen en unidades estándar
            if hasattr(self, 'summary_labels'):
                for tipo_label, lbl in self.summary_labels.items():
                    vol = totales.get(tipo_label, 0.0)
                    unidades_est = vol / self.STANDARD_UNIT_ML if self.STANDARD_UNIT_ML else 0
                    lbl.config(text=f"{tipo_label}: {unidades_est:.2f} uds estándar")
            elif hasattr(self, 'total_label'):
                self.total_label.config(text="No hay stock registrado.")
        except Exception as e:
            print("Error actualizando tabla:", e)

    def cancelar(self):
        for widget in self.parent.winfo_children():
            widget.destroy()

    def limpiar(self):
        self.cancelar()
        logo_path = "imagenbanco.jpg"
        try:
            image = Image.open(logo_path)
            logo = ImageTk.PhotoImage(image)
            logo_label = tk.Label(self.parent, image=logo, bg="white")
            logo_label.image = logo
            logo_label.pack(pady=20)
        except Exception as e:
            tk.Label(self.parent, text="No se encontró el logo.", font=("Arial", 16), bg="white").pack()
