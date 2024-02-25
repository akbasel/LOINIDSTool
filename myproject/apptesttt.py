from flask import Flask, render_template, request, send_file
import xml.etree.ElementTree as ET
from io import BytesIO
import xml
import xml.dom.minidom

app = Flask(__name__)

def convert_loin_to_ids(loin_xml):
    # Parse the LOIN XML string
    loin_root = ET.fromstring(loin_xml)

    # Define the namespace map
    namespace_map = {'ns0': 'http://iso.org/2022/ProductDataTemplates/'}

    # Create the IDS XML structure
    ids_root = ET.Element("ids", xmlns="http://standards.buildingsmart.org/IDS")
    info = ET.SubElement(ids_root, "info")
    title = ET.SubElement(info, "title")
    title.text = "My IDS"
    specifications = ET.SubElement(ids_root, "specifications")

    # Iterate through ConstructionObject elements
    for construction_object in loin_root.findall(".//ns0:ConstructionObject", namespaces=namespace_map):
        construction_object_name = construction_object.find(".//ns0:Name", namespaces=namespace_map).text

#         applicability = ET.SubElement(specifications, "applicability")
#         my_entity = ET.SubElement(applicability, "Entity")
#         simple_value = ET.SubElement(my_entity, "simpleValue")
#         simple_value.text = construction_object_name

        # Iterate through Property elements within the ConstructionObject
    for property_element in loin_root.findall(".//ns0:Property", namespaces=namespace_map):
        print(ET.tostring(property_element, encoding="utf-8").decode("utf-8"), 'property_element')
        property_element_name = property_element.find(".//ns0:Name", namespaces=namespace_map)
        if property_element_name is not None:
            property_element_name = property_element.find(".//ns0:Name", namespaces=namespace_map).text
            print(property_element_name, 'property_element_name')

            # Create Applicability element
            applicability = ET.SubElement(specifications, "applicability")
            my_entity = ET.SubElement(applicability, "Entity")
            simple_value = ET.SubElement(my_entity, "simpleValue")
            simple_value.text = construction_object_name
            # Create Requirement element
            my_property = ET.SubElement(specifications, "requirements")
            my_property_name = ET.SubElement(my_property, "Property")
            simple_value_my_property = ET.SubElement(my_property_name, "simpleValue")
            simple_value_my_property.text = property_element_name

    # Convert the IDS XML structure to a string
    formatted_xml = xml.dom.minidom.parseString(ET.tostring(ids_root)).toprettyxml(indent="    ")
    print(formatted_xml, 'formatted_xml')
    return formatted_xml


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'XMLInput' not in request.files:
        return "No file part"

    file = request.files['XMLInput']

    if file.filename == '':
        return "No selected file"

    if file:
        try:
            loin_xml = file.read().decode('utf-8')
            ids_xml = convert_loin_to_ids(loin_xml)

            # Return the IDS XML as plain text
            return ids_xml
        except Exception as e:
            return f"Error during conversion: {str(e)}"
        
def export_my_ids(loin_file_path):
    with open(loin_file_path, "r", encoding="utf-8") as infile:
        loin_xml = infile.read()

    result_xml = convert_loin_to_ids(loin_xml)

    # You can save the result_xml to a file or do whatever you need with it
    with open("exported_ids.xml", "w", encoding="utf-8") as outfile:
        outfile.write(result_xml)

if __name__ == '__main__':
    app.run(debug=True)
