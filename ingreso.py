import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
# Importar Menu se hace dinamicamente para evitar referencias circulares


# Códigos de acceso permitidos
CODIGOS_VALIDOS = ["1234", "5678", "9101", "5524"]


class Login:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema Gestor Banco de Sangre - Login")
        self.root.geometry("1200x800")
        self.root.configure(bg="white")

        

        tk.Label(root, text="Ingrese el código de acceso", font=("Arial", 14), bg="white").pack(pady=20)
        self.entry_codigo = tk.Entry(root, show="*", font=("Arial", 12))
        self.entry_codigo.pack(pady=5)

        tk.Button(root, text="Ingresar", command=self.verificar_login, bg="#d9a5a5", font=("Arial", 12)).pack(pady=10)

        logo_path = "imagenbanco.jpg"
        try:
            image = Image.open(logo_path)
            image = image.resize((700, 700), Image.LANCZOS)
            logo = ImageTk.PhotoImage(image)
            logo_label = tk.Label(self.root, image=logo, bg="white")
            logo_label.image = logo
            logo_label.pack(pady=20)
        except Exception as e:
            tk.Label(self.root, text="No se encontró el logo.", font=("Arial", 16), bg="white").pack()
       

    def verificar_login(self):
        codigo = self.entry_codigo.get()
        if codigo in CODIGOS_VALIDOS:
            self.mostrar_menu()
        else:
            messagebox.showerror("Error", "Código incorrecto")

    def mostrar_menu(self):
        from menu import Menu  # Importar aquí para evitar referencia circular
        for widget in self.root.winfo_children():
            widget.destroy()
        Menu(self.root)

    

if __name__ == "__main__":
    root = tk.Tk()
    Login(root)
    root.mainloop()