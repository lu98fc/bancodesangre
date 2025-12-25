import tkinter as tk
from tkinter import messagebox, ttk
from tkcalendar import DateEntry, Calendar
from PIL import Image, ImageTk
import mysql.connector
import re  # Para validar email
from datetime import datetime

class Donante:
    def __init__(self, parent, conn):
        self.parent = parent
        self.conn = conn

        tk.Label(parent, text="Registrar Donante", font=("Arial", 16), bg="white").pack(pady=10)

        labels = ["Nombre:", "Apellido:", "Fecha de Nacimiento:", "Sexo:", "DNI:",
                  "Celular:", "Correo:", "Direccion:", "Ultima Donacion:"]
        self.entries = {}

        # Formulario en grid para alinear etiquetas y campos
        form_frame = tk.Frame(parent, bg="white")
        form_frame.pack(padx=20, pady=5, fill=tk.X)

        for i, label in enumerate(labels):
            lbl = tk.Label(form_frame, text=label, font=("Arial", 12), bg="white")
            lbl.grid(row=i, column=0, sticky="w", padx=(0,10), pady=6)

            if label in ["Fecha de Nacimiento:", "Ultima Donacion:"]:
                # Usar Entry + botón para abrir un calendario en Toplevel (más estable que el popup interno)
                entry = tk.Entry(form_frame, width=28)
                btn = tk.Button(form_frame, text="📅", width=3, command=lambda e=entry: self._open_calendar(e))
                entry.grid(row=i, column=1, sticky="w", padx=(0,10))
                btn.grid(row=i, column=2, sticky="w")
                self.entries[label] = entry
                continue
            elif label == "Sexo:":
                entry = ttk.Combobox(form_frame, values=["Masculino", "Femenino"], state="readonly", width=18)
            else:
                entry = tk.Entry(form_frame, width=36)

            entry.grid(row=i, column=1, sticky="w", padx=(0,10))
            self.entries[label] = entry

        # ComboBox para tipo de sangre (alineado en la siguiente fila)
        tipos_sangre = self.cargar_tipos_sangre()
        tk.Label(form_frame, text="Tipo de Sangre:", font=("Arial", 12), bg="white").grid(row=len(labels), column=0, sticky="w", padx=(0,10), pady=8)
        self.tipo_sangre_cb = ttk.Combobox(form_frame, values=tipos_sangre, state="readonly", width=18)
        self.tipo_sangre_cb.grid(row=len(labels), column=1, sticky="w", padx=(0,10), pady=8)

        # Botones centrados
        button_frame = tk.Frame(parent, bg="white")
        button_frame.pack(pady=18)
        tk.Button(button_frame, text="Guardar", bg="#a37676", fg="white", command=self.guardar_donante, width=12).pack(side="left", padx=10)
        tk.Button(button_frame, text="Cancelar", bg="#f8f8f8", command=self.limpiar, width=12).pack(side="left", padx=10)

        # Tabla de donantes existentes
        tk.Label(parent, text="Donantes existentes:", font=("Arial", 12), bg="white").pack(anchor="w", padx=20, pady=(8,0))
        donors_frame = tk.Frame(parent, bg="white")
        self.donors_frame_ref = donors_frame
        donors_frame.pack(fill="both", expand=False, padx=20, pady=(4,12))

        cols = ("ID", "Nombre", "Apellido", "FechaN", "Sexo", "DNI", "Celular", "Correo", "TipoSangre")
        self.donors_tree = ttk.Treeview(donors_frame, columns=cols, show="headings", height=6)
        for c in cols:
            self.donors_tree.heading(c, text=c)
            self.donors_tree.column(c, width=100)
        vsb = tk.Scrollbar(donors_frame, orient="vertical", command=self.donors_tree.yview)
        self.donors_tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.donors_tree.pack(side="left", fill="both", expand=True)

        # Cargar inicialmente la lista de donantes
        self.cargar_donantes()

    def cargar_tipos_sangre(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT TipodeSangre FROM tipodesangre")
            return [row[0] for row in cursor.fetchall()]
        except mysql.connector.Error as e:
            messagebox.showerror("Error", f"Error al cargar tipos de sangre: {e}")
            return []

    def validar_datos(self, datos):
        # Verificar campos vacíos
        for key, value in datos.items():
            if not value.strip():
                raise ValueError(f"El campo '{key}' no puede estar vacío.")
        
        if datos["Sexo:"] not in ["Masculino", "Femenino"]:
           raise ValueError("Debe seleccionar un sexo válido (Masculino, Femenino).")

        # Validar DNI: solo números y 8 dígitos exactos
        if not datos["DNI:"].isdigit():
           raise ValueError("El DNI debe contener solo números.")
        if len(datos["DNI:"]) != 8:
           raise ValueError("El DNI debe tener exactamente 8 dígitos.")

         # Validar Celular: solo números y 10 dígitos exactos
        if not datos["Celular:"].isdigit():
           raise ValueError("El celular debe contener solo números.")
        if len(datos["Celular:"]) != 10:
           raise ValueError("El celular debe tener exactamente 10 dígitos.")


        # Validar formato de correo
        patron_email = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not re.match(patron_email, datos["Correo:"]):
            raise ValueError("El correo electrónico no tiene un formato válido.")

    def guardar_donante(self):
        try:
            # Obtener datos
            datos = {key: entry.get() for key, entry in self.entries.items()}
            datos["Tipo de Sangre:"] = self.tipo_sangre_cb.get()

            # Validar datos antes de guardar
            self.validar_datos(datos)

            # Convertir sexo a letra inicial (M o F)
            sexo_map = {"Masculino": "M", "Femenino": "F"}
            sexo_abreviado = sexo_map.get(datos["Sexo:"], datos["Sexo:"][0].upper())

            # Guardar en la BD
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO donante (nombre, apellido, fecha_n, sexo, dni, telefono, correo, direccion, ultimaD, id_TipodeSangre)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, (
                    SELECT id FROM tipodesangre WHERE TipodeSangre = %s
                ))
            ''', (
                datos["Nombre:"], datos["Apellido:"], datos["Fecha de Nacimiento:"],
                sexo_abreviado, datos["DNI:"], datos["Celular:"], datos["Correo:"],
                datos["Direccion:"], datos["Ultima Donacion:"], datos["Tipo de Sangre:"]
            ))
            self.conn.commit()
            nuevo_id = cursor.lastrowid

            # Se ha eliminado la lógica que agregaba una donación estándar automática.
            # Ahora solo se registra el donante.
            messagebox.showinfo("Éxito", f"Donante {datos['Nombre:']} registrado correctamente.")

            # Recargar tabla de donantes
            self.cargar_donantes()
            self.limpiar()

        except ValueError as e:
            messagebox.showerror("Error de validación", str(e))
        except mysql.connector.Error as err:
            messagebox.showerror("Error de base de datos", str(err))

    def _open_calendar(self, target_entry):
        """Abre un calendario en un Toplevel y pone la fecha seleccionada en target_entry.
        Esto evita problemas del DateEntry popup que se cierra inesperadamente.
        """
        try:
            top = tk.Toplevel(self.parent)
            top.transient(self.parent)
            top.grab_set()
            cal = Calendar(top, selectmode='day', date_pattern='yyyy-mm-dd')
            cal.pack(padx=10, pady=10)

            def on_select():
                try:
                    sel = cal.get_date()
                    target_entry.delete(0, tk.END)
                    target_entry.insert(0, sel)
                finally:
                    top.grab_release()
                    top.destroy()

            tk.Button(top, text="Aceptar", command=on_select).pack(pady=(0,10))
            tk.Button(top, text="Cancelar", command=lambda: (top.grab_release(), top.destroy())).pack()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el calendario: {e}")

    def cancelar(self):
        for widget in self.parent.winfo_children():
            widget.destroy()

    def limpiar(self):
        # Limpia pantalla y vuelve a mostrar logo
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

    def cargar_donantes(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT d.id, d.nombre, d.apellido, d.fecha_n, d.sexo, d.dni, d.telefono, d.correo, ts.TipodeSangre
                FROM donante d
                LEFT JOIN tipodesangre ts ON d.id_TipodeSangre = ts.id
                ORDER BY d.apellido ASC
            ''')
            rows = cursor.fetchall()
            # Limpiar
            for item in self.donors_tree.get_children():
                self.donors_tree.delete(item)
            for r in rows:
                self.donors_tree.insert("", "end", values=r)
        except mysql.connector.Error as e:
            messagebox.showerror("Error", f"No se pudieron cargar los donantes: {e}")
