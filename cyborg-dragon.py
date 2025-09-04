import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
import pyautogui
import time
import ast  # <- para parsear coordenadas de forma segura

class ClickApp:
    # =========================
    #   CONSTRUCTOR / UI
    # =========================
    def __init__(self, root):
        self.root = root
        self.root.title(".:Cyborg Dragon:.")
        self.coords = []  # [(x, y)] o [((x1,y1),(x2,y2))] para rangos
        self.ranges = []  # (se mantiene si lo necesitas)

        # --- UI base ---
        main_frame = tk.Frame(root)
        main_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Panel coordenadas
        coord_frame = tk.Frame(main_frame)
        coord_frame.pack(side=tk.LEFT, fill=tk.Y)

        coord_label = tk.Label(coord_frame, text="Tabla Coord.", font=("Arial", 12, "bold"))
        coord_label.pack(pady=(5, 0))

        # NUEVO: posición de inyección (1-based para el usuario)
        inj_row = tk.Frame(coord_frame)
        inj_row.pack(pady=(0, 6), fill=tk.X)
        tk.Label(inj_row, text="Posición de inyección (1..N):").pack(side=tk.LEFT)
        self.inject_pos_var = tk.IntVar(value=3)  # por defecto 3
        self.inject_pos_spin = tk.Spinbox(
            inj_row, from_=1, to=999, width=5, textvariable=self.inject_pos_var
        )
        self.inject_pos_spin.pack(side=tk.LEFT, padx=(6, 0))

        self.coord_listbox = tk.Listbox(coord_frame, width=40)
        self.coord_listbox.pack(padx=5, pady=5)

        agregar_tabla_btn = tk.Button(
            coord_frame,
            text="Agregar coord. de tabla TXT a lista (no cambia estado)",
            command=self.agregar_coord_tabla_a_lista
        )
        agregar_tabla_btn.pack(pady=5)

        add_btn = tk.Button(coord_frame, text="Capturar coordenada", command=self.capture_coord)
        add_btn.pack(pady=2)

        edit_btn = tk.Button(coord_frame, text="Editar coordenada seleccionada", command=self.edit_coord)
        edit_btn.pack(pady=2)

        clear_btn = tk.Button(coord_frame, text="Limpiar coordenadas", command=self.clear_coords)
        clear_btn.pack(pady=2)

        run_btn = tk.Button(coord_frame, text="Ejecutar clics", command=self.run_clicks)
        run_btn.pack(pady=5)

        # Panel tabla TXT
        table_frame = tk.Frame(main_frame)
        table_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        table_label = tk.Label(table_frame, text="Tabla TXT", font=("Arial", 12, "bold"))
        table_label.pack(pady=(5, 0))

        from tkinter import ttk
        self.txt_table = ttk.Treeview(
            table_frame, columns=("Nombre TXT", "Coordenada", "Estado"),
            show="headings", height=10
        )
        self.txt_table.heading("Nombre TXT", text="Nombre TXT")
        self.txt_table.heading("Coordenada", text="Coordenada")
        self.txt_table.heading("Estado", text="Estado")
        self.txt_table.column("Nombre TXT", width=180)
        self.txt_table.column("Coordenada", width=120)
        self.txt_table.column("Estado", width=80)
        self.txt_table.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)

        # Botones al costado
        btns_table_frame = tk.Frame(table_frame)
        btns_table_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5)

        up_btn = tk.Button(btns_table_frame, text="Subir coordenada", command=self.move_coord_up, width=18)
        up_btn.pack(pady=2)

        down_btn = tk.Button(btns_table_frame, text="Bajar coordenada", command=self.move_coord_down, width=18)
        down_btn.pack(pady=2)

        load_txt_btn = tk.Button(table_frame, text="Cargar carpeta TXT", command=self.load_txt_files)
        load_txt_btn.pack(pady=5)

        asociar_capturada_btn = tk.Button(
            table_frame,
            text="Asociar coord. capturada a TXT seleccionado",
            command=self.asociar_coord_capturada_a_txt
        )
        asociar_capturada_btn.pack(pady=5)

        reset_states_btn = tk.Button(
            table_frame, text="Reiniciar estados (TXT→No)", command=self.reset_txt_states
        )
        reset_states_btn.pack(pady=5)

    # =========================
    #   HELPERS
    # =========================
    def _parse_coord(self, coord_str):
        """Parsea '(x, y)' de forma segura y devuelve (x,y) como ints. Retorna None si inválido."""
        try:
            val = ast.literal_eval(coord_str)
            if (isinstance(val, tuple) and len(val) == 2 and
                all(isinstance(n, (int, float)) for n in val)):
                return int(val[0]), int(val[1])
        except Exception:
            pass
        return None

    def _get_first_no_row(self):
        """
        Devuelve (item_id, archivo, coord_str) de la PRIMERA fila con Estado == 'No'.
        Si no hay, (None, None, None).
        """
        items = self.txt_table.get_children() if hasattr(self, 'txt_table') else []
        for item in items:
            archivo, coord, estado = self.txt_table.item(item, "values")
            if str(estado).strip().lower() == "no":
                return item, archivo, coord
        return None, None, None

    def _get_injection_index0(self, base_len):
        """
        Devuelve el índice 0-based donde insertar, a partir del valor del Spinbox (1-based).
        Si el usuario pone un valor mayor al tamaño+1, se clamp a len (append).
        """
        try:
            pos1 = int(self.inject_pos_var.get())
        except Exception:
            pos1 = 1
        if pos1 < 1:
            pos1 = 1
        # 1-based -> 0-based
        idx0 = pos1 - 1
        if idx0 > base_len:
            idx0 = base_len  # insertar al final
        return idx0

    def _render_temp_coord_list(self, coords_view, injected_idx=None, archivo=None):
        """
        Dibuja en el Listbox una vista temporal (sin tocar self.coords).
        Si injected_idx no es None, imprime una flecha con el nombre del TXT en ese índice.
        """
        self.coord_listbox.delete(0, tk.END)
        for i, coord in enumerate(coords_view, 1):
            if (isinstance(coord, tuple) and len(coord) == 2 and
                all(isinstance(x, tuple) and len(x) == 2 for x in coord)):
                # Rango
                (x1, y1), (x2, y2) = coord
                label = f"{i}. Rango: ({x1}, {y1}) -> ({x2}, {y2})"
            else:
                # Punto
                x, y = coord
                label = f"{i}. Coordenada: ({x}, {y})"

            if injected_idx is not None and (i - 1) == injected_idx and archivo:
                label += f"  -> {archivo} (dinámica)"
            self.coord_listbox.insert(tk.END, label)

    def update_coord_listbox(self):
        """Redibuja la lista base self.coords (sin la vista temporal)."""
        self.coord_listbox.delete(0, tk.END)
        for idx, coord in enumerate(self.coords, 1):
            if (isinstance(coord, tuple) and len(coord) == 2 and
                all(isinstance(x, tuple) and len(x) == 2 for x in coord)):
                (x1, y1), (x2, y2) = coord
                self.coord_listbox.insert(tk.END, f"{idx}. Rango: ({x1}, {y1}) -> ({x2}, {y2})")
            else:
                x, y = coord
                self.coord_listbox.insert(tk.END, f"{idx}. Coordenada: ({x}, {y})")

    # =========================
    #   ACCIONES DE COORDS
    # =========================
    def capture_coord(self):
        messagebox.showinfo("Captura", "Ubica el mouse y espera 3 segundos...")
        time.sleep(3)
        x, y = pyautogui.position()
        self.coords.append((x, y))
        self.update_coord_listbox()

    def capture_range(self):
        messagebox.showinfo("Captura", "Ubica el mouse en el punto INICIAL y espera 3 segundos...")
        time.sleep(3)
        x1, y1 = pyautogui.position()
        messagebox.showinfo("Captura", "Ubica el mouse en el punto FINAL y espera 3 segundos...")
        time.sleep(3)
        x2, y2 = pyautogui.position()
        self.coords.append(((x1, y1), (x2, y2)))
        messagebox.showinfo("Rango capturado", f"Rango: ({x1}, {y1}) -> ({x2}, {y2})")
        self.update_coord_listbox()

    def edit_coord(self):
        selected = self.coord_listbox.curselection()
        if not selected:
            messagebox.showwarning("Advertencia", "Selecciona una coordenada para editar.")
            return
        index = selected[0]
        c = self.coords[index]
        if (isinstance(c, tuple) and len(c) == 2 and
            all(isinstance(x, tuple) and len(x) == 2 for x in c)):
            messagebox.showinfo("No soportado", "Edición rápida solo para puntos, no rangos.")
            return
        x, y = c
        new_x = simpledialog.askinteger("Editar X", "Nueva coordenada X:", initialvalue=x)
        new_y = simpledialog.askinteger("Editar Y", "Nueva coordenada Y:", initialvalue=y)
        if new_x is not None and new_y is not None:
            self.coords[index] = (new_x, new_y)
            self.update_coord_listbox()

    def move_coord_up(self):
        selected = self.coord_listbox.curselection()
        if not selected or selected[0] == 0:
            return
        idx = selected[0]
        self.coords[idx - 1], self.coords[idx] = self.coords[idx], self.coords[idx - 1]
        self.update_coord_listbox()
        self.coord_listbox.selection_set(idx - 1)

    def move_coord_down(self):
        selected = self.coord_listbox.curselection()
        if not selected or selected[0] == len(self.coords) - 1:
            return
        idx = selected[0]
        self.coords[idx + 1], self.coords[idx] = self.coords[idx], self.coords[idx + 1]
        self.update_coord_listbox()
        self.coord_listbox.selection_set(idx + 1)

    def clear_coords(self):
        if not self.coords:
            messagebox.showinfo("Sin coordenadas", "No hay coordenadas para limpiar.")
            return
        if messagebox.askyesno("Confirmar", "¿Seguro que deseas limpiar todas las coordenadas?"):
            self.coords.clear()
            self.coord_listbox.delete(0, tk.END)
            messagebox.showinfo("Limpio", "Todas las coordenadas han sido eliminadas.")

    # =========================
    #   TABLA TXT
    # =========================
    def load_txt_files(self):
        folder = filedialog.askdirectory(title="Selecciona la carpeta de archivos TXT")
        if not folder:
            return
        import os
        self.txt_files = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith('.txt')]
        self.txt_table.delete(*self.txt_table.get_children())
        # Guardamos también la ruta absoluta en el "texto" del item para que no se pierda
        for f in self.txt_files:
            item = self.txt_table.insert("", tk.END, values=(os.path.basename(f), "", "No"))
            self.txt_table.item(item, text=f)  # ruta completa en el campo 'text'

    def reset_txt_states(self):
        """Reinicia todos los estados de la tabla TXT a 'No' (no toca las coordenadas)."""
        items = self.txt_table.get_children()
        for item in items:
            archivo, coord, _ = self.txt_table.item(item, "values")
            self.txt_table.item(item, values=(archivo, coord, "No"))
        messagebox.showinfo("Reinicio", "Todos los estados han sido reiniciados a 'No'.")

    def asociar_coord_capturada_a_txt(self):
        """Captura una coordenada y la asigna a la fila seleccionada (sin cambiar estado)."""
        selected = self.txt_table.selection()
        if not selected:
            messagebox.showwarning("Advertencia", "Selecciona un archivo TXT en la tabla.")
            return
        item = selected[0]
        archivo, coord, estado = self.txt_table.item(item, "values")
        messagebox.showinfo("Captura", f"Ubica el mouse para asociar a {archivo} y espera 3 segundos...")
        time.sleep(3)
        x, y = pyautogui.position()
        self.txt_table.item(item, values=(archivo, f"({x}, {y})", estado))

    # =========================
    #   LÓGICA CLAVE
    # =========================
    def agregar_coord_tabla_a_lista(self):
        """
        Inserta la coordenada de la PRIMERA fila en estado 'No' de la tabla TXT
        en la POSICIÓN ELEGIDA por el usuario dentro de la lista base (self.coords).
        NO cambia el estado de la fila.
        """
        item_id, archivo, coord = self._get_first_no_row()
        if not item_id or not coord:
            messagebox.showinfo("Sin coordenadas válidas", "No hay filas 'No' con coordenada para agregar.")
            return

        xy = self._parse_coord(coord)
        if not xy:
            messagebox.showwarning("Advertencia", f"La coordenada de {archivo} no es válida.")
            return

        inject_idx = self._get_injection_index0(len(self.coords))
        self.coords.insert(inject_idx, xy)
        self.update_coord_listbox()
        messagebox.showinfo("Agregado",
                            f"Coordenada {coord} de {archivo} agregada a la posición {inject_idx + 1}.")

    def run_clicks(self):
        veces = simpledialog.askinteger("Repeticiones", "¿Cuántas veces ejecutar las acciones?", initialvalue=1)
        if veces is None or veces <= 0:
            return

        messagebox.showinfo("Inicio", f"La ejecución comenzará en 5 segundos...\nSe harán {veces} iteraciones.")
        time.sleep(5)

        procesadas = 0
        for i in range(veces):
            # Buscar la primera fila en estado "No"
            item_id, archivo, coord_str = self._get_first_no_row()
            if not item_id:
                messagebox.showinfo("Sin filas", "No hay más filas en estado No.")
                break

            xy = self._parse_coord(coord_str)
            if not xy:
                messagebox.showwarning("Advertencia", f"La coordenada de {archivo} no es válida. Se omite.")
                # Marcarla como "Sí" para no ciclar
                archivo_v, coord_v, _ = self.txt_table.item(item_id, "values")
                self.txt_table.item(item_id, values=(archivo_v, coord_v, "Sí"))
                continue

            # ⚡ Crear SIEMPRE una COPIA LIMPIA de las coordenadas base
            coords_to_run = list(self.coords)

            # Usar la posición elegida por el usuario (Spinbox)
            inject_idx = self._get_injection_index0(len(coords_to_run))
            coords_to_run.insert(inject_idx, xy)

            # Mostrar en la lista temporal (indica cuál fue inyectada)
            self._render_temp_coord_list(coords_view=coords_to_run,
                                         injected_idx=inject_idx,
                                         archivo=archivo)

            # Ejecutar clics de la vista temporal
            for c in coords_to_run:
                if (isinstance(c, tuple) and len(c) == 2 and
                    all(isinstance(x, tuple) and len(x) == 2 for x in c)):
                    # Es un rango
                    (x1, y1), (x2, y2) = c
                    pyautogui.moveTo(x1, y1, duration=0.3)
                    pyautogui.mouseDown()
                    pyautogui.moveTo(x2, y2, duration=0.5)
                    pyautogui.mouseUp()
                else:
                    # Punto
                    x, y = c
                    pyautogui.moveTo(x, y, duration=0.3)
                    pyautogui.click()
                time.sleep(0.25)

            # Marcar fila como "Sí"
            archivo_v, coord_v, _ = self.txt_table.item(item_id, "values")
            self.txt_table.item(item_id, values=(archivo_v, coord_v, "Sí"))

            procesadas += 1

            # 🔄 Restaurar lista base original en el listbox (sin dinámicas)
            self.update_coord_listbox()

        messagebox.showinfo("Finalizado", f"Se completaron {procesadas} iteración(es).")

    # =========================
    #   UTILIDADES EXTRAS
    # =========================
    def show_table(self):
        items = self.txt_table.get_children()
        info = []
        for item in items:
            archivo, coord, cargado = self.txt_table.item(item, "values")
            info.append(f"{archivo} | {coord} | {cargado}")
        messagebox.showinfo("Tabla de archivos", "\n".join(info))

    def show_txt_files(self):
        if not hasattr(self, 'txt_files') or not self.txt_files:
            messagebox.showinfo("Sin archivos", "No hay archivos TXT cargados.")
            return
        archivos = '\n'.join(self.txt_files)
        messagebox.showinfo("Archivos TXT", archivos)


# Crear ventana
root = tk.Tk()
app = ClickApp(root)
root.mainloop()
