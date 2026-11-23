import mongodb as db
import tkinter as tk
from tkinter import ttk, messagebox

class SFPLDataApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SFPL MongoDB Data Viewer")
        self.root.geometry("1000x600")

        self.limit = 50
        self.offset = 0
        self.selected_patron_id = None

        pts, libs, notifs = db.fetch_lookup_options()
        self.pt_to_code = {str(defn): code for code, defn in pts}
        self.lib_to_code = {str(defn): code for code, defn in libs}
        self.notif_to_code = {str(defn): code for code, defn in notifs}

        self._build_search_bar()
        self._build_table()
        self._build_pagination()
        self._build_form()
        self.load_table()

        print(f"App Successfully Loaded: {len(pts)} patron types, {len(libs)} library, {len(notifs)} notification types.")

    def _build_table(self):
        frame = ttk.Frame(self.root, padding=10)
        frame.pack(fill="both", expand=True)

        cols = ("patron_id", "patron_type", "home_library", "notification",
                "age_range", "checkouts", "renewals", "year_registered")
        headers = ("ID", "Patron Type", "Home Library", "Notification",
                "Age Range", "Checkouts", "Renewals", "Registered")

        self.tree = ttk.Treeview(frame, columns=cols, show="headings", height=18)
        for col, text in zip(cols, headers):
            self.tree.heading(col, text=text)
            width = 75 if col in ("patron_id", "checkouts", "renewals", "year_registered") else 145
            self.tree.column(col, width=width, anchor="center")

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self.on_row_select)

    def _build_pagination(self):
        frame = ttk.Frame(self.root, padding=(10, 0, 10, 10))
        frame.pack(fill="x")

        ttk.Button(frame, text="< Previous 50", command=self.prev_page).pack(side="left")
        self.page_label = ttk.Label(frame, text="Page 1")
        self.page_label.pack(side="left", padx=15)
        ttk.Button(frame, text="Next 50 >", command=self.next_page).pack(side="left")

    def load_table(self, search_id=None):
        self.tree.delete(*self.tree.get_children())
        rows = db.fetch_patrons(limit=self.limit, offset=self.offset, search_id=search_id)

        for r in rows:
            self.tree.insert("", "end", values=(
                r["patron_id"], r["patron_type"], r["home_library"], r["notification"],
                r["age_range"], r["checkouts"], r["renewals"], r["year_registered"]
            ))

        if search_id is not None:
            self.page_label.config(text=f"Search result for Patron ID {search_id} ({len(rows)} found)")
        else:
            page_num = (self.offset // self.limit) + 1
            self.page_label.config(text=f"Page {page_num} (Rows {self.offset + 1} - {self.offset + len(rows)})")

    def search_patron(self):
        raw_id = self.search_var.get().strip()
        if not raw_id.isdigit():
            messagebox.showwarning("Invalid ID", "Please enter a numeric Patron ID.")
            return
        self.load_table(search_id=int(raw_id))

    def reset_search(self):
        self.search_var.set("")
        self.offset = 0
        self.load_table()

    def on_row_select(self, _event):
        selected = self.tree.selection()
        if not selected:
            return
        vals = self.tree.item(selected[0], "values")
        self.selected_patron_id = int(vals[0])
        self.pt_var.set(vals[1])
        self.lib_var.set(vals[2])
        self.notif_var.set(vals[3])
        self.age_var.set(vals[4])
        self.checkouts_var.set(vals[5])
        self.renewals_var.set(vals[6])
        self.year_var.set(vals[7])
    
    def next_page(self):
        self.offset += self.limit
        self.load_table()

    def prev_page(self):
        if self.offset >= self.limit:
            self.offset -= self.limit
            self.load_table()

    def _build_search_bar(self):
        frame = ttk.Frame(self.root, padding=(10, 10, 10, 0))
        frame.pack(fill="x")

        ttk.Label(frame, text="Search by Patron ID:").pack(side="left", padx=(0, 5))
        self.search_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.search_var, width=18).pack(side="left", padx=5)

        ttk.Button(frame, text="Search", command=self.search_patron).pack(side="left", padx=5)
        ttk.Button(frame, text="Reset", command=self.reset_search).pack(side="left", padx=5)

    def _build_form(self):
        form = ttk.LabelFrame(self.root, text="Add / Edit Patron Record", padding=10)
        form.pack(fill="x", padx=10, pady=(0, 10))

        # Row 0: 3NF Foreign Key Dropdowns
        ttk.Label(form, text="Patron Type:").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        self.pt_var = tk.StringVar()
        ttk.Combobox(form, textvariable=self.pt_var, values=list(self.pt_to_code.keys()),
                     state="readonly", width=22).grid(row=0, column=1, padx=5, pady=4)

        ttk.Label(form, text="Home Library:").grid(row=0, column=2, sticky="w", padx=5, pady=4)
        self.lib_var = tk.StringVar()
        ttk.Combobox(form, textvariable=self.lib_var, values=list(self.lib_to_code.keys()),
                     state="readonly", width=25).grid(row=0, column=3, padx=5, pady=4)

        ttk.Label(form, text="Notification:").grid(row=0, column=4, sticky="w", padx=5, pady=4)
        self.notif_var = tk.StringVar()
        ttk.Combobox(form, textvariable=self.notif_var, values=list(self.notif_to_code.keys()),
                     state="readonly", width=18).grid(row=0, column=5, padx=5, pady=4)

        # Row 1: Patron Attributes
        ttk.Label(form, text="Age Range:").grid(row=1, column=0, sticky="w", padx=5, pady=4)
        self.age_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.age_var, width=25).grid(row=1, column=1, padx=5, pady=4)

        ttk.Label(form, text="Checkouts:").grid(row=1, column=2, sticky="w", padx=5, pady=4)
        self.checkouts_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.checkouts_var, width=28).grid(row=1, column=3, padx=5, pady=4)

        ttk.Label(form, text="Renewals:").grid(row=1, column=4, sticky="w", padx=5, pady=4)
        self.renewals_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.renewals_var, width=21).grid(row=1, column=5, padx=5, pady=4)

        # Row 2: Year Registered + Action Buttons
        ttk.Label(form, text="Year Registered:").grid(row=2, column=0, sticky="w", padx=5, pady=4)
        self.year_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.year_var, width=25).grid(row=2, column=1, padx=5, pady=4)

        btn_frame = ttk.Frame(form)
        btn_frame.grid(row=2, column=2, columnspan=4, sticky="e", padx=5, pady=4)

        ttk.Button(btn_frame, text="Add New", command=self.add_record).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Update Selected", command=self.update_record).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Delete Selected", command=self.delete_record).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Clear", command=self.clear_form).pack(side="left", padx=5)

    def _get_validated_inputs(self):
        if not (self.pt_var.get() and self.lib_var.get() and self.notif_var.get()):
            raise ValueError("Select a Patron Type, Home Library, and Notification option.")
        if not self.age_var.get().strip():
            raise ValueError("Age Range cannot be empty.")
        return (
            self.pt_to_code[self.pt_var.get()],
            self.lib_to_code[self.lib_var.get()],
            self.notif_to_code[self.notif_var.get()],
            self.age_var.get().strip(),
            int(self.checkouts_var.get()),
            int(self.renewals_var.get()),
            int(self.year_var.get()),
        )

    def add_record(self):
        try:
            args = self._get_validated_inputs()
            new_id = db.insert_patron(*args)
            messagebox.showinfo("Added", f"Inserted new patron (ID: {new_id}).")
            self.clear_form()
            self.load_table()
        except ValueError as ve:
            messagebox.showwarning("Invalid Input", f"Check your inputs (numbers required for checkouts/renewals/year).\n\nDetails: {ve}")
        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    def update_record(self):
        if self.selected_patron_id is None:
            messagebox.showwarning("No Selection", "Click a patron row in the table first.")
            return
        try:
            args = self._get_validated_inputs()
            db.update_patron(self.selected_patron_id, *args)
            messagebox.showinfo("Updated", f"Updated Patron ID {self.selected_patron_id}.")
            self.load_table()
        except ValueError as ve:
            messagebox.showwarning("Invalid Input", f"Check your inputs.\n\nDetails: {ve}")
        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    def delete_record(self):
        if self.selected_patron_id is None:
            messagebox.showwarning("No Selection", "Click a patron row in the table first.")
            return
        if messagebox.askyesno("Confirm Delete", f"Permanently delete Patron ID {self.selected_patron_id}?"):
            try:
                db.delete_patron(self.selected_patron_id)
                messagebox.showinfo("Deleted", f"Deleted Patron ID {self.selected_patron_id}.")
                self.clear_form()
                self.load_table()
            except Exception as e:
                messagebox.showerror("Database Error", str(e))

    def clear_form(self):
        self.selected_patron_id = None
        for var in (self.pt_var, self.lib_var, self.notif_var,
                    self.age_var, self.checkouts_var, self.renewals_var, self.year_var):
            var.set("")


if __name__ == "__main__":
    root = tk.Tk()
    app = SFPLDataApp(root)
    root.mainloop()