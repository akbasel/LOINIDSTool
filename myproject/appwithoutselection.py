from flask import Flask, render_template, request, send_file
import xml.etree.ElementTree as ET
from io import BytesIO
import xml
import xml.dom.minidom

app = Flask(__name__)

def find_element_by_uuid(root, target_uuid, namespace_map):
    # Find elements with the specified UUID
    xpath_query = f".//*[@UUID='{target_uuid}']"
    elements = root.findall(xpath_query, namespaces=namespace_map)
    
    return elements

def convert_loin_to_ids(loin_xml, desite_content):
    # Parse the LOIN XML string
    loin_root = ET.fromstring(loin_xml)
    desite_root = ET.fromstring(desite_content)
    

    
    # Define the namespace map
    namespace_map = {'ns0': 'http://iso.org/2022/ProductDataTemplates/'}

    # Create the IDS XML structure
    ids_root = ET.Element("ids", xmlns="http://standards.buildingsmart.org/IDS")
    info = ET.SubElement(ids_root, "info")
    title = ET.SubElement(info, "title")
    title.text = "My IDS"
    specifications = ET.SubElement(ids_root, "specifications")

    # Iterate through ConstructionObject elements
    for construction_object in loin_root.findall(".//ns0:DataTemplate", namespaces=namespace_map):
        construction_object_name = construction_object.find(".//ns0:IsDataTemplateFor", namespaces=namespace_map)
        if construction_object_name is not None:
            target_name = construction_object_name.get("TargetName")
        
        
        construction_object_name = construction_object.findall(".//ns0:SetOfProperties", namespaces=namespace_map)
        for setofprop in construction_object_name:
            target_UUID = setofprop.get("TargetUUID")
            setofprop_name = setofprop.get("TargetName")      
            
            found_elements = find_element_by_uuid(loin_root, target_UUID, namespace_map)
            for element in found_elements:
                property_elements = element.findall(".//ns0:Property", namespaces=namespace_map)
                for property_element in property_elements:              
                    # Extract Target UUID from the Property element
                    target_UUID_property = property_element.get("TargetUUID")
#                     print("  Target UUID of Component:", target_UUID_property)
                                       
                    my_property_elements = find_element_by_uuid(loin_root, target_UUID_property, namespace_map)
                    for my_element in my_property_elements:
#                         print(ET.tostring(my_element, encoding="utf-8").decode("utf-8"), "hoii")
                        property_elements_name = my_element.find(".//ns0:Name", namespaces=namespace_map)
                        property_elements_datatype = my_element.find(".//ns0:Datatype", namespaces=namespace_map)
#                         print(ET.tostring(property_elements_name, encoding="utf-8").decode("utf-8"), "property_elements_name")
                        if property_elements_name is not None:
                            property_elements_name = my_element.find(".//ns0:Name", namespaces=namespace_map).text
                            property_elements_datatype = my_element.find(".//ns0:Datatype", namespaces=namespace_map).text
#                             print(property_elements_datatype, "property_elements_datatype")
                            
                            
                    # Create Applicability element
                    applicability = ET.SubElement(specifications, "applicability")
                    my_entity = ET.SubElement(applicability, "Entity")
                    simple_value = ET.SubElement(my_entity, "simpleValue")
                    simple_value.text = target_name
                    #     Filter of Desite
                    filter_element_desite = desite_root.findall(".//filter[@name='ifcType']")
                    for filterdesite in filter_element_desite:
#                         print(ET.tostring(filterdesite, encoding="utf-8").decode("utf-8"), "filterdesite")
                        if filter_element_desite is not None:
                            # Change the pattern attribute to the value of target_name
                            filterdesite.set("pattern", target_name)
                            
                    
                
                    
                    # Create Requirement element
                    my_property_set = ET.SubElement(specifications, "requirements")
                    my_property_name = ET.SubElement(my_property_set, "propertySet")
                    simple_value_my_property = ET.SubElement(my_property_name, "simpleValue")
                    simple_value_my_property.text = setofprop_name
                    
                    # Create Requirement element
                    my_property = ET.SubElement(specifications, "requirements")
