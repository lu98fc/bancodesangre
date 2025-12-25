import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import mysql.connector


class VerDonaciones:
    STANDARD_UNIT_ML = 450.0  # Una unidad estándar = 450 ml
    
    def __init__(self, parent, conn):
        self.parent = parent
        self.conn = conn

        # Mapeo de estados (legible <-> valor en BD)
        self.ESTADOS_MAP = {
            
            "Vencida":"V",
            "No vencida":"N"
        }
        self.ESTADOS_REVERSE = {v: k for k, v in self.ESTADOS_MAP.items()}

        tk.Label(parent, text="Ver Donaciones", font=("Arial", 16), bg="white").pack(pady=10)

        # Marco de búsqueda mejorado
        frame_busqueda = tk.Frame(parent, bg="white")
        frame_busqueda.pack(pady=10)

        tk.Label(frame_busqueda, text="Buscar por DNI o Nombre:", font=("Arial", 10), bg="white").grid(row=0, column=0, padx=5, pady=5)
        self.entry_busqueda = tk.Entry(frame_busqueda, width=30, font=("Arial", 10))
        self.entry_busqueda.grid(row=0, column=1, padx=5, pady=5)
        self.entry_busqueda.bind("<KeyRelease>", lambda e: self.buscar_donaciones())  # Búsqueda en tiempo real

        tk.Button(
            frame_busqueda,
            text="🔍 Buscar",
            bg="#d4b3b3",
            command=self.buscar_donaciones,
            font=("Arial", 10)
        ).grid(row=0, column=2, padx=5, pady=5)

        tk.Button(
            frame_busqueda,
            text="📋 Ver Todos",
            bg="#6c95b0",
            fg="white",
            command=self.cargar_todas_donaciones,
            font=("Arial", 10)
        ).grid(row=0, column=3, padx=5, pady=5)

        # Marco para la tabla con scrollbar
        table_frame = tk.Frame(parent, bg="white")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 15))

        columnas = ("ID", "Donante", "DNI", "Fecha", "Volumen (ml)", "Unidades", "Estado")
        self.tree = ttk.Treeview(table_frame, columns=columnas, show="headings", height=15)
        vsb = tk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.pack(side="left", fill=tk.BOTH, expand=True)

        # Configurar encabezados y anchos
        for col in columnas:
            self.tree.heading(col, text=col)
            if col == "ID":
                self.tree.column(col, width=50, anchor="center")
            elif col == "Donante":
                self.tree.column(col, width=120, anchor="w")
            elif col == "DNI":
                self.tree.column(col, width=80, anchor="center")
            elif col == "Fecha":
                self.tree.column(col, width=100, anchor="center")
            elif col == "Volumen (ml)":
                self.tree.column(col, width=90, anchor="center")
            elif col == "Unidades":
                self.tree.column(col, width=80, anchor="center")
            else:
                self.tree.column(col, width=100, anchor="center")

        # Botones
        frame_botones = tk.Frame(parent, bg="#f8f8f8")
        frame_botones.pack(pady=8)

        tk.Button(
            frame_botones,
            text="Editar Información",
            bg="#a37676",
            fg="white",
            command=self.editar_donacion,
            font=("Arial", 10)
        ).pack(side="left", padx=5)

        tk.Button(self.parent, text="Cancelar", bg="#f8f8f8", command=self.limpiar, font=("Arial", 10)).pack(side="top", padx=5)

        # Doble clic para editar
        def _on_double_click(event):
            try:
                if self.tree.selection():
                    self.editar_donacion()
            except Exception:
                pass

        self.tree.bind("<Double-1>", _on_double_click)
        
        # Cargar todas las donaciones al inicio
        self.cargar_todas_donaciones()



    def buscar_donaciones(self):
        """Busca donaciones por DNI o Nombre del donante"""
        busqueda = self.entry_busqueda.get().strip()
        
        try:
            cursor = self.conn.cursor()
            
            if not busqueda:
                # Si el campo está vacío, cargar todas
                self.cargar_todas_donaciones()
                return
            
            # Buscar por DNI o Nombre (LIKE para búsqueda parcial)
            query = """
                SELECT r.id_Donante, d.nombre, d.apellido, d.dni, 
                       r.FechaExtraccion, r.VolumenDisp, r.Estado
                FROM reserva r
                LEFT JOIN donante d ON r.id_Donante = d.id
                WHERE (d.dni LIKE %s OR CONCAT(d.nombre, ' ', d.apellido) LIKE %s)
                ORDER BY d.nombre, d.apellido, r.FechaExtraccion DESC
            """
            
            param = f"%{busqueda}%"
            cursor.execute(query, (param, param))
            resultados = cursor.fetchall()
            self.mostrar_resultados(resultados)
            
        except mysql.connector.Error as e:
            messagebox.showerror("Error", f"Error al buscar: {str(e)}")
        finally:
            cursor.close()

    def cargar_todas_donaciones(self):
        """Carga todas las donaciones disponibles"""
        try:
            cursor = self.conn.cursor()
            query = """
                SELECT r.id_Donante, d.nombre, d.apellido, d.dni,
                       r.FechaExtraccion, r.VolumenDisp, r.Estado
                FROM reserva r
                LEFT JOIN donante d ON r.id_Donante = d.id
                ORDER BY d.nombre, d.apellido, r.FechaExtraccion DESC
            """
            cursor.execute(query)
            resultados = cursor.fetchall()
            self.mostrar_resultados(resultados)
            
        except mysql.connector.Error as e:
            messagebox.showerror("Error", f"Error al cargar donaciones: {str(e)}")
        finally:
            cursor.close()


    def mostrar_resultados(self, datos):
        """Muestra resultados en la tabla, con cálculo de unidades"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        for fila in datos:
            fila_list = list(fila)
            # fila esperada: (id_Donante, nombre, apellido, dni, FechaExtraccion, VolumenDisp, Estado)
            
            # Convertir estado a legible
            if len(fila_list) >= 7:
                fila_list[6] = self.ESTADOS_REVERSE.get(fila_list[6], fila_list[6])
            
            # Calcular unidades: VolumenDisp / 450
            volumen_index = 5  # VolumenDisp está en índice 5
            if len(fila_list) > volumen_index and fila_list[volumen_index]:
                try:
                    volumen = float(fila_list[volumen_index])
                    unidades = round(volumen / self.STANDARD_UNIT_ML, 2)
                except (ValueError, TypeError):
                    unidades = 0
            else:
                unidades = 0
            
            # Armar fila para mostrar: (ID, Donante, DNI, Fecha, Volumen, Unidades, Estado)
            id_donante = fila_list[0]
            nombre_completo = f"{fila_list[1]} {fila_list[2]}" if fila_list[1] and fila_list[2] else "Anónimo"
            dni = fila_list[3] if len(fila_list) > 3 else ""
            fecha = fila_list[4] if len(fila_list) > 4 else ""
            volumen = fila_list[5] if len(fila_list) > 5 else ""
            estado = fila_list[6] if len(fila_list) > 6 else ""
            
            valores_mostrar = (id_donante, nombre_completo, dni, fecha, volumen, unidades, estado)
            self.tree.insert("", "end", values=valores_mostrar)


    def editar_donacion(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Debe seleccionar un registro para editar.")
            return

        item = self.tree.item(selected_item[0])
        datos = item["values"]
        # datos = (ID, Donante, DNI, Fecha, Volumen, Unidades, Estado)
        
        id_donante = datos[0]
        fecha = datos[3]
        volumen = datos[4]
        estado = datos[6]

        ventana_editar = tk.Toplevel(self.parent)
        ventana_editar.title("Editar Donación")
        ventana_editar.geometry("400x300")

        tk.Label(ventana_editar, text="ID Donante:", font=("Arial", 10), bg="white").grid(row=0, column=0, padx=10, pady=5)
        tk.Label(ventana_editar, text=str(id_donante), font=("Arial", 10), bg="white").grid(row=0, column=1, padx=10, pady=5)

        tk.Label(ventana_editar, text="Fecha:", font=("Arial", 10), bg="white").grid(row=1, column=0, padx=10, pady=5)
        fecha_entry = tk.Entry(ventana_editar, font=("Arial", 10))
        fecha_entry.insert(0, str(fecha))
        fecha_entry.grid(row=1, column=1, padx=10, pady=5)

        tk.Label(ventana_editar, text="Volumen (ml):", font=("Arial", 10), bg="white").grid(row=2, column=0, padx=10, pady=5)
        volumen_entry = tk.Entry(ventana_editar, font=("Arial", 10))
        volumen_entry.insert(0, str(volumen))
        volumen_entry.grid(row=2, column=1, padx=10, pady=5)

        tk.Label(ventana_editar, text="Estado:", font=("Arial", 10), bg="white").grid(row=3, column=0, padx=10, pady=5)
        # El estado ya viene legible, buscar su código en ESTADOS_MAP
        estado_entry = ttk.Combobox(ventana_editar, values=list(self.ESTADOS_MAP.keys()), state="readonly", font=("Arial", 10))
        try:
            estado_entry.set(estado)
        except Exception:
            estado_entry.set(estado)
        estado_entry.grid(row=3, column=1, padx=10, pady=5)

        def guardar_cambios():
            nueva_fecha = fecha_entry.get().strip()
            nuevo_volumen = volumen_entry.get().strip()
            nuevo_estado = estado_entry.get().strip()
            nuevo_estado_bd = self.ESTADOS_MAP.get(nuevo_estado, nuevo_estado)

            if not nueva_fecha or not nuevo_volumen or not nuevo_estado:
                messagebox.showwarning("Advertencia", "Todos los campos son obligatorios.")
                return

            try:
                nuevo_volumen = float(nuevo_volumen)
                cursor = self.conn.cursor()
                cursor.execute('''
                    UPDATE reserva
                    SET FechaExtraccion = %s, VolumenDisp = %s, Estado = %s
                    WHERE id_Donante = %s AND FechaExtraccion = %s
                ''', (nueva_fecha, nuevo_volumen, nuevo_estado_bd, id_donante, fecha))
                self.conn.commit()
                cursor.close()

                messagebox.showinfo("Éxito", "Donación actualizada correctamente.")
                ventana_editar.destroy()
                self.cargar_todas_donaciones()
            except ValueError:
                messagebox.showerror("Error", "El volumen debe ser un número válido.")
            except mysql.connector.Error as e:
                messagebox.showerror("Error", f"No se pudo actualizar la donación: {e}")

        tk.Button(ventana_editar, text="Guardar", command=guardar_cambios, bg="#a37676", fg="white", font=("Arial", 10)).grid(row=4, column=0, columnspan=2, pady=10)


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