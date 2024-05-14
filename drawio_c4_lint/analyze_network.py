import os
import networkx as nx
from drawio_c4_lint.c4_lint import C4Lint

def extract_systems_and_connections(xml_file):
    lint = C4Lint(xml_file)
    systems = {elem.get('id'): elem.get('c4Name') for elem in lint.root.findall(".//object[@c4Type='Software System']")}
    connections = [(systems[elem.get('source')], systems[elem.get('target')]) for elem in lint.root.findall(".//mxCell[@source][@target]") if elem.get('source') in systems and elem.get('target') in systems]
    return systems.values(), connections

def analyze_network(directory):
    system_names = set()
    connections = []

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.drawio'):
                file_path = os.path.join(root, file)
                try:
                    lint = C4Lint(file_path)
                    if lint.is_c4():
                        systems, system_connections = extract_systems_and_connections(file_path)
                        system_names.update(systems)
                        connections.extend(system_connections)
                        print(f"File: {file}")
                        print(f"Systems: {list(systems)}\n")

                except Exception as e:
                    print(f"Failed to process {file_path}: {e}")

    graph = nx.Graph()
    graph.add_edges_from(connections)

    return graph, system_names, connections

if __name__ == "__main__":
    directory_path = 'C:\\Solutions\\Python\\drawio_c4_lint\\c4_github_examples'  # Update this path to your specific top level directory
    graph, system_names, connections = analyze_network(directory_path)
    print(f"Nodes (Systems): {len(graph.nodes)}")
    print(f"Edges (Connections): {len(graph.edges)}")
    if len(graph.nodes) == 0:
        print("No systems found.")
    elif len(graph.edges) == 0:
        print("No connections found.")
    else:
        print(f"Is the network connected? {nx.is_connected(graph)}")
        if not nx.is_connected(graph):
            print(f"Number of connected components: {nx.number_connected_components(graph)}")
            print("Systems in each connected component:")
            for component in nx.connected_components(graph):
                print(component)
