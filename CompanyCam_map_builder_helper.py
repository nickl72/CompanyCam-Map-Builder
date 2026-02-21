from tkinter import messagebox
import requests
from typing import Literal, get_args

# define acceptable options for the type of api call to make
API_CALL_TYPES = Literal["project", "photo", "tag"]

# The Photo class takes the photo data from a CompanyCam photo and uses the info to build a placemark for a kml file
# Placemarks use the annotated images
class Photo:
    def __init__ (self, photo, name, is_annotated = True):
        self.name = name
        self.original_uri = photo['uris'][0]['uri']
        self.annotated_uri = photo['uris'][3]['uri']
        self.coordinates = photo['coordinates']
        self.is_annotated = is_annotated
        self.kml_placemark = self.create_kml_placemark()
        
    def create_kml_placemark(self):
        gps_coordinates = str(self.coordinates['lon']) + ',' + str(self.coordinates['lat'])
        placemark_kml = f"""
        <Placemark>
            <name>{self.name}</name>
            <description><![CDATA[<img style="max-width:500px;" src="{self.annotated_uri if self.is_annotated else self.original_uri}">]]></description>
            <styleUrl>#msn_placemark_circle</styleUrl>
            <Point>
                <coordinates>{gps_coordinates}</coordinates>
            </Point>
        </Placemark>"""
        return placemark_kml

# This function creates the text to put into a .kml file using the Photo class     
def create_kml_text(file_name, photos):
    # Beginning .kml boilerplate
    output_kml = f"""<?xml version="1.0" encoding="UTF-8"?>
    <kml xmlns="http://www.opengis.net/kml/2.2">
    <Document>
        <name>{file_name}</name>
        <StyleMap id="msn_placemark_circle">
            <Pair>
                <key>normal</key>
                <styleUrl>#sn_placemark_circle</styleUrl>
            </Pair>
            <Pair>
                <key>highlight</key>
                <styleUrl>#sh_placemark_circle_highlight</styleUrl>
            </Pair>
        </StyleMap>
        <Style id="sh_placemark_circle_highlight">
            <IconStyle>
                <scale>1.3</scale>
                <Icon>
                    <href>http://maps.google.com/mapfiles/kml/paddle/ylw-circle.png</href>
                </Icon>
                <hotSpot x="32" y="1" xunits="pixels" yunits="pixels"/>
            </IconStyle>
            <ListStyle>
                <ItemIcon>
                    <href>http://maps.google.com/mapfiles/kml/paddle/ylw-circle-lv.png</href>
                </ItemIcon>
            </ListStyle>
        </Style>
        <Style id="sn_placemark_circle">
            <IconStyle>
                <scale>1.1</scale>
                <Icon>
                    <href>http://maps.google.com/mapfiles/kml/paddle/ylw-circle.png</href>
                </Icon>
                <hotSpot x="32" y="1" xunits="pixels" yunits="pixels"/>
            </IconStyle>
            <ListStyle>
                <ItemIcon>
                    <href>http://maps.google.com/mapfiles/kml/paddle/ylw-circle-lv.png</href>
                </ItemIcon>
            </ListStyle>
        </Style>"""

    ####################
    # Do the programming here

    # output .kml for each photo and pin. The leg work is done in the Photo class
    counter = 1
    for item in photos:
        photo = Photo(item, counter)
        output_kml += photo.kml_placemark
        counter += 1

    # End The Programming here
    ####################

    # This is the ending Boilerplate for the kml document
    output_kml += """
    </Document>
    </kml>"""

    return output_kml

# This function creates a new file to store the output text. If a file already exists, it asks if you want to overwrite it
def write_to_kml_file(file_path, file_contents):
    try:
        f = open(file_path, "x")
    except:
        if messagebox.askyesno("File already exists.","The file name you've chosen already exists. Would you like to overwrite it?"):
            f = open(file_path, "w")
        else:
            return False
    f.write(file_contents)
    return True

# This function creates a pop up window with an error message in it
def error_popup_message(title, message):
    messagebox.showerror(title, message)

# This function makes the api calls and returns the results or False depending on the api response
def api_call(call_type: API_CALL_TYPES,headers,page = 1,results_per_page=25,project_id='',tag_id=''):
    options = get_args(API_CALL_TYPES)
    # send error if we don't have the correct api call type
    assert call_type in options, f"'{call_type}' is not in {options}"

    # Set the URL based on the desired API call
    if call_type == get_args(API_CALL_TYPES)[0]:
        # project API Call
        url = f'https://api.companycam.com/v2/projects?page={page}&per_page={results_per_page}'
    elif call_type == get_args(API_CALL_TYPES)[1]:
        # photo API Call
        url = f'https://api.companycam.com/v2/projects/{project_id}/photos?tag_ids={tag_id}'
    elif call_type == get_args(API_CALL_TYPES)[2]:
        # tag API Call
        url = f'https://api.companycam.com/v2/tags?page={page}&per_page={results_per_page}'
    
    # Attempt to make the API call
    try:
        response = requests.get(url,headers=headers)
        status = response.status_code
    except:
        status = 0 # sets status to 0 if there is no connection to CompanyCam

    # Return data, or prompt the appropriate error message 
    if status == 200: # 
        return response.json()
    elif status == 401 or status == 403:
        error_title = "Authorization Error"
        error_message = "You are not authorized to access the requested records."
    elif status == 0:
        error_title = "Connection Error"
        error_message = "Could not connect to the CompanyCam website. Please check your internet connection and try again."
    else:
        error_title = "Request Error"
        error_message = "CompanyCam could not provide the requested info."
    error_popup_message(error_title, error_message)
    return False  



