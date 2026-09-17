import os.path
import xml.etree.ElementTree as ET
import lxml.etree as etree
import json
import logging
import re
import os
from drawio_c4_lint.drawio import drawio_serialization
import pandas as pd
import difflib



#TODO need to distinguish objects and other mxGraph cell elements in the XML and include them as a 3rd count in the summary

# Set up logging
logging.basicConfig(
    handlers=[
        logging.StreamHandler()
    ],
    level=logging.INFO,
    format='%(asctime)s [%(levelname)-8s] %(name)s %(funcName)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

class XMLParseException(Exception):
    pass

class C4Lint:
    def __init__(self, xml_file, output_text_description_file=False, include_ids=False,
                 structurizr=False, known_applications=None, check_filename=False):
        logger.debug((f"Initializing C4Lint with xml_file: {xml_file}, "))
        self.errors = {'Systems': [], 'Actors': [], 'Relationships': [], 'Other': []}
        self.warnings = {'Systems': [], 'Actors': [], 'Relationships': [], 'Other': []}
        self.objects = {'Systems': [], 'Actors': [], 'Relationships': [], 'Other': []}
        self.c4_object_count = 0
        self.non_c4_object_count = 0
        self.xml_file = xml_file
        self.output_text_description_file = output_text_description_file
        self.include_ids = include_ids
        self.root = self.parse_xml(xml_file)
        self.linted = False
        self.known_applications = self.load_known_applications(known_applications) if known_applications else []
        self.check_filename = check_filename
        self.structurizr = structurizr
        self.lint()

    def load_known_applications(self, csv_path):
        logger.debug(f"Loading known strings from {csv_path}")
        df = pd.read_csv(csv_path)
        known_strings = df['Business Application Name'].dropna().tolist()
        return known_strings

    def match_strings(self, input_string, known_strings):
        """Match a system name against the known list, ignoring case.

        Returns the matching known name in its own spelling, or, when there is no
        match, up to three near misses worth looking at.
        """
        by_lowercase = {name.lower(): name for name in known_strings}
        input_string_lower = input_string.lower()

        if input_string_lower in by_lowercase:
            return [by_lowercase[input_string_lower]]

        close = difflib.get_close_matches(input_string_lower, by_lowercase, n=3, cutoff=0.6)
        return [by_lowercase[name] for name in close]

    def find_parent(self, element, tree):
        for parent in tree.iter():
            for child in parent:
                if child is element:
                    return parent
        return None

    def parse_xml(self, xml_file):
        logger.debug(f"Parsing XML file: {xml_file}")
        try:
            tree = etree.parse(xml_file)
            xml_data = tree.findall('.//diagram')[0]
            # sometimes the "plain xml" files create with drawio desktop will still have the text
            # attribute in them with '\n ' as content so we need to check for that as well
            if hasattr(xml_data, 'text') and not xml_data.text.isspace():
                try:
                    xml_string = drawio_serialization.decode_diagram_data(xml_data.text)
                    return ET.fromstring(xml_string)
                except Exception:
                    pass
            else:
                xml_data = xml_data.find('.//mxGraphModel')
            xml_string = ET.tostring(xml_data, encoding='utf-8').decode('utf-8')
            return ET.fromstring(xml_string)
        except Exception as e:
            error_message = f"Error parsing XML file: {xml_file}, {str(e)}"
            self.errors['Other'].append(error_message)
            raise XMLParseException(error_message)

    def check_all_systems_connected(self):
        logger.debug("Checking all systems are connected")
        systems = {elem.get('id'): elem for elem in self.root.findall(".//object[@c4Type!='Relationship']")}

        def find_connected_systems(self):
            results = set()
            objects = self.root.findall(".//object")
            for obj in objects:
                mxcell = obj.find(".//mxCell")
                if mxcell is not None:
                    if 'source' in mxcell.attrib or 'target' in mxcell.attrib:
                        # at least one leg is connected
                        if 'source' in mxcell.attrib and 'target' in mxcell.attrib:
                            results.add(mxcell.attrib['source'])
                            results.add(mxcell.attrib['target'])
                        else:
                            self.errors['Relationships'].append(
                                # TODO - include a test case
                                f"ERROR: {obj.attrib['c4Description']} -- one leg disconnected")

            return results

        systems_with_at_least_one_connection = find_connected_systems(self)

        for system_id, system_details in systems.items():
            if system_id not in systems_with_at_least_one_connection:
                self.errors['Systems'].append(f"ERROR: Software System (c4Name: {system_details.attrib['c4Name']}, c4Type: {system_details.attrib['c4Type']}, id {system_id}) is not connected by any relationship.")


    def check_c4_objects(self):
        logger.debug("Checking C4 objects")
        required_attribs = {'c4Name', 'c4Description', 'c4Type', 'c4Technology'}
        objects_found = False

        for elem in self.root.findall(".//object"):
            objects_found = True
            elem_attribs = set(elem.attrib.keys())
            c4_type = elem.attrib.get('c4Type', '').strip()

            if c4_type == "Relationship":
                self.c4_object_count += 1
                self.check_required_attributes(elem, {'c4Description', 'c4Technology'}, category='Relationships', is_relationship=True)
            elif 'c4Type' in elem_attribs:
                self.c4_object_count += 1
                # ToDo this looks like flimsy logic. Need to refactor. Both and add the type lookup by colour
                # parent = self.find_parent(elem, self.root)
                # self.objects['Systems'].append(self.parse_fill_color(parent.attrib.get('style', '')))
                if c4_type == 'Software System':
                    category = 'Systems'
                    system_name = elem.attrib.get('c4Name', '').strip()
                    if not system_name:
                        self.errors['Systems'].append(f"ERROR: 'c4Name' property missing ---  {self.get_readable_properties(elem)}")
                        continue
                    if self.known_applications:
                        matches = self.match_strings(system_name, self.known_applications)
                        if not any(system_name.lower() == match.lower() for match in matches):
                            suggestion = (f" Did you mean {', '.join(matches)}?"
                                          if matches else "")
                            self.warnings['Systems'].append(
                                f"WARN: '{system_name}' is not a known application.{suggestion}")
                elif c4_type == 'Person':
                    category = 'Actors'
                else:
                    category = 'Other'


                self.check_required_attributes(elem, {'c4Name', 'c4Description', 'c4Type'}, category=category)
            else:
                if elem_attribs.isdisjoint(required_attribs):
                    self.non_c4_object_count += 1
                    self.errors['Other'].append(f"ERROR: Non-C4 element found. Label: {elem.attrib.get('label', 'No label')}")
        if not objects_found:
            self.errors['Other'].append("ERROR: No elements of type Object found.")

    def parse_fill_color(style):
        parts = style.split(';')
        color_dict = {p.split('=')[0]: p.split('=')[1] for p in parts if '=' in p}
        fillColor = color_dict.get('fillColor', '#FFFFFF')  # Default to white if no color specified
        if fillColor == '#1061B0':
            return 'Internal'
        elif fillColor == '#8C8496':
            return 'External'
        elif fillColor == '#23A2D9':
            return 'Component'
        else:
            return 'Other'

    def check_required_attributes(self, elem, required_attribs, category, is_relationship=False):
        missing_attribs = [attrib for attrib in required_attribs if not elem.attrib.get(attrib, '').strip()]
        if missing_attribs:
            readable_properties = self.get_readable_properties(elem)
            missing_descr = ', '.join(missing_attribs)
            error_message = f"ERROR: '{missing_descr}' property missing ---  {readable_properties}"
            if self.include_ids:
                error_message += f" (mxCell id: {elem.attrib.get('id')})"
            self.errors[category].append(error_message)

    def get_readable_properties(self, elem):
        props = {k: v.replace('\n', ' ') for k, v in elem.attrib.items() if v.strip() and k not in {'label', 'placeholders', 'id'}}
        readable_props = ', '.join(f"{k}: {v}" for k, v in props.items())
        return readable_props or "No additional properties"

    def is_c4(self):
        required_attribs = {'c4Name', 'c4Description', 'c4Type', 'c4Technology'}
        for elem in self.root.findall(".//object"):
            elem_attribs = set(elem.attrib.keys())
            if not elem_attribs.isdisjoint(required_attribs):
                return True
        return False

    def has_errors(self):
        if not self.linted:
            self.lint()
        return any(self.errors.values())

    @property
    def error_count(self):
        if not self.linted:
            raise RuntimeError("Use .lint() method first")
        return sum(len(errors) for errors in self.errors.values())

    def lint(self):
        if self.linted:
            return self.errors

        self.check_c4_objects()
        self.check_all_systems_connected()
        if self.check_filename:
            self.check_filename_format()
        self.linted = True
        return self.errors

    def to_model(self):
        """The diagram as plain data: elements keyed by id, plus relationships between them."""
        elements = {}
        relationships = []
        for elem in self.root.findall(".//object"):
            c4_type = elem.attrib.get("c4Type", "").strip()
            description = elem.attrib.get("c4Description", "").replace("\n", " ").strip()
            if c4_type == "Relationship":
                # source and target live on the mxCell inside the object, not on the object
                mxcell = elem.find(".//mxCell")
                relationships.append({
                    "source": mxcell.attrib.get("source", "") if mxcell is not None else "",
                    "target": mxcell.attrib.get("target", "") if mxcell is not None else "",
                    "description": description,
                    "technology": elem.attrib.get("c4Technology", "").strip(),
                })
            else:
                elements[elem.attrib.get("id", "")] = {
                    "id": elem.attrib.get("id", ""),
                    "name": elem.attrib.get("c4Name", "").replace("\n", " ").strip(),
                    "description": description,
                    "type": c4_type,
                    "technology": elem.attrib.get("c4Technology", "").strip(),
                }
        return {"elements": elements, "relationships": relationships}

    def to_json(self):
        return json.dumps(self.to_model(), indent=2)

    def to_structurizr(self):
        """Render the diagram as a Structurizr DSL workspace."""
        model = self.to_model()

        def identifier(element_id, name):
            base = re.sub(r'\W+', '', (name or element_id).title()) or 'element'
            return base[0].lower() + base[1:]

        keywords = {'Person': 'person', 'Software System': 'softwareSystem'}
        names = {}
        lines = ['workspace {', '', '    model {']
        for element_id, element in model['elements'].items():
            names[element_id] = identifier(element_id, element['name'])
            keyword = keywords.get(element['type'], 'softwareSystem')
            description = element['description'].replace('"', "'")
            lines.append(f'        {names[element_id]} = {keyword} '
                         f'"{element["name"]}" "{description}"')
        for relationship in model['relationships']:
            source = names.get(relationship['source'])
            target = names.get(relationship['target'])
            if not source or not target:
                continue
            description = relationship['description'].replace('"', "'")
            technology = relationship['technology'].replace('"', "'")
            line = f'        {source} -> {target} "{description}"'
            if technology:
                line += f' "{technology}"'
            lines.append(line)
        lines += ['    }', '}']
        return "\n".join(lines)

    def check_filename_format(self):
        file = os.path.basename(self.xml_file)
        filename_pattern = r"C4 L[01234] .*?.drawio"
        if not re.match(filename_pattern, file):
            self.errors['Other'].append(f"ERROR: Filename '{self.xml_file}' does not match expected format 'C4 L<x> <system name>.drawio'")


    def summary(self):
        if not self.linted:
            self.lint()
        return {
            'errors': sum(len(v) for v in self.errors.values()),
            'warnings': sum(len(v) for v in self.warnings.values()),
            'c4_objects': self.c4_object_count,
            'non_c4_objects': self.non_c4_object_count,
        }

    def __str__(self):
        if not self.linted:
            self.lint()

        lines = [60 * '#', f"C4 Linter Input: {self.xml_file}"]

        if not self.is_c4():
            lines.append("  No C4 objects found. No linting performed.")
            return "\n".join(lines) + "\n"

        for category in ('Systems', 'Actors', 'Relationships', 'Other'):
            findings = self.errors[category] + self.warnings[category]
            if findings:
                lines.append(f"\n  === {category} ===")
                lines.extend(f"  {finding}" for finding in findings)

        counts = self.summary()
        lines.append("\n  === Summary ===")
        lines.append(f"  {counts['errors']} error(s), {counts['warnings']} warning(s).")
        lines.append(f"  {counts['c4_objects']} C4 object(s), {counts['non_c4_objects']} non-C4 object(s).")

        if self.structurizr:
            lines.append("\n  === Structurizr DSL ===")
            lines.append(self.to_structurizr())

        return "\n".join(lines) + "\n"
