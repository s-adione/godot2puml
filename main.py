import os
import argparse
from project_godot2puml import ProjectGodot2PUML

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate pUML class diagrams from a Godot project.")
    parser.add_argument("godot_project_directory", help="Path to the Godot project directory")
    parser.add_argument("output_directory", help="Path to the .puml files directory")

    args = parser.parse_args()
    if not args.godot_project_directory or not args.output_directory: # should not happens
        parser.print_help()
        exit(1)

    os.makedirs(args.output_directory, exist_ok=True)

    project_Godot2pUML = ProjectGodot2PUML(args.godot_project_directory, args.output_directory)
    project_Godot2pUML.process_godot_project()

    merged_path = os.path.join(args.output_directory, "godot_project.puml")
    project_Godot2pUML.merge_uml(merged_path)

    print(f"UML generation complete at {merged_path}")