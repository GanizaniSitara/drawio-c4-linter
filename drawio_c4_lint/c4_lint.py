import xml.etree.ElementTree as ET
import lxml.etree as etree


class C4Lint:
    def __init__(self, xml_file):
        self.errors = []
        self.xml_file = xml_file
        try:
            self.x = etree.parse(self.xml_file)
            self.xml_data = self.x.findall('.//diagram')[0]
            self.xml_string = ET.tostring(self.xml_data, encoding='utf8').decode('utf8')
            self.root = ET.fromstring(self.xml_string)
        except Exception as e:
            error_message = f"Error parsing XML file: {xml_file}, {str(e)}"
            self.errors.append(error_message)
            raise Exception(error_message)



    def check_all_systems_connected(self):
        systems = {elem.get('id'): elem for elem in self.root.findall(".//object[@c4Type='Software System']")}
        connections = {elem.get('source'): elem.get('target') for elem in
                       self.root.findall(".//mxCell[@source][@target]")}

        for system_id in systems:
            if system_id not in connections and system_id not in connections.values():
                self.errors.append(f"Software System (id: {system_id}) is not connected by any relationship.")


    # def check_c4_objects(self):
    #     objects_found = False
    #     required_attribs = {'c4Name', 'c4Description', 'c4Type', 'c4Technology'}
    #
    #     for elem in self.root.findall(".//object"):
    #         objects_found = True
    #         elem_attribs = set(elem.attrib.keys())
    #         c4_type = elem.attrib.get('c4Type', '').strip()
    #
    #         if c4_type == "Relationship":
    #             c4_description = elem.attrib.get('c4Description', '').strip()
    #             c4_technology = elem.attrib.get('c4Technology', '').strip()
    #
    #             if not c4_description:
    #                 self.errors.append(f"mxCell (id: {elem.attrib.get('id')}) missing 'C4 relationship description' property.")
    #             if not c4_technology:
    #                 self.errors.append(f"mxCell (id: {elem.attrib.get('id')}) missing 'C4 relationship technology' property.")
    #         elif 'c4Type' in elem_attribs:
    #             c4_name = elem.attrib.get('c4Name', '').strip()
    #             c4_description = elem.attrib.get('c4Description', '').strip()
    #
    #             if not c4_name:
    #                 self.errors.append(f"mxCell (id: {elem.attrib.get('id')}) missing 'C4 name' property.")
    #             if not c4_description:
    #                 self.errors.append(f"mxCell (id: {elem.attrib.get('id')}) missing 'C4 description' property.")
    #             if not c4_type:
    #                 self.errors.append(f"mxCell (id: {elem.attrib.get('id')}) missing 'C4 type' property.")
    #         else:
    #             if elem_attribs.isdisjoint(required_attribs):
    #                 self.errors.append(f"Non C4 element (id: {elem.attrib.get('id')}) found.")
    #
    #     if not objects_found:
    #         self.errors.append("No elements of type Object found.")

    def check_c4_objects(self):
        self.c4_object_count = 0
        self.non_c4_object_count = 0
        objects_found = False
        required_attribs = {'c4Name', 'c4Description', 'c4Type', 'c4Technology'}

        for elem in self.root.findall(".//object"):
            objects_found = True
            elem_attribs = set(elem.attrib.keys())
            c4_type = elem.attrib.get('c4Type', '').strip()

            if c4_type == "Relationship":
                self.c4_object_count += 1
                c4_description = elem.attrib.get('c4Description', '').strip()
                c4_technology = elem.attrib.get('c4Technology', '').strip()

                if not c4_description:
                    self.errors.append(f"mxCell (id: {elem.attrib.get('id')}) missing 'C4 relationship description' property.")
                if not c4_technology:
                    self.errors.append(f"mxCell (id: {elem.attrib.get('id')}) missing 'C4 relationship technology' property.")
            elif 'c4Type' in elem_attribs:
                self.c4_object_count += 1
                c4_name = elem.attrib.get('c4Name', '').strip()
                c4_description = elem.attrib.get('c4Description', '').strip()

                if not c4_name:
                    self.errors.append(f"mxCell (id: {elem.attrib.get('id')}) missing 'C4 name' property.")
                if not c4_description:
                    self.errors.append(f"mxCell (id: {elem.attrib.get('id')}) missing 'C4 description' property.")
                if not c4_type:
                    self.errors.append(f"mxCell (id: {elem.attrib.get('id')}) missing 'C4 type' property.")
            else:
                if elem_attribs.isdisjoint(required_attribs):
                    self.non_c4_object_count += 1
                    self.errors.append(f"Non-C4 element (id: {elem.attrib.get('id')}) found.")

        if not objects_found:
            self.errors.append("No elements of type Object found.")


    def is_c4(self):
        """Check if the XML contains objects with C4 attributes."""
        required_attribs = {'c4Name', 'c4Description', 'c4Type', 'c4Technology'}
        for elem in self.root.findall(".//object"):
            elem_attribs = set(elem.attrib.keys())
            if not elem_attribs.isdisjoint(required_attribs):
                return True
        return False


    def check_all_systems_connected(self):
        systems = {elem.get('id'): elem for elem in self.root.findall(".//object[@c4Type='Software System']")}
        connections = {elem.get('source'): elem.get('target') for elem in
                       self.root.findall(".//mxCell[@source][@target]")}

        for system_id in systems:
            if system_id not in connections and system_id not in connections.values():
                self.errors.append(f"Software System (id: {system_id}) is not connected by any relationship.")


    def lint(self):
        self.check_c4_objects()
        self.check_all_systems_connected()
        return self.errors

    def __str__(self):
        output = f"Linter Output for {self.xml_file}:\n"
        if not self.errors:
            if self.is_c4():
                self.lint()
                if self.errors:
                    error_messages = '\n'.join(f"  ERROR: {error}" for error in self.errors)
                    return f"{output}{error_messages}\n  Summary: {self.c4_object_count} C4 objects, {self.non_c4_object_count} non-C4 objects found.\n"
                else:
                    return f"{output}  No linting issues detected.\n  Summary: {self.c4_object_count} C4 objects, {self.non_c4_object_count} non-C4 objects found.\n"
            else:
                return f"{output}  No C4 objects found. No linting performed.\n"
        else:
            if "Error parsing XML file" in self.errors[0]:
                return f"{output}  Unable to parse file. It may be empty or malformed.\n"
            else:
                error_messages = '\n'.join(f"  ERROR: {error}" for error in self.errors)
                return f"{output}{error_messages}\n"



