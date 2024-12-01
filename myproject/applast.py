from flask import Flask, render_template, request, send_file
import xml.etree.ElementTree as ET
from io import BytesIO
import xml
import xml.dom.minidom
from flask import jsonify
import csv
from flask import session
app = Flask(__name__)

app.secret_key = 'elif'

def find_element_by_uuid(root, target_uuid, namespace_map):
    xpath_query = f".//*[@UUID='{target_uuid}']"
    elements = root.findall(xpath_query, namespaces=namespace_map)    
    return elements
 
 
def get_desite_content():
    desite_file_path = "data/desiterule.qa.xml"
    with open(desite_file_path, "r", encoding="utf-8") as desite_file:
        desite_xml = desite_file.read()
    return desite_xml 
 
# Datatype Conversion
def datatypetranslation(value, target_column):
    csv_file = 'data\datatypeconv.csv'  
    with open(csv_file, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            for column_name, column_value in row.items():
                if column_value == value and column_name != target_column:
                    print("column_value", column_value)
                    print("column_name", column_name)
                    return row[target_column]
    return None

@app.route('/convert_loin_to_ids')
def convert_loin_to_ids(loin_xml, desite_content):
    # Parse the LOIN XML string
    loin_root = ET.fromstring(loin_xml)
    desite_root = ET.fromstring(desite_content)
    
    # Get Selections from Dashboard
    selected_filter = request.form.get('selectedFilter')
    session['selected_filter'] = selected_filter
    
    selected_filterpropertySet = session.get('selected_filterpropertySet')
      
    selected_filterproperty = request.form.get('selectedProperty')
    session['selected_filterproperty'] = selected_filterproperty

    selected_filterDatatype = request.form.get('Filter - selectedDatatype')
    session['selected_filterDatatype'] = selected_filterDatatype
    # Translate Datatype
    selected_filterDatatype_ids = datatypetranslation(selected_filterDatatype, 'IDS')

    selected_reqpropertySet = request.form.get('Requirement - selectedPropertySet')
    session['selected_reqpropertySet'] = selected_reqpropertySet
 
    selected_reqproperty = request.form.get('Requirement - selectedProperty')
    session['selected_reqproperty'] = selected_reqproperty

    selected_reqDatatype = request.form.get('Requirement - selectedDatatype')
    session['selected_reqDatatype'] = selected_reqDatatype
    # Translate Datatype
    selected_reqDatatype_ids = datatypetranslation(selected_reqDatatype, 'IDS')

    
    # Define the namespace map
    namespace_map = {'ns0': 'http://iso.org/2022/ProductDataTemplates/'}

    # Create the IDS XML structure
    ids_root = ET.Element("ids", xmlns="http://standards.buildingsmart.org/IDS")
    info = ET.SubElement(ids_root, "info")
    title = ET.SubElement(info, "title")
    title.text = "My IDS"
    specifications = ET.SubElement(ids_root, "specifications")

                      
    # Create Applicability element
    if selected_filter != "None":
        applicability = ET.SubElement(specifications, "applicability")
        my_entity = ET.SubElement(applicability, "Entity")
        simple_value = ET.SubElement(my_entity, "simpleValue")
        # Translate Name
        simple_value.text = ("Ifc"+ selected_filter)
        
    
    if selected_filterproperty is not None:
        applicability_filter = ET.SubElement(specifications, "applicability")
        my_filter_entity = ET.SubElement(applicability_filter, "PropertySet",datatype=selected_filterDatatype_ids)
        simple_value_filter = ET.SubElement(my_filter_entity, "simpleValue")
        simple_value_filter.text = selected_filterpropertySet
        simple_value_my_filter = ET.SubElement(my_filter_entity, "name")
        simple_value_my_filter.text = selected_filterproperty
        
           
                    
    # Filter of Desite
    filter_element_desite = desite_root.findall(".//filter[@name='ifcType']")
    for filterdesite in filter_element_desite:
        print(ET.tostring(filterdesite, encoding="utf-8").decode("utf-8"), "filterdesite")
        if filterdesite is not None:
            # Change the pattern attribute to the value of target_name
            filterdesite.set("pattern", selected_filter)
                            
                                   
                    
    # Create Requirement element
    my_property_set = ET.SubElement(specifications, "requirements")
    print("my_property_set", my_property_set)
    my_property_name = ET.SubElement(my_property_set, "propertySet")
    print("my_property_name", my_property_name)
    simple_value_my_property = ET.SubElement(my_property_name, "name")
    print("simple_value_my_property", simple_value_my_property)
    print("selected_reqpropertySet", selected_reqpropertySet)
    simple_value_my_property.text = selected_reqpropertySet
    print("simple_value_my_property.text", simple_value_my_property.text)
    
                    
    # Create Requirement element
    my_property_name = ET.SubElement(my_property_set, "Property", datatype=selected_reqDatatype_ids)
    simple_value_my_property = ET.SubElement(my_property_name, "name")
    simple_value_my_property.text = selected_reqproperty
                    
    desite_property_name = f"{selected_reqpropertySet}:{selected_reqproperty}"
    selected_reqDatatype_desite = datatypetranslation(selected_reqDatatype_ids, 'DESITE')
    desite_datatype = selected_reqDatatype_desite
    
    print("desite_datatype", desite_datatype)
                    
    for script_code_element in desite_root.findall(".//ruleScript/code"):
        script_code = script_code_element.text
        my_param = f"desiteAPI.getPropertyValue(id,'PropertySet:Property','xs:Datatype')"
        if my_param in script_code:
                            # Modify the script code
            new_script_code = script_code.replace(
                my_param,
                f"desiteAPI.getPropertyValue(id,'{desite_property_name}','{desite_datatype}')"
            )

            script_code_element.text = new_script_code
            break  




    # Convert the IDS XML structure to a string
    formatted_xml = xml.dom.minidom.parseString(ET.tostring(ids_root)).toprettyxml(indent="    ")
    return formatted_xml, new_script_code, desite_root


@app.route('/process_xml_endpoint', methods=['POST'])
def process_xml_endpoint():
    file = request.files['XMLInput']
    
    loin_xml = file.read().decode('utf-8')  # Assuming the file is LOIN XML.
    
    loin_root = ET.fromstring(loin_xml)

    desite_content = get_desite_content()
    
    selected_filter = request.form.get('selectedFilter')
    session['selected_filter'] = selected_filter
    
    
    selected_filterpropertySet = request.form.get('Filter - selectedPropertySet')
    session['selected_filterpropertySet'] = selected_filterpropertySet
    print("selected_filterpropertySet2", selected_filterpropertySet)
    
    selected_filterproperty = request.form.get('selectedProperty')
    session['selected_filterproperty'] = selected_filterproperty
    print("selected_filterproperty2", selected_filterproperty)
    
    selected_filterDatatype = request.form.get('Filter - selectedDatatype')
    print("selected_filterDatatype2", selected_filterDatatype)
    session['selected_filterDatatype'] = selected_filterDatatype
    
    selected_reqpropertySet = request.form.get('Requirement - selectedPropertySet')
    print("selected_reqpropertySet2", selected_reqpropertySet)
    session['selected_reqpropertySet'] = selected_reqpropertySet
    
    selected_reqproperty = request.form.get('Requirement - selectedProperty')
    print("selected_reqproperty2", selected_reqproperty)
    session['selected_reqproperty'] = selected_reqproperty
    
    selected_reqDatatype = request.form.get('Requirement - selectedDatatype')
    print("selected_reqDatatype2", selected_reqDatatype)
    session['selected_reqDatatype'] = selected_reqDatatype
    
    

    # Call your conversion function with the selectedFilter value
    formatted_xml, new_script_code, desite_root = convert_loin_to_ids(loin_xml, desite_content)

    # Use the returned data as needed...
    return jsonify({
        'formattedXml': formatted_xml,
        'newScriptCode': new_script_code
        # Include other data as needed
    })



def get_construction_objects(loin_xml):
    
    # Parse the LOIN XML string
    loin_root = ET.fromstring(loin_xml)

    # Define the namespace map
    namespace_map = {'ns0': 'http://iso.org/2022/ProductDataTemplates/'}

    # Find distinct ConstructionObjects in the LOIN XML via DataTemplate
    construction_objects = set()   
    for construction_object in loin_root.findall(".//ns0:DataTemplate", namespaces=namespace_map):     
        construction_object_name = construction_object.find(".//ns0:IsDataTemplateFor", namespaces=namespace_map)
        if construction_object_name is not None:
            target_name = construction_object_name.get("TargetName")
            construction_objects.add(target_name)
            
    return construction_objects


def get_property_sets_and_properties(loin_xml):
    # Parse the LOIN XML string
    loin_root = ET.fromstring(loin_xml)

    # Define the namespace map
    namespace_map = {'ns0': 'http://iso.org/2022/ProductDataTemplates/'}

    # Find distinct property sets and properties in the LOIN XML via DataTemplate
    property_sets = set()
    properties = set()
    property_datatypes = set()
    
    for construction_object in loin_root.findall(".//ns0:DataTemplate", namespaces=namespace_map):
        construction_object_name = construction_object.find(".//ns0:IsDataTemplateFor", namespaces=namespace_map)
        if construction_object_name is not None:
            target_name = construction_object_name.get("TargetName")
        
        construction_object_name = construction_object.findall(".//ns0:SetOfProperties", namespaces=namespace_map)
        for setofprop in construction_object_name:
            target_UUID = setofprop.get("TargetUUID")
            setofprop_name = setofprop.get("TargetName")
            property_sets.add(setofprop_name)         
            found_elements = find_element_by_uuid(loin_root, target_UUID, namespace_map)
            for element in found_elements:
                property_elements = element.findall(".//ns0:Property", namespaces=namespace_map)
                # Find Target UUID 
                for property_element in property_elements:              
                    target_UUID_property = property_element.get("TargetUUID")
                    property_name = property_element.get("TargetName")
                    properties.add(f"{property_name}")                                  
                    my_property_elements = find_element_by_uuid(loin_root, target_UUID_property, namespace_map)
                    # Find Datatype
                    for my_element in my_property_elements:
                        property_elements_name = my_element.find(".//ns0:Name", namespaces=namespace_map)
                        property_elements_datatype = my_element.find(".//ns0:Datatype", namespaces=namespace_map)
                        if property_elements_name is not None:
                            property_elements_name = my_element.find(".//ns0:Name", namespaces=namespace_map).text
                            property_elements_datatype = my_element.find(".//ns0:Datatype", namespaces=namespace_map).text
                            property_datatypes.add(f"{property_elements_datatype}")
                    

    return property_sets, properties, property_datatypes


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/uploadinfo', methods=['POST'])
def uploadinfo():
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
            desite_xml = get_desite_content()


            construction_objects = get_construction_objects(loin_xml)

            
            property_sets, properties, property_datatypes = get_property_sets_and_properties(loin_xml)



            return jsonify({
                            'message': 'File received',
                            'filename': file.filename,
                            'constructionObjects': list(construction_objects),
                            'propertySets': list(property_sets),
                            'properties': list(properties),
                            'dataTypes': list(property_datatypes)
                        })
        except Exception as e:
            return f"Error during conversion: {str(e)}"

  
  
  
@app.route('/processxml', methods=['POST'])
def process_xml():
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
            desite_xml = get_desite_content()

            # Convert LOIN to IDS and modify Desite
            formatted_xml, new_script_code, desite_root = convert_loin_to_ids(loin_xml, desite_xml)


            construction_objects = get_construction_objects(loin_xml)

            property_sets, properties, property_datatypes = get_property_sets_and_properties(loin_xml)


            # Return the HTML template with options for dynamic dropdowns
            return formatted_xml

        except Exception as e:
            return f"Error during conversion: {str(e)}"





  
# Save IDS.xml Export to the local device  
def export_my_ids(loin_file_path):
    with open(loin_file_path, "r", encoding="utf-8") as infile:
        loin_xml = infile.read()
    result_xml = convert_loin_to_ids(loin_xml)


# Save desite.qa.xml Export to the local device        
def create_desite_xml(desite_root, output_path):
    desite_tree = ET.ElementTree(desite_root)
    with open(output_path, "wb") as desite_file:
        desite_tree.write(desite_file, encoding="utf-8", xml_declaration=True)


# Generate desite.qa.xml 
@app.route('/generate_desite', methods=['GET'])
def generate_desite():
    try:
        desite_xml = get_desite_content()           
        desite_root = ET.fromstring(desite_xml)
        output_path = "output/output_desite.qa.xml"
        create_desite_xml(desite_root, output_path)

        # Send the generated file as a response for download
        return send_file(output_path, as_attachment=True)
    except Exception as e:
        return f"Error during desite XML generation: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True)


