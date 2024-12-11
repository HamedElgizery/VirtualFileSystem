# TODO: better to use tree down here but for now we just make it for the ids
# class TreeNode:
#     def __init__(self, name: str, is_directory: bool, metadata=None):
#         # self.name = name
#         # self.is_directory = is_directory
#         # self.metadata = metadata  # Store additional data (e.g., FileIndexNode)
#         # self.children = {}  # Dictionary for fast lookup of children by name

#     def add_child(self, child):
#         if child.name in self.children:
#             raise ValueError(f"Child with name '{child.name}' already exists.")
#         self.children[child.name] = child

#     def remove_child(self, name: str):
#         if name not in self.children:
#             raise Val ueError(f"Child with name '{name}' does not exist.")
#         del self.children[name]

#     def get_child(self, name: str):
#         return self.children.get(name, None)
