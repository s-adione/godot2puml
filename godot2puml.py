import re


class Godot2PUML:
    def __init__(self, filename, godot_script, class_names):
        self.godot_script = godot_script
        self.filename = filename
        self.class_names = class_names
        self.class_info = {
            'namespace': None,
            'extends': None,
            'class_name': None,
            'signals': [],
            'methods': [],
            'properties': [],
            'associations': [],
            'lists_associations': []
        }

    def parse_script(self):
        """
        Main entry point to parse class metadata from a Godot script.
        """
        self._parse_namespace()
        self._parse_extends()
        self._parse_class_name()
        self._parse_signals()
        self._parse_methods()
        self._parse_properties()

    def _parse_namespace(self):
        namespace_pattern = r'^###\s*namespace\s+(\w+)'
        match = re.match(namespace_pattern, self.godot_script)
        if match:
            self.class_info['namespace'] = match.group(1)

    def _parse_extends(self):
        extends_pattern = r'extends (\w+)'
        match = re.search(extends_pattern, self.godot_script)
        if match:
            self.class_info['extends'] = match.group(1)

    def _parse_class_name(self):
        class_name_pattern = r'class_name (\w+)'
        match = re.search(class_name_pattern, self.godot_script)
        if match:
            self.class_info['class_name'] = match.group(1)

    def _parse_signals(self):
        signal_pattern = r'^signal\s+(\w+)\s*(?:\(([^)]*)\))?'
        matches = re.findall(signal_pattern, self.godot_script)
        signals = []

        for name, args in matches:
            args_data = self._parse_args(args)
            signals.append({'signal': name, 'args': args_data})

        self.class_info['signals'] = signals

    def _parse_methods(self):
        method_pattern = r'^func\s+(\w+)\s*\(([^)]*)\)\s*(?:->\s*(\w+))?'
        matches = re.findall(method_pattern, self.godot_script, re.MULTILINE)
        methods = []

        for name, args_str, return_type in matches:
            args_data = self._parse_args(args_str)
            methods.append({
                'method': name,
                'args': args_data,
                'return': return_type if return_type else None
            })

        self.class_info['methods'] = methods

    def _parse_properties(self):
        var_pattern = r'^var\s+([^\n=]+)'

        matches = re.findall(var_pattern, self.godot_script, flags=re.MULTILINE)

        for match in matches:
            arg_str = match.strip()
            parsed_args = self._parse_args(arg_str)
            self.class_info['properties'].extend(parsed_args)

    def _parse_args(self, args_str):
        args = []
        if not args_str:
            return args

        for arg in args_str.split(','):
            arg = arg.strip()
            if not arg:
                continue
            if ':' in arg:
                name, type_ = [part.strip() for part in arg.split(':', 1)]
                args.append((name, type_))
            else:
                args.append((arg, None))
        return args


    def _type_mentions_class(self, type_str, class_name):
        if not type_str:
            return False
        return re.search(rf'\b{re.escape(class_name)}\b', type_str) is not None

    def generate_plantuml(self):
        """
        Generates a PlantUML class diagram based on the parsed class information
        """
        uml = ["@startuml"]

        class_name = self.class_info.get('class_name')
        if not class_name:
            sanitized_name = re.sub(r'\W+', '_', self.filename)  # \W matches anything not [a-zA-Z0-9_]
            class_name = '__GD__' + sanitized_name

        namespace = self.class_info.get("namespace")
        if namespace:
            uml.append(f'package "{namespace}" #DDDDDD {{')

        uml.append(self._generate_class_block(class_name))

        if namespace:
            uml.append("}")

        if self.class_info.get('extends'):
            uml.append(self._generate_inheritance(class_name))

        uml.extend(self._generate_associations(class_name))

        uml.append("@enduml")
        return "\n".join(uml)

    def _generate_class_block(self, class_name):
        lines = [f'class {class_name} {{']
        lines.extend(self._generate_properties())
        lines.extend(self._generate_methods())
        lines.extend(self._generate_signals())
        lines.append('}')
        return "\n".join(lines)

    def _generate_properties(self):
        lines = []
        for var, var_type in self.class_info.get('properties', []):
            if var_type:
                lines.append(f'  +{var}: {var_type}')
            else:
                lines.append(f'  +{var}')
        return lines

    def _generate_methods(self):
        lines = []
        for method in self.class_info.get('methods', []):
            method_name = method['method']
            return_type = method.get('return', 'void')  # fallback to void if missing
            args = ", ".join(
                f"{arg}: {arg_type}" if arg_type else f"{arg}"
                for arg, arg_type in method.get('args', [])
            )
            if return_type != 'void':
                lines.append(f'  +{method_name}({args}): {return_type}')
            else:
                lines.append(f'  +{method_name}({args})')
        return lines

    def _generate_signals(self):
        lines = []
        for signal in self.class_info.get('signals', []):
            signal_name = signal['signal']
            args = ", ".join(
                f"{arg}: {arg_type}" if arg_type else f"{arg}"
                for arg, arg_type in signal.get('args', [])
            )
            lines.append(f'  +{signal_name}({args}) <<signal>>')
        return lines

    def _generate_inheritance(self, class_name):
        parent = self.class_info['extends']
        return f'{parent} <|-- {class_name}'

    def _generate_associations(self, class_name):
        associations = set()  # avoid duplicates

        # Check properties
        for var, var_type in self.class_info.get('properties', []):
            if not var_type:
                continue
            for known_class in self.class_names:
                if self._type_mentions_class(var_type, known_class):
                    associations.add(known_class)

        # Check method parameters
        for method in self.class_info.get('methods', []):
            for param_name, param_type in method.get('args', []):  # not 'args'
                for known_class in self.class_names:
                    if self._type_mentions_class(param_type, known_class):
                        associations.add(known_class)

        # Check signal arguments
        for signal in self.class_info.get('signals', []):
            for arg_name, arg_type in signal.get('args', []):
                for known_class in self.class_names:
                    if self._type_mentions_class(arg_type, known_class):
                        associations.add(known_class)


        # Generate UML lines
        return [
            f'{class_name} --> {assoc} : 1'
            for assoc in associations
        ]

    def process(self):
        """Extract class info and generate PlantUML, given a list of valid class names."""
        self.parse_script()
        return self.generate_plantuml()