#                     my_property_name = ET.SubElement(my_property, "Property")
                    my_property_name = ET.SubElement(my_property, "Property", datatype=property_elements_datatype)
                    simple_value_my_property = ET.SubElement(my_property_name, "simpleValue")
                    simple_value_my_property.text = property_elements_name
                    
                    desite_property_name = f"{setofprop_name}:{property_elements_name}"
                    desite_datatype = property_elements_datatype
#                     print(desite_property_name, desite_datatype)
                    
                    for script_code_element in desite_root.findall(".//ruleScript/code"):
                        script_code = script_code_element.text
#                         print(script_code, "script_code")
                        my_param = f"desiteAPI.getPropertyValue(id,'PropertySet:Property','xs:Datatype')"
                        if my_param in script_code:
                            # Modify the script code
                            new_script_code = script_code.replace(
                                my_param,
                                f"desiteAPI.getPropertyValue(id,'{desite_property_name}','{desite_datatype}')"
                            )
#                 print("Original script code:", script_code)
#                 print("Modified script code:", new_script_code)

                            script_code_element.text = new_script_code
                            break  
    
#                     print("new_script_code", new_script_code)




    # Convert the IDS XML structure to a string
    formatted_xml = xml.dom.minidom.parseString(ET.tostring(ids_root)).toprettyxml(indent="    ")
    print(ET.tostring(desite_root, encoding="utf-8").decode("utf-8"), "desite_root")
#     print(formatted_xml, 'formatted_xml')
    return formatted_xml, new_script_code, desite_root


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
            # Read the LOIN XML directly from the uploaded file
            loin_xml = file.read().decode('utf-8')
            
            # The XML content for desite can be read from the existing desite file or any other source
            desite_file_path = "C:/Users/MSI-NB/Desktop/LOIN/desiterule.qa.xml"
            with open(desite_file_path, "r", encoding="utf-8") as desite_file:
                desite_xml = desite_file.read()

            # Convert LOIN to IDS and modify Desite
            formatted_xml, new_script_code, desite_root = convert_loin_to_ids(loin_xml, desite_xml)

            # Return the IDS XML as plain text
            return formatted_xml
        except Exception as e:
            return f"Error during conversion: {str(e)}"
        
def export_my_ids(loin_file_path):
    with open(loin_file_path, "r", encoding="utf-8") as infile:
        loin_xml = infile.read()

    result_xml = convert_loin_to_ids(loin_xml)

    # You can save the result_xml to a file or do whatever you need with it
    with open("exported_ids.xml", "w", encoding="utf-8") as outfile:
        outfile.write(result_xml)
        
def create_desite_xml(desite_root, output_path):
    # Create a new ElementTree with the modified Desite root
    desite_tree = ET.ElementTree(desite_root)

    # Write the ElementTree to the output file
    with open(output_path, "wb") as desite_file:
        desite_tree.write(desite_file, encoding="utf-8", xml_declaration=True)

# ... Your other functions ...

@app.route('/generate_desite', methods=['GET'])
def generate_desite():
    try:
        # The XML content for desite can be read from the existing desite file or any other source
        desite_file_path = "C:/Users/MSI-NB/Desktop/LOIN/desiterule.qa.xml"
        with open(desite_file_path, "r", encoding="utf-8") as desite_file:
            desite_xml = desite_file.read()

        # Assuming you already have desite_root available (e.g., from a previous conversion)
        # If not, modify accordingly based on your actual data source
        desite_root = ET.fromstring(desite_xml)

        # Specify the output path for the generated file
        output_path = "C:/Users/MSI-NB/Downloads/output_desite.qa.xml"

        # Call the create_desite_xml function
        create_desite_xml(desite_root, output_path)

        # Send the generated file as a response for download
        return send_file(output_path, as_attachment=True)
    except Exception as e:
        return f"Error during desite XML generation: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True)
