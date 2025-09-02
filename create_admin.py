import tkinter as tk
from tkinter import messagebox
import mysql.connector

class AdminForm:
    def __init__(self):
        self.conn = mysql.connector.connect(
            host="localhost",  
            user="root",       
            password="",      
            database="squtiel_db" 
        )
        self.cursor = self.conn.cursor()

        self.cursor.execute(''' 
            CREATE TABLE IF NOT EXISTS admin (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) UNIQUE,
                password VARCHAR(255)
            )
        ''')
        self.conn.commit()

    def create_admin(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showerror("Error", "Both fields are required!")
            return

        try:
            self.cursor.execute("INSERT INTO admin (username, password) VALUES (%s, %s)", (username, password))
            self.conn.commit()
            messagebox.showinfo("Success", f"Admin {username} created successfully!")
            self.username_entry.delete(0, tk.END)
            self.password_entry.delete(0, tk.END)
        except mysql.connector.IntegrityError:
            messagebox.showerror("Error", "Admin already exists!")

    def delete_admin_all(self):
        if messagebox.askyesno("Delete All Candidates", "Are you sure you want to delete all candidates?"):
            self.cursor.execute('DELETE FROM admin')
            self.conn.commit()

    def delete_admin_selected(self):
        username = self.username_entry.get()
        self.cursor.execute("SELECT * FROM admin WHERE username = %s", (username,))
        admin = self.cursor.fetchone()
        if admin:
            self.cursor.execute("DELETE FROM admin WHERE username = %s", (username,))
            self.conn.commit()
            messagebox.showinfo("Success", f"Admin '{username}' deleted successfully!")
            self.username_entry.delete(0, tk.END)
            self.password_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Error", f"Admin '{username}' does not exist!")


    def run(self):
        root = tk.Tk()
        root.title("Admin Form")
        root.geometry("500x500")

        root.attributes("-topmost", 1)

    
        root.config(bg="red")

        tk.Label(root, text="Create Admin", font=("Helvetica", 16), bg="red", fg="white", bd=0).pack(pady=10)

        tk.Label(root, text="Username:", bg="black", fg="white").pack()
        self.username_entry = tk.Entry(root)
        self.username_entry.pack(pady=5)

        tk.Label(root, text="Password:", bg="black", fg="white").pack()
        self.password_entry = tk.Entry(root, show="*")
        self.password_entry.pack(pady=5)


        def on_enter(button):
            button.config(bg="darkred", fg="white")

        def on_leave(button):
            button.config(bg="lightgray", fg="black")


        create_button = tk.Button(root, text="Create Admin", width=20, height=2, command=self.create_admin, bg="lightgray")
        create_button.pack(pady=10)
        create_button.bind("<Enter>", lambda e: on_enter(create_button))  
        create_button.bind("<Leave>", lambda e: on_leave(create_button)) 

        delete_selected_button = tk.Button(root, text="Delete Selected Admin", width=20, height=2, command=self.delete_admin_selected, bg="lightgray")
        delete_selected_button.pack(pady=10)
        delete_selected_button.bind("<Enter>", lambda e: on_enter(delete_selected_button))  
        delete_selected_button.bind("<Leave>", lambda e: on_leave(delete_selected_button))  

        delete_all_button = tk.Button(root, text="Delete All Admins", width=20, height=2, command=self.delete_admin_all, bg="lightgray")
        delete_all_button.pack(pady=10)
        delete_all_button.bind("<Enter>", lambda e: on_enter(delete_all_button))  
        delete_all_button.bind("<Leave>", lambda e: on_leave(delete_all_button))  

        root.mainloop()
        self.conn.close()


if __name__ == "__main__":
    app = AdminForm()
    app.run()
