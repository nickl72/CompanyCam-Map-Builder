import tkinter as tk
from tkinter import ttk
from tkinter import messagebox, filedialog
import webbrowser as wb
from CompanyCam_map_builder_helper import create_kml_text, write_to_kml_file, api_call, error_popup_message
import os
from dotenv import load_dotenv, dotenv_values
import sys

load_dotenv()
token = os.getenv("COMPANYCAM_ACCESS_TOKEN")
if token is None:
    error_popup_message('Token Error', 'There is no access token available for your CompanyCam account. Please update the environment file to include an access token.')
    sys.exit()
headers = {
    'Authorization': f'Bearer {token}',
}

#### Program Flow

######## step 1: Appliocation starts with Tkinter GUI
######## step 2a: User is asked how they want to proceed -> With project ID or by selecting from a list of projects
######## step 2b: API Request to CompanyCam for a list of projects
######## step 2c: GUI Lists all CompanyCam Projects for user
######## step 2d: User selects desired project
######## Step 3a: User is asked if there are any tags they want to target for photo retrival
######## Step 3b: API call to retireve list of tags
######## Step 3c: optional: program cross references tags list with tags used in the selected project
######## Step 3d: GUI Displays list of tags to select from
######## Step 3e: User selects the appropriate tag from the GUI
######## step 4: API Request to CompanyCam for a list of photos from the project that have the appropriate tag
######## Step 5: GUI prompts user to name the output file and save location
######## Step 6: Program creates a KML file that includes each photo's CompanyCam URL and GPS coordinates
######## Step 7: **May not be programmable** user uploads KML file to mymaps.google.com that can be shared with the client

