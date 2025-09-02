import tkinter as tk
from tkinter import Listbox, ttk
from tkinter import font
from datetime import datetime
import mysql.connector
from tkinter import messagebox
from PIL import Image, ImageTk
from create_admin import AdminForm

class VotingSystem:
    # FUNCTIONS
    def __init__(self):
        self.conn = mysql.connector.connect(
            host="localhost",  
            user="root",       
            password="",      
            database="squtiel_db" 
        )
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.history = []
        self.voters = {}
        self.announcement = ""
        self.voting_type = ""

    def create_tables(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS candidates (
                                        id INT AUTO_INCREMENT PRIMARY KEY,
                                        name VARCHAR(255),
                                        party VARCHAR(255),
                                        position VARCHAR(255),
                                        description TEXT,
                                        platform TEXT)''')
        
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                                        id INT AUTO_INCREMENT PRIMARY KEY,
                                        first_name VARCHAR(255),
                                        middle_name VARCHAR(255),
                                        last_name VARCHAR(255),
                                        age INT,
                                        address TEXT,
                                        contact_number VARCHAR(15),
                                        username VARCHAR(255) UNIQUE,
                                        password VARCHAR(255))''')
                
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS voter_logs (
                                        id INT AUTO_INCREMENT PRIMARY KEY,
                                        name VARCHAR(255),
                                        candidate_id INT,
                                        user_id INT,
                                        vote_date DATETIME,
                                        FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE,
                                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE)''')
                
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS activity_logs (
                                        id INT AUTO_INCREMENT PRIMARY KEY,
                                        action VARCHAR(255),
                                        timestamp DATETIME,
                                        candidate_id INT,
                                        user_id INT,
                                        FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE,
                                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE)''')
                
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS admin (
                                        id INT AUTO_INCREMENT PRIMARY KEY,
                                        username VARCHAR(255) UNIQUE,
                                        password VARCHAR(255))''')
                
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS announcements (
                                    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                                    announcement TEXT NOT NULL,
                                    admin_id INT NOT NULL,
                                    FOREIGN KEY (admin_id) REFERENCES admin(id) ON DELETE CASCADE
                                                        )
                                                    ''')

                
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS type_of_election (
                                        id INT AUTO_INCREMENT PRIMARY KEY,
                                        election_type VARCHAR(255),
                                        admin_id INT,
                                        FOREIGN KEY (admin_id) REFERENCES admin(id) ON DELETE CASCADE)''')
                
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS voting_result (
                                        id INT AUTO_INCREMENT PRIMARY KEY,
                                        candidate_name VARCHAR(255),
                                        position VARCHAR(255),
                                        votes INT,
                                        candidate_id INT,
                                        FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE)''')
        self.conn.commit()

    def close_db(self):
        if self.conn:
            self.conn.commit()
            self.conn.close()
            print("Database connection closed.")

    def set_announcement(self, announcement_text, admin_id):
        self.announcement = announcement_text
        self.cursor.execute('''REPLACE INTO announcements (announcement, admin_id) VALUES (%s, %s)''',
                    (announcement_text, admin_id))

        self.conn.commit()
        self.add_activity_log("New announcement set", admin_id=admin_id)

    def set_voting_type(self, voting_type_text, admin_id):
        self.voting_type = voting_type_text
        self.cursor.execute('''REPLACE INTO type_of_election (election_type, admin_id) VALUES (%s, %s)''', 
                    (voting_type_text, admin_id))

        self.conn.commit()
        self.add_activity_log("Voting type set", admin_id=admin_id)

    def add_candidate(self, name, party, position, description, platform, user_id):
        self.cursor.execute('''INSERT INTO candidates (name, party, position, description, platform)
                               VALUES (%s, %s, %s, %s, %s)''', (name, party, position, description, platform))
        self.conn.commit()
        self.add_activity_log(f"Added candidate: {name}", user_id=user_id)

    def delete_candidate(self, candidate_id, user_id):
        candidate = self.cursor.execute('''SELECT name FROM candidates WHERE id = %s''', (candidate_id,))
        candidate = self.cursor.fetchone()
        if candidate:
            self.cursor.execute('''DELETE FROM candidates WHERE id = %s''', (candidate_id,))
            self.conn.commit()
            self.add_activity_log(f"Deleted candidate: {candidate[0]}", user_id=user_id)

    def delete_all_candidates(self, user_id):
        if messagebox.askyesno("Delete All Candidates", "Are you sure you want to delete all candidates%s"):
            self.cursor.execute('''DELETE FROM candidates''')
            self.conn.commit()
            self.add_activity_log("Deleted all candidates", user_id=user_id)

    def update_candidate(self, candidate_id, new_name=None, new_party=None, new_position=None, new_description=None,
                         new_platform=None, user_id=None):
        candidate = self.cursor.execute('''SELECT * FROM candidates WHERE id = %s''', (candidate_id,))
        candidate = self.cursor.fetchone()
        if candidate:
            new_name = new_name if new_name else candidate[1]
            new_party = new_party if new_party else candidate[2]
            new_position = new_position if new_position else candidate[3]
            new_description = new_description if new_description else candidate[4]
            new_platform = new_platform if new_platform else candidate[5]
            self.cursor.execute('''UPDATE candidates SET name = %s, party = %s, position = %s, description = %s, platform = %s
                                   WHERE id = %s''',
                                (new_name, new_party, new_position, new_description, new_platform, candidate_id))
            self.conn.commit()
            self.add_activity_log(f"Updated candidate: {candidate[1]} to {new_name}", user_id=user_id)
            return candidate, (new_name, new_party, new_position, new_description, new_platform)
        return None, None

    def add_activity_log(self, action, user_id=None, admin_id=None, candidate_id=None):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute('''INSERT INTO activity_logs (action, timestamp, user_id, candidate_id)
                               VALUES (%s, %s, %s, %s)''', (action, timestamp, user_id or admin_id, candidate_id))
        self.conn.commit()
        user_full_name = self.get_user_full_name(user_id or admin_id)
        candidate_name, _ = self.get_candidate_name_position(candidate_id)
        if user_full_name and candidate_name:
            self.history.append(f"{action} by {user_full_name} on {candidate_name} at {timestamp}")
        elif user_full_name:
            self.history.append(f"{action} by {user_full_name} at {timestamp}")
        else:
            self.history.append(f"{action} at {timestamp}")

    def vote(self, voter_name, candidate_id, user_id):
        candidate = self.cursor.execute('''SELECT * FROM candidates WHERE id = %s''', (candidate_id,))
        candidate = self.cursor.fetchone()
        if candidate:
            position = candidate[3]
            existing_vote = self.cursor.execute(
                '''SELECT * FROM voter_logs WHERE name = %s AND candidate_id IN (SELECT id FROM candidates WHERE position = %s)''',
                (voter_name, position))
            existing_vote = self.cursor.fetchone()
            if existing_vote:
                return f"You have already voted for a candidate in the position: {position}."
            vote_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.cursor.execute('''INSERT INTO voter_logs (name, candidate_id, user_id, vote_date)
                                   VALUES (%s, %s, %s, %s)''', (voter_name, candidate_id, user_id, vote_date))
            self.conn.commit()
            self.add_activity_log(f"Voted for: {candidate[1]} by {voter_name}", user_id=user_id, candidate_id=candidate_id)
            if voter_name not in self.voters:
                self.voters[voter_name] = []
            self.voters[voter_name].append({
                'Name': candidate[1],
                'Party': candidate[2],
                'Position': candidate[3],
                'Vote Date': vote_date
            })
            return f"Vote for '{candidate[1]}' by {voter_name} recorded."
        return f"Candidate not found."

    def unvote(self, voter_name, candidate_id, user_id):
        self.cursor.execute('''DELETE FROM voter_logs WHERE name = %s AND candidate_id = %s''', (voter_name, candidate_id))
        self.conn.commit()
        self.add_activity_log(f"Unvoted for candidate ID: {candidate_id} by {voter_name}", user_id=user_id, candidate_id=candidate_id)
        if voter_name in self.voters:
            self.voters[voter_name] = [vote for vote in self.voters[voter_name] if vote['Name'] != candidate_id]
            return f"Vote for candidate ID: {candidate_id} by {voter_name} removed."
        return f"Vote not found."

    def get_activity_logs(self):
        logs = self.cursor.execute('''SELECT action, timestamp, user_id, candidate_id FROM activity_logs''')
        logs = self.cursor.fetchall()
        display_logs = []
        for log in logs:
            user_full_name = self.get_user_full_name(log[2])
            candidate_name, _ = self.get_candidate_name_position(log[3])
            if user_full_name and candidate_name:
                display_logs.append(f"{log[0]} by {user_full_name} on {candidate_name} at {log[1]}")
            elif user_full_name:
                display_logs.append(f"{log[0]} by {user_full_name} at {log[1]}")
            else:
                display_logs.append(f"{log[0]} at {log[1]}")
        return "\n".join(display_logs)

    def get_voter_logs(self):
        logs = self.cursor.execute('''SELECT name, candidate_id, user_id, vote_date FROM voter_logs''')
        logs = self.cursor.fetchall()
        display_logs = []
        for log in logs:
            user_full_name = self.get_user_full_name(log[2])
            candidate_name, candidate_position = self.get_candidate_name_position(log[1])
            if user_full_name and candidate_name and candidate_position:
                display_logs.append(
                    f"Name: {user_full_name}, Candidate: {candidate_name}, Position: {candidate_position}, Vote Date: {log[3]}")
        return "\n".join(display_logs)

    def get_voting_results(self):
        results = self.cursor.execute('''SELECT candidates.name, candidates.position, COUNT(voter_logs.id) as votes
                                             FROM candidates
                                             LEFT JOIN voter_logs ON candidates.id = voter_logs.candidate_id
                                             GROUP BY candidates.id
                                             ORDER BY votes DESC''')
        results = self.cursor.fetchall()
        grouped_results = {}
        for result in results:
            position = result[1]
            if position not in grouped_results:
                grouped_results[position] = []
            grouped_results[position].append(result)
        return grouped_results

    def get_announcement(self):
        announcements_records = self.cursor.execute(
            '''SELECT announcement FROM announcements ORDER BY id DESC LIMIT 1''')
        announcements_records = self.cursor.fetchone()
        return announcements_records[0] if announcements_records else ""

    def get_voting_type(self):
        voting_type_record = self.cursor.execute(
            '''SELECT election_type FROM type_of_election ORDER BY id DESC LIMIT 1''')
        voting_type_record = self.cursor.fetchone()
        return voting_type_record[0] if voting_type_record else ""

    def get_leading_candidates(self):
        results = self.get_voting_results()
        leading_candidates = {}
        for position, candidates in results.items():
            leading_candidates[position] = candidates[0]
        return leading_candidates

    def register_user(self, first_name, middle_name, last_name, age, address, contact_number, username, password):
        try:
            self.cursor.execute('''INSERT INTO users (first_name, middle_name, last_name, age, address, contact_number, username, password)
                                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
                                (first_name, middle_name, last_name, age, address, contact_number, username, password))
            self.conn.commit()
            user_table_name = f"voter_{username}"
            self.cursor.execute(f'''CREATE TABLE IF NOT EXISTS {user_table_name} (
                                        id INTEGER PRIMARY KEY,
                                        name TEXT,
                                        contact_number TEXT,
                                        candidate_id INTEGER,
                                        vote_date TEXT,
                                        FOREIGN KEY(candidate_id) REFERENCES candidates(id))''')
            self.conn.commit()
            return True
        except mysql.connector.IntegrityError:
            return False

    def sort_candidates(self, category):
        if category not in ["name", "party", "position"]:
            raise ValueError("Invalid category. Must be one of ['name', 'party', 'position']")
        candidates = self.cursor.execute(f'''SELECT * FROM candidates ORDER BY {category}''')
        candidates = self.cursor.fetchall()
        return candidates
    
    

    def login_user(self, username, password):
        user = self.cursor.execute('''SELECT * FROM users WHERE username = %s AND password = %s''',
                                   (username, password))
        user = self.cursor.fetchone()
        return user

    def login_admin(self, username, password):
        admin = self.cursor.execute('''SELECT * FROM admin WHERE username = %s AND password = %s''',
                                    (username, password))
        admin = self.cursor.fetchone()
        return admin

    def get_user_full_name(self, user_id):
        user_info = self.cursor.execute('''SELECT first_name, middle_name, last_name FROM users WHERE id = %s''',
                                        (user_id,))
        user_info = self.cursor.fetchone()
        if user_info:
            return f"{user_info[0]} {user_info[1]} {user_info[2]}"
        return None

    def get_candidate_name_position(self, candidate_id):
        candidate_info = self.cursor.execute('''SELECT name, position FROM candidates WHERE id = %s''',
                                             (candidate_id,))
        candidate_info = self.cursor.fetchone()
        if candidate_info:
            return candidate_info[0], candidate_info[1]
        return None, None

    def add_activity_log(self, action, user_id=None, admin_id=None, candidate_id=None):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute('''INSERT INTO activity_logs (action, timestamp, user_id, candidate_id)
                               VALUES (%s, %s, %s, %s)''', (action, timestamp, user_id or admin_id, candidate_id))
        self.conn.commit()
        user_full_name = self.get_user_full_name(user_id or admin_id)
        candidate_name, _ = self.get_candidate_name_position(candidate_id)
        if user_full_name and candidate_name:
            self.history.append(f"{action} by {user_full_name} on {candidate_name} at {timestamp}")
        elif user_full_name:
            self.history.append(f"{action} by {user_full_name} at {timestamp}")
        else:
            self.history.append(f"{action} at {timestamp}")

    def add_voter_log(self, voter_name, candidate_id, user_id):
        vote_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute('''INSERT INTO voter_logs (name, candidate_id, user_id, vote_date)
                               VALUES (%s, %s, %s, %s)''', (voter_name, candidate_id, user_id, vote_date))
        self.conn.commit()
        candidate_name, candidate_position = self.get_candidate_name_position(candidate_id)
        if candidate_name and candidate_position:
            self.voters[voter_name].append({
                'Name': candidate_name,
                'Position': candidate_position,
                'Vote Date': vote_date
            })
            return f"Vote for '{candidate_name}' by {voter_name} recorded."
        return f"Candidate not found."

    def get_activity_logs(self):
        logs = self.cursor.execute('''SELECT action, timestamp, user_id, candidate_id FROM activity_logs''')
        logs = self.cursor.fetchall()
        display_logs = []
        for log in logs:
            user_full_name = self.get_user_full_name(log[2])
            candidate_name, _ = self.get_candidate_name_position(log[3])
            if user_full_name and candidate_name:
                display_logs.append(f"{log[0]} by {user_full_name} on {candidate_name} at {log[1]}")
            elif user_full_name:
                display_logs.append(f"{log[0]} by {user_full_name} at {log[1]}")
            else:
                display_logs.append(f"{log[0]} at {log[1]}")
        return "\n".join(display_logs)

    def get_voter_logs(self):
        logs = self.cursor.execute('''SELECT name, candidate_id, user_id, vote_date FROM voter_logs''')
        logs = self.cursor.fetchall()
        display_logs = []
        for log in logs:
            user_full_name = self.get_user_full_name(log[2])
            candidate_name, candidate_position = self.get_candidate_name_position(log[1])
            if user_full_name and candidate_name and candidate_position:
                display_logs.append(f"Name: {user_full_name}, Candidate: {candidate_name}, Position: {candidate_position}, Vote Date: {log[3]}")
        return "\n".join(display_logs)

    def get_voting_results(self):
        results = self.cursor.execute('''SELECT candidates.name, candidates.position, COUNT(voter_logs.id) as votes
                                         FROM candidates
                                         LEFT JOIN voter_logs ON candidates.id = voter_logs.candidate_id
                                         GROUP BY candidates.id
                                         ORDER BY votes DESC''')
        results = self.cursor.fetchall()
        grouped_results = {}
        for result in results:
            position = result[1]
            if position not in grouped_results:
                grouped_results[position] = []
            grouped_results[position].append(result)
        return grouped_results

    def get_announcement(self):
        announcements_records = self.cursor.execute('''SELECT announcement FROM announcements ORDER BY id DESC LIMIT 1''')
        announcements_records = self.cursor.fetchone()
        return announcements_records[0] if announcements_records else ""

    def get_voting_type(self):
        voting_type_record = self.cursor.execute('''SELECT election_type FROM type_of_election ORDER BY id DESC LIMIT 1''')
        voting_type_record = self.cursor.fetchone()
        return voting_type_record[0] if voting_type_record else ""

    def get_leading_candidates(self):
        results = self.get_voting_results()
        leading_candidates = {}
        for position, candidates in results.items():
            leading_candidates[position] = candidates[0]
        return leading_candidates

    def register_user(self, first_name, middle_name, last_name, age, address, contact_number, username, password):
        try:
            self.cursor.execute('''INSERT INTO users (first_name, middle_name, last_name, age, address, contact_number, username, password)
                                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''', (first_name, middle_name, last_name, age, address, contact_number, username, password))
            self.conn.commit()
            user_table_name = f"voter_{username}"
            self.cursor.execute(f'''CREATE TABLE IF NOT EXISTS {user_table_name} (
                                    id INTEGER PRIMARY KEY,
                                    name TEXT,
                                    contact_number TEXT,
                                    candidate_id INTEGER,
                                    vote_date TEXT,
                                    FOREIGN KEY(candidate_id) REFERENCES candidates(id))''')
            self.conn.commit()
            return True
        except mysql.connector.IntegrityError:
            return False

def main():
    voting_system = VotingSystem()

    # Function to update both candidate lists and voter information
    def update_all_lists():
        update_candidates_list()
        update_voter_candidates_list()
        update_voters_list()

    def update_candidates_list():
        candidates_list.delete(*candidates_list.get_children())
        candidates = voting_system.cursor.execute('''SELECT * FROM candidates''')
        candidates = voting_system.cursor.fetchall()
        for candidate in candidates:
            candidates_list.insert('', 'end', values=(candidate[0], candidate[1], candidate[2], candidate[3]))

    def update_voter_candidates_list():
        voter_candidates_list.delete(*voter_candidates_list.get_children())
        for candidate in voting_system.sort_candidates('name'):
            voter_candidates_list.insert('', 'end', values=(candidate[0], candidate[1], candidate[2], candidate[3]))

    def update_voters_list():
        voters_list.delete(1.0, tk.END)
        voters_list.insert(tk.END, voting_system.get_voter_logs())

    def load_announcement():
        announcement = voting_system.get_announcement()
        announcement_list.delete(1.0, tk.END)
        announcement_list.insert(tk.END, announcement)
        voter_announcement_text.delete(1.0, tk.END)
        voter_announcement_text.insert(tk.END, announcement)

    def load_voting_type():
        voting_type = voting_system.get_voting_type()
        voting_type_entry.delete("1.0", tk.END)
        voting_type_entry.insert(tk.END, voting_type)
        voting_type_label.config(text=voting_type)

    # Login Frame
    def show_login_frame():
        register_frame.pack_forget()
        candidates_frame.pack_forget()
        voter_frame.pack_forget()
        login_frame.pack(fill='both', expand=True)

    # Register Frame
    def show_register_frame():
        login_frame.pack_forget()
        candidates_frame.pack_forget()
        voter_frame.pack_forget()
        register_frame.pack(fill='both', expand=True)

    # Admin Frame
    def show_candidates_frame():
        update_candidates_list()
        candidates_frame.pack(fill='both', expand=True)
        login_frame.pack_forget()
        register_frame.pack_forget()
        voter_frame.pack_forget()

    # Voter Frame
    def show_voter_frame():
        voter_frame.pack(fill='both', expand=True)
        login_frame.pack_forget()
        register_frame.pack_forget()
        candidates_frame.pack_forget()
        refresh()

    def update_voting_type_label():
        voting_type_label.config(text=voting_system.voting_type if voting_system.voting_type else "VOTER INTERFACE")

    # Login Function
    def login():
        username = username_entry.get()
        password = password_entry.get()
        user = voting_system.login_user(username, password)
        admin = voting_system.login_admin(username, password)
        if user:
            show_voter_frame()
            update_voting_type_label()
        else:
            if admin:
                show_candidates_frame()
            else:
                messagebox.showerror("Login Failed", "Invalid username or password")

    # Register Function
    def register():
        first_name = first_name_entry.get()
        middle_name = middle_name_entry.get()
        last_name = last_name_entry.get()
        age = age_entry.get()
        address = address_entry.get()
        contact_number = contact_number_entry.get()
        username = reg_username_entry.get()
        password = reg_password_entry.get()
        if not (first_name and middle_name and last_name and age and address and contact_number and username and password):
            messagebox.showinfo("Registration Failure", "Please fill in all the fields")
            return
        if voting_system.register_user(first_name, middle_name, last_name, age, address, contact_number, username, password):
            messagebox.showinfo("Registration Successful", "Account created successfully")
            show_login_frame()
        else:
            messagebox.showerror("Registration Failed", "Username already exists")

    def add_candidate():
        name = name_entry.get()
        party = party_entry.get()
        position = position_entry.get()
        description = description_entry.get("1.0", tk.END).strip()
        platform = platform_entry.get("1.0", tk.END).strip()
        user_id = voting_system.login_user(username_entry.get(), password_entry.get())[0]
        if name and party and position and description and platform:
            voting_system.add_candidate(name, party, position, description, platform, user_id)
            refresh()
        else:
            messagebox.showwarning("Input Error", "Please fill in all fields.")

    def delete_candidate():
        selected_item = candidates_list.selection()[0]
        candidate_id = candidates_list.item(selected_item)['values'][0]
        candidate_name = candidates_list.item(selected_item)['values'][1]
        user_id = voting_system.login_user(username_entry.get(), password_entry.get())[0]
        if messagebox.askyesno("Delete Candidate", f"Are you sure you want to delete '{candidate_name}'%s"):
            voting_system.delete_candidate(candidate_id, user_id)
            refresh()

    def delete_all_candidates():
        user_id = voting_system.login_user(username_entry.get(), password_entry.get())[0]
        if messagebox.askyesno("Delete All Candidates", "Are you sure you want to delete all candidates%s"):
            voting_system.delete_all_candidates(user_id)
            refresh()

    def update_candidate():
        selected_item = candidates_list.selection()[0]
        candidate_id = candidates_list.item(selected_item)['values'][0]
        new_name = name_entry.get()
        new_party = party_entry.get()
        new_position = position_entry.get()
        new_description = description_entry.get("1.0", tk.END).strip()
        new_platform = platform_entry.get("1.0", tk.END).strip()
        user_id = voting_system.login_user(username_entry.get(), password_entry.get())[0]
        old_candidate_info, new_candidate_info = voting_system.update_candidate(candidate_id, new_name, new_party,
                                                                                new_position, new_description,
                                                                                new_platform, user_id)
        if old_candidate_info and new_candidate_info:
            refresh()
        else:
            messagebox.showerror("Update Failed", "Unable to update candidate.")

    def sort_candidates():
        category = category_combobox.get()
        sorted_candidates = voting_system.sort_candidates(category)
        candidates_list.delete(*candidates_list.get_children())
        for candidate in sorted_candidates:
            candidates_list.insert('', 'end', values=(candidate[0], candidate[1], candidate[2], candidate[3]))
        update_history_list()

    def manage_admin():
        adminform = AdminForm()
        adminform.run()

    def refresh():
        name_entry.delete(0, tk.END)
        party_entry.delete(0, tk.END)
        position_entry.delete(0, tk.END)
        description_entry.delete("1.0", tk.END)
        platform_entry.delete("1.0", tk.END)
        category_combobox.set('')
        update_all_lists()
        update_vote_summary()
        update_voting_results()
        update_history_list()
        update_announcement()
        update_voting_type_label()

    def update_history_list():
        history_list.delete(1.0, tk.END)
        history_list.insert(tk.END, voting_system.get_activity_logs())

    def vote():
        user = voting_system.login_user(username_entry.get(), password_entry.get())
        if user:
            voter_name = f"{user[1]} {user[2]} {user[3]}"
            user_id = user[0]
            try:
                selected_item = voter_candidates_list.selection()[0]
                candidate_id = voter_candidates_list.item(selected_item)['values'][0]
                voter_candidates_list.tag_configure('voted', background='lightblue')
                voter_candidates_list.item(selected_item, tags=('voted',))
                result = voting_system.vote(voter_name, candidate_id, user_id)
                messagebox.showinfo("Vote", result)
                refresh()
            except IndexError:
                messagebox.showwarning("Vote", "Please select a candidate before voting.")
        else:
            messagebox.showwarning("Vote", "Please log in before voting.")

    def unvote():
        user = voting_system.login_user(username_entry.get(), password_entry.get())
        if user:
            voter_name = f"{user[1]} {user[2]} {user[3]}"
            user_id = user[0]
            try:
                selected_item = voter_candidates_list.selection()[0]
                candidate_id = voter_candidates_list.item(selected_item)['values'][0]
                result = voting_system.unvote(voter_name, candidate_id, user_id)
                messagebox.showinfo("Unvote", result)
                refresh()
            except IndexError:
                messagebox.showwarning("Unvote", "Please select a candidate before unvoting.")
        else:
            messagebox.showwarning("Unvote", "Please log in before unvoting.")

    def view_description():
        selected_item = voter_candidates_list.selection()[0]
        candidate_id = voter_candidates_list.item(selected_item)['values'][0]
        candidate = voting_system.cursor.execute('''SELECT description FROM candidates WHERE id = %s''',
                                                 (candidate_id,))
        candidate = voting_system.cursor.fetchall()
        if candidate:
            voter_description_text.delete(1.0, tk.END)
            voter_description_text.insert(tk.END, candidate[0])

    def view_platform():
        selected_item = voter_candidates_list.selection()[0]
        candidate_id = voter_candidates_list.item(selected_item)['values'][0]
        candidate = voting_system.cursor.execute('''SELECT platform FROM candidates WHERE id = %s''',
                                                 (candidate_id,))
        candidate = voting_system.cursor.fetchone()
        if candidate:
            voter_platform_text.delete(1.0, tk.END)
            voter_platform_text.insert(tk.END, candidate[0])

    def view_description1():
        selected_item = candidates_list.selection()[0]
        candidate_id = candidates_list.item(selected_item)['values'][0]
        candidate = voting_system.cursor.execute('''SELECT description FROM candidates WHERE id = %s''',
                                                 (candidate_id,))
        candidate = voting_system.cursor.fetchone()
        if candidate:
            description_text.delete(1.0, tk.END)
            description_text.insert(tk.END, candidate[0])

    def view_platform1():
        selected_item = candidates_list.selection()[0]
        candidate_id = candidates_list.item(selected_item)['values'][0]
        candidate = voting_system.cursor.execute('''SELECT platform FROM candidates WHERE id = %s''',
                                                 (candidate_id,))
        candidate = voting_system.cursor.fetchone()
        if candidate:
            platform_text.delete(1.0, tk.END)
            platform_text.insert(tk.END, candidate[0])

    def update_vote_summary():
        user = voting_system.login_user(username_entry.get(), password_entry.get())
        if user:
            voter_name = f"{user[1]} {user[2]} {user[3]}"
            votes = voting_system.cursor.execute('''SELECT candidates.name, candidates.position, voter_logs.vote_date
                                                            FROM voter_logs
                                                            JOIN candidates ON voter_logs.candidate_id = candidates.id
                                                            WHERE voter_logs.name = %s''', (voter_name,))
            votes = voting_system.cursor.fetchall()
            voter_summary_text.delete(1.0, tk.END)
            for vote in votes:
                voter_summary_text.insert(tk.END, f"Name: {vote[0]}, Position: {vote[1]}, Vote Date: {vote[2]}\n")
        else:
            voter_summary_text.delete(1.0, tk.END)

    def update_voting_results():
        results = voting_system.get_voting_results()
        voting_results_list.delete(1.0, tk.END)
        for position, candidates in results.items():
            voting_results_list.insert(tk.END, f"Position: {position}\n")
            for candidate in candidates:
                voting_results_list.insert(tk.END, f"Name: {candidate[0]}, Votes: {candidate[2]}\n")
            voting_results_list.insert(tk.END, "\n")

    def set_announcement():
        announcement_text = announcement_entry.get("1.0", tk.END).strip()
        admin_id = voting_system.login_admin(username_entry.get(), password_entry.get())[0]
        voting_system.set_announcement(announcement_text, admin_id)
        announcement_list.delete(1.0, tk.END)
        announcement_list.insert(tk.END, announcement_text)
        refresh()

    def update_announcement():
        announcement_list.delete(1.0, tk.END)
        announcement_list.insert(tk.END, voting_system.get_announcement())
        voter_announcement_text.delete(1.0, tk.END)
        voter_announcement_text.insert(tk.END, voting_system.announcement)
        refresh()

    def set_voting_type():
        voting_type_text = voting_type_entry.get("1.0", tk.END).strip()
        admin_id = voting_system.login_admin(username_entry.get(), password_entry.get())[0]
        voting_system.set_voting_type(voting_type_text, admin_id)
        update_voting_type_label()
        refresh()

    def sort_voter_candidates():
        category = voter_category_combobox.get()
        sorted_candidates = voting_system.sort_candidates(category)
        voter_candidates_list.delete(*voter_candidates_list.get_children())
        for candidate in sorted_candidates:
            voter_candidates_list.insert('', 'end', values=(candidate[0], candidate[1], candidate[2], candidate[3]))

    def on_exit():
        voting_system.close_db()
        root.quit()

    # Background Image
    def background():
        background_image = Image.open(r"C:\Users\gilgr\Desktop\Projects\Voting_System\image\Background.png")
        background_image = background_image.resize((root.winfo_screenwidth(), root.winfo_screenheight()),Image.Resampling.LANCZOS)
        background_image = ImageTk.PhotoImage(background_image)
        return background_image 

    # GUI

    root = tk.Tk()
    root.attributes('-fullscreen', True)
    root.title("Online Voting System")

    root.protocol("WM_DELETE_WINDOW", on_exit)

    bg = background()  # Background Image Declared
    candidates_frame = tk.Frame(root, bg="firebrick")
    voter_frame = tk.Frame(root, bg="firebrick")
    login_frame = tk.Frame(root, bg="firebrick")
    register_frame = tk.Frame(root, bg="firebrick")
    bold_font = font.Font(weight="bold")

    # Button Hover
    def on_enter(event):
        event.widget.config(bg='lightblue')  # Change to hover color

    def on_leave(event):
        event.widget.config(bg='firebrick')  # Change back to default color

    def hover(button):
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
        button.pack(pady=5)
        return button

    # Login Frame
    login_canvas = tk.Canvas(login_frame, width=root.winfo_screenwidth(), height=root.winfo_screenheight())
    login_canvas.pack(fill="both", expand=True)

    login_canvas.create_image(0, 0, image=bg, anchor="nw")

    # Create an inner frame that will hold the login widgets
    login_inner_frame = tk.Frame(login_canvas, bg="firebrick")
    login_canvas.create_window((0, 0), window=login_inner_frame, anchor="nw")

    tk.Label(login_inner_frame, text="Log-in", font=("Consolas", 40), bg="firebrick", fg="beige").pack(pady=(150, 20),
                                                                                                       padx=70,
                                                                                                       anchor="w")
    tk.Label(login_inner_frame, text="Username:", font=15, bg="firebrick", fg="beige").pack(pady=10, padx=110,
                                                                                            anchor="w")
    username_entry = tk.Entry(login_inner_frame, width=25)
    username_entry.pack(pady=10, padx=70, anchor="w")
    tk.Label(login_inner_frame, text="Password:", font=15, bg="firebrick", fg="beige").pack(pady=10, padx=110,
                                                                                            anchor="w")
    password_entry = tk.Entry(login_inner_frame, width=25, show="*")
    password_entry.pack(pady=10, padx=70, anchor="w")
    # Login Button / Register Button
    login_button = tk.Button(login_inner_frame, text="Login", command=login, width=15, height=1, bg="firebrick",
                             fg="beige")
    login_button.bind("<Enter>", on_enter)
    login_button.bind("<Leave>", on_leave)
    login_button.pack(pady=(20, 10), padx=90, anchor="w")

    tk.Label(login_inner_frame, text="Doesn't have account?", font=15, bg="firebrick", fg="beige").pack(pady=(170, 0.5),
                                                                                                        padx=70,
                                                                                                        anchor="w")
    register_to_button = tk.Button(login_inner_frame, text="Register", command=show_register_frame, width=15, height=1,
                                   bg="firebrick", fg="beige")
    register_to_button.bind("<Enter>", on_enter)
    register_to_button.bind("<Leave>", on_leave)
    register_to_button.pack(pady=(40, 130), padx=90, anchor="w")
    login_inner_frame.update_idletasks()
    login_canvas.config(scrollregion=login_canvas.bbox("all"))

    login_frame.pack_propagate(False)
    login_frame.pack(fill='both', expand=True)

    # Register Frame
    register_canvas = tk.Canvas(register_frame, width=root.winfo_screenwidth(), height=root.winfo_screenheight())
    register_canvas.pack(fill="both", expand=True)
    register_canvas.create_image(0, 0, image=bg, anchor="nw")

    # Create an inner frame that will hold the login widgets
    register_inner_frame = tk.Frame(register_canvas, bg="firebrick")
    register_canvas.create_window((0, 0), window=register_inner_frame, anchor="nw")

    tk.Label(register_inner_frame, text="Register", font=("Consolas", 24), bg="firebrick", fg="beige").pack(pady=20,
                                                                                                            anchor="w")
    tk.Label(register_inner_frame, text="First Name:", bg="firebrick", fg="beige").pack(pady=5, anchor="w")
    first_name_entry = tk.Entry(register_inner_frame)
    first_name_entry.pack(pady=5, anchor="w")
    tk.Label(register_inner_frame, text="Middle Name:", bg="firebrick", fg="beige").pack(pady=5, anchor="w")
    middle_name_entry = tk.Entry(register_inner_frame)
    middle_name_entry.pack(pady=5, anchor="w")
    tk.Label(register_inner_frame, text="Last Name:", bg="firebrick", fg="beige").pack(pady=5, anchor="w")
    last_name_entry = tk.Entry(register_inner_frame)
    last_name_entry.pack(pady=5, anchor="w")
    tk.Label(register_inner_frame, text="Age:", bg="firebrick", fg="beige").pack(pady=5, anchor="w")
    age_entry = tk.Entry(register_inner_frame)
    age_entry.pack(pady=5, anchor="w")
    tk.Label(register_inner_frame, text="Address:", bg="firebrick", fg="beige").pack(pady=5, anchor="w")
    address_entry = tk.Entry(register_inner_frame)
    address_entry.pack(pady=5, anchor="w")
    tk.Label(register_inner_frame, text="Contact Number:", bg="firebrick", fg="beige").pack(pady=5, anchor="w")
    contact_number_entry = tk.Entry(register_inner_frame)
    contact_number_entry.pack(pady=5, anchor="w")
    tk.Label(register_inner_frame, text="Username:", bg="firebrick", fg="beige").pack(pady=5, anchor="w")
    reg_username_entry = tk.Entry(register_inner_frame)
    reg_username_entry.pack(pady=5, anchor="w")
    tk.Label(register_inner_frame, text="Password:", bg="firebrick", fg="beige").pack(pady=5, anchor="w")
    reg_password_entry = tk.Entry(register_inner_frame, show="*")
    reg_password_entry.pack(pady=5, anchor="w")

    # Button
    register_button = tk.Button(register_inner_frame, text="Register", command=register, width=20, bg="firebrick",
                                fg="beige", activebackground="darkblue")  # Register button
    hover(register_button)
    login_to_button = tk.Button(register_inner_frame, text="Back to Login", command=show_login_frame, width=20,
                                bg="firebrick", fg="beige", activebackground="darkblue")  # Back to login button
    hover(login_to_button)
    register_inner_frame.update_idletasks()
    register_canvas.config(scrollregion=register_canvas.bbox("all"))

    register_frame.pack_propagate(False)
    register_frame.pack(fill='both', expand=True)

    # Candidates Frame / ADMIN FRAME
    tk.Label(candidates_frame, text="LIST OF CANDIDATES", font=("Consolas", 16), bg="firebrick", fg="beige").pack(
        pady=10, side=tk.TOP)

    candidates_list_frame = tk.Frame(candidates_frame, bg="firebrick")
    candidates_list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    candidates_list = ttk.Treeview(candidates_list_frame, columns=("ID", "Name", "Party", "Position"), show='headings')
    candidates_list.heading("ID", text="ID", anchor=tk.W)
    candidates_list.column("ID", width=50, anchor=tk.W)
    candidates_list.heading("Name", text="Name", anchor=tk.W)
    candidates_list.column("Name", width=150, anchor=tk.W)
    candidates_list.heading("Party", text="Party", anchor=tk.W)
    candidates_list.column("Party", width=100, anchor=tk.W)
    candidates_list.heading("Position", text="Position", anchor=tk.W)
    candidates_list.column("Position", width=100, anchor=tk.W)
    candidates_list.pack(fill=tk.BOTH, expand=True)

    buttons_frame = tk.Frame(candidates_frame, bg="firebrick")
    buttons_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)

    scrollbar = tk.Scrollbar(buttons_frame, orient="vertical")
    scrollbar.pack(side="right", fill="y")

    buttons_canvas = tk.Canvas(buttons_frame, yscrollcommand=scrollbar.set, bg="firebrick")
    buttons_canvas.pack(side="left", fill="both", expand=True)

    scrollbar.config(command=buttons_canvas.yview)

    buttons_inner_frame = tk.Frame(buttons_canvas, bg="firebrick")
    buttons_canvas.create_window((0, 0), window=buttons_inner_frame, anchor="nw")

    # Refresh Button
    refresh_button = tk.Button(buttons_inner_frame, text="Refresh", command=refresh, width=20, bg="firebrick",
                               fg="beige")
    hover(refresh_button)
    admin_button = tk.Button(buttons_inner_frame, text="Manage Admin", command=manage_admin, width=20,
                            bg="firebrick", fg="beige")
    hover(admin_button)
    # Sort Candidates
    tk.Label(buttons_inner_frame, text="Sort Candidates", bg="firebrick", fg="beige", font=bold_font).pack(pady=5)
    tk.Label(buttons_inner_frame, text="Category:", bg="firebrick", fg="beige").pack(pady=5)
    category_combobox = ttk.Combobox(buttons_inner_frame, values=["name", "party", "position"])
    category_combobox.pack(pady=5)
    sort_button = tk.Button(buttons_inner_frame, text="Sort Candidates", command=sort_candidates, width=20,
                            bg="firebrick", fg="beige")
    hover(sort_button)

    # Add Candidate
    tk.Label(buttons_inner_frame, text="Add Candidate", bg="firebrick", fg="beige", font=bold_font).pack(pady=5)
    tk.Label(buttons_inner_frame, text="Name:", bg="firebrick", fg="beige").pack(pady=5)
    name_entry = tk.Entry(buttons_inner_frame)
    name_entry.pack(pady=5)
    tk.Label(buttons_inner_frame, text="Party:", bg="firebrick", fg="beige").pack(pady=5)
    party_entry = tk.Entry(buttons_inner_frame)
    party_entry.pack(pady=5)
    tk.Label(buttons_inner_frame, text="Position:", bg="firebrick", fg="beige").pack(pady=5)
    position_entry = tk.Entry(buttons_inner_frame)
    position_entry.pack(pady=5)
    tk.Label(buttons_inner_frame, text="Description:", bg="firebrick", fg="beige").pack(pady=5)
    description_entry = tk.Text(buttons_inner_frame, height=10, width=40, bg="indianred", fg="beige")
    description_entry.pack(pady=5)
    tk.Label(buttons_inner_frame, text="Platform:", bg="firebrick", fg="beige").pack(pady=5)
    platform_entry = tk.Text(buttons_inner_frame, height=10, width=40, bg="indianred", fg="beige")
    platform_entry.pack(pady=5)
    add_button = tk.Button(buttons_inner_frame, text="Add Candidate", command=add_candidate, width=20, bg="firebrick",
                           fg="beige")
    hover(add_button)

    # Delete Candidate
    tk.Label(buttons_inner_frame, text="Delete Candidate", bg="firebrick", fg="beige", font=bold_font).pack(pady=5)
    delete_selected_button = tk.Button(buttons_inner_frame, text="Delete Selected Candidate", command=delete_candidate,
                                       width=20, bg="firebrick", fg="beige")
    hover(delete_selected_button)
    delete_all_button = tk.Button(buttons_inner_frame, text="Delete All Candidates", command=delete_all_candidates,
                                  width=20, bg="firebrick", fg="beige")
    hover(delete_all_button)

    # Update Candidate
    update_button = tk.Button(buttons_inner_frame, text="Update Selected Candidate", command=update_candidate, width=20,
                              bg="firebrick", fg="beige")
    hover(update_button)

    # View Description
    view_dbutton = tk.Button(buttons_inner_frame, text="View Description", command=view_description1, width=20,
                             bg="firebrick", fg="beige")
    hover(view_dbutton)
    description_text = tk.Text(buttons_inner_frame, wrap=tk.WORD, height=10, width=50, bg="indianred", fg="beige")
    description_text.pack(pady=5)

    # View Platform
    view_pbutton = tk.Button(buttons_inner_frame, text="View Platform", command=view_platform1, width=20,
                             bg="firebrick", fg="beige")
    hover(view_pbutton)
    platform_text = tk.Text(buttons_inner_frame, wrap=tk.WORD, height=10, width=50, bg="indianred", fg="beige")
    platform_text.pack(pady=5)

    tk.Label(buttons_inner_frame, text="Write Announcement", bg="firebrick", fg="beige", font=bold_font).pack(pady=5)
    announcement_entry = tk.Text(buttons_inner_frame, wrap=tk.WORD, height=5, width=50, bg="indianred", fg="beige")
    announcement_entry.pack(pady=5)
    set_announcement_button = tk.Button(buttons_inner_frame, text="Set Announcement", command=set_announcement,
                                        width=20, bg="firebrick", fg="beige")
    hover(set_announcement_button)

    tk.Label(buttons_inner_frame, text="Write Voting Type", bg="firebrick", fg="beige", font=bold_font).pack(pady=5)
    voting_type_entry = tk.Text(buttons_inner_frame, wrap=tk.WORD, height=2, width=50, bg="indianred", fg="beige")
    voting_type_entry.pack(pady=5)
    set_voting_type_button = tk.Button(buttons_inner_frame, text="Set Voting Type", command=set_voting_type, width=20,
                                       bg="firebrick", fg="beige")
    hover(set_voting_type_button)
    back_button = tk.Button(buttons_inner_frame, text="Back", command=show_login_frame, width=20, bg="firebrick",
                            fg="beige")
    hover(back_button)

    buttons_inner_frame.update_idletasks()
    buttons_canvas.config(scrollregion=buttons_canvas.bbox("all"))

    bottom_frame = tk.Frame(candidates_list_frame, bg="firebrick")
    bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

    history_frame = tk.Frame(bottom_frame, width=25, bg="firebrick")
    history_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    tk.Label(history_frame, text="Activity Logs", font=("Consolas", 12), bg="firebrick", fg="beige").pack(pady=5)
    history_list = tk.Text(history_frame, wrap=tk.WORD, height=10, width=25, bg="indianred", fg="beige")
    history_list.pack(fill=tk.BOTH, expand=True)

    voters_frame = tk.Frame(bottom_frame, width=25, bg="firebrick")
    voters_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
    tk.Label(voters_frame, text="Voter Logs", font=("Consolas", 12), bg="firebrick", fg="beige").pack(pady=5)
    voters_list = tk.Text(voters_frame, wrap=tk.WORD, height=10, width=25, bg="indianred", fg="beige")
    voters_list.pack(fill=tk.BOTH, expand=True)

    # Voter Frame / User Frame
    voting_type_label = tk.Label(voter_frame, font=("Consolas", 16), bg="firebrick", fg="beige")
    voting_type_label.pack(pady=10, side=tk.TOP)
    voter_list_frame = tk.Frame(voter_frame, bg="firebrick")
    voter_list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    voter_candidates_list = ttk.Treeview(voter_list_frame, columns=("ID", "Name", "Party", "Position"), show='headings')
    voter_candidates_list.heading("ID", text="ID")
    voter_candidates_list.heading("Name", text="Name")
    voter_candidates_list.heading("Party", text="Party")
    voter_candidates_list.heading("Position", text="Position")
    voter_candidates_list.pack(fill=tk.BOTH, expand=True)

    voter_buttons_frame = tk.Frame(voter_frame, bg="firebrick")
    voter_buttons_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)
    voter_scrollbar = tk.Scrollbar(voter_buttons_frame, orient="vertical")
    voter_scrollbar.pack(side="right", fill="y")
    voter_buttons_canvas = tk.Canvas(voter_buttons_frame, yscrollcommand=voter_scrollbar.set, bg="firebrick")
    voter_buttons_canvas.pack(side="left", fill="both", expand=True)
    voter_scrollbar.config(command=voter_buttons_canvas.yview)
    voter_buttons_inner_frame = tk.Frame(voter_buttons_canvas, bg="firebrick")
    voter_buttons_canvas.create_window((0, 0), window=voter_buttons_inner_frame, anchor="nw")

    tk.Label(voter_buttons_inner_frame, text="Sort Candidates", bg="firebrick", fg="beige", font=bold_font).pack(pady=5)
    tk.Label(voter_buttons_inner_frame, text="Category:", bg="firebrick", fg="beige").pack(pady=5)
    voter_category_combobox = ttk.Combobox(voter_buttons_inner_frame, values=["name", "party", "position"])
    voter_category_combobox.pack(pady=5)
    sort_voter_candidates_button = tk.Button(voter_buttons_inner_frame, text="Sort Candidates",
                                             command=sort_voter_candidates, width=20, bg="firebrick", fg="beige")
    hover(sort_voter_candidates_button)
    vote_button = tk.Button(voter_buttons_inner_frame, text="Vote for Selected Candidate", command=vote, width=20,
                            bg="firebrick", fg="beige")
    hover(vote_button)
    unvote_button = tk.Button(voter_buttons_inner_frame, text="Unselect Vote", command=unvote, width=20, bg="firebrick",
                              fg="beige")
    hover(unvote_button)
    view_description_button = tk.Button(voter_buttons_inner_frame, text="View Description", command=view_description,
                                        width=20, bg="firebrick", fg="beige")
    hover(view_description_button)
    voter_description_text = tk.Text(voter_buttons_inner_frame, wrap=tk.WORD, height=5, width=40, bg="indianred",
                                     fg="beige")
    voter_description_text.pack(pady=5)
    view_platform_button = tk.Button(voter_buttons_inner_frame, text="View Platform", command=view_platform, width=20,
                                     bg="firebrick", fg="beige")
    hover(view_platform_button)
    voter_platform_text = tk.Text(voter_buttons_inner_frame, wrap=tk.WORD, height=5, width=40, bg="indianred",
                                  fg="beige")
    voter_platform_text.pack(pady=5)

    tk.Label(voter_buttons_inner_frame, text="Vote Summary", bg="firebrick", fg="beige", font=bold_font).pack(pady=5)
    voter_summary_text = tk.Text(voter_buttons_inner_frame, wrap=tk.WORD, height=10, width=40, bg="indianred",
                                 fg="beige")
    voter_summary_text.pack(pady=5)

    tk.Label(voter_buttons_inner_frame, text="Announcement", bg="indianred", fg="beige", font=bold_font).pack(pady=5)
    voter_announcement_text = tk.Text(voter_buttons_inner_frame, wrap=tk.WORD, height=5, width=40, bg="indianred",
                                      fg="beige")
    voter_announcement_text.pack(pady=5)
    voter_announcement_text.insert(tk.END, voting_system.announcement)

    show_login_frame_button = tk.Button(voter_buttons_inner_frame, text="Back", command=show_login_frame, width=20,
                                        bg="firebrick", fg="beige")
    hover(show_login_frame_button)

    voter_buttons_inner_frame.update_idletasks()
    voter_buttons_canvas.config(scrollregion=buttons_canvas.bbox("all"))

    voting_results_frame = tk.Frame(candidates_frame, bg="firebrick")
    voting_results_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

    Vote_logo = Image.open(r"C:\Users\gilgr\Desktop\Projects\Voting_System\image\Vote_logo.png")
    Vote_logo = ImageTk.PhotoImage(Vote_logo)
    tk.Label(voting_results_frame, image=Vote_logo, bd=0).pack(side=tk.TOP)

    tk.Label(voting_results_frame, text="Announcement", font=("Consolas", 16), bg="firebrick", fg="beige").pack(pady=10, side=tk.TOP)

    announcement_list = tk.Text(voting_results_frame, wrap=tk.WORD, height=10, width=30, bg="indianred", fg="beige")
    announcement_list.pack(fill=tk.BOTH, expand=True)

    tk.Label(voting_results_frame, text="VOTING RESULTS", font=("Consolas", 16), bg="firebrick", fg="beige").pack(pady=10, side=tk.TOP)

    voting_results_list = tk.Text(voting_results_frame, wrap=tk.WORD, height=50, width=30, bg="indianred", fg="beige")
    voting_results_list.pack(fill=tk.BOTH, expand=True)

    update_all_lists()
    load_announcement()
    load_voting_type()
    show_login_frame()
    root.mainloop()

if __name__ == "__main__":
    main()

