class ToolRegistry:
    def __init__(self):
        self._tools = {}
        self._loaded_tools = {}

    def register_tool(
        self, name, loader_func, description, parameters=None, dependencies=None
    ):
        if name in self._tools:
            raise ValueError(f"tool '{name}' already exists")
        if not description:
            raise ValueError(f"tool '{name}' needs a description")

        self._tools[name] = {
            "loader": loader_func,
            "description": description,
            "parameters": parameters or {},
            "dependencies": dependencies or [],
            "loaded": False,
        }

    def get_tool(self, name):
        if name not in self._tools:
            raise KeyError(f"tool '{name}' not found")

        if name in self._loaded_tools:
            return self._loaded_tools[name]

        tool_info = self._tools[name]
        tool = tool_info["loader"]()
        self._loaded_tools[name] = tool
        tool_info["loaded"] = True
        return tool

    def get_tool_specs(self):
        specs = []
        for name, info in self._tools.items():
            specs.append(
                {
                    "name": name,
                    "description": info["description"],
                    "parameters": info["parameters"],
                }
            )
        return specs

    def get_registered_tools(self):
        return list(self._tools.keys())
