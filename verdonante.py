import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
from tkcalendar import DateEntry
import mysql.connector
from datetime import datetime

class VerDonante:
    def __init__(self, parent, conn):
        self.parent = parent
        self.conn = conn
        self.tabla_donantes = None

        tk.Label(parent, text="Consulta de Donantes", font=("Arial", 16), bg="white").pack(pady=10)
        
        frame_busqueda = tk.Frame(parent, bg="white")
        frame_busqueda.pack(pady=10)

        tk.Label(frame_busqueda, text="Ingrese el DNI del donante:", bg="white").grid(row=0, column=0, padx=5)
        self.entrada_dni = tk.Entry(frame_busqueda, width=30)
        self.entrada_dni.grid(row=0, column=1, padx=5)

        tk.Button(
            frame_busqueda,
            text="🔍 Buscar",
            bg="#d4b3b3",
            command=lambda: self.realizar_busqueda(self.entrada_dni.get())
        ).grid(row=0, column=2, padx=5)

        tk.Button(
            frame_busqueda,
            text="📋 Ver Todos",
            bg="#6c95b0",
            fg="white",
            command=self.cargar_todos_los_donantes
        ).grid(row=0, column=3, padx=5)

        columnas = ("ID", "Nombre", "Apellido", "Fecha Nacimiento", "Sexo", "DNI", "Teléfono", "Correo", "Dirección", "Última donación", "Tipo Sangre")
        self.tabla_donantes = ttk.Treeview(parent, columns=columnas, show="headings", height=15)

        for col in columnas:
            self.tabla_donantes.heading(col, text=col)
            self.tabla_donantes.column(col, width=100)

        self.tabla_donantes.pack(pady=20)

        button_frame = tk.Frame(parent, bg="white")
        button_frame.pack(pady=20)

        tk.Button(button_frame, text="Editar Donante", bg="#a37676", fg="white", command=self.editar_donante).pack(side="left", padx=10)
        tk.Button(button_frame, text="Eliminar Donante", bg="#f8f8f8", command=self.eliminar_donante).pack(side="left", padx=10)
        tk.Button(self.parent, text="Cancelar", bg="#f8f8f8", command=self.limpiar).pack(side="top", padx=5)
        
        # Cargar todos los donantes al iniciar la vista
        self.cargar_todos_los_donantes()

    def realizar_busqueda(self, dni):
        if not dni:
            # Si el DNI está vacío, simplemente cargamos todos los donantes
            self.cargar_todos_los_donantes()
            return

        try:
            cursor = self.conn.cursor()
            query = """
                SELECT d.id, d.nombre, d.apellido, d.fecha_n, d.sexo, d.DNI, d.telefono, d.Correo, 
                       d.direccion, d.UltimaD, ts.TipodeSangre 
                FROM donante d 
                JOIN TipodeSangre ts ON ts.id = d.id_TipodeSangre 
                WHERE dni = %s
            """
            cursor.execute(query, (dni,))
            resultado = cursor.fetchall()

            for row in self.tabla_donantes.get_children():
                self.tabla_donantes.delete(row)

            if resultado:
                for registro in resultado:
                    self.tabla_donantes.insert("", "end", values=registro)
            else:
                messagebox.showinfo("Información", "No se encontró un donante con ese DNI.")
        except mysql.connector.Error as e:
            messagebox.showerror("Error", f"Error al conectar con la base de datos: {e}")

    def cargar_todos_los_donantes(self):
        """Carga todos los donantes de la base de datos en la tabla."""
        try:
            cursor = self.conn.cursor()
            query = """
                SELECT d.id, d.nombre, d.apellido, d.fecha_n, d.sexo, d.DNI, d.telefono, d.Correo, 
                       d.direccion, d.UltimaD, ts.TipodeSangre 
                FROM donante d 
                LEFT JOIN TipodeSangre ts ON ts.id = d.id_TipodeSangre 
                ORDER BY d.apellido, d.nombre
            """
            cursor.execute(query)
            resultado = cursor.fetchall()

            for row in self.tabla_donantes.get_children():
                self.tabla_donantes.delete(row)

            if resultado:
                for registro in resultado:
                    self.tabla_donantes.insert("", "end", values=registro)
        except mysql.connector.Error as e:
            messagebox.showerror("Error", f"Error al cargar todos los donantes: {e}")

    def editar_donante(self):
        seleccionado = self.tabla_donantes.selection()
        if not seleccionado:
            messagebox.showwarning("Advertencia", "Por favor, seleccione un registro para editar.")
            return

        valores = self.tabla_donantes.item(seleccionado)["values"]
        entrada_dni = valores[5]

        ventana_editar = tk.Toplevel()
        ventana_editar.title("Editar Donante")
        ventana_editar.geometry("400x600")

        etiquetas = [
            "Nombre", "Apellido", "Fecha Nacimiento", "Sexo", "DNI", 
            "Teléfono", "Correo", "Dirección", "Última Donación", "Tipo Sangre"
        ]

        entradas = []

        for i, campo in enumerate(valores[1:]):
            tk.Label(ventana_editar, text=etiquetas[i]).pack(pady=5)

            if etiquetas[i] in ["Fecha Nacimiento", "Última Donación"]:
                entrada = DateEntry(ventana_editar, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
                try:
                    entrada.set_date(datetime.strptime(str(campo), "%Y-%m-%d"))
                except:
                    pass
                entrada.pack(pady=5)

            elif etiquetas[i] == "Sexo":
                entrada = ttk.Combobox(ventana_editar, values=["Masculino", "Femenino", "Otro"])
                entrada.set(campo)
                entrada.pack(pady=5)

            elif etiquetas[i] == "Tipo Sangre":
                try:
                    cursor = self.conn.cursor()
                    cursor.execute("SELECT TipodeSangre FROM TipodeSangre")
                    tipos_sangre = [fila[0] for fila in cursor.fetchall()]
                except:
                    tipos_sangre = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
                entrada = ttk.Combobox(ventana_editar, values=tipos_sangre)
                entrada.set(campo)
                entrada.pack(pady=5)

            else:
                entrada = tk.Entry(ventana_editar)
                entrada.insert(0, campo)
                entrada.pack(pady=5)

            entradas.append(entrada)

        # Frame para los botones de acción
        frame_botones = tk.Frame(ventana_editar)
        frame_botones.pack(pady=20)

        # Botón Guardar (verde, con tilde)
        btn_guardar = tk.Button(
            frame_botones, 
            text="✅ Guardar",
            bg="green",
            fg="white",
            font=("Arial", 10, "bold"),
            width=12,
            command=lambda: self.guardar_cambios(entrada_dni, entradas)
        )
        btn_guardar.pack(side="left", padx=10)

        # Botón Cancelar (rojo, con X)
        btn_cancelar = tk.Button(
            frame_botones, 
            text="❌ Cancelar",
            bg="red",
            fg="white",
            font=("Arial", 10, "bold"),
            width=12,
            command=ventana_editar.destroy
        )
        btn_cancelar.pack(side="left", padx=10)


    def guardar_cambios(self, entrada_dni, entradas):
        nuevos_datos = []
        for entrada in entradas:
            if isinstance(entrada, DateEntry):
                nuevos_datos.append(entrada.get_date().strftime("%Y-%m-%d"))
            else:
                nuevos_datos.append(entrada.get())

        # Convertir sexo a letra inicial (M o F) - es el índice 3
        sexo_map = {"Masculino": "M", "Femenino": "F", "Otro": "O"}
        if len(nuevos_datos) > 3:
            sexo_original = nuevos_datos[3]
            nuevos_datos[3] = sexo_map.get(sexo_original, sexo_original[0].upper() if sexo_original else "")

        tipo_sangre_nombre = nuevos_datos[-1]
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id FROM TipodeSangre WHERE TipodeSangre = %s", (tipo_sangre_nombre,))
            resultado = cursor.fetchone()
            if resultado:
                id_tipo_sangre = resultado[0]
            else:
                messagebox.showerror("Error", f"No se encontró el tipo de sangre '{tipo_sangre_nombre}' en la base de datos.")
                return
        except mysql.connector.Error as e:
            messagebox.showerror("Error", f"No se pudo obtener el ID del tipo de sangre: {e}")
            return

        nuevos_datos[-1] = id_tipo_sangre

        try:
            cursor = self.conn.cursor()
            update_query = """
            UPDATE donante
            SET nombre = %s, apellido = %s, fecha_n = %s, sexo = %s, DNI = %s,
                telefono = %s, Correo = %s, direccion = %s, UltimaD = %s, id_TipodeSangre = %s
            WHERE DNI = %s
            """
            cursor.execute(update_query, (*nuevos_datos, entrada_dni))
            self.conn.commit()
            messagebox.showinfo("Éxito", "Datos actualizados correctamente.")            
            self.realizar_busqueda()
        except mysql.connector.Error as e:
            messagebox.showerror("Error", f"No se pudo actualizar el donante: {e}")
         
    def eliminar_donante(self):
        seleccionado = self.tabla_donantes.selection()
        if not seleccionado:
            messagebox.showwarning("Advertencia", "Por favor, seleccione un registro para eliminar.")
            return

        valores = self.tabla_donantes.item(seleccionado)["values"]
        entrada_dni = valores[5]

        respuesta = messagebox.askyesno("Confirmación", "¿Estás seguro de que deseas eliminar este registro?")
        if respuesta:
            try:
                cursor = self.conn.cursor()
                cursor.execute("SET FOREIGN_KEY_CHECKS=0")
                cursor.execute("DELETE FROM donante WHERE DNI = %s", (entrada_dni,))
                cursor.execute("SET FOREIGN_KEY_CHECKS=1")
                self.conn.commit()
                messagebox.showinfo("Éxito", "Donante eliminado correctamente.")
                self.cargar_todos_los_donantes() # Recargar todos tras eliminar
            except mysql.connector.Error as e:
                messagebox.showerror("Error", f"No se pudo eliminar el donante: {e}")

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
        except Exception:
            tk.Label(self.parent, text="No se encontró el logo.", font=("Arial", 16), bg="white").pack()
