import zipfile
import os
import xml.etree.ElementTree as ET
import csv
import re

def sanitize_filename(filename):
    # Remove or replace any characters that are not allowed in filenames
    return re.sub(r'[\\/*?:"<>|]', "_", filename)

def create_imscc_from_csv(csv_filename, output_filename="content.imscc"):
    # Adding a new module 'Additional Resources' specifically for links
    def add_additional_resources_module(manifest):
        # Create 'Additional Resources' module
        resources_module = ET.SubElement(manifest, "resources")
        additional_module = ET.SubElement(resources_module, "resource", {
            "identifier": "res_additional_resources",
            "type": "webcontent",
            "href": "additional_resources/index.html"
        })
        
        # Set up 'Additional Resources' module structure
        add_module_title(additional_module, "Additional Resources")
        
        # Adding all link resources to this module
        links_element = ET.SubElement(additional_module, "links")
        link_items = [("Link 1", "http://example.com"), ("Link 2", "http://example.org")]  # Add your links here

        for link_title, link_url in link_items:
            link_item = ET.SubElement(links_element, "item", {
                "title": link_title,
                "url": link_url
            })
    
    # Original code follows here...
    
    # Temporary directory for creating IMSCC structure
    temp_dir = "temp_imscc"
    os.makedirs(temp_dir, exist_ok=True)
    
    # Define manifest XML structure
    manifest = ET.Element("manifest", {
        "identifier": "com.example.manifest",
        "xmlns": "http://www.imsglobal.org/xsd/imscp_v1p1",
        "xmlns:lomimscc": "http://ltsc.ieee.org/xsd/LOM",
        "xmlns:lom": "http://ltsc.ieee.org/xsd/LOM",
        "xmlns:imsmd": "http://www.imsglobal.org/xsd/imsmd_v1p2",
        "xmlns:imscc": "http://www.imsglobal.org/xsd/imscc_v1p1"
    })
    
    organizations = ET.SubElement(manifest, "organizations")
    organization = ET.SubElement(organizations, "organization", {"identifier": "ORG1"})
    
    resources = ET.SubElement(manifest, "resources")
    
    # Read CSV and process each row
    with open(csv_filename, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for i, row in enumerate(reader):
            if len(row) != 2:
                raise ValueError(f"Row {i + 1} does not contain exactly two columns.")
            title, link = row
            
            # Sanitize the filename
            safe_title = sanitize_filename(title)
            
            # Create a new item in the organization for each link
            item = ET.SubElement(organization, "item", {"identifier": f"ITEM{i+1}"})
            ET.SubElement(item, "title").text = title
            
            # Create a new resource for each link
            resource = ET.SubElement(resources, "resource", {
                "identifier": f"RES{i+1}",
                "type": "webcontent",
                "href": f"{safe_title}.html"
            })
            ET.SubElement(resource, "file", {"href": f"{safe_title}.html"})
            
            # Create an HTML file that redirects to the external link
            html_content = f"""<html><head><meta http-equiv="refresh" content="0; url={link}" /></head><body></body></html>"""
            html_filename = os.path.join(temp_dir, f"{safe_title}.html")
            with open(html_filename, "w", encoding='utf-8') as html_file:
                html_file.write(html_content)
    
    # Add metadata
    metadata = ET.SubElement(manifest, "metadata")
    schema = ET.SubElement(metadata, "schema")
    schema.text = "IMS Common Cartridge"
    schemaversion = ET.SubElement(metadata, "schemaversion")
    schemaversion.text = "1.1"
    
    # Write XML manifest file
    manifest_tree = ET.ElementTree(manifest)
    manifest_tree.write(os.path.join(temp_dir, "imsmanifest.xml"), encoding="utf-8", xml_declaration=True)
    
    # Create the IMSCC (ZIP) file
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as imscc_zip:
        for root, _, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                imscc_zip.write(file_path, os.path.relpath(file_path, temp_dir))
    
    # Cleanup temporary directory
    for file in os.listdir(temp_dir):
        os.remove(os.path.join(temp_dir, file))
    os.rmdir(temp_dir)
    
    print(f"IMSCC file '{output_filename}' created successfully.")

# Example usage
csv_filename = "links.csv"  # Replace with your CSV file
create_imscc_from_csv(csv_filename)
