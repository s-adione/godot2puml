import os
from godot2puml import Godot2PUML
import re

class ProjectGodot2PUML:
    def __init__(self, project_dir, output_dir):
        self.project_dir = project_dir
        self.output_dir = output_dir

    def get_class_names(self):
        """
        Scans all .gd files in the project directory and return all class names defined with `class_name`.
        """
        class_names = set()

        # Walk through the project directory
        for root, dirs, files in os.walk(self.project_dir):
            for file in files:
                if file.endswith('.gd'):
                    file_path = os.path.join(root, file)
                    print(f'Gathering class names from {file_path}...')

                    with open(file_path, 'r', encoding='utf-8') as f:
                        godot_script = f.read()

                    for class_name in re.findall(r'class_name (\w+)', godot_script):
                        class_names.add(class_name)

        return list(class_names)


    def process_godot_project(self):
        """
        Walks through a Godot project directory and generates PlantUML diagrams for all .gd scripts.
        The diagrams are saved in a separate output directory.
        """

        os.makedirs(self.output_dir, exist_ok=True)

        # We gather the class names to setup the relations between classes when processing the pUML files
        # For example, in the example below if MyWeapon is not known as a class, we cannot setup the relations
        # @startuml
        # class MyPlayer {
        # }
        # Node3D <|-- MyPlayer
        # MyPlayer --> MyWeapon : 1
        # @enduml

        class_names = self.get_class_names()
        print(f'Gathered class names: {class_names}')

        for dirpath, dirnames, filenames in os.walk(self.project_dir):
            for filename in filenames:
                if filename.endswith('.gd'):
                    filepath = os.path.join(dirpath, filename)
                    print(f'Processing {filepath}...')

                    with open(filepath, 'r', encoding='utf-8') as f:
                        godot_script = f.read()

                    #if not re.search(r'class_name (\w+)', godot_script):
                    #    print(f'No class_name found in {file}. Skipping file.')
                    #    continue  # Skip the file if no class_name is found

                    godot2PUML = Godot2PUML(filename, godot_script, class_names)
                    uml_code = godot2PUML.process()

                    uml_file_name = os.path.splitext(filename)[0] + '.puml'
                    uml_file_path = os.path.join(self.output_dir, uml_file_name)

                    with open(uml_file_path, 'w', encoding='utf-8') as uml_file:
                        uml_file.write(uml_code)
                    print(f'Generated PlantUML for {filename} at {uml_file_path}')

    def merge_uml(self, merged_file_path):
        """
        Merges all generated .puml files into a single PlantUML file.
        The merged file will include all class diagrams from individual files using !include.
        """
        # Find all .puml files in the output directory
        uml_files = [f for f in os.listdir(self.output_dir) if f.endswith('.puml')]

        # Start the merged PlantUML file with @startuml
        merged_uml = "@startuml\n"

        # Include each individual .puml file
        for uml_file in uml_files:
            uml_file_path = os.path.join(self.output_dir, uml_file)
            merged_uml += f'!include {uml_file_path}\n'

        # End the merged PlantUML file with @enduml
        merged_uml += "@enduml"

        # Save the merged content to the specified file
        with open(merged_file_path, 'w', encoding='utf-8') as merged_file:
            merged_file.write(merged_uml)

        print(f'Merged PlantUML saved to {merged_file_path}')