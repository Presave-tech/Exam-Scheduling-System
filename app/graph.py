"""
graph.py — Conflict Graph Construction & Greedy Graph Coloring Algorithm
=========================================================================
DAA Core Module

ALGORITHM: Greedy Graph Coloring (Welsh-Powell Heuristic)
TIME COMPLEXITY: O(V² + E)  where V = subjects, E = conflict edges

Steps:
  1. Build adjacency list from enrollment data
  2. Order vertices by degree (descending) — Welsh-Powell ordering
  3. Greedily assign the lowest available color to each vertex
     such that no two adjacent vertices share a color
  4. Return color assignment dict {subject_id: color}
"""


class ConflictGraph:
    """
    Represents the Subject Conflict Graph.

    Vertices : Subjects (identified by subject_id)
    Edges    : Exist between two subjects if they share ≥1 common student
    """

    def __init__(self):
        # adjacency list: {subject_id: set(conflicting_subject_ids)}
        self.adjacency = {}
        # vertex labels: {subject_id: subject_code+name}
        self.labels = {}

    # ------------------------------------------------------------------
    # Step 1 — Build graph from enrollment data
    # ------------------------------------------------------------------
    def build_from_enrollments(self, subjects, enrollments):
        """
        Constructs the conflict graph.

        :param subjects:    list of Subject ORM objects
        :param enrollments: list of Enrollment ORM objects
        """
        # Initialize all vertices (even isolated ones)
        for subj in subjects:
            self.adjacency[subj.id] = set()
            self.labels[subj.id] = f"{subj.code} — {subj.name}"

        # Group subjects by student: {student_id: [subject_id, ...]}
        student_subjects = {}
        for enr in enrollments:
            student_subjects.setdefault(enr.student_id, []).append(enr.subject_id)

        # Step 2 — Add edges between subjects sharing a student
        for sid, sub_list in student_subjects.items():
            for i in range(len(sub_list)):
                for j in range(i + 1, len(sub_list)):
                    u, v = sub_list[i], sub_list[j]
                    self.adjacency[u].add(v)
                    self.adjacency[v].add(u)

    # ------------------------------------------------------------------
    # Step 3 — Welsh-Powell vertex ordering (by degree, descending)
    # ------------------------------------------------------------------
    def get_ordered_vertices(self):
        """
        Returns vertices sorted by degree (number of conflicts) in
        descending order — higher-conflict subjects scheduled first.
        Time: O(V log V)
        """
        return sorted(self.adjacency.keys(),
                      key=lambda v: len(self.adjacency[v]),
                      reverse=True)

    # ------------------------------------------------------------------
    # Step 4 — Greedy Graph Coloring
    # ------------------------------------------------------------------
    def greedy_color(self):
        """
        Assigns colors (integer time-slot indices) to each vertex
        using the Greedy algorithm on Welsh-Powell ordered vertices.

        Returns:
            color_map  : {subject_id: color}   (0-indexed)
            steps_log  : list of step strings for UI display
            num_colors : total distinct colors used
        Time Complexity: O(V² + E) — for each vertex we scan neighbor colors
        """
        color_map = {}   # {subject_id: assigned_color}
        steps_log = []   # human-readable steps for UI

        ordered = self.get_ordered_vertices()
        steps_log.append(
            f"Step 1 — Vertex ordering (Welsh-Powell): {[self.labels.get(v, v) for v in ordered]}"
        )

        for vertex in ordered:
            # Collect colors already used by adjacent vertices
            neighbour_colors = {
                color_map[nb] for nb in self.adjacency[vertex] if nb in color_map
            }

            # Assign the smallest non-conflicting color (greedy choice)
            color = 0
            while color in neighbour_colors:
                color += 1

            color_map[vertex] = color
            steps_log.append(
                f"  Assign color {color} (Slot {color + 1}) → {self.labels.get(vertex, vertex)}"
                f"  [conflicts with colors: {sorted(neighbour_colors)}]"
            )

        num_colors = max(color_map.values(), default=-1) + 1
        steps_log.append(
            f"\nStep 2 — Coloring complete. Total time slots required: {num_colors}"
        )
        return color_map, steps_log, num_colors

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------
    def get_conflict_pairs(self):
        """
        Returns a list of (subject_id_A, subject_id_B) tuples
        representing all conflict edges in the graph.
        """
        seen = set()
        pairs = []
        for u, neighbours in self.adjacency.items():
            for v in neighbours:
                edge = tuple(sorted([u, v]))
                if edge not in seen:
                    seen.add(edge)
                    pairs.append(edge)
        return pairs

    def get_graph_data_json(self):
        """
        Returns a dict suitable for vis.js Network rendering:
          { nodes: [...], edges: [...] }
        (Used by the /api/graph-data route — Phase 2)
        """
        nodes = [
            {"id": vid, "label": lbl}
            for vid, lbl in self.labels.items()
        ]
        edges = [
            {"from": u, "to": v}
            for (u, v) in self.get_conflict_pairs()
        ]
        return {"nodes": nodes, "edges": edges}
