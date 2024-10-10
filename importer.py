
import zipfile
import os
import xml.etree.ElementTree as ET
import csv
import re

def sanitize_filename(filename):
    # Remove or replace any characters that are not allowed in filenames
    return re.sub(r'[\\/*?:"<>|]', "_", filename)

def create_imscc_from_csv(csv_filename, output_filename="content.imscc"):
    # Temporary directory for creating IMSCC structure
    temp_dir = "temp_imscc"
    os.makedirs(temp_dir, exist_ok=True)

    # Define manifest XML structure according to Common Cartridge v1.3 specification
    manifest = ET.Element("manifest", {
        "identifier": "com.example.manifest",
        "xmlns": "http://www.imsglobal.org/xsd/imscp_v1p1",
        "xmlns:imsmd": "http://www.imsglobal.org/xsd/imsmd_v1p2",
        "xmlns:imscc": "http://www.imsglobal.org/xsd/imsccv1p3",
    })
    
    metadata = ET.SubElement(manifest, "metadata")
    schema = ET.SubElement(metadata, "schema")
    schema.text = "IMS Common Cartridge"
    schemaversion = ET.SubElement(metadata, "schemaversion")
    schemaversion.text = "1.3"
    
    organizations = ET.SubElement(manifest, "organizations")
    organization = ET.SubElement(organizations, "organization", {
        "identifier": "org_additional_resources",
        "structure": "rooted-hierarchy"
    })
    
    item_module = ET.SubElement(organization, "item", {"identifier": "item_additional_resources_module"})
    title_module = ET.SubElement(item_module, "title")
    title_module.text = "Additional Resources"

    # Define the resources element globally
    resources = ET.SubElement(manifest, 'resources')

    # Read links from CSV file and add as resources and items
    with open(csv_filename, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for idx, row in enumerate(reader):
            if 'Title' in row and 'URL' in row:
                link_title = row['Title']
                link_url = row['URL']
                
                # Define the resource for the link
                link_resource_id = f'link_resource_{idx}'
                link_resource = ET.SubElement(resources, 'resource', {
                    'identifier': link_resource_id,
                    'type': 'imswl_xmlv1p3',
                    'href': link_url
                })
                
                # Each resource needs a file element per Common Cartridge v1.3
                file_element = ET.SubElement(link_resource, 'file', {'href': link_url})
                
                # Define the item for the link in the organization structure
                link_item = ET.SubElement(item_module, 'item', {
                    'identifier': f'item_{link_resource_id}',
                    'identifierref': link_resource_id
                })
                title_link = ET.SubElement(link_item, 'title')
                title_link.text = link_title
            else:
                print("CSV format error: 'Title' or 'URL' column missing.")

    # Write the manifest to the temporary directory
    tree = ET.ElementTree(manifest)
    manifest_path = os.path.join(temp_dir, "imsmanifest.xml")
    tree.write(manifest_path, encoding="utf-8", xml_declaration=True)

    # Create the zip file for IMSCC
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as imscc_zip:
        imscc_zip.write(manifest_path, arcname="imsmanifest.xml")
    
    print(f"IMSCC package created at {output_filename}")

# Example usage
csv_filename = "links.csv"  # Adjust this to your CSV filename
create_imscc_from_csv(csv_filename)