# GUI pop up to select the desired project
def select_project_window():
    current_page = 1
        
    project_list = api_call('project', headers)
    api_counter.set(api_counter.get() + 1)
    print(f'\n\napi called {api_counter.get()} times\n')
    if project_list is False:
        return
    
    project_selector = tk.Toplevel(root)
    

    project_selector.title("Project Selector")
    tk.Label(project_selector,text="Select from the available projects").pack()
    tk.Label(project_selector,text="right click the project link to view the project on your web browser").pack()

    tree = ttk.Treeview(project_selector, columns=('Project Name','Project Address','# of Photos', 'Project Link'), show="headings",selectmode='browse')
    tree['columns'] = ('Project Name','Project Address','# of Photos', 'Project Link')
    tree.heading('Project Name', text='Project Name')
    tree.heading('Project Address', text='Project Address')
    tree.heading('# of Photos', text='# of Photos')
    tree.heading('Project Link', text='Project Link')

    def open_link(event):
        tre = event.widget  # get the treeview widget
        region = tre.identify_region(event.x, event.y)
        col = tre.identify_column(event.x)
        iid = tre.identify('item', event.x, event.y)
        if region == 'cell' and col == '#4':
            link = tre.item(iid)['values'][3]  # get the link from the selected row
            wb.open_new_tab(link)  # open the link in a browser tab


    scrollbar = ttk.Scrollbar(project_selector, orient="vertical",command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")

    for  project in project_list:
        address = ''
        for key in project['address']:
            if project['address'][key] is not None:
                address +=project['address'][key] +' '
        value = [project['name'],address,project['photo_count'], project['project_url']]
        tree.insert("",'end',id=project['id'],values=value)

    def select_project(event):
        project_id.set(tree.focus())
        project_selector.destroy()
    tree.pack()
    tree.bind('<Button-3>', open_link)
    tree.bind('<Double-Button-1>',select_project)
    tk.Button(project_selector,text="Confrim Selection", command= lambda: [project_id.set(tree.focus()),project_selector.destroy()]).pack()



#### Tag selection
def select_tag_window():
    current_page = 1
        
    tag_list = api_call('tag',headers)
    api_counter.set(api_counter.get() + 1)
    print(f'api called {api_counter.get()} times\n')
    if tag_list is False:
        return
    
    tag_selector = tk.Toplevel(root)
    

    tag_selector.title("Tag Selector")
    tk.Label(tag_selector,text="Select from the available tags").pack()
    listbox = tk.Listbox(tag_selector, height=10)

    tree = ttk.Treeview(tag_selector, columns=('Tag Name'), show="headings",selectmode='browse')
    scrollbar = ttk.Scrollbar(tag_selector, orient="vertical",command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")

    tag_dict = {}
 
    for  tag in tag_list:
        tag_dict[tag['display_value']] = tag['id']
    listbox.insert(tk.END,*tag_dict.keys())

    def get_tag_value(*args):
        tag_name = listbox.get(listbox.curselection())
        tag_var.set(tag_dict[tag_name])
        tag_selector.destroy()
        
    listbox.pack()
    listbox.bind('<Double-Button-1>',get_tag_value)
    tk.Button(tag_selector,text="Confrim Selection", command=get_tag_value).pack()


# function that will get all the data together needed to build the KML file
def build_map():
    tag=tag_var.get()
    # Gets photos to build the map with
 
    photo_list = api_call('photo',headers,tag_id=tag,project_id=project_id.get())
    api_counter.set(api_counter.get() + 1)
    print(f'\n\napi called {api_counter.get()} times\n')

    kml_text = create_kml_text('test',photo_list)

    def select_save_location():
        file_path = filedialog.asksaveasfilename(defaultextension=".kml")
        if file_path:
            file_path_var.set(file_path)

    def save():
        if write_to_kml_file(file_path_var.get(),kml_text):
            root.destroy()

    # File name entry
    for child in root.winfo_children(): child.destroy()

    tk.Label(root, text="where would you like to save the output file?").grid(row=1,column=0,padx=5,pady=5)
    tk.Entry(root,textvariable=file_path_var, width=60).grid(row=1,column=1,padx=5,pady=5)
    tk.Button(root, text="Browse", command=select_save_location).grid(row=1,column=3,padx=5,pady=5)
    tk.Button(root, text="save", command=save).grid(row=2, column=2,padx=5,pady=5)

    # if write_to_kml_file('Test', 'C:/Users/nlapo/Documents/Programming/CompanyCam_map_builder',kml_text):
    #     root.destroy()


def get_tag_window():
    # check for valid project id
    if project_id.get() == "":
        return
    # clear all elements in the main window
    for child in root.winfo_children(): child.destroy()
    tk.Label(root, text="Enter the photo tag ID you would like to check: ").grid(row=1,column=0,padx=5,pady=5)
    tag_entry = tk.Entry(root,textvariable=tag_var, width=60)
    tag_entry.focus_set()
    tag_entry.grid(row=1,column=1,padx=5,pady=5)
    tk.Button(root, text="Browse", command=lambda: select_tag_window()).grid(row=1,column=3,padx=5,pady=5)
    tk.Button(root, text="Create Map",command=build_map).grid(row=2, column=2, padx=5,pady=5)



############### GUI #################
# Set up the main window
root = tk.Tk()
root.title("Map Builder from CompanyCam")
root.geometry("800x200")
open_file= tk.BooleanVar()
tk.Label(root, text="This tool Will connect to CompanyCam and create a .kml file that places photos on a map based on GPS coordniates.").grid(column=0,padx=5,pady=5,columnspan=6)
api_counter = tk.IntVar()
api_counter.set(0)
# Project Selector
file_path_var = tk.StringVar()
project_id = tk.StringVar()
tag_var =tk.StringVar()

tk.Label(root, text="Enter the Project ID you would like to make a map from: ").grid(row=1,column=0,padx=5,pady=5)
project_entry = tk.Entry(root,textvariable=project_id, width=60)
project_entry.grid(row=1,column=1,padx=5,pady=5)
project_entry.focus_set()

tk.Button(root, text="Browse", command=lambda: select_project_window()).grid(row=1,column=3,padx=5,pady=5)
tk.Button(root, text="Next",command=get_tag_window).grid(row=2, column=2, padx=5,pady=5)









# # Submit button
# tk.Button(root, text="Create pins", command=submit).grid(row=6,column=1,padx=5,pady=5)

# Start the GUI loop
root.mainloop()
