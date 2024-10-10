import zipfile
import os
import xml.etree.ElementTree as ET
import csv
import re
import uuid
from collections import defaultdict

def sanitize_filename(filename):
    # Remove or replace any characters that are not allowed in filenames
    return re.sub(r'[\\/*?:"<>|]', "_", filename)

def create_imscc_from_csv(csv_filename, output_filename="content.imscc"):
    # Temporary directory for creating IMSCC structure
    temp_dir = "temp_imscc"
    os.makedirs(temp_dir, exist_ok=True)

    # Define manifest XML structure according to the provided characteristics
    manifest = ET.Element("manifest", {
        "identifier": str(uuid.uuid4()),
        "xmlns": "http://www.imsglobal.org/xsd/imsccv1p3/imscp_v1p1",
        "xmlns:lomr": "http://ltsc.ieee.org/xsd/imsccv1p3/LOM/resource",
        "xmlns:lomm": "http://ltsc.ieee.org/xsd/imsccv1p3/LOM/manifest",
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "xsi:schemaLocation": "http://ltsc.ieee.org/xsd/imsccv1p3/LOM/resource "
                              "http://www.imsglobal.org/profile/cc/ccv1p3/LOM/ccv1p3_lomresource_v1p0.xsd "
                              "http://www.imsglobal.org/xsd/imsccv1p3/imscp_v1p1 "
                              "http://www.imsglobal.org/profile/cc/ccv1p3/ccv1p3_imscp_v1p2_v1p0.xsd "
                              "http://ltsc.ieee.org/xsd/imsccv1p3/LOM/manifest "
                              "http://www.imsglobal.org/profile/cc/ccv1p3/LOM/ccv1p3_lommanifest_v1p0.xsd"
    })
    
    metadata = ET.SubElement(manifest, "metadata")
    schema = ET.SubElement(metadata, "schema")
    schema.text = "IMS Common Cartridge"
    schemaversion = ET.SubElement(metadata, "schemaversion")
    schemaversion.text = "1.3.0"
    
    # Adding LOM metadata
    lom = ET.SubElement(metadata, "lomm:lom")
    general = ET.SubElement(lom, "lomm:general")
    title = ET.SubElement(general, "lomm:title")
    title_string = ET.SubElement(title, "lomm:string", {"language": "en-US"})
    title_string.text = "Frazier Smith Sandbox"

    organizations = ET.SubElement(manifest, "organizations")
    organization = ET.SubElement(organizations, "organization", {
        "identifier": str(uuid.uuid4()),
        "structure": "rooted-hierarchy"
    })

    # Dictionary to track chapter items for grouping resources
    chapter_items = {}

    # Define the resources element globally
    resources = ET.SubElement(manifest, 'resources')

    # Read links from CSV file and group by chapters
    with open(csv_filename, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if 'Title' in row and 'URL' in row and 'Chapter' in row:
                link_title = row['Title']
                link_url = row['URL']
                chapter = row['Chapter']

                # Check if chapter already exists in the manifest, else create it
                if chapter not in chapter_items:
                    chapter_id = f"chapter_{uuid.uuid4()}"
                    chapter_item = ET.SubElement(organization, "item", {"identifier": chapter_id})
                    chapter_title = ET.SubElement(chapter_item, "title")
                    chapter_title.text = f"Chapter {chapter} Resources"
                    chapter_items[chapter] = chapter_item
                
                # Create unique UUID for weblink
                link_uuid = str(uuid.uuid4())
                link_folder = f"weblinks/{link_uuid}"
                os.makedirs(os.path.join(temp_dir, link_folder), exist_ok=True)
                
                # Define the resource for the link
                link_resource_id = f"link_resource_{link_uuid}"
                link_resource = ET.SubElement(resources, 'resource', {
                    'identifier': link_resource_id,
                    'type': 'imswl_xmlv1p3',
                    'href': f"{link_folder}/weblink_{link_uuid}.xml"
                })
                
                # Write weblink XML file
                weblink_xml = ET.Element("webLink", {
                    "xmlns": "http://www.imsglobal.org/xsd/imsccv1p3/imswl_v1p3",
                    "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                    "xsi:schemaLocation": "http://www.imsglobal.org/xsd/imsccv1p3/imswl_v1p3 http://www.imsglobal.org/profile/cc/ccv1p3/ccv1p3_imswl_v1p3.xsd"
                })
                title = ET.SubElement(weblink_xml, "title")
                title.text = link_title
                url = ET.SubElement(weblink_xml, "url", {"href": link_url, "target": "_blank"})
                
                weblink_path = os.path.join(temp_dir, link_folder, f"weblink_{link_uuid}.xml")
                weblink_tree = ET.ElementTree(weblink_xml)
                weblink_tree.write(weblink_path, encoding="utf-8", xml_declaration=True)
                
                # Reference weblink file in manifest resource
                file_element = ET.SubElement(link_resource, 'file', {
                    'href': f"{link_folder}/weblink_{link_uuid}.xml"
                })
                
                # Define the item for the link in the organization structure
                item = ET.SubElement(chapter_items[chapter], 'item', {
                    'identifier': f'item_{link_resource_id}',
                    'identifierref': link_resource_id
                })
                title_link = ET.SubElement(item, 'title')
                title_link.text = link_title

    # Write the manifest to the temporary directory
    manifest_path = os.path.join(temp_dir, "imsmanifest.xml")
    tree = ET.ElementTree(manifest)
    tree.write(manifest_path, encoding="utf-8", xml_declaration=True)

    # Create the zip file for IMSCC and add manifest only once
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as imscc_zip:
        imscc_zip.write(manifest_path, arcname="imsmanifest.xml")
        
        # Add weblinks folder and contents to the zip
        for root, _, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, start=temp_dir)
                if arcname != "imsmanifest.xml":  # Avoid adding duplicate imsmanifest.xml
                    imscc_zip.write(file_path, arcname=arcname)
    
    print(f"IMSCC package created at {output_filename}")

# Example usage
csv_filename = "links.csv"  # Adjust this to your CSV filename
create_imscc_from_csv(csv_filename)
