# Day-7-work-Main
from csv import *
from tkinter import *
from tkinter import messagebox

import re

window = Tk()
window.title("Data Entry")
window.geometry("700x350")
main_lst = []

def Add():
    contact_number = contact.get()

    # Remove all non-digit characters for checking length and duplication
    clean_number = re.sub(r'\D', '', contact_number)

    if len(clean_number) != 8:
        messagebox.showerror("Error", "Contact number must contain exactly 8 digits.")
        return

    # Check if number already exists
    for entry in main_lst:
        existing_number_clean = re.sub(r'\D', '', entry[2])
        if existing_number_clean == clean_number:
            messagebox.showerror("Error", "Contact number already exists.")
            return

    lst = [name.get(), age.get(), contact_number]
    main_lst.append(lst)
    messagebox.showinfo("Information", "The data has been added successfully.")
    Clear()

def Save():
    with open("data_entry.csv", "w", newline='') as file:
        Writer = writer(file)
        Writer.writerow(["Name", "Age", "Contact"])
        Writer.writerows(main_lst)
        messagebox.showinfo("Information", "Saved successfully.")

def Clear():
    name.delete(0, END)
    age.delete(0, END)
    contact.delete(0, END)

# Validation function for contact entry to allow only numbers and specific symbols
def validate_contact(char):
    allowed = "0123456789()-+ "
    return all(c in allowed for c in char)

# Labels
label1 = Label(window, text="Name: ", padx=20, pady=10)
label2 = Label(window, text="Age: ", padx=20, pady=10)
label3 = Label(window, text="Contact: ", padx=20, pady=10)

# Entry fields
name = Entry(window, width=30, borderwidth=3)
age = Entry(window, width=30, borderwidth=3)

vcmd = (window.register(validate_contact), "%P")
contact = Entry(window, width=30, borderwidth=3, validate="key", validatecommand=vcmd)

# Buttons
save = Button(window, text="Save", padx=20, pady=10, command=Save)
add = Button(window, text="Add", padx=20, pady=10, command=Add)
clear = Button(window, text="Clear", padx=18, pady=10, command=Clear)
Exit = Button(window, text="Exit", padx=20, pady=10, command=window.quit)

# Layout
label1.grid(row=0, column=0)
label2.grid(row=1, column=0)
label3.grid(row=2, column=0)

name.grid(row=0, column=1)
age.grid(row=1, column=1)
contact.grid(row=2, column=1)
add.grid(row=3, column=0, columnspan=2)
save.grid(row=4, column=0, columnspan=2)
clear.grid(row=5, column=0, columnspan=2)
Exit.grid(row=6, column=0, columnspan=2)

window.mainloop()

print(main_lst)
