import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
import pyautogui
import time

class ClickApp:
    def __init__(self, root):
        self.root = root
        self.root.title(".:Cyborg Dragon:.")
        self.coords = []  # [(x, y)] para clics simples, [((x1, y1), (x2, y2))] para rangos

        # UI
        self.coord_listbox = tk.Listbox(root, width=40)
        self.coord_listbox.pack(padx=10, pady=10)

        add_btn = tk.Button(root, text="Capturar coordenada", command=self.capture_coord)
        add_btn.pack(pady=5)

        edit_btn = tk.Button(root, text="Editar coordenada seleccionada", command=self.edit_coord)
        edit_btn.pack(pady=5)

        clear_btn = tk.Button(root, text="Limpiar coordenadas", command=self.clear_coords)
        clear_btn.pack(pady=5)

        # Botón para ejecutar los clics
        run_btn = tk.Button(root, text="Ejecutar clics", command=self.run_clicks)
        run_btn.pack(pady=10)

        # Botón para seleccionar rango
        select_range_btn = tk.Button(root, text="Capturar selección de rango", command=self.capture_range)
        select_range_btn.pack(pady=5)

        # Guardar rangos de selección
        self.ranges = []
    def capture_range(self):
        messagebox.showinfo("Captura", "Ubica el mouse en el punto INICIAL y espera 3 segundos...")
        time.sleep(3)
        x1, y1 = pyautogui.position()
        messagebox.showinfo("Captura", "Ubica el mouse en el punto FINAL y espera 3 segundos...")
        time.sleep(3)
        x2, y2 = pyautogui.position()
        # Guardar como tupla especial para distinguir rango
        self.coords.append(((x1, y1), (x2, y2)))
        messagebox.showinfo("Rango capturado", f"Rango: ({x1}, {y1}) -> ({x2}, {y2})")
        self.coord_listbox.insert(tk.END, f"({x1}, {y1}) -> ({x2}, {y2})")

    def run_selections(self):
        if not self.ranges:
            messagebox.showinfo("Sin rangos", "Agrega al menos un rango de selección.")
            return
        veces = simpledialog.askinteger("Repeticiones", "¿Cuántas veces ejecutar las selecciones?", initialvalue=1)
        if veces is None:
            return
        messagebox.showinfo("Inicio", "La ejecución de selecciones comenzará en 5 segundos...")
        time.sleep(5)
        for i in range(veces):
            for (x1, y1), (x2, y2) in self.ranges:
                pyautogui.moveTo(x1, y1, duration=0.3)
                pyautogui.mouseDown()
                pyautogui.moveTo(x2, y2, duration=0.5)
                pyautogui.mouseUp()
                time.sleep(0.2)
        messagebox.showinfo("Finalizado", "Selecciones completadas.")

    def clear_coords(self):
        if not self.coords:
            messagebox.showinfo("Sin coordenadas", "No hay coordenadas para limpiar.")
            return
        if messagebox.askyesno("Confirmar", "¿Seguro que deseas limpiar todas las coordenadas?"):
            self.coords.clear()
            self.coord_listbox.delete(0, tk.END)
            messagebox.showinfo("Limpio", "Todas las coordenadas han sido eliminadas.")

    def capture_coord(self):
        messagebox.showinfo("Captura", "Ubica el mouse y espera 3 segundos...")
        time.sleep(3)
        x, y = pyautogui.position()
        self.coords.append((x, y))
        self.coord_listbox.insert(tk.END, f"({x}, {y})")

    def edit_coord(self):
        selected = self.coord_listbox.curselection()
        if not selected:
            messagebox.showwarning("Advertencia", "Selecciona una coordenada para editar.")
            return
        index = selected[0]
        x, y = self.coords[index]

        new_x = simpledialog.askinteger("Editar X", "Nueva coordenada X:", initialvalue=x)
        new_y = simpledialog.askinteger("Editar Y", "Nueva coordenada Y:", initialvalue=y)

        if new_x is not None and new_y is not None:
            self.coords[index] = (new_x, new_y)
            self.coord_listbox.delete(index)
            self.coord_listbox.insert(index, f"({new_x}, {new_y})")

    def run_clicks(self):
        if not self.coords:
            messagebox.showinfo("Sin acciones", "Agrega al menos una coordenada o un rango de selección.")
            return
        veces = simpledialog.askinteger("Repeticiones", "¿Cuántas veces ejecutar las acciones?", initialvalue=1)
        if veces is None:
            return
        messagebox.showinfo("Inicio", "La ejecución comenzará en 5 segundos...")
        time.sleep(5)
        for i in range(veces):
            for item in self.coords:
                if isinstance(item, tuple) and len(item) == 2 and all(isinstance(x, tuple) and len(x) == 2 for x in item):
                    # Es un rango
                    (x1, y1), (x2, y2) = item
                    pyautogui.moveTo(x1, y1, duration=0.3)
                    pyautogui.mouseDown()
                    pyautogui.moveTo(x2, y2, duration=0.5)
                    pyautogui.mouseUp()
                    time.sleep(0.2)
                else:
                    # Es un clic simple
                    x, y = item
                    pyautogui.moveTo(x, y, duration=0.3)
                    pyautogui.click()
                    time.sleep(0.2)
        messagebox.showinfo("Finalizado", "Acciones completadas.")

# Crear ventana
root = tk.Tk()
app = ClickApp(root)
root.mainloop()
